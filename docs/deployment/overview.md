---
title: "Deployment Overview"
category: deployment
complexity: beginner
duration: 10 minutes
mcp_use: reference
last_updated: 2025-11-10
---

# Deployment Overview

Transire applications deploy to cloud providers as serverless functions. This guide explains the deployment process and how Transire maintains local/cloud parity.

## How Deployment Works

```
┌──────────────────────────────────────────────┐
│  1. Code Analysis                            │
│     transire gen                             │
│     • Scans Go code with AST                 │
│     • Extracts routes, queues, schedules     │
│     • Generates transire_manifest.json       │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  2. Packaging                                │
│     transire deploy                          │
│     • Compiles Go code                       │
│     • Creates deployment artifacts           │
│     • One artifact per handler type          │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  3. Infrastructure Generation                │
│     • OpenTofu configuration generated       │
│     • HTTP gateways, queues, schedulers      │
│     • IAM roles and policies                 │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  4. Cloud Deployment                         │
│     • OpenTofu applies infrastructure        │
│     • Uploads function code                  │
│     • Configures triggers                    │
└──────────────────────────────────────────────┘
```

## Quick Start

Deploy in three steps:

### 1. Install Provider

```bash
# Choose your cloud provider
go get github.com/transire/transire-cloud-aws@latest
```

### 2. Add Provider Import

```go
import _ "github.com/transire/transire-cloud-aws" // Auto-registers
```

### 3. Deploy

```bash
transire deploy --environment=dev
```

That's it! Your application is now running in the cloud.

## The Manifest

The manifest (`transire_manifest.json`) is the source of truth for deployment:

```json
{
  "version": "1.0",
  "service": "myapp",
  "runtime": "go",
  "http_routes": [
    {
      "method": "GET",
      "path": "/users/{id}",
      "handler": "main.getUserHandler"
    }
  ],
  "queue_handlers": [
    {
      "queue_key": "orders",
      "handler": "main.processOrders",
      "message_type": "main.Order"
    }
  ],
  "scheduled_handlers": [
    {
      "schedule": "@daily 09:00",
      "handler": "main.generateReport"
    }
  ]
}
```

**Generated automatically** by `transire gen` through static code analysis.

## Deployment Artifacts

Transire creates optimized artifacts for each handler type:

### HTTP Handler
- **Contains:** All HTTP route handlers
- **Triggered by:** API Gateway HTTP events
- **Environment:** `TRANSIRE_RUNTIME=http`

### Queue Handlers
- **Contains:** One artifact per queue
- **Triggered by:** Queue service events (batched)
- **Environment:** `TRANSIRE_HANDLER=queue-name`

### Scheduled Handlers
- **Contains:** One artifact per schedule
- **Triggered by:** Scheduler service events
- **Environment:** `TRANSIRE_HANDLER=schedule-expression`

### Why Separate Artifacts?

- **Faster cold starts** - Smaller code bundles
- **Independent scaling** - Each handler scales separately
- **Isolated failures** - One handler crash doesn't affect others
- **Fine-grained monitoring** - Per-handler metrics

## Infrastructure as Code

Transire generates OpenTofu (Terraform-compatible) configuration:

```hcl
# Generated in .transire/generated/main.tf

resource "aws_lambda_function" "http" {
  function_name = "myapp-dev-http"
  handler       = "bootstrap"
  runtime       = "provided.al2023"
  architectures = ["arm64"]

  # Auto-generated from transire.yaml
  memory_size = 512
  timeout     = 30
}

resource "aws_sqs_queue" "orders" {
  name = "myapp-dev-orders"

  # From transire.yaml queues config
  visibility_timeout_seconds = 30

  # DLQ configuration
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.orders_dlq.arn
    maxReceiveCount     = 3
  })
}
```

**Benefits:**
- ✅ **Version controlled** - Infrastructure changes tracked in git
- ✅ **Reproducible** - Same config = same infrastructure
- ✅ **Reviewable** - See exactly what will be deployed
- ✅ **Modular** - Generated code is human-readable

## Local vs Cloud Parity

Transire maintains **functional parity** between local and cloud:

| Feature | Local | Cloud | Notes |
|---------|-------|-------|-------|
| HTTP routing | ✅ Same | ✅ Same | Chi router in both |
| Request handling | ✅ Same | ✅ Same | Identical handler signatures |
| Queue processing | ✅ Emulated | ✅ Native | Same batch behavior |
| Scheduled jobs | ✅ Fixed-rate | ✅ Distributed | Same cron expressions |
| Middleware | ✅ Same | ✅ Same | Standard Go middleware |
| Error handling | ✅ Same | ✅ Same | Same retry logic |

### Known Differences

Not everything can be identical:

| Aspect | Local | Cloud | Why Different |
|--------|-------|-------|---------------|
| Persistence | In-memory | Durable | Cloud queues are persistent |
| Concurrency | Single process | Massive scale | Cloud auto-scales |
| Cold starts | None | Possible | Cloud functions may be cold |
| Network | Localhost | Internet | Different network topology |
| Costs | Free | Pay-per-use | Cloud has infrastructure costs |

**Design principle:** Code works the same, but operational characteristics differ.

## Deployment Workflows

### Development Workflow

```bash
# 1. Develop locally
transire run

# 2. Test locally
curl http://localhost:8080/api

# 3. Generate manifest
transire gen

# 4. Deploy to dev environment
transire deploy --environment=dev

# 5. Test in cloud
curl https://api-dev.example.com/api
```

### CI/CD Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.22'

      - name: Install Transire
        run: go install github.com/transire/cli/cmd/transire@latest

      - name: Deploy
        run: transire deploy --environment=prod
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

## Environment Management

Manage multiple environments with workspaces:

```yaml
# transire.yaml
service: myapp

env:
  dev:
    memory_mb: 512
    variables:
      LOG_LEVEL: debug
      DB_URL: postgres://dev-db

  prod:
    memory_mb: 1024
    variables:
      LOG_LEVEL: info
      DB_URL: postgres://prod-db
```

Deploy to specific environment:

```bash
# Dev environment
transire deploy --environment=dev

# Production environment
transire deploy --environment=prod
```

## Backend State Management

OpenTofu state can be stored locally or remotely:

### Local Backend (Development)

```bash
transire deploy --environment=dev
# State stored in: infra/terraform.tfstate
```

**Pros:** Simple, no setup
**Cons:** Not suitable for teams, state not shared

### Remote Backend (Production)

```bash
# Initialize remote backend
transire init backend --environment=prod

# Deploy uses remote state
transire deploy --environment=prod
```

**Pros:** Shared state, locking, versioning
**Cons:** Requires cloud storage setup

## Deployment Configuration

Configure deployment in `transire.yaml`:

```yaml
service: myapp
runtime: go

# Function configuration
deploy:
  architecture: arm64        # arm64 or x86_64
  memory_mb: 512            # 128 - 10240
  timeout_s: 30             # 1 - 900

# Queue configuration
queues:
  max_batch_size: 10
  visibility_timeout_s: 30
  max_receive_count: 3

# HTTP configuration
http:
  timeout_s: 30
  max_request_size_mb: 10

# Logging
logging:
  retention_days: 7
  format: json
```

## Monitoring Deployment

Track deployment progress:

```bash
transire deploy --environment=dev

# Output:
✓ Analyzing code (2s)
✓ Generating manifest (1s)
✓ Packaging handlers (5s)
  → HTTP handler: 5.2 MB
  → Queue handler (orders): 5.1 MB
  → Scheduled handler (daily-report): 5.1 MB
✓ Generating infrastructure (1s)
✓ Initializing backend (2s)
✓ Planning changes (3s)
  → 12 resources to create
  → 0 resources to update
  → 0 resources to delete
✓ Applying infrastructure (45s)

Deployment complete!
API URL: https://abc123.execute-api.us-east-1.amazonaws.com
```

## Rollback

If deployment fails or has issues:

```bash
# Check deployment history
transire deployments list

# Rollback to previous version
transire rollback --version=v1.2.3
```

Or use OpenTofu directly:

```bash
cd .transire/generated
tofu state list
tofu state show aws_lambda_function.http
```

## See Also

- [Provider Overview](/providers/overview.md) - Choose a provider
- [AWS Deployment](/providers/aws/getting-started.md) - AWS-specific guide
- [Configuration Reference](/reference/config-schema.md) - Full config options
- [Manifest Schema](/reference/manifest-schema.md) - Manifest format
