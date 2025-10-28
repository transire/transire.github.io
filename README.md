# transire/docs

**Transire Documentation** - User-facing documentation, guides, examples, and API reference for the Transire framework.

## Repository Responsibility

This repository contains all user-facing documentation:
- Getting started guides
- API reference (per language SDK)
- Architectural guides (local vs cloud parity, performance, etc.)
- Best practices and patterns (idempotency, testing, middleware, etc.)
- Example applications (complete working apps)
- Troubleshooting guides
- Migration guides (from other frameworks)
- Compatibility matrices

## Functional Requirements

### FR-DOCS-1: Getting Started

#### FR-DOCS-1.1: Quick Start Guide
- **Requirement**: Guide users from zero to deployed app in < 15 minutes
- **Location**: `/docs/getting-started/quickstart.md`
- **Contents**:
  - Prerequisites (Go, AWS account, GitHub account)
  - Install transire CLI
  - Create new project (`transire init` or manual setup)
  - Write first HTTP handler
  - Run locally (`transire run`)
  - Deploy to AWS (`transire deploy`)
- **Source**: REQUIREMENTS_MAPPING Part 4.3

#### FR-DOCS-1.2: Installation Guide
- **Requirement**: Detailed installation instructions for all platforms
- **Location**: `/docs/getting-started/installation.md`
- **Contents**:
  - Install via Homebrew (macOS/Linux)
  - Install via download (Windows, Linux, macOS)
  - Install from source (`go install`)
  - Verify installation (`transire --version`)
- **Source**: REQUIREMENTS_MAPPING Part 4.3

#### FR-DOCS-1.3: Project Setup
- **Requirement**: Guide for setting up new Transire project
- **Location**: `/docs/getting-started/project-setup.md`
- **Contents**:
  - Directory structure
  - `go.mod` setup
  - `transire.yaml` configuration
  - `main.go` boilerplate
  - Running `transire gen` for first time
- **Source**: REQUIREMENTS_MAPPING Part 4.3

### FR-DOCS-2: API Reference

#### FR-DOCS-2.1: Go SDK API Reference
- **Requirement**: Complete API documentation for Go SDK
- **Location**: `/docs/reference/go-sdk/`
- **Structure**:
  - `/handlers.md` - Get, Post, Queue, Scheduled, Run
  - `/http.md` - HTTPRequest, HTTPResponse, helpers
  - `/queue.md` - Enqueue, EnqueueBatch, BatchResult
  - `/di.md` - Provide, ProvideRequest, Get, MustGet
  - `/middleware.md` - Use, Group
  - `/errors.md` - HTTPError
  - `/observability.md` - Logger, Tracer, Meter
  - `/testkit.md` - Testing API
- **Format**: Godoc-style with examples
- **Source**: HLD §1, §3, §8, §9, REQUIREMENTS_MAPPING Part 4.3

#### FR-DOCS-2.2: CLI Reference
- **Requirement**: Complete CLI command documentation
- **Location**: `/docs/reference/cli.md`
- **Contents**:
  - `transire gen` - Flags, behavior, error codes
  - `transire run` - Flags (--watch), behavior
  - `transire deploy` - Flags (--env, --dry-run), behavior
  - `transire init --backend` - Backend bootstrap
  - `transire --version`, `transire --help`
- **Source**: HLD §21, REQUIREMENTS_MAPPING §20

#### FR-DOCS-2.3: Config Schema Reference
- **Requirement**: Complete `transire.yaml` schema documentation
- **Location**: `/docs/reference/config-schema.md`
- **Contents**:
  - All fields with types, defaults, examples
  - `service`, `runtime`, `cloud`, `ci`, `timezone`
  - `deploy` (arch, memory_mb, timeout_s)
  - `http` (simulate_apigw_limits, cors, rate_limit)
  - `queues` (batch size, window, visibility, retries, error_mode)
  - `scheduled` (timezone inheritance)
  - `observability` (logging, tracing)
  - `infra` (backend, vpc, route53, tags)
  - `env` (per-environment variables)
- **Source**: HLD §7.1, REQUIREMENTS_MAPPING §7.1

#### FR-DOCS-2.4: Manifest Schema Reference
- **Requirement**: Document `transire_manifest.json` schema
- **Location**: `/docs/reference/manifest-schema.md`
- **Contents**:
  - Top-level fields
  - Routes (Chi-native paths, path params)
  - Queues (message type, serialization)
  - Schedules (resolved expressions, timezone)
  - IAM intents
  - Packaging metadata
- **Audience**: Provider implementers, advanced users
- **Source**: HLD §23, REQUIREMENTS_MAPPING §2.2

#### FR-DOCS-2.5: Error Code Reference
- **Requirement**: Document all error codes (E1001-E1007)
- **Location**: `/docs/reference/error-codes.md`
- **Contents**:
  - E1001: Handler Not A Function
  - E1002: Invalid Handler Signature
  - E1003: Duplicate HTTP Route
  - E1004: Duplicate Queue Key
  - E1005: Type Inference Failed
  - E1006: Duplicate Path Parameter
  - E1007: Greedy Parameter Not Last
  - Each with description, cause, resolution
- **Source**: HLD §2.2, REQUIREMENTS_MAPPING §2.2

### FR-DOCS-3: Architectural Guides

#### FR-DOCS-3.1: Local vs Cloud Parity Guide
- **Requirement**: Document parity guarantees and known differences
- **Location**: `/docs/guides/local-vs-cloud.md`
- **Contents**:
  - Philosophy: local is for development, cloud is source of truth
  - Parity guarantees (routing, error handling, type validation, message format)
  - Known differences (concurrency, timeouts, scheduler, queues, VPC)
  - When to test locally vs in cloud
- **Source**: HLD §6, REQUIREMENTS_MAPPING §6, Part 4.3

#### FR-DOCS-3.2: Performance & Cold Start Guide
- **Requirement**: Best practices for optimizing Lambda performance
- **Location**: `/docs/guides/performance.md`
- **Contents**:
  - Cold start basics
  - DI initialization guidance (< 5s)
  - Logging init times in `Provide()`
  - ARM64 vs x86_64 performance
  - Memory sizing guidance
  - Timeout tuning
  - SnapStart (future, out of MVP)
- **Source**: HLD §14, REQUIREMENTS_MAPPING §14, Part 4.3

#### FR-DOCS-3.3: Cost Optimization Guide
- **Requirement**: Guide for minimizing AWS costs
- **Location**: `/docs/guides/cost-optimization.md`
- **Contents**:
  - Default architecture choices (ARM64, 256MB, 30s timeout)
  - HTTP mono-Lambda rationale
  - Batch queue processing
  - VPC cost considerations (NAT Gateway)
  - Provisioned Concurrency (when to use)
  - Cost estimation tools
- **Source**: HLD §14, §20, REQUIREMENTS_MAPPING §14

#### FR-DOCS-3.4: Deployment Guide
- **Requirement**: End-to-end deployment instructions
- **Location**: `/docs/guides/deployment.md`
- **Contents**:
  - AWS credentials setup (OIDC, IAM user)
  - Backend bootstrap (`transire init --backend`)
  - Running `transire deploy`
  - Deployment failure handling (manual intervention)
  - Rollback strategies (manual in MVP)
  - Multi-environment deployment (dev, staging, prod)
  - CI/CD integration (GitHub Actions)
- **Source**: HLD §13, REQUIREMENTS_MAPPING §13, Part 4.3

#### FR-DOCS-3.5: Environments Guide
- **Requirement**: Guide for managing multiple environments
- **Location**: `/docs/guides/environments.md`
- **Contents**:
  - `env` config in `transire.yaml`
  - Tofu workspaces (dev, prod)
  - Environment-specific variables
  - Secrets per environment
  - GitHub environments (protection rules)
  - Promotion strategies (dev → staging → prod)
- **Source**: HLD §7, REQUIREMENTS_MAPPING §7, Part 4.3

#### FR-DOCS-3.6: API Gateway Guide
- **Requirement**: Advanced API Gateway usage (authorizers, custom domains, etc.)
- **Location**: `/docs/guides/api-gateway.md`
- **Contents**:
  - HTTP API v2 overview
  - $default route behavior
  - API Gateway limits (6MB payload, throttling)
  - Custom authorizers (JWT, Lambda, IAM) via override
  - Custom domains + SSL (Route53, ACM)
  - Rate limiting config
  - CORS config
- **Source**: HLD §17, REQUIREMENTS_MAPPING §17, Part 4.3

### FR-DOCS-4: Best Practices & Patterns

#### FR-DOCS-4.1: Idempotency Guide
- **Requirement**: Patterns for writing idempotent handlers
- **Location**: `/docs/guides/idempotency.md`
- **Contents**:
  - Standard SQS realities (at-least-once, unordered)
  - Idempotency patterns:
    - Content-derived keys
    - Upsert-style updates
    - Processed-key stores (e.g., DynamoDB)
  - Example: order processing with deduplication
  - Outbox pattern (future)
- **Source**: HLD §18, REQUIREMENTS_MAPPING §18, Part 4.3

#### FR-DOCS-4.2: Testing Guide
- **Requirement**: Comprehensive testing strategies
- **Location**: `/docs/guides/testing.md`
- **Contents**:
  - Unit tests (handler logic)
  - Integration tests (testkit: full app, HTTP, queue, schedule)
  - Middleware testing (isolation)
  - Mocking Enqueue
  - DI overrides for tests
  - Parity tests (local vs cloud)
  - E2E tests (deploy to test AWS account)
- **Source**: HLD §8, REQUIREMENTS_MAPPING §8

#### FR-DOCS-4.3: DI Patterns Guide
- **Requirement**: Dependency injection best practices
- **Location**: `/docs/guides/di-patterns.md`
- **Contents**:
  - Singleton vs request-scoped
  - When to use each
  - DI side-effects (allowed: DB connections; disallowed: Enqueue at init)
  - Cleanup patterns
  - Error handling in providers
  - Testing with DI overrides
- **Source**: HLD §3, REQUIREMENTS_MAPPING §3

#### FR-DOCS-4.4: Middleware Patterns Guide
- **Requirement**: Middleware authoring best practices
- **Location**: `/docs/guides/middleware-patterns.md`
- **Contents**:
  - Built-in middleware (panic recovery, logging, tracing)
  - Config-based middleware (CORS, rate limiting)
  - Custom middleware examples (auth, request ID, logging)
  - Middleware execution order
  - HTTP-specific vs universal middleware
  - Grouping middleware (path prefixes)
- **Source**: HLD §9, REQUIREMENTS_MAPPING §9

#### FR-DOCS-4.5: Error Handling Patterns Guide
- **Requirement**: Error handling best practices
- **Location**: `/docs/guides/error-handling.md`
- **Contents**:
  - HTTPError vs generic error
  - Problem+JSON format
  - Queue batch errors (BatchResult vs whole-batch retry)
  - Panic recovery
  - Logging errors with trace_id
  - DLQ inspection and reprocessing
- **Source**: HLD §4, REQUIREMENTS_MAPPING §4

#### FR-DOCS-4.6: Observability Guide
- **Requirement**: Logging, tracing, metrics best practices
- **Location**: `/docs/guides/observability.md`
- **Contents**:
  - Structured logging (JSON to stdout)
  - trace_id in all logs
  - OTEL tracing (opt-in)
  - X-Ray integration
  - Trace propagation (HTTP → Queue)
  - Custom Logger/Tracer/Meter implementations
  - CloudWatch Logs Insights queries
- **Source**: HLD §4.3, REQUIREMENTS_MAPPING §4.3

### FR-DOCS-5: Example Applications

#### FR-DOCS-5.1: Complete Orders Example
- **Requirement**: Full working app with all handler types
- **Location**: `/examples/orders/`
- **Contents**:
  - `main.go` - HTTP, queue, scheduled handlers
  - `middleware.go` - Custom middleware (auth, logging)
  - `service.go` - OrderService (DI)
  - `transire.yaml` - Full config
  - `README.md` - Setup, run locally, deploy
  - Tests (`*_test.go`) - Unit, integration tests
- **Source**: HLD §19, REQUIREMENTS_MAPPING §19

#### FR-DOCS-5.2: Middleware Examples
- **Location**: `/examples/middleware/`
- **Examples**:
  - `auth.go` - JWT authentication middleware
  - `cors.go` - CORS middleware (if not using config-based)
  - `request_id.go` - Request ID injection
  - `rate_limit.go` - Custom rate limiting
- **Source**: HLD §17, REQUIREMENTS_MAPPING §17, Part 4.3

#### FR-DOCS-5.3: Secrets Integration Examples
- **Location**: `/examples/secrets/`
- **Examples**:
  - `aws-secrets-manager.go` - Fetch secrets from AWS Secrets Manager
  - `aws-ssm.go` - Fetch parameters from SSM Parameter Store
  - `env-vars.go` - Read from environment variables (CI secrets)
- **Source**: HLD §17, REQUIREMENTS_MAPPING §17, Part 4.3

#### FR-DOCS-5.4: Database Integration Examples
- **Location**: `/examples/databases/`
- **Examples**:
  - `postgres.go` - PostgreSQL connection via DI
  - `dynamodb.go` - DynamoDB client via DI
  - `redis.go` - Redis client via DI
- **Note**: DB/secrets are out of MVP scope but examples provided
- **Source**: HLD §3

#### FR-DOCS-5.5: Testing Examples
- **Location**: `/examples/testing/`
- **Examples**:
  - `http_test.go` - Testing HTTP handlers
  - `queue_test.go` - Testing queue handlers
  - `schedule_test.go` - Testing scheduled jobs
  - `middleware_test.go` - Testing middleware in isolation
  - `di_test.go` - Testing with DI overrides
- **Source**: HLD §8, REQUIREMENTS_MAPPING §8

### FR-DOCS-6: Troubleshooting

#### FR-DOCS-6.1: Troubleshooting Guide
- **Requirement**: Common issues and solutions
- **Location**: `/docs/guides/troubleshooting.md`
- **Contents**:
  - `transire gen` failures (error codes E1001-E1007)
  - `transire run` failures (port conflicts, config errors)
  - `transire deploy` failures (Tofu errors, AWS permissions)
  - Lambda errors (cold start timeouts, OOM)
  - Queue message stuck in DLQ (type mismatch, handler errors)
  - API Gateway 502 errors (Lambda timeout, panic)
  - CloudWatch Logs debugging
- **Source**: Part 4.3

#### FR-DOCS-6.2: FAQ
- **Requirement**: Frequently asked questions
- **Location**: `/docs/faq.md`
- **Contents**:
  - General (What is Transire? Why use it?)
  - Setup (How to install? Prerequisites?)
  - Development (How to test locally? Hot reload?)
  - Deployment (How to deploy? How to rollback?)
  - Cost (How much does it cost? How to optimize?)
  - Parity (What differs between local and cloud?)
- **Source**: Part 4.3

### FR-DOCS-7: Migration Guides

#### FR-DOCS-7.1: Migration from Lambda Direct
- **Requirement**: Guide for migrating existing Lambda + API Gateway apps
- **Location**: `/docs/guides/migration-from-lambda.md`
- **Contents**:
  - Compare Lambda handler → Transire handler
  - Compare API Gateway setup → transire.yaml
  - Compare IAM policies → generated IAM
  - Step-by-step migration
- **Source**: Part 4.3

#### FR-DOCS-7.2: Migration from Serverless Framework
- **Requirement**: Guide for migrating from Serverless Framework
- **Location**: `/docs/guides/migration-from-serverless.md`
- **Contents**:
  - Compare `serverless.yml` → `transire.yaml`
  - Compare handler registration → Transire API
  - Compare plugins → Transire providers
  - Step-by-step migration
- **Source**: Part 4.3

#### FR-DOCS-7.3: Migration from SAM
- **Requirement**: Guide for migrating from AWS SAM
- **Location**: `/docs/guides/migration-from-sam.md`
- **Contents**:
  - Compare `template.yaml` → `transire.yaml` + generated IaC
  - Compare handler code → Transire API
  - Step-by-step migration
- **Source**: Part 4.3

### FR-DOCS-8: Compatibility Matrices

#### FR-DOCS-8.1: SDK-CLI Compatibility Matrix
- **Requirement**: Document compatible SDK and CLI versions
- **Location**: `/docs/reference/compatibility.md`
- **Contents**:
  - CLI version → compatible SDK versions
  - CLI version → compatible provider versions
  - Breaking changes per major version
  - Deprecation timeline
- **Source**: REQUIREMENTS_MAPPING Part 4.5, NFR-14

#### FR-DOCS-8.2: Provider Compatibility Matrix
- **Requirement**: Document provider capabilities and requirements
- **Location**: `/docs/reference/compatibility.md`
- **Contents**:
  - Provider version → required CLI version
  - Provider features (which features supported by each provider)
  - Provider-specific limitations
- **Source**: REQUIREMENTS_MAPPING Part 4.6

### FR-DOCS-9: Contributing & Development

#### FR-DOCS-9.1: Contributing Guide
- **Requirement**: Guide for contributing to Transire
- **Location**: `/CONTRIBUTING.md`
- **Contents**:
  - Code of conduct
  - Development setup
  - Running tests
  - Submitting PRs
  - Coding standards
  - Repo structure
- **Source**: Standard OSS practice

#### FR-DOCS-9.2: Provider Development Guide
- **Requirement**: Guide for building custom providers
- **Location**: `/docs/development/provider-development.md`
- **Contents**:
  - CloudProvider interface
  - CIProvider interface
  - Manifest consumption
  - Config consumption
  - Testing (unit, integration, contract tests)
  - Example: building a GCP provider
- **Source**: HLD §16, REQUIREMENTS_MAPPING Part 4.6

#### FR-DOCS-9.3: Changelog
- **Requirement**: Version history and changes
- **Location**: `/CHANGELOG.md`
- **Contents**:
  - Per-version release notes
  - Breaking changes
  - New features
  - Bug fixes
  - Deprecations
- **Source**: Standard OSS practice

## Non-Functional Requirements

### NFR-DOCS-1: Clarity
- **Requirement**: Clear, concise, actionable documentation
- **Implementation**:
  - Step-by-step guides with code examples
  - Visual diagrams for architecture
  - Consistent formatting (Markdown, CommonMark)
- **Source**: REQUIREMENTS_MAPPING NFR-9

### NFR-DOCS-2: Completeness
- **Requirement**: Cover all functional requirements from HLD and mapping doc
- **Implementation**:
  - API reference for every public SDK function
  - Guide for every major feature
  - Example for every common use case
- **Source**: Part 7 (Validation Checklist)

### NFR-DOCS-3: Discoverability
- **Requirement**: Easy to find relevant docs
- **Implementation**:
  - Clear navigation structure
  - Search functionality (via docs framework)
  - Cross-references between related docs
  - Table of contents per page
- **Source**: REQUIREMENTS_MAPPING NFR-9

### NFR-DOCS-4: Maintainability
- **Requirement**: Easy to update as framework evolves
- **Implementation**:
  - Docs versioned alongside code (in same monorepo or tagged)
  - Automated link checking
  - Automated code example testing
- **Source**: REQUIREMENTS_MAPPING NFR-13

## Deliverables

### Phase 1: Getting Started
- [ ] Quick start guide
- [ ] Installation guide
- [ ] Project setup guide

### Phase 2: API Reference
- [ ] Go SDK API reference (handlers, http, queue, di, middleware, errors, observability, testkit)
- [ ] CLI reference
- [ ] Config schema reference
- [ ] Manifest schema reference
- [ ] Error code reference

### Phase 3: Architectural Guides
- [ ] Local vs cloud parity guide
- [ ] Performance & cold start guide
- [ ] Cost optimization guide
- [ ] Deployment guide
- [ ] Environments guide
- [ ] API Gateway guide

### Phase 4: Best Practices
- [ ] Idempotency guide
- [ ] Testing guide
- [ ] DI patterns guide
- [ ] Middleware patterns guide
- [ ] Error handling patterns guide
- [ ] Observability guide

### Phase 5: Examples
- [ ] Complete orders example
- [ ] Middleware examples (auth, CORS, request ID, rate limit)
- [ ] Secrets integration examples (Secrets Manager, SSM, env vars)
- [ ] Database integration examples (Postgres, DynamoDB, Redis)
- [ ] Testing examples

### Phase 6: Troubleshooting
- [ ] Troubleshooting guide
- [ ] FAQ

### Phase 7: Migration Guides
- [ ] Migration from Lambda Direct
- [ ] Migration from Serverless Framework
- [ ] Migration from SAM

### Phase 8: Compatibility
- [ ] SDK-CLI compatibility matrix
- [ ] Provider compatibility matrix

### Phase 9: Development
- [ ] Contributing guide
- [ ] Provider development guide
- [ ] Changelog

### Phase 10: Documentation Site
- [ ] Set up docs framework (MkDocs, Docusaurus, or similar)
- [ ] Deploy docs site (GitHub Pages, Netlify, or similar)
- [ ] Custom domain (docs.transire.dev or similar)
- [ ] Search functionality
- [ ] Version switcher (for docs versioning)

## Directory Structure

```
transire-docs/
├── docs/
│   ├── getting-started/
│   │   ├── quickstart.md
│   │   ├── installation.md
│   │   └── project-setup.md
│   ├── reference/
│   │   ├── go-sdk/
│   │   │   ├── handlers.md
│   │   │   ├── http.md
│   │   │   ├── queue.md
│   │   │   ├── di.md
│   │   │   ├── middleware.md
│   │   │   ├── errors.md
│   │   │   ├── observability.md
│   │   │   └── testkit.md
│   │   ├── cli.md
│   │   ├── config-schema.md
│   │   ├── manifest-schema.md
│   │   ├── error-codes.md
│   │   └── compatibility.md
│   ├── guides/
│   │   ├── local-vs-cloud.md
│   │   ├── performance.md
│   │   ├── cost-optimization.md
│   │   ├── deployment.md
│   │   ├── environments.md
│   │   ├── api-gateway.md
│   │   ├── idempotency.md
│   │   ├── testing.md
│   │   ├── di-patterns.md
│   │   ├── middleware-patterns.md
│   │   ├── error-handling.md
│   │   ├── observability.md
│   │   ├── troubleshooting.md
│   │   ├── migration-from-lambda.md
│   │   ├── migration-from-serverless.md
│   │   └── migration-from-sam.md
│   ├── development/
│   │   └── provider-development.md
│   └── faq.md
├── examples/
│   ├── orders/                    # Complete working app
│   │   ├── main.go
│   │   ├── middleware.go
│   │   ├── service.go
│   │   ├── transire.yaml
│   │   ├── README.md
│   │   └── *_test.go
│   ├── middleware/
│   │   ├── auth.go
│   │   ├── cors.go
│   │   ├── request_id.go
│   │   └── rate_limit.go
│   ├── secrets/
│   │   ├── aws-secrets-manager.go
│   │   ├── aws-ssm.go
│   │   └── env-vars.go
│   ├── databases/
│   │   ├── postgres.go
│   │   ├── dynamodb.go
│   │   └── redis.go
│   └── testing/
│       ├── http_test.go
│       ├── queue_test.go
│       ├── schedule_test.go
│       ├── middleware_test.go
│       └── di_test.go
├── CONTRIBUTING.md
├── CHANGELOG.md
├── mkdocs.yml                     # Or docusaurus.config.js, etc.
└── README.md                      # This file
```

## Documentation Framework

### Recommended: MkDocs (Material Theme)
- Static site generator for Markdown
- Beautiful, responsive theme
- Built-in search
- Version switcher support
- Easy deployment (GitHub Pages, Netlify)
- Python-based, simple setup

### Alternative: Docusaurus
- React-based documentation site
- MDX support (Markdown + JSX)
- Versioning built-in
- Algolia search integration
- More complex but more powerful

## Testing Strategy

### Automated Testing
- **Link checking**: Validate all internal/external links
- **Code example testing**: Run all code examples to ensure they work
- **Spelling/grammar**: Automated checks (e.g., Vale)

### Manual Review
- Peer review for new/updated docs
- User testing (ask users to follow guides and provide feedback)

## Cross-Repo Dependencies

### This Repo References
- `transire/sdk-go` - API reference, code examples
- `transire/cli` - CLI reference, error codes
- `transire/cloud-aws` - AWS-specific guides (Lambda, API Gateway, SQS, IAM)
- `transire/ci-github` - GitHub Actions workflow examples

### Other Repos Reference This Repo
- All repos link to docs site in README

## Build & Release

### Build Docs Site
```bash
# MkDocs
pip install mkdocs-material
mkdocs build

# Docusaurus
npm install
npm run build
```

### Serve Locally
```bash
# MkDocs
mkdocs serve

# Docusaurus
npm run start
```

### Deploy
```bash
# GitHub Pages (MkDocs)
mkdocs gh-deploy

# Netlify (any framework)
# Push to main → auto-deploy via Netlify hook
```

## Versioning

- Docs versioned alongside code (same repo or tagged)
- Version switcher on docs site
- Latest version = current main branch
- Previous versions frozen (e.g., v1.0, v1.1, etc.)

## Compatibility

This repo is language/version agnostic; it documents all versions of Transire.

## Contributing to Documentation

- Docs improvements welcome via PRs
- Follow Markdown style guide (e.g., Google's)
- Include code examples (runnable if possible)
- Add to appropriate section (getting-started, reference, guides, examples)
- Update table of contents / navigation config

## Future Enhancements

- [ ] Video tutorials (YouTube, Loom)
- [ ] Interactive tutorials (Katacoda, Instruqt)
- [ ] API playground (live editor for trying Transire in browser)
- [ ] Community contributions (blog posts, case studies)
- [ ] Translations (i18n for non-English users)

## Additional Language SDKs (Post-MVP)

When new language SDKs are added, create equivalent API reference docs:
- `/docs/reference/python-sdk/` (for `transire/sdk-python`)
- `/docs/reference/java-sdk/` (for `transire/sdk-java`)
- `/docs/reference/rust-sdk/` (for `transire/sdk-rust`)

## License

[License TBD]
