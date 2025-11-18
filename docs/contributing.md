---
title: "Contributing"
description: "Guide for contributing to Transire"
keywords:
  - contributing
  - development
  - pull requests
  - issues
  - community
category: other
difficulty: intermediate
estimated_time: 10 minutes
prerequisites:
  - "Go development"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Contributing code"
    - "Reporting issues"
    - "Development setup"
  common_questions:
    - "How do I contribute?"
    - "How do I report issues?"
    - "How do I set up development?"
---

# Contributing to Transire

Learn how to contribute to Transire development and help build the future of cloud-agnostic Go serverless frameworks.

---

## Overview

We welcome contributions from the community! Whether you're fixing bugs, adding features, improving documentation, or suggesting ideas, your help is appreciated.

**Ways to contribute:**
- 🐛 Report bugs and issues
- ✨ Propose new features
- 🔧 Submit bug fixes and improvements
- 📝 Improve documentation
- 💬 Help others in discussions
- 🧪 Write tests and improve code quality

---

## Code of Conduct

We follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code.

**Key principles:**
- Be respectful and inclusive
- Welcome newcomers and help them learn
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

**Reporting issues:** If you experience or witness unacceptable behavior, contact the maintainers via [GitHub](https://github.com/transire/transire/discussions).

---

## Getting Started

### Prerequisites

- **Go 1.21+** – [Download here](https://go.dev/dl/)
- **Git** – Version control
- **AWS CLI** (optional) – For deployment testing
- **Docker** (optional) – For local database testing

### Development Setup

**1. Fork and clone the repository:**

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/transire
cd transire

# Add upstream remote
git remote add upstream https://github.com/transire/transire
```

**2. Install dependencies:**

```bash
go mod download
```

**3. Verify setup:**

```bash
# Run tests
go test ./...

# Build CLI
go build -o transire ./cmd/transire

# Verify CLI works
./transire --version
```

**4. Create a feature branch:**

```bash
git checkout -b feature/my-amazing-feature
```

---

## Project Structure

Understanding the codebase layout:

```
transire/
├── cmd/
│   └── transire/              # CLI entry point
│       └── main.go
├── pkg/
│   └── transire/              # Public API (user-facing)
│       ├── transire.go        # Core Application type
│       ├── interfaces.go      # QueueHandler, ScheduleHandler
│       ├── config.go          # Configuration types
│       └── runtime.go         # Runtime detection
├── internal/                  # Internal packages (not exported)
│   ├── cli/                   # CLI command implementations
│   │   ├── init.go
│   │   ├── run.go
│   │   ├── build.go
│   │   └── deploy.go
│   ├── providers/             # Cloud provider adapters
│   │   ├── aws/
│   │   │   ├── lambda.go
│   │   │   └── cdk.go
│   │   └── local/
│   │       ├── http.go
│   │       ├── queue.go
│   │       └── scheduler.go
│   ├── builder/               # Build system
│   │   ├── builder.go
│   │   └── bundler.go
│   └── config/                # Configuration loading
│       └── loader.go
├── examples/                  # Example applications
│   ├── hello-world/
│   ├── rest-api/
│   └── queue-processing/
├── docs/                      # Documentation source
└── tests/                     # Integration tests
```

**Key areas:**
- **`pkg/transire/`** – User-facing API, minimize breaking changes
- **`internal/`** – Implementation details, can change freely
- **`cmd/transire/`** – CLI commands and flags
- **`examples/`** – Working example applications

---

## Development Workflow

### Making Changes

**1. Keep your fork up-to-date:**

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

**2. Make your changes:**

- Write code following [code style guidelines](#code-style)
- Add tests for new functionality
- Update documentation if needed
- Keep commits focused and atomic

**3. Test your changes:**

```bash
# Run all tests
go test ./...

# Run specific package tests
go test ./pkg/transire

# Run with race detector
go test -race ./...

# Run with coverage
go test -cover ./...
```

**4. Commit your changes:**

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Good commit messages
git commit -m "feat: add support for DynamoDB streams"
git commit -m "fix: resolve panic in queue handler batch processing"
git commit -m "docs: update quickstart with ARM64 example"
git commit -m "test: add integration tests for Lambda runtime"
git commit -m "refactor: simplify config loading logic"
git commit -m "perf: optimize HTTP router initialization"

# Commit types
# feat:     New feature
# fix:      Bug fix
# docs:     Documentation changes
# test:     Test additions or changes
# refactor: Code refactoring (no behavior change)
# perf:     Performance improvements
# chore:    Build/tooling changes
```

**5. Push to your fork:**

```bash
git push origin feature/my-amazing-feature
```

**6. Open a Pull Request:**

- Navigate to https://github.com/transire/transire
- Click "New Pull Request"
- Select your fork and branch
- Fill out the PR template
- Link any related issues

---

## Code Style Guidelines

### Go Conventions

Follow [Effective Go](https://go.dev/doc/effective_go) and [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments).

**Formatting:**

```bash
# Run gofmt before committing
gofmt -w .

# Or use goimports (handles imports too)
goimports -w .
```

**Key principles:**

1. **Keep functions small and focused**

```go
// Good: Single responsibility
func (app *Application) startHTTPServer(ctx context.Context) error {
    server := &http.Server{
        Addr:    fmt.Sprintf(":%d", app.config.HTTPPort),
        Handler: app.router,
    }
    return server.ListenAndServe()
}

// Bad: Too many responsibilities
func (app *Application) start(ctx context.Context) error {
    // 100+ lines of mixed concerns
}
```

2. **Use meaningful variable names**

```go
// Good
func GetUser(ctx context.Context, userID string) (*User, error) { }

// Bad
func GetUser(ctx context.Context, id string) (*User, error) { }  // What ID?
```

3. **Comment exported functions**

```go
// QueueHandler processes messages from SQS queues.
// Implementations must be idempotent as messages may be delivered more than once.
type QueueHandler interface {
    // QueueName returns the name of the queue to process.
    QueueName() string

    // HandleMessages processes a batch of messages and returns IDs of failed messages.
    HandleMessages(ctx context.Context, messages []Message) ([]string, error)
}
```

4. **Handle errors explicitly**

```go
// Good
user, err := repository.GetUser(ctx, userID)
if err != nil {
    if errors.Is(err, ErrUserNotFound) {
        return nil, ErrNotFound
    }
    return nil, fmt.Errorf("failed to get user: %w", err)
}

// Bad
user, _ := repository.GetUser(ctx, userID)  // Ignoring errors
```

5. **Use table-driven tests**

```go
func TestParseConfig(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    *Config
        wantErr bool
    }{
        {
            name: "valid config",
            input: "name: my-api\nlambda:\n  memory_mb: 256",
            want: &Config{Name: "my-api", Lambda: LambdaConfig{MemoryMB: 256}},
        },
        {
            name:    "invalid yaml",
            input:   "invalid: [[[",
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ParseConfig(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("ParseConfig() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if !reflect.DeepEqual(got, tt.want) {
                t.Errorf("ParseConfig() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

---

## Testing Requirements

### Test Coverage

- **Minimum coverage:** 80% for new code
- **Critical paths:** 100% coverage (runtime detection, config loading, build system)

**Check coverage:**

```bash
# Generate coverage report
go test -coverprofile=coverage.out ./...

# View in browser
go tool cover -html=coverage.out

# Show per-package coverage
go test -cover ./...
```

---

### Test Types

**1. Unit Tests**

Test individual functions in isolation:

```go
package config

import "testing"

func TestLoadConfig_ValidFile(t *testing.T) {
    cfg, err := LoadConfig("testdata/valid.yaml")
    if err != nil {
        t.Fatalf("LoadConfig() error = %v", err)
    }

    if cfg.Name != "my-api" {
        t.Errorf("expected name 'my-api', got '%s'", cfg.Name)
    }
}
```

**2. Integration Tests**

Test component interactions:

```go
package integration

func TestApplication_HTTPHandlers(t *testing.T) {
    app := transire.New()
    r := app.Router()
    r.Get("/health", healthHandler)

    // Test HTTP request handling
    req := httptest.NewRequest("GET", "/health", nil)
    w := httptest.NewRecorder()
    r.ServeHTTP(w, req)

    if w.Code != http.StatusOK {
        t.Errorf("expected status 200, got %d", w.Code)
    }
}
```

**3. End-to-End Tests**

Test full CLI workflows (located in `tests/e2e/`):

```go
func TestCLI_InitBuildDeploy(t *testing.T) {
    // Create temp directory
    tmpDir := t.TempDir()

    // Run: transire init
    cmd := exec.Command("transire", "init", "--name", "test-app")
    cmd.Dir = tmpDir
    if err := cmd.Run(); err != nil {
        t.Fatalf("init failed: %v", err)
    }

    // Verify files created
    if _, err := os.Stat(filepath.Join(tmpDir, "transire.yaml")); err != nil {
        t.Error("transire.yaml not created")
    }
}
```

---

### Running Tests

```bash
# All tests
go test ./...

# Verbose output
go test -v ./...

# Specific package
go test ./pkg/transire

# Run specific test
go test -run TestApplication_Run ./pkg/transire

# With race detector
go test -race ./...

# With coverage
go test -cover ./...

# Integration tests only
go test -tags=integration ./tests/integration/...
```

---

## Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Tests pass (`go test ./...`)
- [ ] Code formatted (`gofmt -w .`)
- [ ] Commits follow conventional commits
- [ ] Documentation updated (if needed)
- [ ] Changelog updated (for significant changes)
- [ ] No breaking changes (or discussed with maintainers)

---

### PR Template

Fill out the GitHub PR template:

```markdown
## Description
Brief description of what this PR does.

## Related Issues
Fixes #123
Related to #456

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Testing
Describe how you tested your changes:
- Unit tests added: `TestXYZ()`
- Integration tests: `TestIntegration_XYZ()`
- Manual testing: Deployed to AWS, tested endpoints

## Checklist
- [ ] My code follows the code style of this project
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] I have updated the documentation accordingly
- [ ] I have read the CONTRIBUTING guide
```

---

### Review Process

1. **Automated checks** run (tests, linting, coverage)
2. **Maintainer review** provides feedback
3. **Address feedback** by pushing new commits
4. **Approval** from maintainer(s)
5. **Merge** by maintainer (squash or rebase)

**Review time:** Most PRs reviewed within 2-3 business days.

---

## Documentation Contributions

Documentation is as important as code! Help improve:

### Documentation Structure

```
docs/
├── getting-started/        # Tutorials for new users
├── core-concepts/          # Understanding Transire internals
├── guides/                 # How-to guides
├── configuration/          # Configuration reference
└── faq.md                  # Common questions
```

### Writing Style

- **Clear and concise** – Short sentences, simple words
- **Action-oriented** – "Add a queue handler" not "Queue handlers can be added"
- **Code examples** – Show, don't just tell
- **Assume beginner context** – Explain concepts thoroughly
- **Link to related pages** – Help users navigate

**Example structure:**

```markdown
# Feature Name

Brief description of the feature and why it's useful.

!!! tip "TL;DR"
    One-sentence summary for quick reference.

---

## Overview

1-2 paragraphs explaining the concept.

---

## Quick Start

Minimal example to get started:

\`\`\`go
// Code example
\`\`\`

---

## Detailed Guide

Step-by-step instructions with explanations...
```

---

### Testing Documentation

**Preview documentation locally:**

```bash
# Install MkDocs
pip install mkdocs mkdocs-material

# Serve locally
cd docs/
mkdocs serve

# Open http://localhost:8000
```

**Check for broken links:**

```bash
# Install link checker
npm install -g markdown-link-check

# Check all files
find docs -name "*.md" -exec markdown-link-check {} \;
```

---

## Issue Guidelines

### Reporting Bugs

Use the [Bug Report template](https://github.com/transire/transire/issues/new?template=bug_report.md).

**Include:**
- Transire version (`transire --version`)
- Go version (`go version`)
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/stack traces
- Minimal reproduction code

**Example:**

```markdown
## Bug Description
`transire deploy` fails with "role not found" error

## Steps to Reproduce
1. Create new app: `transire init --name test-app`
2. Build: `transire build`
3. Deploy: `transire deploy`

## Expected Behavior
Deployment succeeds, stack created

## Actual Behavior
Error: "IAM role not found: test-app-MainFunctionRole"

## Environment
- Transire: v0.2.1
- Go: 1.21.5
- OS: macOS 14.1
- AWS Region: us-east-1

## Error Output
```
Error: failed to deploy: IAM role not found: test-app-MainFunctionRole
```

## Additional Context
First deployment to this AWS account
```

---

### Feature Requests

Use the [Feature Request template](https://github.com/transire/transire/issues/new?template=feature_request.md).

**Include:**
- Problem you're trying to solve
- Proposed solution
- Alternative solutions considered
- Example use case
- Willingness to contribute

---

## Communication Channels

### GitHub Discussions

For general questions, ideas, and community chat:
- [Q&A](https://github.com/transire/transire/discussions/categories/q-a) – Ask questions
- [Ideas](https://github.com/transire/transire/discussions/categories/ideas) – Propose features
- [Show and Tell](https://github.com/transire/transire/discussions/categories/show-and-tell) – Share projects

### GitHub Issues

For bug reports and concrete feature requests:
- [Bug Reports](https://github.com/transire/transire/issues/new?template=bug_report.md)
- [Feature Requests](https://github.com/transire/transire/issues/new?template=feature_request.md)

---

## Release Process

### Versioning

Transire follows [Semantic Versioning](https://semver.org/):

- **v1.2.3** = MAJOR.MINOR.PATCH
- **MAJOR** – Breaking changes
- **MINOR** – New features (backward compatible)
- **PATCH** – Bug fixes (backward compatible)

### Changelog

Update `CHANGELOG.md` for significant changes:

```markdown
## [Unreleased]

### Added
- Support for DynamoDB streams (#123)
- `--profile` flag for AWS CLI profiles (#456)

### Fixed
- Panic in queue handler batch processing (#789)
- Incorrect timeout in scheduler events (#234)

### Changed
- Default Lambda memory increased to 256 MB (#567)
```

---

## License

By contributing to Transire, you agree that your contributions will be licensed under the [MIT License](https://github.com/transire/transire/blob/main/LICENSE).

**What this means:**
- Your code can be used commercially
- Your code can be modified
- Your code can be distributed
- You retain copyright to your contributions

---

## Recognition

Contributors are recognized in:
- [CONTRIBUTORS.md](https://github.com/transire/transire/blob/main/CONTRIBUTORS.md)
- GitHub contributor graph
- Release notes (for significant contributions)

Thank you for contributing to Transire! 🎉

---

## Additional Resources

- **[Architecture Overview (DESIGN.md)](https://github.com/transire/transire/blob/main/DESIGN.md)** – System design and decisions
- **[Development Guide](https://github.com/transire/transire/blob/main/CONTRIBUTING.md)** – Detailed contribution guide
- **[Effective Go](https://go.dev/doc/effective_go)** – Go best practices
- **[Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)** – Go style guide

---

## Questions?

- [GitHub Discussions](https://github.com/transire/transire/discussions) – Ask the community
- [GitHub Issues](https://github.com/transire/transire/issues) – Report problems

We're here to help! Don't hesitate to ask questions. 🙌
