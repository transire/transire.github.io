---
title: CLI Commands Reference
description: Complete reference for all Transire CLI commands and options
category: reference
subcategory: cli
complexity: beginner
mcp_use: reference
features_covered:
  - CLI commands
  - Command options
  - Configuration
  - Deployment
  - Development workflow
code_blocks: true
last_updated: 2025-11-10
---

# CLI Commands Reference

> **Complete reference** for the Transire command-line interface

## Table of Contents

- [Installation](#installation)
- [Global Options](#global-options)
- [Development Commands](#development-commands)
- [Deployment Commands](#deployment-commands)
- [Management Commands](#management-commands)
- [Information Commands](#information-commands)
- [Configuration](#configuration)

---

## Installation

### Install via Homebrew (macOS/Linux)

```bash
brew install transire/tap/transire
```

### Install via Go

```bash
go install github.com/transire/cli/cmd/transire@latest
```

### Install from Binary

```bash
# Download latest release
curl -L https://github.com/transire/cli/releases/latest/download/transire-$(uname -s)-$(uname -m) -o transire

# Make executable
chmod +x transire

# Move to PATH
sudo mv transire /usr/local/bin/
```

### Verify Installation

```bash
$ transire version
transire version 0.1.0
```

---

## Global Options

Available for all commands:

```bash
transire [command] [options]
```

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--help`, `-h` | Show help | `transire deploy --help` |
| `--version`, `-v` | Show version | `transire --version` |
| `--verbose` | Verbose output | `transire deploy --verbose` |
| `--quiet`, `-q` | Minimal output | `transire gen --quiet` |
| `--config` | Config file path | `transire deploy --config prod.yaml` |
| `--env` | Environment | `transire deploy --env prod` |

---

## Development Commands

### run

Start local development server.

```bash
transire run [options]
```

**Options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--port`, `-p` | HTTP port | 8080 | `transire run -p 3000` |
| `--watch` | Enable hot reload | false | `transire run --watch` |
| `--env-file` | Environment file | `.env` | `transire run --env-file .env.local` |

**Examples:**

```bash
# Basic run
transire run

# Custom port
transire run --port 3000

# With hot reload
transire run --watch

# Custom env file
transire run --env-file .env.development
```

**Output:**

```
✓ Starting HTTP server on :8080
✓ Queue emulator: 2 queues, 1 worker each
✓ Scheduler: 1 job (daily-report, next run: tomorrow at 09:00)
→ Ready: http://localhost:8080

Watching for changes... (Ctrl+C to stop)
```

**Hot Reload:**

When `--watch` is enabled:
- Detects Go file changes
- Rebuilds automatically
- Restarts server
- Preserves state where possible

```bash
$ transire run --watch

✓ Ready: http://localhost:8080
Watching: *.go

# Edit main.go
→ Change detected: main.go
→ Rebuilding...
✓ Restarted in 1.2s
```

---

### gen

Generate deployment manifest from Go code.

```bash
transire gen [options]
```

**Options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--output`, `-o` | Output file | `transire_manifest.json` | `transire gen -o manifest.json` |
| `--validate` | Validate manifest | true | `transire gen --validate=false` |

**Examples:**

```bash
# Generate manifest
transire gen

# Custom output
transire gen --output build/manifest.json

# Skip validation
transire gen --validate=false
```

**Output:**

```
Analyzing Go code...
  ✓ Found 3 HTTP handlers
  ✓ Found 1 queue handler
  ✓ Found 2 scheduled jobs

Validating handlers...
  ✓ All handler signatures valid

Generating manifest...
  ✓ Manifest generated: transire_manifest.json

Build tags: lambda.norpc
```

**What it does:**
- Analyzes Go AST
- Extracts handler registrations
- Validates handler signatures
- Infers message types for queues
- Generates type metadata
- Creates `transire_manifest.json`

---

### test

Run tests with Transire test kit.

```bash
transire test [options]
```

**Options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--coverage` | Enable coverage | false | `transire test --coverage` |
| `--verbose`, `-v` | Verbose output | false | `transire test -v` |
| `--timeout` | Test timeout | 10m | `transire test --timeout 5m` |

**Examples:**

```bash
# Run all tests
transire test

# With coverage
transire test --coverage

# Verbose
transire test -v

# Specific package
transire test ./handlers/...
```

---

## Deployment Commands

### deploy

Deploy application to cloud.

```bash
transire deploy [options]
```

**Options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--env`, `-e` | Environment | `dev` | `transire deploy -e prod` |
| `--region` | AWS region | From config | `transire deploy --region us-west-2` |
| `--yes`, `-y` | Skip confirmation | false | `transire deploy -y` |
| `--dry-run` | Show plan only | false | `transire deploy --dry-run` |

**Examples:**

```bash
# Deploy to dev (default)
transire deploy

# Deploy to production
transire deploy --env prod

# Dry run
transire deploy --env prod --dry-run

# Skip confirmation
transire deploy --env prod --yes
```

**Output:**

```
Building application...
  ✓ go build -tags lambda.norpc
  ✓ Binary size: 8.2 MB
  ✓ Compressed: 2.8 MB

Packaging handlers...
  ✓ HTTP handler: my-app-http.zip
  ✓ Queue handler: my-app-queue.zip

Generating infrastructure...
  ✓ Generated: infra/main.tf
  ✓ Generated: infra/http.tf
  ✓ Generated: infra/queue.tf

Deploying with OpenTofu...
  ✓ tofu init
  ✓ tofu plan

Plan: 12 resources to create
  + AWS Lambda functions (3)
  + API Gateway HTTP API
  + SQS queues (2)
  + EventBridge rules (1)
  + IAM roles and policies

Apply changes? (yes/no): yes

  ✓ tofu apply

✅ Deployment complete! (45 seconds)

Endpoint: https://abc123.execute-api.us-east-1.amazonaws.com/dev
```

**Deployment flow:**
1. Build Go binary with Lambda tags
2. Package handlers into zip files
3. Generate Terraform/OpenTofu files
4. Initialize Terraform backend
5. Plan infrastructure changes
6. Apply changes to AWS
7. Output endpoint URL

---

### destroy

Remove all deployed resources.

```bash
transire destroy [options]
```

**Options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--env`, `-e` | Environment | `dev` | `transire destroy -e staging` |
| `--yes`, `-y` | Skip confirmation | false | `transire destroy -y` |

**Examples:**

```bash
# Destroy dev environment
transire destroy

# Destroy production (with confirmation)
transire destroy --env prod

# Skip confirmation
transire destroy --env staging --yes
```

**Output:**

```
⚠️  Destroy Resources
   Environment: prod
   Service: orders-api

Resources to destroy:
  - Lambda functions (3)
  - API Gateway
  - SQS queues (2)
  - EventBridge rules (1)
  - IAM roles and policies
  - CloudWatch log groups

This action cannot be undone.

Continue? (yes/no): yes

Destroying resources...
  ✓ Deleted Lambda functions
  ✓ Deleted API Gateway
  ✓ Deleted SQS queues
  ✓ Deleted EventBridge rules
  ✓ Deleted IAM resources
  ✓ Deleted CloudWatch logs

✅ All resources destroyed
```

**Note:** Does NOT delete:
- S3 backend bucket
- DynamoDB state table
- Database instances
- Manually created resources

---

### rollback

Rollback to previous deployment.

```bash
transire rollback [options]
```

**Options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--env`, `-e` | Environment | `dev` | `transire rollback -e prod` |
| `--version` | Specific version | Previous | `transire rollback --version v1.2.0` |

**Examples:**

```bash
# Rollback to previous version
transire rollback --env prod

# Rollback to specific version
transire rollback --env prod --version v1.2.0
```

**Output:**

```
⚠️  Rollback Deployment
   Current: v1.2.3 (deployed 2025-11-10 14:30)
   Target: v1.2.2 (deployed 2025-11-09 10:15)

Continue? (yes/no): yes

Rolling back...
  ✓ Deploying v1.2.2
  ✓ Updated Lambda functions
  ✓ Verified health checks

✅ Rollback complete
```

---

### init

Initialize project or backend.

```bash
transire init [options]
```

**Options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--backend` | Initialize backend | false | `transire init --backend` |
| `--example` | Example template | none | `transire init --example hello-world` |

**Examples:**

```bash
# Initialize new project
transire init

# Initialize backend (one-time per AWS account)
transire init --backend

# Create from example
transire init --example rest-api
```

**Initialize Project:**

```bash
$ transire init

Creating new Transire project...

Project name: my-app
Runtime: [go] go
Cloud provider: [aws] aws

Creating files...
  ✓ main.go
  ✓ transire.yaml
  ✓ go.mod
  ✓ .gitignore

Next steps:
  1. cd my-app
  2. transire run
  3. transire deploy
```

**Initialize Backend:**

```bash
$ transire init --backend

Initializing Transire backend...

Creating resources:
  ✓ S3 bucket: transire-state-123456789012-us-east-1
  ✓ DynamoDB table: transire-state-locks
  ✓ Encryption: Enabled
  ✓ Versioning: Enabled

Configuration saved to: infra/backend.tf

✅ Backend initialized
```

---

## Management Commands

### logs

View application logs.

```bash
transire logs [options]
```

**Options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--env`, `-e` | Environment | `dev` | `transire logs -e prod` |
| `--follow`, `-f` | Follow logs | false | `transire logs -f` |
| `--since` | Time range | none | `transire logs --since 1h` |
| `--filter` | Filter pattern | none | `transire logs --filter ERROR` |
| `--handler` | Handler type | all | `transire logs --handler http` |

**Examples:**

```bash
# View recent logs
transire logs

# Follow logs (live tail)
transire logs --follow

# Last hour
transire logs --since 1h

# Last 24 hours
transire logs --since 24h

# Specific time
transire logs --since "2025-11-10 12:00:00"

# Filter for errors
transire logs --filter ERROR

# HTTP handler only
transire logs --handler http

# Queue handler only
transire logs --handler queue

# Production logs with filter
transire logs --env prod --filter "user-123" --since 30m
```

**Output:**

```
2025-11-10 15:23:45 START RequestId: abc-123
2025-11-10 15:23:45 [INFO] GET /orders
2025-11-10 15:23:45 [INFO] Returned 10 orders
2025-11-10 15:23:45 END RequestId: abc-123
2025-11-10 15:23:45 REPORT RequestId: abc-123
  Duration: 12.34 ms
  Billed Duration: 13 ms
  Memory Size: 256 MB
  Max Memory Used: 45 MB
```

---

### metrics

View application metrics.

```bash
transire metrics [options]
```

**Options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--env`, `-e` | Environment | `dev` | `transire metrics -e prod` |
| `--period` | Time period | 24h | `transire metrics --period 7d` |
| `--format` | Output format | table | `transire metrics --format json` |

**Examples:**

```bash
# View metrics
transire metrics

# Production metrics
transire metrics --env prod

# Last 7 days
transire metrics --period 7d

# JSON output
transire metrics --format json
```

**Output:**

```
Orders API - Metrics (Last 24 hours)
════════════════════════════════════

HTTP Metrics:
  Invocations:     12,456
  Errors:          23 (0.18%)
  Duration (avg):  145ms
  Duration (p50):  98ms
  Duration (p99):  890ms
  Cold Starts:     34 (0.27%)

Queue Metrics:
  Messages:        1,234
  Successes:       1,230 (99.7%)
  Failures:        4 (0.3%)
  DLQ Messages:    0

Schedule Metrics:
  Executions:      24
  Successes:       24 (100%)
  Duration (avg):  2.3s

Cost Estimate (Last 24h):
  Lambda:          $0.52
  API Gateway:     $0.23
  SQS:             $0.01
  Total:           $0.76
  Monthly Est:     $22.80
```

---

### invoke

Manually invoke a handler.

```bash
transire invoke [options]
```

**Options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--env`, `-e` | Environment | `dev` | `transire invoke -e prod` |
| `--handler` | Handler type | required | `transire invoke --handler http` |
| `--path` | HTTP path | / | `transire invoke --handler http --path /orders` |
| `--method` | HTTP method | GET | `transire invoke --handler http --method POST` |
| `--key` | Queue/schedule key | required | `transire invoke --handler queue --key fulfill-orders` |
| `--payload` | Request payload | none | `transire invoke --handler http --payload @data.json` |

**Examples:**

```bash
# Invoke HTTP handler
transire invoke --handler http --path /health

# POST request
transire invoke --handler http --method POST --path /orders --payload '{"product":"Widget"}'

# From file
transire invoke --handler http --method POST --path /orders --payload @order.json

# Trigger queue handler
transire invoke --handler queue --key fulfill-orders

# Trigger scheduled job
transire invoke --handler schedule --key daily-report
```

**Output:**

```
Invoking HTTP handler: GET /health

Response:
  Status: 200
  Duration: 123ms

Body:
{
  "status": "healthy"
}
```

---

## Information Commands

### info

Show deployment information.

```bash
transire info [options]
```

**Options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--env`, `-e` | Environment | `dev` | `transire info -e prod` |
| `--output` | Output format | table | `transire info --output json` |

**Examples:**

```bash
# Show info
transire info

# Production info
transire info --env prod

# JSON output
transire info --output json
```

**Output:**

```
Orders API - Dev Environment
════════════════════════════

Endpoint:
  https://abc123.execute-api.us-east-1.amazonaws.com/dev

Resources:
  Lambda Functions:
    - orders-api-dev-http
    - orders-api-dev-queue
    - orders-api-dev-schedule

  API Gateway:
    - orders-api-dev (HTTP API)

  Queues:
    - orders-api-dev-fulfill-orders
    - orders-api-dev-fulfill-orders-dlq

  EventBridge:
    - orders-api-dev-daily-report

  IAM Role:
    - orders-api-dev-execution-role

Deployed: 2025-11-10 14:30:15
Version: v1.2.3
Region: us-east-1
```

---

### deployments

List deployment history.

```bash
transire deployments [options]
```

**Options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--env`, `-e` | Environment | `dev` | `transire deployments -e prod` |
| `--limit` | Number of results | 10 | `transire deployments --limit 20` |

**Examples:**

```bash
# List deployments
transire deployments

# Production history
transire deployments --env prod

# Last 20 deployments
transire deployments --limit 20
```

**Output:**

```
Deployment History - Production
════════════════════════════════

Version  | Deployed At          | Status  | Duration
---------|---------------------|---------|----------
v1.2.3   | 2025-11-10 14:30:00 | SUCCESS | 45s
v1.2.2   | 2025-11-09 10:15:00 | SUCCESS | 38s
v1.2.1   | 2025-11-08 09:00:00 | SUCCESS | 42s
v1.2.0   | 2025-11-07 15:30:00 | SUCCESS | 51s
v1.1.9   | 2025-11-06 11:20:00 | FAILED  | -
```

---

### validate

Validate configuration and manifest.

```bash
transire validate [options]
```

**Options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--env`, `-e` | Environment | `dev` | `transire validate -e prod` |
| `--strict` | Strict validation | false | `transire validate --strict` |

**Examples:**

```bash
# Validate configuration
transire validate

# Validate production config
transire validate --env prod

# Strict mode
transire validate --strict
```

**Output:**

```
Validating configuration...
  ✓ transire.yaml syntax valid
  ✓ Service name valid
  ✓ Region valid
  ✓ Environment config valid

Validating manifest...
  ✓ Handler signatures valid
  ✓ Queue message types valid
  ✓ Schedule expressions valid

Validating AWS setup...
  ✓ AWS credentials configured
  ✓ Required permissions available
  ✓ Backend initialized

✅ All validations passed
```

**Errors:**

```
Validating configuration...
  ✗ transire.yaml not found

Validating manifest...
  ✗ Handler signature invalid: fulfillOrders
    Expected: func(context.Context, []Order) error
    Got: func(context.Context, Order) error

❌ Validation failed
```

---

### version

Show CLI version.

```bash
transire version
```

**Output:**

```
transire version 0.1.0

Runtime: go1.22.0
Build: 2025-11-10T12:00:00Z
Commit: abc123
```

---

### help

Show help information.

```bash
transire help [command]
```

**Examples:**

```bash
# General help
transire help

# Command help
transire help deploy
transire help logs
transire help run
```

---

## Configuration

### Config File Locations

Transire looks for `transire.yaml` in:

1. Current directory: `./transire.yaml`
2. Parent directories: `../transire.yaml`, `../../transire.yaml`, ...
3. Custom path: `--config path/to/config.yaml`

### Environment Variables

Override config with environment variables:

```bash
# AWS credentials
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"

# Transire config
export TRANSIRE_ENV="prod"
export TRANSIRE_REGION="us-west-2"
export TRANSIRE_LOG_LEVEL="debug"
```

### Config Precedence

Configuration values are merged in this order (highest to lowest priority):

1. Command-line flags: `transire deploy --env prod`
2. Environment variables: `TRANSIRE_ENV=prod`
3. Config file: `transire.yaml`
4. Defaults

---

## Common Workflows

### Development Workflow

```bash
# Start local dev server with hot reload
transire run --watch

# In another terminal: make changes
# Server auto-reloads on file changes

# Run tests
transire test --coverage

# Validate before deploy
transire validate
```

### Deployment Workflow

```bash
# Deploy to staging
transire deploy --env staging

# Test staging
curl https://staging-api.yourdomain.com/health

# Deploy to production
transire deploy --env prod

# Monitor logs
transire logs --env prod --follow
```

### Troubleshooting Workflow

```bash
# Check deployment info
transire info --env prod

# View recent errors
transire logs --env prod --filter ERROR --since 1h

# Check metrics
transire metrics --env prod

# Validate configuration
transire validate --env prod

# Manual invocation for testing
transire invoke --env prod --handler http --path /health
```

---

## Exit Codes

Transire CLI uses standard exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Validation error |
| 4 | Deployment error |
| 130 | Interrupted (Ctrl+C) |

**Usage in scripts:**

```bash
#!/bin/bash
set -e  # Exit on error

transire validate || exit 1
transire deploy --env prod || exit 1

echo "Deployment successful"
```

---

## Bash Completion

Enable command completion:

```bash
# Bash
source <(transire completion bash)

# Zsh
source <(transire completion zsh)

# Fish
transire completion fish | source

# Add to shell profile for persistence
echo 'source <(transire completion bash)' >> ~/.bashrc
```

**Features:**
- Command completion: `transire de<TAB>` → `transire deploy`
- Option completion: `transire deploy --e<TAB>` → `transire deploy --env`
- Value completion: `transire deploy --env <TAB>` → `dev prod staging`

---

## See Also

- [First Deployment Guide](../../guides/deployment/first-deployment/) - Deploy first app
- [Local Development](../../guides/development/local-development/) - Development workflow
- [Production Checklist](../../guides/deployment/production-checklist/) - Pre-launch checklist
- [Configuration Reference](../config/reference/) - Config file options
- [Troubleshooting](../../guides/troubleshooting/) - Common issues

