# Transire docs

MkDocs site for the Transire Go framework, published to https://transire.github.io.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

`./scripts/ci.sh` wraps this and runs `mkdocs build --strict` inside `.venv`. A pre-commit hook at `.githooks/pre-commit` runs the same checks; enable it with:

```bash
git config core.hooksPath .githooks
```

## CI/CD

- GitHub Actions workflow `.github/workflows/docs.yml` runs the docs build on every PR and push.
- On merges to `main`, the workflow deploys with `mkdocs gh-deploy`.
- Branch protection on `main` requires an approved PR and the `Docs / Build docs` check to pass.

## Content structure

- `docs/` holds Markdown content with SEO-friendly front matter.
- `mkdocs.yml` configures navigation, Material theme, and metadata.
- `styles/extra.css` customizes the landing hero and typography.
- `site/` is the built output; kept in the repo for GitHub Pages compatibility with `gh-pages` via `mkdocs gh-deploy`.

## Contributing

- Open a PR targeting `main`; direct pushes and force pushes are blocked.
- Ensure `./scripts/ci.sh` passes locally before pushing.
