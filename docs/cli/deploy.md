---
title: "transire deploy"
category: cli
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - Go 1.22+
  - Transire project set up
  - Cloud provider credentials configured (e.g., AWS CLI)
  - Backend initialized (transire init --backend)
mcp_use: reference
mcp_operations:
  - deploy_to_cloud
  - generate_infrastructure
features_covered:
  - Cloud deployment
  - Infrastructure as Code
  - OpenTofu integration
  - Multi-environment deployment
code_blocks: true
last_updated: 2025-10-30
---

# transire deploy

## Overview

`transire deploy` deploys your application to the cloud using Infrastructure as Code (IaC). It generates all necessary infrastructure (API Gateway, Lambda functions, queues, schedules, IAM roles) and applies changes using OpenTofu (or your configured IaC provider).

**Purpose:**
- Deploy your application to cloud provider (AWS, etc.)
- Generate and apply infrastructure automatically
- Manage multiple environments (dev, staging, prod)
- Track infrastructure state safely

## Usage

### Deploy to Default Environment

```bash
transire deploy
```

Deploys to the first environment in `transire.yaml` (usually `dev`).

### Deploy to Specific Environment

```bash
transire deploy --env prod
```

Deploys to the `prod` environment.

### Plan Only (Dry Run)

```bash
transire deploy --plan
```

Shows what changes would be made without applying them.

### Auto-Approve

```bash
transire deploy --auto-approve
```

Skips confirmation prompt (use in CI/CD).

## Prerequisites

### 1. Cloud Credentials

Configure your cloud provider credentials:

**AWS:**
```bash
aws configure
# or
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1
```

Verify credentials:
```bash
aws sts get-caller-identity
```

### 2. Backend Initialized

Initialize backend for state storage (first-time only):

```bash
transire init --backend
```

This creates:
- S3 bucket for state storage
- DynamoDB table for state locking

### 3. Manifest Generated

Ensure manifest is up-to-date:

```bash
transire gen
```

## What It Does

When you run `transire deploy`, the CLI:

### 1. Validates Configuration

- Checks `transire.yaml` syntax and semantics
- Validates environment configuration
- Verifies cloud credentials

### 2. Generates Manifest

- Runs `transire gen` if manifest is outdated
- Validates all handlers and routes

### 3. Generates Infrastructure Code

- Reads manifest
- Generates OpenTofu/Terraform files:
  - API Gateway (HTTP endpoints)
  - Lambda functions (HTTP, queue, schedule handlers)
  - SQS queues and DLQs
  - EventBridge rules (schedules)
  - IAM roles and policies (least-privilege)

### 4. Plans Changes

- Runs `tofu plan` (or `terraform plan`)
- Shows what resources will be created/updated/deleted
- Calculates cost estimates (if available)

### 5. Applies Changes

- Prompts for confirmation (unless `--auto-approve`)
- Runs `tofu apply`
- Creates/updates infrastructure
- Deploys Lambda function code

### 6. Outputs Results

- API Gateway URL
- Queue names
- Schedule rules
- Deployment duration

## Example Deployment

### First Deploy

```bash
$ transire deploy
✓ Configuration loaded (dev environment)
✓ Manifest generated
✓ Infrastructure code generated
✓ Cloud provider: AWS (us-east-1)

Planning changes...

Terraform will perform the following actions:

  # aws_apigatewayv2_api.http will be created
  + resource "aws_apigatewayv2_api" "http" {
      + api_endpoint = (known after apply)
      + name         = "orders-dev"
      + protocol_type = "HTTP"
    }

  # aws_lambda_function.get_orders will be created
  + resource "aws_lambda_function" "get_orders" {
      + function_name = "orders-dev-get-orders"
      + handler       = "bootstrap"
      + runtime       = "provided.al2023"
      + architectures = ["arm64"]
      + memory_size   = 256
      + timeout       = 30
    }

  # ... more resources

Plan: 15 to add, 0 to change, 0 to destroy.

Do you want to perform these actions? (yes/no): yes

Applying changes...
✓ API Gateway created
✓ Lambda functions deployed
✓ SQS queues created
✓ EventBridge rules created
✓ IAM roles configured

Deployment complete! (45s)

API URL: https://abc123.execute-api.us-east-1.amazonaws.com
```

### Subsequent Deploys

```bash
$ transire deploy
✓ Configuration loaded (dev environment)
✓ Manifest up-to-date
✓ Infrastructure code generated

Planning changes...

Terraform will perform the following actions:

  # aws_lambda_function.create_order will be updated in-place
  ~ resource "aws_lambda_function" "create_order" {
        function_name = "orders-dev-create-order"
      ~ last_modified = "2025-10-29T10:30:00Z" -> (known after apply)
      ~ source_code_hash = "abc123" -> "def456"
    }

Plan: 0 to add, 1 to change, 0 to destroy.

Do you want to perform these actions? (yes/no): yes

Applying changes...
✓ Lambda function updated: create_order

Deployment complete! (12s)
```

## Multi-Environment Deployment

Configure multiple environments in `transire.yaml`:

```yaml
service: orders
cloud: aws

env:
  - name: dev
    workspace: dev
    variables:
      DB_URL: postgres://dev.db.example.com/orders
      LOG_LEVEL: debug

  - name: staging
    workspace: staging
    variables:
      DB_URL: postgres://staging.db.example.com/orders
      LOG_LEVEL: info

  - name: prod
    workspace: prod
    variables:
      DB_URL: postgres://prod.db.example.com/orders
      LOG_LEVEL: warn
```

### Deploy to Each Environment

```bash
# Dev
transire deploy --env dev

# Staging
transire deploy --env staging

# Production (with extra confirmation)
transire deploy --env prod
```

### Environment-Specific Resources

Resources are namespaced by environment:

- **Lambda:** `orders-dev-get-orders`, `orders-prod-get-orders`
- **Queues:** `orders-dev-OrderCreated`, `orders-prod-OrderCreated`
- **API Gateway:** `orders-dev`, `orders-prod`

This prevents conflicts between environments.

## Infrastructure Generation

Transire generates all infrastructure automatically:

### HTTP Handlers → API Gateway + Lambda

```go
app.GET("/orders/{id}", getOrder)
```

Generates:
- API Gateway HTTP API
- Lambda function for getOrder
- Integration between Gateway and Lambda
- IAM role with Lambda invoke permissions

### Queue Handlers → SQS + Lambda

```go
app.RegisterQueue("OrderCreated", processOrder)
```

Generates:
- SQS queue: `orders-dev-OrderCreated`
- SQS DLQ: `orders-dev-OrderCreated-dlq`
- Lambda function for processOrder
- Event source mapping (SQS → Lambda)
- IAM role with SQS permissions

### Scheduled Jobs → EventBridge + Lambda

```go
app.RegisterScheduled("@daily 09:00", sendReport)
```

Generates:
- EventBridge rule with cron expression
- Lambda function for sendReport
- Target mapping (EventBridge → Lambda)
- IAM role with Lambda invoke permissions

## State Management

Transire uses OpenTofu (Terraform) for state management:

### State Storage

State is stored in S3 (configured during `transire init --backend`):

```yaml
infra:
  backend:
    type: s3
    bucket: transire-tf-state
    dynamodb_table: tf-locks
    key_prefix: orders/
```

### State Location

- **Bucket:** `transire-tf-state`
- **Key:** `orders/dev/terraform.tfstate` (per environment)
- **Lock:** DynamoDB table `tf-locks`

### State Locking

DynamoDB prevents concurrent modifications:

```bash
$ transire deploy  # Terminal 1
# Acquires lock

$ transire deploy  # Terminal 2 (simultaneously)
Error: Failed to acquire state lock
Another deployment is in progress
```

## Plan vs Apply

### Plan Only (`--plan`)

Preview changes without applying:

```bash
$ transire deploy --plan
✓ Planning changes...

Terraform will perform the following actions:

  # aws_lambda_function.get_orders will be updated
  ~ resource "aws_lambda_function" "get_orders" {
      ~ memory_size = 256 -> 512
    }

Plan: 0 to add, 1 to change, 0 to destroy.

Note: This is a plan only. Run without --plan to apply changes.
```

### Apply Changes

Apply changes interactively:

```bash
$ transire deploy
...
Plan: 0 to add, 1 to change, 0 to destroy.

Do you want to perform these actions? (yes/no): yes
```

Or auto-approve (CI/CD):

```bash
$ transire deploy --auto-approve
```

## Custom Infrastructure

Override or extend generated infrastructure:

### 1. Create Override Directory

```bash
mkdir -p infra/overrides
```

### 2. Add Custom Resources

`infra/overrides/custom.tf`:

```hcl
# Custom S3 bucket
resource "aws_s3_bucket" "uploads" {
  bucket = "${var.service_name}-${var.environment}-uploads"
}

# Grant Lambda access to bucket
resource "aws_iam_role_policy_attachment" "http_s3" {
  role       = aws_iam_role.http_lambda.name
  policy_arn = aws_iam_policy.s3_access.arn
}

resource "aws_iam_policy" "s3_access" {
  name = "${var.service_name}-${var.environment}-s3-access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject"]
        Resource = "${aws_s3_bucket.uploads.arn}/*"
      }
    ]
  })
}
```

### 3. Deploy

```bash
transire deploy
```

Transire merges generated + custom infrastructure.

**Important:** `transire gen` never overwrites `infra/overrides/`—it's user-controlled.

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.22'

      - name: Install Transire CLI
        run: |
          curl -sSL https://get.transire.dev | sh
          echo "$HOME/.transire/bin" >> $GITHUB_PATH

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to dev
        run: transire deploy --env dev --auto-approve
```

### Guard Blocks for Production

Require manual approval for prod:

```yaml
jobs:
  deploy-prod:
    runs-on: ubuntu-latest
    environment: production  # GitHub environment with protection rules

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to production
        run: transire deploy --env prod --auto-approve
```

## Command-Line Options

### `--env` (default: first environment)

```bash
transire deploy --env prod
```

Deploy to specific environment.

### `--plan` (default: false)

```bash
transire deploy --plan
```

Preview changes only, don't apply.

### `--auto-approve` (default: false)

```bash
transire deploy --auto-approve
```

Skip confirmation prompt.

### `--force` (default: false)

```bash
transire deploy --force
```

Force regeneration of infrastructure code (useful if templates change).

## Troubleshooting

### "Backend not initialized"

**Problem:** State backend not set up

**Solution:** Run init first:

```bash
transire init --backend
transire deploy
```

### "Failed to acquire lock"

**Problem:** Another deployment is in progress or previous deployment crashed

**Solution:** Wait for other deployment or force unlock:

```bash
# Check DynamoDB for lock
aws dynamodb get-item \
  --table-name tf-locks \
  --key '{"LockID": {"S": "orders-dev"}}'

# Force unlock (use with caution)
tofu force-unlock <lock-id>
```

### "Insufficient permissions"

**Problem:** AWS credentials lack required permissions

**Solution:** Verify IAM permissions:

```bash
aws iam get-user
```

Required permissions:
- Lambda: CreateFunction, UpdateFunctionCode, etc.
- API Gateway: CreateApi, CreateRoute, etc.
- SQS: CreateQueue, etc.
- EventBridge: PutRule, PutTargets, etc.
- IAM: CreateRole, AttachRolePolicy, etc.
- S3: PutObject, GetObject (for state)
- DynamoDB: PutItem, GetItem (for locking)

### "Resource already exists"

**Problem:** Resource created outside Transire

**Solution:** Import existing resource:

```bash
tofu import aws_lambda_function.get_orders orders-dev-get-orders
```

Or delete and let Transire recreate:

```bash
aws lambda delete-function --function-name orders-dev-get-orders
transire deploy
```

## Best Practices

### Always Run `transire gen` Before Deploy

```bash
transire gen && transire deploy
```

Ensures manifest is up-to-date.

### Use `--plan` for Production

```bash
# Preview changes
transire deploy --env prod --plan

# Review carefully

# Apply
transire deploy --env prod
```

### Separate State Per Environment

Configure unique state keys:

```yaml
env:
  - name: dev
    workspace: dev
  - name: prod
    workspace: prod
```

State keys:
- Dev: `orders/dev/terraform.tfstate`
- Prod: `orders/prod/terraform.tfstate`

### Tag Resources

Add tags for cost tracking:

```yaml
infra:
  tags:
    service: orders
    team: platform
    cost-center: engineering
```

### Monitor Deployments

Enable CloudWatch logs and set up alerts for deployment failures.

## See Also

- [transire init](/docs/cli/init.md) - Initialize backend
- [transire gen](/docs/cli/gen.md) - Generate manifest
- [Deployment Guide](/docs/guides/deployment.md) - Deployment best practices
- [Environments](/docs/guides/environments.md) - Multi-environment setup
- [AWS Overview](/docs/cloud/aws/overview.md) - AWS-specific details
- [OpenTofu](/docs/iac/opentofu.md) - IaC provider details
