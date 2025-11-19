---
title: "transire init"
description: "Initialize a new Transire project"
keywords:
  - transire init
  - initialize
  - new project
  - scaffold
  - setup
category: cli-reference
difficulty: beginner
estimated_time: 5 minutes
prerequisites:
  []
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Creating new projects"
    - "Scaffolding applications"
  common_questions:
    - "How do I create a new project?"
    - "What does init create?"
    - "What flags are available?"
---

# transire init

Initialize a new Transire project with scaffolded code and configuration.

!!! tip "TL;DR"
    `transire init [project-name]` creates a new project with code scaffolding, configuration, and infrastructure setup. Use `--force` to overwrite existing files.

---

## Synopsis

```bash
transire init [project-name] [flags]
```

---

## Description

Creates a new Transire project with:
- Application code scaffolding (minimal `main.go`)
- `transire.yaml` configuration file
- `go.mod` with Transire dependency
- Infrastructure as Code setup (CDK TypeScript project structure)
- CI/CD pipeline configuration (GitHub Actions workflow)

Source: [`internal/cli/commands/init.go:13-113`](https://github.com/transire/transire/blob/main/internal/cli/commands/init.go), scaffolding via [`internal/cli/scaffold/`](https://github.com/transire/transire/tree/main/internal/cli/scaffold/)

---

## Arguments

- **`project-name`** (optional) – Name of project directory to create. If omitted, initializes in current directory.

---

## Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--language` | string | `go` | Programming language (only `go` supported in MVP) |
| `--cloud` | string | `aws` | Cloud provider (only `aws` supported in MVP) |
| `--runtime` | string | `lambda` | Runtime platform (only `lambda` supported in MVP) |
| `--iac` | string | `cdk` | Infrastructure as Code tool (only `cdk` supported in MVP) |
| `--ci` | string | `github` | CI/CD platform (only `github` supported in MVP) |
| `--force` | bool | `false` | Force initialization even if directory is not empty |

Source: [`internal/cli/commands/init.go:105-110`](https://github.com/transire/transire/blob/main/internal/cli/commands/init.go)

---

## Examples

### Create new project in subdirectory

```bash
transire init my-api
cd my-api
```

### Initialize in current directory

```bash
mkdir my-api && cd my-api
transire init .
```

### Force init (overwrite existing files)

```bash
transire init my-api --force
```

**Warning:** `--force` will overwrite existing files. Use with caution.

---

## Generated Project Structure

```
my-api/
├── main.go                    # Application entry point
├── go.mod                     # Go module
├── transire.yaml             # Transire configuration
├── infrastructure/           # CDK project (generated on first build)
│   ├── bin/
│   │   └── app.ts           # CDK app entry point
│   ├── lib/
│   │   └── my-api-dev.ts  # CDK stack (auto-generated)
│   ├── package.json
│   └── tsconfig.json
└── .github/
    └── workflows/
        └── deploy.yml       # GitHub Actions workflow
```

### Generated `main.go`

The generated `main.go` includes:
- Basic application setup with `transire.New()`
- Chi router with health endpoint
- Example queue and schedule handler placeholders
- Ready to run locally with `transire run`

### Generated `transire.yaml`

Includes sensible defaults for:
- Local development ports
- Lambda configuration (ARM64, 256MB)
- Empty queue/schedule configurations

---

## Next Steps

After initialization:

```bash
cd my-api
transire run        # Start local development
```

See also:
- [Quickstart Guide](../getting-started/quickstart.md) – 5-minute tutorial
- [transire run](transire-run.md) – Run locally with hot reload
- [Configuration Reference](../configuration/transire-yaml.md) – Customize settings

---

## Troubleshooting

### Directory already exists

**Error:**
```
Error: directory already exists and is not empty
```

**Solution:**
Use `--force` flag to overwrite:
```bash
transire init my-api --force
```

### Permission denied

**Error:**
```
Error: permission denied
```

**Solution:**
- Check directory permissions
- Ensure you have write access to parent directory
- Run without `sudo` (not recommended for Go projects)

### Go not found

**Error:**
```
Error: go command not found
```

**Solution:**
- Install Go 1.21 or higher
- Add Go to your PATH: `export PATH=$PATH:$(go env GOPATH)/bin`

---

## See Also

- [transire run](transire-run.md) – Run locally with hot reload
- [transire build](transire-build.md) – Build deployment artifacts
- [transire deploy](transire-deploy.md) – Deploy to AWS
- [Quickstart](../getting-started/quickstart.md) – Get started in 5 minutes
