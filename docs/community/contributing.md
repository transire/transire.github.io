---
title: "Contributing Guide"
category: community
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - Go 1.22+
  - Git
mcp_use: reference
features_covered:
  - Contributing guidelines
  - Development setup
  - Pull request process
code_blocks: true
last_updated: 2025-10-31
---

# Contributing to Transire

Thank you for your interest in contributing to Transire! This guide will help you get started.

## Code of Conduct

Be respectful, constructive, and professional in all interactions.

## Ways to Contribute

- Report bugs
- Suggest features
- Improve documentation
- Submit pull requests
- Help others in discussions

## Repository Structure

Transire is organized as multiple repositories:

- **transire-sdk-go** - Go SDK
- **transire-cli** - CLI tool
- **transire-cloud-aws** - AWS provider
- **transire-ci-github** - GitHub Actions provider
- **transire-docs** - Documentation
- **transire-iac-opentofu** - OpenTofu integration

## Development Setup

### Prerequisites

- Go 1.22 or later
- Git
- OpenTofu (for IaC testing)

### Clone the Repository

```bash
# Clone the repository you want to contribute to
git clone https://github.com/transire/sdk-go.git
cd sdk-go

# Install dependencies
go mod download
```

### Run Tests

```bash
# Run all tests
go test ./...

# Run tests with coverage
go test -cover ./...

# Run tests with verbose output
go test -v ./...
```

### Code Style

Follow standard Go conventions:

- Run `gofmt` on all code
- Use meaningful variable names
- Write tests for new functionality
- Document exported functions

### Commit Messages

Use clear, descriptive commit messages:

```
Add support for custom middleware

- Implement middleware chain builder
- Add tests for middleware ordering
- Update documentation
```

## Submitting Changes

### 1. Create an Issue

Before starting work, create an issue describing:
- What you want to change
- Why it's needed
- How you plan to implement it

### 2. Fork and Branch

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR-USERNAME/sdk-go.git

# Create a branch
git checkout -b feature/your-feature-name
```

### 3. Make Changes

- Write clean, tested code
- Follow existing code style
- Update documentation
- Add tests

### 4. Test Thoroughly

```bash
# Run tests
go test ./...

# Check formatting
gofmt -d .

# Run linter (if available)
golangci-lint run
```

### 5. Commit and Push

```bash
git add .
git commit -m "Your descriptive commit message"
git push origin feature/your-feature-name
```

### 6. Create Pull Request

- Go to GitHub and create a pull request
- Describe your changes clearly
- Reference related issues
- Wait for review

## Pull Request Guidelines

### Required

- All tests must pass
- Code must be formatted with `gofmt`
- New features must include tests
- Public APIs must be documented
- Breaking changes must be clearly noted

### Pull Request Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- List of changes made

## Testing
How has this been tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted with gofmt
- [ ] All tests pass
```

## Development Guidelines

### Writing Tests

Write clear, comprehensive tests:

```go
func TestFeature(t *testing.T) {
    // Arrange
    input := setupTestData()

    // Act
    result := functionUnderTest(input)

    // Assert
    if result != expected {
        t.Errorf("Expected %v, got %v", expected, result)
    }
}
```

### Documentation

- Document all exported functions
- Include code examples in documentation
- Update relevant guides when adding features

### Error Handling

- Return errors, don't panic
- Use descriptive error messages
- Wrap errors with context

```go
if err != nil {
    return fmt.Errorf("failed to process order: %w", err)
}
```

## Getting Help

If you need help:

1. Check existing documentation
2. Search existing issues
3. Ask in discussions
4. Create a new issue

## Recognition

Contributors will be:

- Listed in release notes
- Credited in the changelog
- Recognized in the repository

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Thank You!

Your contributions help make Transire better for everyone. Thank you for your time and effort!
