# CLI Reference

Complete reference for the Transire command-line interface.

!!! tip "TL;DR"
    The Transire CLI provides commands to initialize projects, run locally with hot reload, build Lambda artifacts, and deploy to AWS. All commands work from your project directory.

---

## Overview

The Transire CLI (`transire`) is built with [Cobra](https://github.com/spf13/cobra) and provides a unified interface for the entire development lifecycle:

1. **`transire init`** – Bootstrap new projects
2. **`transire run`** – Local development with hot reload
3. **`transire dev`** – Development utilities for testing queues and schedules
4. **`transire build`** – Build Lambda deployment artifacts
5. **`transire deploy`** – Deploy to AWS with CDK

Source: [`cmd/transire/main.go`](https://github.com/transire/transire/blob/main/cmd/transire/main.go)

---

## Installation

Install via Go:

```bash
go install github.com/transire/transire/cmd/transire@latest
```

Verify installation:

```bash
transire --version
```

See the [Installation Guide](../getting-started/installation.md) for detailed instructions.

---

## Commands

### Project Initialization

```bash
transire init [project-name] [flags]
```

Create a new Transire project with scaffolded code and configuration.

[:octicons-arrow-right-24: transire init Reference](transire-init.md)

---

### Local Development

```bash
transire run
```

Run your application locally with hot reload, queue simulators, and schedule simulators.

[:octicons-arrow-right-24: transire run Reference](transire-run.md)

---

### Development Utilities

```bash
transire dev queues list
transire dev queues send <queue> <message>
transire dev schedules list
transire dev schedules execute <schedule>
```

Test queue and schedule handlers during local development with CLI commands.

[:octicons-arrow-right-24: transire dev Reference](transire-dev.md)

---

### Building Artifacts

```bash
transire build [flags]
```

Build Lambda deployment packages and generate AWS CDK infrastructure code.

[:octicons-arrow-right-24: transire build Reference](transire-build.md)

---

### Deployment

```bash
transire deploy [flags]
```

Deploy your application to AWS Lambda using CDK.

[:octicons-arrow-right-24: transire deploy Reference](transire-deploy.md)

---

## Command Comparison

| Command | Purpose | When to Use |
|---------|---------|-------------|
| **`init`** | Create new project | Starting fresh project |
| **`run`** | Local development | Writing code, testing locally |
| **`dev`** | Test queues/schedules | Testing handlers during development |
| **`build`** | Generate artifacts | Before deployment |
| **`deploy`** | Deploy to AWS | Pushing to staging/production |

---

## Common Workflows

### New Project Setup

```bash
# 1. Create project
transire init my-api
cd my-api

# 2. Start development
transire run

# 3. Test locally
curl http://localhost:3000/health
```

---

### Development Workflow

```bash
# Run with hot reload
transire run

# Edit code in your editor
# Changes auto-rebuild and restart

# Test HTTP endpoints
curl http://localhost:3000/api/...

# Test queue handlers
transire dev queues send email-queue '{"to":"test@example.com"}'

# Test schedule handlers
transire dev schedules execute daily-cleanup
```

---

### Deployment Workflow

```bash
# 1. Build artifacts
transire build

# 2. Preview changes (optional)
transire deploy --dry-run

# 3. Deploy to AWS
transire deploy

# 4. Test deployed endpoint
curl https://abc123.execute-api.us-east-1.amazonaws.com/health
```

---

## Global Options

All commands support these global flags:

| Flag | Type | Description |
|------|------|-------------|
| `--help`, `-h` | bool | Show help for any command |
| `--version`, `-v` | bool | Show CLI version |

---

## Configuration

Most behavior is controlled via `transire.yaml` in your project root.

See the [Configuration Reference](../configuration/transire-yaml.md) for all options.

---

## Getting Help

### Command Help

```bash
# Help for specific command
transire init --help
transire run --help
transire build --help
transire deploy --help
```

### Documentation

- [Quickstart Guide](../getting-started/quickstart.md) – Get started in 5 minutes
- [Local Development Guide](../guides/local-development.md) – Best practices for dev workflow
- [Deploying to AWS Guide](../guides/deploying-to-aws.md) – Complete deployment walkthrough

### Community

- [GitHub Issues](https://github.com/transire/transire/issues) – Report bugs or request features
- [GitHub Discussions](https://github.com/transire/transire/discussions) – Ask questions, share ideas

---

## Next Steps

### Start Using Transire

New to Transire? Start here:

[:octicons-arrow-right-24: Quickstart Guide](../getting-started/quickstart.md)

### Learn Local Development

Master the `transire run` workflow:

[:octicons-arrow-right-24: Local Development Guide](../guides/local-development.md)

### Deploy to Production

Ready to deploy? Learn the process:

[:octicons-arrow-right-24: Deploying to AWS Guide](../guides/deploying-to-aws.md)

---

## See Also

- [Installation](../getting-started/installation.md) – Install Transire CLI
- [Configuration](../configuration/transire-yaml.md) – Configure projects
- [FAQ](../faq.md) – Frequently asked questions
