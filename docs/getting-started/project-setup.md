---
title: Project Setup
category: getting-started
complexity: beginner
duration: 10 minutes
prerequisites:
  - Transire CLI installed
  - Go 1.22 or later
mcp_use: template
mcp_operations:
  - scaffold_project
  - validate_setup
features_covered:
  - Project structure
  - Configuration
  - Module initialization
code_blocks: true
---

# Project Setup

This guide walks you through creating a new Transire project from scratch.

## Quick Start

The fastest way to create a new project:

```bash
# Create project directory
mkdir my-api
cd my-api

# Initialize Go module
go mod init github.com/yourusername/my-api

# Install Transire SDK
go get github.com/transire/sdk-go@latest

# Initialize Transire workspace
transire init

# Install dependencies
go mod tidy
```

The `transire init` command creates the following structure:

```
my-api/
├── .transire/
│   ├── workspace.lock   # Workspace lock file
│   └── .gitignore       # Ignores workspace artifacts
├── transire.yaml        # Transire configuration
├── go.mod               # Go module definition
└── go.sum               # Dependency checksums
```

You'll need to create `main.go` yourself (see Step 4 below).

## Step-by-Step Setup

### 1. Create Project Directory

```bash
mkdir my-api
cd my-api
```

### 2. Initialize Go Module

```bash
go mod init github.com/yourusername/my-api
```

This creates `go.mod`:

```go
module github.com/yourusername/my-api

go 1.25
```

### 3. Install Transire SDK

```bash
go get github.com/transire/sdk-go@latest
```

If deploying to AWS:

```bash
go get github.com/transire/cloud-aws@latest
```

### 4. Initialize Workspace

```bash
$ transire init
✓ Workspace initialized successfully

Workspace root: /path/to/my-api

Created:
  • .transire/  (workspace directory)
  • .transire/workspace.lock
  • .transire/.gitignore
  • transire.yaml  (configuration file)

Configured providers:
  • Cloud: aws
  • IaC: opentofu
  • CI: github

Next steps:
  1. Review and customize transire.yaml
  2. Create your application code (main.go)
  3. Run 'transire gen' to generate the manifest
  4. Run 'transire run' to start local development
```

This creates the `.transire/` workspace directory and a default `transire.yaml` configuration file.

### 5. Create Application Entry Point

Create `main.go`:

```go
package main

import (
    "context"
    "log"
    "net/http"

    "github.com/transire/sdk-go"
    "github.com/transire/sdk-go/response"
    _ "github.com/transire/cloud-aws" // Auto-registers AWS provider
)

func main() {
    // Create Transire application
    app := transire.New()

    // Register HTTP handlers
    app.GET("/health", healthCheck)
    app.GET("/", home)

    // Start application
    if err := app.Run(); err != nil {
        log.Fatal(err)
    }
}

func healthCheck(w http.ResponseWriter, r *http.Request) {
    response.OK(w, map[string]string{
        "status": "healthy",
    })
}

func home(w http.ResponseWriter, r *http.Request) {
    response.OK(w, map[string]string{
        "message": "Welcome to Transire!",
    })
}
```

### 6. Customize Configuration (Optional)

The `transire init` command created a default configuration. Review and customize `transire.yaml` if needed:

```yaml
version: 1
service: my-api
runtime: go
cloud: aws
iac: opentofu
ci: github
timezone: America/New_York

deploy:
  arch: arm64
  memory_mb: 256
  timeout_s: 30

http:
  simulate_apigw_limits: true

queues:
  max_batch_size: 10
  batch_window_s: 5
  visibility_timeout_s: 30
  max_receive_count: 3

observability:
  logging:
    level: info
    format: json
  tracing:
    enabled: false

infra:
  backend:
    type: s3
    bucket: my-api-tf-state
    dynamodb_table: tf-locks
    key_prefix: my-api/

env:
  - name: dev
    workspace: dev
    variables:
      LOG_LEVEL: debug

  - name: prod
    workspace: prod
    variables:
      LOG_LEVEL: info
```

**Note:** Since `transire init` already created this file with sensible defaults, you can skip this step and proceed directly to manifest generation if the defaults work for you.

### 7. Generate Manifest

```bash
$ transire gen
✓ Analyzed package main
✓ Found 2 HTTP routes
✓ Validated handler signatures
✓ Generated transire_manifest.json
```

This creates `transire_manifest.json`:

```json
{
  "version": "1.0",
  "service": "my-api",
  "runtime": "go",
  "http_routes": [
    {
      "method": "GET",
      "path": "/health",
      "handler": "healthCheck"
    },
    {
      "method": "GET",
      "path": "/",
      "handler": "home"
    }
  ],
  "queues": [],
  "schedules": [],
  "dependencies": [],
  "permissions": []
}
```

### 8. Run Locally

```bash
$ transire run
✓ Starting HTTP server on :8080
→ Ready: http://localhost:8080

# Test in another terminal
$ curl http://localhost:8080/health
{"status":"healthy"}
```

## Project Structure

A typical Transire project follows this structure:

```
my-api/
├── main.go                  # Application entry point
├── transire.yaml            # Transire configuration
├── transire_manifest.json   # Generated manifest (do not edit)
├── go.mod                   # Go module definition
├── go.sum                   # Dependency checksums
│
├── .transire/               # Workspace directory (created by transire init)
│   ├── workspace.lock       # Workspace lock file
│   └── .gitignore           # Ignores workspace artifacts
│
├── handlers/                # HTTP handlers (optional organization)
│   ├── orders.go
│   └── users.go
│
├── queues/                  # Queue handlers (optional organization)
│   └── process_order.go
│
├── scheduled/               # Scheduled jobs (optional organization)
│   └── daily_report.go
│
├── services/                # Business logic
│   ├── order_service.go
│   └── user_service.go
│
├── models/                  # Data models
│   ├── order.go
│   └── user.go
│
├── infra/                   # Generated infrastructure (do not edit)
│   ├── backend.tf
│   ├── api_gateway.tf
│   ├── lambdas/
│   │   ├── http.tf
│   │   ├── queues.tf
│   │   └── scheduled.tf
│   ├── iam.tf
│   ├── outputs.tf
│   └── overrides/           # User-managed custom Tofu
│       └── custom.tf
│
├── build/                   # Build artifacts (ignored by git)
│   ├── my-api-dev-http.zip
│   └── ...
│
└── .gitignore
```

**Important notes:**

- Handler functions must be in `package main` for MVP
- `.transire/` directory is created by `transire init` and contains workspace metadata
- `infra/` directory is generated by `transire gen` (except `infra/overrides/`)
- `build/` directory contains deployment artifacts
- `transire_manifest.json` is generated, do not edit manually

## Configuration Details

### Service Configuration

```yaml
version: 1              # Config schema version
service: my-api         # Service name (used in resource naming)
runtime: go             # Runtime language
cloud: aws              # Cloud provider (aws, gcp - future)
iac: opentofu           # IaC tool (opentofu, terraform - future)
ci: github              # CI provider (github, gitlab - future)
timezone: America/New_York  # Timezone for scheduled jobs
```

### Deployment Configuration

```yaml
deploy:
  arch: arm64           # Lambda architecture (arm64 or x86_64)
  memory_mb: 256        # Lambda memory in MB
  timeout_s: 30         # Lambda timeout in seconds
```

**Recommendation:** Use `arm64` for better price/performance ratio.

### HTTP Configuration

```yaml
http:
  simulate_apigw_limits: true  # Enforce API Gateway limits locally (6MB)
  cors:
    enabled: true
    allow_origins: ["https://app.example.com"]
    allow_methods: ["GET", "POST", "PUT", "DELETE"]
    allow_headers: ["Content-Type", "Authorization"]
  rate_limit:
    requests_per_minute: 100
    burst: 20
```

### Queue Configuration

```yaml
queues:
  max_batch_size: 10          # Maximum messages per batch
  batch_window_s: 5           # Max seconds to wait for batch
  visibility_timeout_s: 30    # Message visibility timeout
  max_receive_count: 3        # Max retries before DLQ
```

### Observability Configuration

```yaml
observability:
  logging:
    level: info               # debug, info, warn, error
    format: json              # json or text
  tracing:
    enabled: false            # Opt-in distributed tracing
    provider: aws-xray        # aws-xray or otel
```

### Infrastructure Backend

```yaml
infra:
  backend:
    type: s3                           # Backend type (s3 for AWS)
    bucket: my-api-tf-state            # S3 bucket name
    dynamodb_table: tf-locks           # DynamoDB table for locking
    key_prefix: my-api/                # Key prefix in bucket
  vpc:
    enabled: false                     # VPC integration (future)
  tags:
    team: backend
    cost-center: engineering
```

### Environment Variables

```yaml
env:
  - name: dev
    workspace: dev
    variables:
      LOG_LEVEL: debug
      DB_URL: postgres://localhost/myapi_dev

  - name: prod
    workspace: prod
    variables:
      LOG_LEVEL: info
      DB_URL: postgres://prod-db/myapi
```

**Note:** Environment variables are passed to Lambda functions. Use AWS Secrets Manager for sensitive data in production.

## Git Ignore

Add this to `.gitignore`:

```gitignore
# Transire build artifacts
build/
infra/*.tf
infra/*.tfstate*
infra/.terraform/

# Keep overrides directory
!infra/overrides/

# Go
*.so
*.dylib
*.test
*.out
vendor/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

## Best Practices

### Project Organization

- Keep handler functions in `package main` (MVP requirement)
- Organize business logic in separate packages (`services/`, `models/`)
- Use descriptive handler names that match their purpose
- Group related routes using path prefixes

### Configuration Management

- Use environment-specific variables in `transire.yaml`
- Store secrets in AWS Secrets Manager, not in config
- Use separate workspaces for dev/staging/prod
- Version control `transire.yaml`, ignore `transire_manifest.json`

### Development Workflow

1. Make code changes
2. Run `transire gen` to update manifest
3. Run `transire run` to test locally
4. Commit changes (including `transire.yaml`)
5. Deploy with `transire deploy`

## Troubleshooting

### `transire gen` Fails

**Error:** `E1001: Handler 'myHandler' not found in package main`

**Solution:** Ensure handler function is defined in `package main` and matches the registration name.

### `transire run` Port Already in Use

**Error:** `listen tcp :8080: bind: address already in use`

**Solution:** Stop other processes using port 8080 or change the port:

```bash
PORT=3000 transire run
```

### AWS Credentials Not Found

**Error:** `NoCredentialProviders: no valid providers in chain`

**Solution:** Configure AWS credentials:

```bash
aws configure
```

See [Installation Guide](installation.md#configure-aws-credentials) for details.

## Next Steps

Now that your project is set up:

**[Quick Start →](quickstart.md){ .md-button .md-button--primary }**

Follow the Quick Start guide to deploy your first app.

## See Also

- [Quick Start](quickstart.md) - Deploy your first app in 15 minutes
- [Config Schema](../reference/config-schema.md) - Complete configuration reference
- [CLI Reference](../cli/overview.md) - Command-line interface documentation
- [Troubleshooting](../guides/troubleshooting.md) - Common issues and solutions
