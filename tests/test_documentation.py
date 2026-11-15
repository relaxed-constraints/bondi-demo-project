"""Check inherited capabilities and the demo's deployment policy."""

from pathlib import Path

import pytest

config_module = pytest.importorskip("zensical.config")
ROOT = Path(__file__).resolve().parents[1]


def test_shared_defaults_keep_project_specific_features():
    cli = pytest.importorskip("relcon_docs.cli")
    assert cli.main(["configure", "--project", str(ROOT), "--check"]) == 0
    config = config_module.parse_config(str(ROOT / "mkdocs.yml"))
    tutorials = next(item["children"] for item in config["nav"] if item["title"] == "Tutorials")
    assert [item["url"] for item in tutorials] == [
        "1_general.md",
        "2_preparation.md",
        "3_workload.md",
        "4_benchmark.md",
        "5_analysis.md",
    ]
    assert [script["path"] for script in config["extra_javascript"]] == [
        "javascripts/relcon-docs-math.js"
    ]
    assert "admonition" in config["markdown_extensions"]
    assert "pymdownx.details" in config["markdown_extensions"]
    fences = config["mdx_configs"]["pymdownx.superfences"]["custom_fences"]
    assert any(fence["name"] == "mermaid" for fence in fences)
    python = config["plugins"]["mkdocstrings"]["config"]["handlers"]["python"]
    assert python["paths"] == ["src"]
    assert python["options"]["show_root_heading"] is True
    assert python["options"]["heading_level"] == 2
    assert python["options"]["signature_crossrefs"] is True
    assert "content.action.copy" in config["theme"]["features"]
    assert config["extra_css"] == ["stylesheets/relcon-docs.css"]
    assert not (ROOT / "docs/stylesheets/diagrams.css").exists()
    assert config["plugins"]["llmstxt"]["config"]["enabled"] is True


def test_deployment_keeps_main_and_manual_triggers_after_checks():
    yaml = pytest.importorskip("yaml")
    workflow = yaml.load((ROOT / ".github/workflows/docs.yml").read_text(), Loader=yaml.BaseLoader)
    assert workflow["on"] == {"workflow_dispatch": "", "push": {"branches": ["main"]}}
    assert workflow["jobs"]["docs"]["needs"] == "checks"
    assert not (ROOT / ".github/workflows/pages.yml").exists()
