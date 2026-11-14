# Documentation

The site uses Zensical's modern theme with light and dark palettes, code-copy
buttons, tabs, callouts, Mermaid diagrams and a Python API reference.
The configuration and styles are included in this repository. No sibling checkout
or separate theme package is needed.

## Preview and build

Activate the project environment, then run:

```sh
zensical serve
zensical build --strict
```

The preview command prints a local URL. Generated files go into `site/`, which
is excluded from Git.

## Adapt the template

1. Update the package name and metadata in `pyproject.toml`, then regenerate `uv.lock`.
2. Update `site_name`, `site_description`, `site_url`, `repo_url`, `repo_name` and
   `copyright` in `zensical.toml`.
3. Update the clone command and project links in the README and installation page.
4. Replace the placeholder pages and update the navigation in `zensical.toml`.
5. Point the API reference at your renamed Python modules.
6. In your GitHub repository, open **Settings → Pages** and choose **GitHub Actions**
   as the source. Enable Actions if your repository has them disabled.

The included CI workflow checks tests, formatting and a strict documentation build.
The Documentation workflow deploys from `main` after its checks pass. It can also
be started manually. Pull requests do not deploy the site. No PyPI release is needed.

## Tabs and callouts

Use `=== "uv"` and `=== "pip"` with indented content for tabs, as on the
installation page. Use `!!! note "Title"` with indented content for a callout.

The copied `stylesheets/diagrams.css` defines light and dark diagram colors.
Custom Mermaid block diagrams can use `fill:var(--jb-node-bg)`,
`stroke:var(--jb-node-border)` and `color:var(--jb-diagram-text)` in their styles.
