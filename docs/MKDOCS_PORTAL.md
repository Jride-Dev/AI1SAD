# MkDocs Portal

AI1SAD uses MkDocs Material for the public documentation portal.

## Run Locally

Install documentation dependencies in your Python environment, then serve the site:

```powershell
pip install mkdocs mkdocs-material
mkdocs serve
```

The local server usually starts at:

```text
http://127.0.0.1:8000
```

## Build

Generate the static site with:

```powershell
mkdocs build
```

MkDocs writes the generated site to `site/`.

## GitHub Pages

For a GitHub Pages deployment, build from the repository docs configuration or use:

```powershell
mkdocs gh-deploy
```

Use GitHub Actions or manual deployment depending on the repository settings.

## Why `site/` Is Ignored

`site/` is generated output. It can be rebuilt from `mkdocs.yml` and the files under `docs/`, so it should not be committed to the source branch.

Keeping `site/` ignored prevents local builds from adding generated HTML, CSS, JavaScript, search indexes, and asset copies to normal feature commits.

For deployment readiness details, see [Deployment Readiness](DEPLOYMENT_READINESS.md).
