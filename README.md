# Transire Documentation

User-facing documentation for the Transire cloud-native development framework.

## What is Transire?

Transire is a cloud-native development framework for Go that lets you write your application once and run it anywhere—locally or in the cloud. No serverless complexity. No infrastructure boilerplate. Just code.

## Documentation

The documentation is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) and deployed to GitHub Pages.

**Live documentation:** [docs.transire.dev](https://docs.transire.dev) (when deployed)

## Local Development

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Serve documentation locally
mkdocs serve

# Build static site
mkdocs build
```

The documentation will be available at `http://localhost:8000`.

### Hot Reload

MkDocs automatically watches for changes and rebuilds the site. Just edit any file in `docs/` and refresh your browser.

## Documentation Structure

```
docs/
├── index.md                 # Landing page
├── intro/                   # Introduction to Transire
├── getting-started/         # Installation and quick start
├── sdk/                     # Go SDK reference
├── cli/                     # CLI command reference
├── cloud/                   # Cloud provider documentation
├── iac/                     # Infrastructure as Code documentation
├── ci/                      # CI/CD documentation
├── guides/                  # How-to guides
├── examples/                # Complete example applications
├── reference/               # Technical reference (config, errors)
└── community/               # FAQ, contributing, changelog
```

## Writing Guidelines

### Target Audience

Transire's users are **developers**. Write documentation that:

- Shows code examples first, explanations second
- Uses realistic scenarios (orders, users, payments) instead of foo/bar
- Provides complete, runnable code with all imports
- Walks users through the full flow with just enough guidance
- Assumes developer competence but provides clear explanations

### Voice and Tone

- **Active voice:** "Deploy your app" not "Your app can be deployed"
- **Second person:** "You configure" not "One configures"
- **Present tense:** "Transire uses" not "Transire will use"
- **Direct:** "Do X" not "You might want to consider doing X"
- **Confident but not arrogant**
- **Helpful but not condescending**

### Document Structure

Every documentation page should include:

```markdown
---
title: [Page Title]
description: [Brief description]
---

# [Page Title]

## Overview
[1-2 paragraphs: What is this? Why does it matter?]

## [Main Content]
[Progressive disclosure: simple → complex]

## See Also
- [Related Doc 1](/path/to/doc)
- [Related Doc 2](/path/to/doc)
```

### Code Examples

All code examples must be:

- ✅ **Complete** - All imports, no missing context
- ✅ **Runnable** - Copy-paste should work
- ✅ **Realistic** - Real-world names, not foo/bar
- ✅ **Commented** - Explain non-obvious parts
- ✅ **Idiomatic** - Follow Go conventions

## Deployment

Documentation is automatically deployed to GitHub Pages when changes are pushed to `main`.

The deployment is handled by `.github/workflows/deploy-docs.yml`.

## Contributing

### Adding New Pages

1. Create a new markdown file in the appropriate `docs/` subdirectory
2. Add frontmatter with title and description
3. Add the page to `nav` section in `mkdocs.yml`
4. Follow the writing guidelines above

### Updating Existing Pages

1. Edit the markdown file
2. Test locally with `mkdocs serve`
3. Commit and push changes

### Reporting Issues

If you find errors or have suggestions for improving the documentation:

1. Open an issue in the main [transire/transire](https://github.com/transire/transire) repository
2. Use the "documentation" label
3. Be specific about what needs improvement

## License

Documentation is licensed under [MIT License](LICENSE).

## Questions?

- **Documentation issues:** Open an issue in [transire/transire](https://github.com/transire/transire)
- **General questions:** See [FAQ](docs/community/faq.md)
- **Contributing:** See [Contributing Guide](docs/community/contributing.md)
