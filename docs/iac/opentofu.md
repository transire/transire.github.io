---
title: "OpenTofu Integration"
category: iac
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - OpenTofu basics
  - Infrastructure as Code concepts
mcp_use: reference
features_covered:
  - OpenTofu usage
  - Infrastructure management
  - State management
code_blocks: true
last_updated: 2025-10-31
---

# OpenTofu Integration

This guide covers how Transire uses OpenTofu for infrastructure management.

## Overview

Transire uses OpenTofu (Terraform-compatible) to:
- Generate infrastructure code from your manifest
- Manage cloud resources declaratively
- Track infrastructure state
- Enable safe updates and rollbacks

## Installation

### macOS

```bash
brew install opentofu
```

### Linux

```bash
# Download and install
curl -Lo /tmp/tofu.tar.gz \
  https://github.com/opentofu/opentofu/releases/download/v1.6.0/tofu_1.6.0_linux_amd64.tar.gz

tar -xzf /tmp/tofu.tar.gz -C /usr/local/bin
```

### Verify Installation

```bash
tofu --version
```

## Project Structure

After running `transire deploy`, you'll see:

```
infra/
├── backend.tf           # Backend configuration
├── provider.tf          # Cloud provider config
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── resources/           # Generated resources
│   ├── http.tf         # API Gateway, Lambda functions
│   ├── queues.tf       # SQS queues
│   └── schedules.tf    # EventBridge rules
├── overrides/          # User customizations
│   └── custom.tf
└── terraform.tfstate   # State file (if using local backend)
```

## Generated Infrastructure

### HTTP Resources

Generated in `infra/resources/http.tf`:

```hcl
# API Gateway
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.service_name}-api"
  protocol_type = "HTTP"
}

# Lambda function for HTTP handler
resource "aws_lambda_function" "get_users" {
  function_name = "${var.service_name}-GetUsers"
  role          = aws_iam_role.get_users.arn
  handler       = "bootstrap"
  runtime       = "provided.al2023"
  architectures = ["arm64"]

  filename         = "../../.transire/packages/GetUsers.zip"
  source_code_hash = filebase64sha256("../../.transire/packages/GetUsers.zip")

  memory_size = 512
  timeout     = 30

  environment {
    variables = var.env_vars
  }
}

# API Gateway integration
resource "aws_apigatewayv2_integration" "get_users" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  integration_uri    = aws_lambda_function.get_users.invoke_arn
  integration_method = "POST"
}

# Route
resource "aws_apigatewayv2_route" "get_users" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /users"
  target    = "integrations/${aws_apigatewayv2_integration.get_users.id}"
}
```

### Queue Resources

Generated in `infra/resources/queues.tf`:

```hcl
# SQS queue
resource "aws_sqs_queue" "orders" {
  name                      = "${var.service_name}-orders"
  visibility_timeout_seconds = 60
  message_retention_seconds = 345600  # 4 days

  # Dead letter queue
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.orders_dlq.arn
    maxReceiveCount     = 3
  })
}

# Dead letter queue
resource "aws_sqs_queue" "orders_dlq" {
  name                      = "${var.service_name}-orders-dlq"
  message_retention_seconds = 1209600  # 14 days
}

# Lambda function for queue handler
resource "aws_lambda_function" "process_orders" {
  function_name = "${var.service_name}-ProcessOrders"
  # ... similar to HTTP function
}

# Event source mapping
resource "aws_lambda_event_source_mapping" "orders" {
  event_source_arn = aws_sqs_queue.orders.arn
  function_name    = aws_lambda_function.process_orders.arn

  batch_size                         = 10
  maximum_batching_window_in_seconds = 5
}
```

### Scheduled Resources

Generated in `infra/resources/schedules.tf`:

```hcl
# EventBridge rule
resource "aws_cloudwatch_event_rule" "daily_cleanup" {
  name                = "${var.service_name}-daily-cleanup"
  schedule_expression = "cron(0 0 * * ? *)"  # Daily at midnight UTC
}

# Lambda function
resource "aws_lambda_function" "daily_cleanup" {
  function_name = "${var.service_name}-DailyCleanup"
  # ... similar to HTTP function
}

# EventBridge target
resource "aws_cloudwatch_event_target" "daily_cleanup" {
  rule      = aws_cloudwatch_event_rule.daily_cleanup.name
  target_id = "lambda"
  arn       = aws_lambda_function.daily_cleanup.arn
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge_daily_cleanup" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.daily_cleanup.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_cleanup.arn
}
```

## Customization

### Override Files

Add customizations in `infra/overrides/`:

```hcl
# infra/overrides/custom.tf

# Add custom resource
resource "aws_dynamodb_table" "users" {
  name           = "${var.service_name}-users"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }
}

# Modify generated resource
resource "aws_lambda_function" "get_users" {
  # Override memory size
  memory_size = 1024
}
```

### Variables

Define custom variables in `infra/overrides/variables.tf`:

```hcl
variable "database_name" {
  description = "Database name"
  type        = string
  default     = "myapp"
}

variable "enable_caching" {
  description = "Enable caching"
  type        = bool
  default     = true
}
```

Use in resources:

```hcl
resource "aws_elasticache_cluster" "cache" {
  count = var.enable_caching ? 1 : 0

  cluster_id           = "${var.service_name}-cache"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
}
```

## State Management

### Local Backend

Default for development:

```hcl
# infra/backend.tf
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}
```

### S3 Backend

For production, use S3 backend (created by `transire init --backend`):

```hcl
# infra/backend.tf
terraform {
  backend "s3" {
    bucket         = "transire-state-bucket"
    key            = "myapp/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "transire-state-lock"
    encrypt        = true
  }
}
```

## Workspaces

Use workspaces for environments:

```bash
# List workspaces
cd infra
tofu workspace list

# Create workspace
tofu workspace new production

# Switch workspace
tofu workspace select production

# Deploy to workspace
cd ..
transire deploy --env production
```

Each workspace has its own state file.

## Common Operations

### View Plan

See what will change:

```bash
cd infra
tofu plan
```

### Apply Changes

Apply infrastructure changes:

```bash
tofu apply
```

### View State

```bash
# List resources
tofu state list

# Show resource details
tofu state show aws_lambda_function.get_users
```

### Import Existing Resources

```bash
# Import existing Lambda function
tofu import aws_lambda_function.get_users myapp-GetUsers
```

### Destroy Infrastructure

```bash
# Destroy all resources
tofu destroy

# Destroy specific resource
tofu destroy -target=aws_lambda_function.get_users
```

## Troubleshooting

### State Lock Issues

If state is locked:

```bash
# Force unlock (use with caution)
tofu force-unlock LOCK_ID
```

### State Drift

Check for drift between code and actual resources:

```bash
tofu plan -refresh-only
```

### Debugging

Enable debug logging:

```bash
TF_LOG=DEBUG tofu apply
```

## Best Practices

1. **Use remote backend** - Don't commit `terraform.tfstate`
2. **Use workspaces** - Separate environments
3. **Review plans** - Always run `tofu plan` before `apply`
4. **Version lock** - Lock OpenTofu version in CI
5. **Modularize** - Use modules for reusable infrastructure
6. **Tag resources** - Tag all resources for organization
7. **Enable versioning** - On S3 state bucket
8. **Backup state** - Regular backups of state files
9. **Test changes** - Test in dev before production
10. **Document overrides** - Comment custom resources

## Integration with Transire

Transire automates OpenTofu:

```bash
# This command:
transire deploy

# Does:
# 1. transire gen           (generate manifest)
# 2. Package functions      (create Lambda packages)
# 3. Generate .tf files     (in infra/resources/)
# 4. tofu init             (initialize)
# 5. tofu plan             (show plan)
# 6. tofu apply            (if approved)
```

You can also run OpenTofu manually:

```bash
cd infra
tofu init
tofu plan
tofu apply
```

## See Also

- [IaC Overview](/docs/iac/overview.md)
- [Backend Configuration](/docs/iac/backend.md)
- [Workspaces](/docs/iac/workspaces.md)
- [AWS Deployment](/docs/cloud/aws/deployment.md)
- [OpenTofu Documentation](https://opentofu.org/docs/)
