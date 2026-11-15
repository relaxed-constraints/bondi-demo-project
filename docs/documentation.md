# Documentation

The site uses Zensical's modern theme with light and dark palettes, code-copy
buttons, tabs, callouts, Mermaid diagrams and a Python API reference.
Shared defaults and copy-button styling come from
[relcon-docs](https://github.com/relaxed-constraints/relcon-docs), installed through
the `docs` dependency group at a pinned Git commit. No sibling checkout is needed.
Project-specific configuration lives in `mkdocs.yml`, including navigation,
Mermaid support and API headings.

Shared relcon-docs defaults automatically export `llms.txt` and a Markdown version of each page, available through
the copy-as-Markdown button.

## Preview and build

Install the docs group, then activate the project environment:

```sh
uv sync --locked --group docs
source .venv/bin/activate
```

With pip, use `python -m pip install --group docs` in the active environment.
Git is required to install the pinned dependency. Then run:

```sh
zensical serve
zensical build --strict
```

The preview command prints a local URL. Generated files go into `site/`, which
is excluded from Git.

## Adapt the template

1. Update the package name and metadata in `pyproject.toml`, then regenerate `uv.lock`.
2. Update `site_name`, `site_description`, `site_url`, `repo_url`, `repo_name` and
   `copyright` in `mkdocs.yml`.
3. Update the clone command and project links in the README and installation page.
4. Replace the placeholder pages and update the navigation in `mkdocs.yml`.
5. Point the API reference at your renamed Python modules.
6. Follow [Publish under your own repository](#publish-under-your-own-repository)
   to enable GitHub Pages.

The included CI workflow checks tests, formatting and a strict documentation build.
The Documentation workflow deploys from `main` after its checks pass. It can also
be started manually. Pull requests do not deploy the site. No PyPI release is needed.

## Publish under your own repository

Each repository can have its own GitHub Pages site. For example, the repository
`alice/index-advisor` publishes at `https://alice.github.io/index-advisor/`.
An organisation name works in place of the username. You do not need a separate
`alice.github.io` repository for a project site.

### Connect your repository

Create an empty repository on GitHub under your own account or organisation.
If you have not already disconnected the starter remote, run:

```sh
git remote remove origin
```

Then add your own remote. Replace `alice` and `index-advisor` with your account
and repository names:

```sh
git remote add origin https://github.com/alice/index-advisor.git
git remote -v
```

Check that both displayed URLs point to your repository before pushing.

### Update the site settings

Edit these top-level fields in `mkdocs.yml`:

```yaml
site_name: Index Advisor
site_url: https://alice.github.io/index-advisor/
repo_url: https://github.com/alice/index-advisor
repo_name: alice/index-advisor
```

Keep the repository name in `site_url` and include the trailing slash.
Changing the Git remote does not update these documentation settings.

### Enable Pages and deploy

1. In your GitHub repository, open **Settings → Pages**.
2. Under **Build and deployment**, select **GitHub Actions** as the source.
3. Enable GitHub Actions if it is disabled for your repository.
4. Commit your changes and push the `main` branch:

   ```sh
   git add mkdocs.yml
   git commit -m "Configure documentation for my project"
   git push -u origin main
   ```

5. Open the repository's **Actions** tab and select the **Documentation** run.
   Wait for the checks, build and deployment jobs to finish successfully.
6. Open the published URL shown in **Settings → Pages**. In this example, it is
   `https://alice.github.io/index-advisor/`.

Later pushes to `main` update the site automatically. You can also select
**Actions → Documentation → Run workflow** and choose `main` to deploy manually.
Pull requests run checks without publishing. If checks fail, fix the reported
problem and push again; the previous published site stays available.

The workflow deploys to the repository in which it runs. It does not publish to
the starter project's site. No separate hosting account or PyPI release is needed.
GitHub Free supports Pages for public repositories; private repositories need a
plan that supports Pages. See the [GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

## Shared defaults and upgrades

`.relcon-docs/base.yml`, `.relcon-docs/state.json` and
`docs/stylesheets/relcon-docs.css` and `docs/javascripts/relcon-docs-math.js`
are managed files. Keep them committed and put
customizations in `mkdocs.yml` or a separate stylesheet. YAML mappings merge;
lists replace inherited lists. The shared stylesheet includes diagram colours;
no local `extra_css` override is required.

To upgrade, update the relcon-docs commit in `pyproject.toml`, run `uv lock`
and `uv sync --locked --group docs`, then review and apply:

```sh
relcon-docs configure --dry-run
relcon-docs configure
relcon-docs configure --check
zensical build --strict
```

Manual edits to managed files cause conflicts. Review them before using
`--force` to replace package-owned files. Existing `mkdocs.yml` and
`.github/workflows/docs.yml` files are never overwritten, even with force.

The project-owned `docs.yml` calls the reusable deployment workflow at a pinned
commit, after the project's CI checks succeed. Its triggers remain pushes to
`main` and manual runs. Update this workflow pin separately when adopting new
deployment tooling. To publish only releases instead, replace the `push` trigger:

```yaml
on:
  workflow_dispatch:
  release:
    types: [published]
```

For release deployment, allow release tags in the `github-pages` environment's
deployment protection rules.

## Tabs and callouts

Use `=== "uv"` and `=== "pip"` with indented content for tabs, as on the
installation page. Use `!!! note "Title"` with indented content for a callout.

Shared relcon-docs styling supplies light and dark diagram colours.
Custom Mermaid block diagrams can use `fill:var(--relcon-diagram-node-bg)`,
`stroke:var(--relcon-diagram-node-border)` and `color:var(--relcon-diagram-text)`.
Standard flowcharts inherit colours without inline styling.

## Shared authoring features

Callouts (`!!! note`), collapsible notes (`??? tip`) and Mermaid fenced blocks
are enabled by relcon-docs. No project-level Markdown extension settings are
needed for them. Light/dark diagram colours also come from the shared stylesheet.
See the [diagram examples](https://relaxed-constraints.github.io/relcon-docs/diagrams/).

Inline (`$...$`) and display (`$$...$$`) equations are supported by the shared
math configuration and managed `docs/javascripts/relcon-docs-math.js` loader.
The loader fetches MathJax from jsDelivr only on pages containing equations.
The shared stylesheet also supplies dark-mode copy controls and diagram accent
colours; see the [shared feature examples](https://relaxed-constraints.github.io/relcon-docs/).
