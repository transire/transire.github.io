# Transire Documentation

Official documentation site for [Transire](https://github.com/transire/transire) - a cloud-agnostic Go framework for building production APIs.

## 🚀 Live Site

[https://transire.github.io](https://transire.github.io)

## 📖 About

This repository contains the complete documentation for Transire, built with [MkDocs](https://www.mkdocs.org/) and the [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme.

## 🏗️ Structure

```
docs/
├── index.md                    # Home page
├── getting-started/            # Getting Started guides
│   ├── quickstart.md          # 5-minute quickstart
│   ├── installation.md        # Installation guide
│   └── your-first-api.md      # First API tutorial
├── core-concepts/              # Core concepts
│   ├── application-runtime.md # App & Runtime
│   ├── http-handlers.md       # HTTP routing
│   ├── queue-handlers.md      # Queue processing
│   ├── schedule-handlers.md   # Scheduled tasks
│   └── configuration.md       # Configuration overview
├── guides/                     # Detailed guides
│   ├── local-development.md   # Local dev best practices
│   ├── deploying-to-aws.md    # AWS deployment
│   ├── testing.md             # Testing strategies
│   ├── queue-processing.md    # Queue patterns
│   ├── multi-function-architecture.md
│   ├── custom-cdk.md          # CDK customization
│   ├── database-integration.md
│   └── observability.md       # Monitoring & logging
├── configuration/              # Configuration reference
│   ├── transire-yaml.md       # Complete config reference
│   ├── lambda.md              # Lambda settings
│   ├── queues.md              # Queue configuration
│   ├── schedules.md           # Schedule configuration
│   ├── vpc.md                 # VPC networking
│   ├── existing-resources.md  # Using existing AWS resources
│   └── environment-variables.md
├── cli-reference/              # CLI command reference
│   ├── transire-init.md       # transire init
│   ├── transire-run.md        # transire run
│   ├── transire-build.md      # transire build
│   ├── transire-deploy.md     # transire deploy
│   └── transire-version.md    # transire version
├── api-reference/              # API documentation
│   ├── transire.md            # Main package API
│   ├── interfaces.md          # Handler interfaces
│   ├── config.md              # Config types
│   ├── runtime.md             # Runtime API
│   └── testing-utilities.md   # Testing helpers
├── examples/                   # Example walkthroughs
│   ├── simple-api.md          # Simple API example
│   ├── ecommerce-api.md       # E-commerce example
│   └── microservices.md       # Microservices example
├── faq.md                      # FAQ
└── contributing.md             # Contributing guide
```

## 🛠️ Local Development

### Prerequisites

- Python 3.8+
- pip or pipx

### Install Dependencies

```bash
pip install mkdocs-material
```

Or with pipx:

```bash
pipx install mkdocs-material
```

### Run Local Server

```bash
mkdocs serve
```

Visit [http://localhost:8000](http://localhost:8000) to preview the site.

### Build Static Site

```bash
mkdocs build
```

This generates static HTML in the `site/` directory.

## 🧪 Quality Checks

### Pre-commit Hooks

Install local pre-commit hooks to catch issues before pushing:

```bash
./scripts/install-hooks.sh
```

This installs hooks that run:
- YAML linting (mkdocs.yml)
- Documentation build in strict mode
- Broken internal link detection
- TODO/FIXME comment scanning
- Build artifact validation

### Continuous Integration

All pull requests and pushes to `main` automatically run:
- YAML linting
- Strict documentation build
- Link validation
- Build artifact checks

See `.github/workflows/ci.yml` for details.

## 🚢 Deployment

### GitHub Pages (Automatic)

This site is configured for automatic deployment to GitHub Pages. On every push to `main`:

1. GitHub Actions runs CI checks
2. Builds the site
3. Deploys to `gh-pages` branch
4. Available at https://transire.github.io

See `.github/workflows/deploy-docs.yml` for deployment configuration.

### Manual Deployment

```bash
mkdocs gh-deploy
```

This builds and pushes to the `gh-pages` branch.

## 📝 Content Status

### ✅ Phase 1 Complete (Critical Pages)

- [x] Home page with overview and quick example
- [x] Quickstart guide (5-minute tutorial)
- [x] Core Concepts: Application & Runtime
- [x] Core Concepts: Queue Handlers (complete with examples)
- [x] CLI Reference: transire run

### 🚧 Phase 2+ (Under Construction)

Most other pages are stubs with basic outlines. See `DOCS_IMPLEMENTATION_SUMMARY.md` in the main repository for the complete implementation roadmap.

## 🤝 Contributing

Found a typo? Want to improve the docs? Contributions are welcome!

1. Fork this repository
2. Make your changes
3. Test locally with `mkdocs serve`
4. Submit a pull request

See [Contributing Guide](docs/contributing.md) for more details.

## 📚 Documentation Philosophy

All documentation is:

- **Fact-grounded**: Every technical claim is cited with source file paths
- **Example-driven**: Real code examples from the `transire/transire` repository
- **Practical**: Focused on getting things done
- **Complete**: From quickstart to production deployment

## 🔗 Links

- **Main Repository**: [transire/transire](https://github.com/transire/transire)
- **Documentation Design**: See `DOCS_DESIGN.md` in the main repository
- **Issues**: [GitHub Issues](https://github.com/transire/transire/issues)
- **Discussions**: [GitHub Discussions](https://github.com/transire/transire/discussions)

## 📄 License

Documentation is licensed under [MIT License](LICENSE).

---

**Built with** [MkDocs](https://www.mkdocs.org/) and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
