---
title: "Environments Guide"
category: guides
subcategory: null
complexity: intermediate
duration: 15 minutes
prerequisites:
  - Understanding of Transire deployment
  - Familiarity with transire.yaml
  - OpenTofu/Terraform basics
mcp_use: reference
mcp_operations:
  - configure_environments
  - manage_workspaces
features_covered:
  - Multi-environment strategy
  - Environment configuration
  - OpenTofu workspaces
  - Environment variables
  - Environment promotion
  - Isolation and security
code_blocks: true
last_updated: 2025-10-30
---

# Environments Guide

## Overview

Transire supports multiple deployment environments (development, staging, production) with isolated infrastructure, separate configurations, and environment-specific variables. Each environment uses OpenTofu workspaces to maintain separate state.

**Key benefits:**
- Complete resource isolation between environments
- Environment-specific configuration
- Safe testing before production
- Cost management per environment
- Parallel development workflows

## Environment Strategy

### Standard Environment Setup

Most teams use a three-tier environment structure:

| Environment | Purpose | Branch | Auto-Deploy | Approval |
|-------------|---------|--------|-------------|----------|
| **Development** | Active development and testing | `develop` | Yes | No |
| **Staging** | Pre-production validation | `develop` or `staging` | Yes | No |
| **Production** | Live application | `main` | Optional | Yes |

### Environment Naming

Use consistent, short environment names:

```yaml
# transire.yaml
env:
  - name: dev      # Development
  - name: staging  # Staging
  - name: prod     # Production
```

**Resource naming convention:**
```
{service}-{environment}-{resource}

Examples:
  myapp-dev-http         (Lambda function)
  myapp-prod-http        (Lambda function)
  myapp-staging-orders   (SQS queue)
```

## Configuring Environments

### Basic Configuration

Define environments in `transire.yaml`:

```yaml
version: 1
service: myapp
runtime: go
cloud: aws

env:
  - name: dev
    workspace: dev
    variables:
      LOG_LEVEL: debug
      FEATURE_FLAGS: all

  - name: staging
    workspace: staging
    variables:
      LOG_LEVEL: info
      FEATURE_FLAGS: stable

  - name: prod
    workspace: prod
    variables:
      LOG_LEVEL: warn
      FEATURE_FLAGS: stable
```

### Environment-Specific Settings

Override deployment settings per environment:

```yaml
env:
  - name: dev
    workspace: dev
    deploy:
      memory_mb: 256
      timeout_s: 30
    variables:
      LOG_LEVEL: debug

  - name: prod
    workspace: prod
    deploy:
      memory_mb: 512      # More memory in production
      timeout_s: 60       # Longer timeout
    variables:
      LOG_LEVEL: warn
```

### Environment Variables

**Static variables** (checked into git):

```yaml
env:
  - name: dev
    variables:
      API_URL: https://api-dev.example.com
      MAX_RETRIES: "3"
      ENABLE_CACHE: "true"
```

**Secrets** (from AWS Secrets Manager or Parameter Store):

```yaml
env:
  - name: prod
    variables:
      API_URL: https://api.example.com
    secrets:
      - DB_PASSWORD: /myapp/prod/db_password  # SSM Parameter Store
      - API_KEY: myapp/prod/api_key           # Secrets Manager
```

**Accessing variables in code:**

```go
func main() {
    logLevel := os.Getenv("LOG_LEVEL")
    if logLevel == "" {
        logLevel = "info"
    }

    apiURL := os.Getenv("API_URL")
    // ... use variables ...
}
```

## OpenTofu Workspaces

Transire uses OpenTofu workspaces to isolate environment state:

```
Backend: s3://myapp-tf-state/myapp/
├── dev/          # Development workspace
│   └── terraform.tfstate
├── staging/      # Staging workspace
│   └── terraform.tfstate
└── prod/         # Production workspace
    └── terraform.tfstate
```

### Workspace Management

**List workspaces:**

```bash
cd infra
tofu workspace list
```

**Select workspace:**

```bash
tofu workspace select prod
```

**View current workspace:**

```bash
tofu workspace show
```

### Automatic Workspace Selection

Transire automatically selects the correct workspace during deployment:

```bash
# Deploys to dev workspace
transire deploy --env dev

# Deploys to prod workspace
transire deploy --env prod
```

## Deploying to Environments

### Development Environment

Deploy frequently to development:

```bash
transire deploy --env dev
```

**Development characteristics:**
- Rapid iteration
- Lower resource limits
- Debug logging enabled
- Shorter timeouts acceptable
- Lower cost

### Staging Environment

Deploy to staging before production:

```bash
transire deploy --env staging
```

**Staging characteristics:**
- Production-like configuration
- Production-like data (anonymized)
- Integration testing
- Performance testing
- Pre-production validation

### Production Environment

Deploy to production with care:

```bash
transire deploy --env prod
```

**Production characteristics:**
- Manual approval gates (recommended)
- Higher resource limits
- Monitoring and alerting
- Optimized for performance
- Real user traffic

## Environment Isolation

### Resource Isolation

Each environment has completely separate resources:

**Lambda functions:**
```
myapp-dev-http
myapp-staging-http
myapp-prod-http
```

**SQS queues:**
```
myapp-dev-orders
myapp-staging-orders
myapp-prod-orders
```

**API Gateway:**
```
https://dev-api.example.com
https://staging-api.example.com
https://api.example.com
```

### IAM Isolation

Create separate IAM roles per environment:

```hcl
# Generated by Transire in infra/iam.tf
resource "aws_iam_role" "http_lambda" {
  name = "${var.service}-${var.environment}-http-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}
```

**Principle of least privilege:**
- Dev has minimal permissions
- Staging mirrors production permissions
- Production has exactly what's needed

### Network Isolation

**With VPC (optional):**

```yaml
infra:
  vpc:
    enabled: true
    cidr: 10.0.0.0/16
    subnets:
      - dev: 10.0.1.0/24
      - staging: 10.0.2.0/24
      - prod: 10.0.3.0/24
```

**Separate VPCs per environment:**
```
myapp-dev-vpc     (10.0.0.0/16)
myapp-staging-vpc (10.1.0.0/16)
myapp-prod-vpc    (10.2.0.0/16)
```

## Environment Promotion

### Code Promotion Workflow

**1. Develop in feature branch:**

```bash
git checkout -b feature/new-endpoint
# ... make changes ...
git push origin feature/new-endpoint
```

**2. Merge to develop (deploys to dev):**

```bash
git checkout develop
git merge feature/new-endpoint
git push origin develop
# CI/CD auto-deploys to dev
```

**3. Test in development:**

```bash
curl https://dev-api.example.com/orders
```

**4. Merge to staging branch (if using):**

```bash
git checkout staging
git merge develop
git push origin staging
# CI/CD auto-deploys to staging
```

**5. Merge to main (deploys to production):**

```bash
git checkout main
git merge staging
git push origin main
# CI/CD deploys to prod with approval
```

### Data Promotion

**DO NOT** promote data from dev/staging to production.

**For testing:**
- Use anonymized production data in staging
- Use synthetic data in development
- Never use production credentials in non-prod

**Seed data script:**

```go
// cmd/seed/main.go
package main

import (
    "os"
    "github.com/yourorg/myapp"
)

func main() {
    env := os.Getenv("ENVIRONMENT")

    if env == "prod" {
        panic("Cannot seed production environment")
    }

    // Seed test data for dev/staging
    seedTestData()
}
```

## Cost Management

### Environment Cost Allocation

**Tag resources for cost tracking:**

```yaml
infra:
  tags:
    Environment: "{{ .Environment }}"
    Service: "{{ .Service }}"
    CostCenter: engineering
```

**View costs per environment:**

```bash
# AWS Cost Explorer CLI
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=TAG,Key=Environment
```

### Development Cost Optimization

**Lower resource limits in dev:**

```yaml
env:
  - name: dev
    deploy:
      memory_mb: 128      # Minimum
      timeout_s: 15       # Short timeout
      arch: arm64         # Cost-effective
```

**Auto-shutdown dev resources (optional):**

```hcl
# infra/overrides/dev_shutdown.tf
resource "aws_lambda_function" "shutdown_dev" {
  count = var.environment == "dev" ? 1 : 0

  # Lambda that stops dev resources at night
}
```

### Production Cost Optimization

**Right-size resources:**

```yaml
env:
  - name: prod
    deploy:
      memory_mb: 512      # Based on profiling
      timeout_s: 30       # Optimized
      arch: arm64         # 20% cheaper than x86
```

**Monitor and adjust:**
- Review Lambda CloudWatch Metrics
- Check actual memory usage
- Optimize cold start time
- Use Lambda Power Tuning tool

## Multi-Region Deployment

Deploy to multiple AWS regions:

```yaml
env:
  - name: prod-us
    workspace: prod-us
    region: us-east-1
    variables:
      PRIMARY_REGION: "true"

  - name: prod-eu
    workspace: prod-eu
    region: eu-west-1
    variables:
      PRIMARY_REGION: "false"
```

**Deploy to specific region:**

```bash
transire deploy --env prod-us
transire deploy --env prod-eu
```

**Global routing (via Route 53):**

```hcl
# infra/overrides/global_routing.tf
resource "aws_route53_record" "api" {
  zone_id = var.hosted_zone_id
  name    = "api.example.com"
  type    = "A"

  alias {
    name                   = aws_api_gateway_domain_name.global.regional_domain_name
    zone_id                = aws_api_gateway_domain_name.global.regional_zone_id
    evaluate_target_health = true
  }

  latency_routing_policy {
    region = var.region
  }

  set_identifier = var.region
}
```

## Environment-Specific Testing

### Development Testing

```bash
# Run tests against dev environment
ENVIRONMENT=dev go test ./integration/...

# Or use test fixtures
APP_URL=https://dev-api.example.com go test ./e2e/...
```

### Staging Smoke Tests

```bash
# Run smoke tests after staging deployment
./scripts/smoke-test.sh staging
```

**Smoke test script:**

```bash
#!/bin/bash
ENV=$1
API_URL=$(aws ssm get-parameter --name "/myapp/${ENV}/api_url" --query Parameter.Value --output text)

# Test health endpoint
curl -f "${API_URL}/health" || exit 1

# Test critical endpoints
curl -f "${API_URL}/orders" || exit 1

echo "✓ Smoke tests passed"
```

### Production Monitoring

Set up continuous monitoring:

```yaml
# CloudWatch Synthetics Canary
Resources:
  HealthCheckCanary:
    Type: AWS::Synthetics::Canary
    Properties:
      Name: myapp-prod-health
      RuntimeVersion: syn-nodejs-puppeteer-3.9
      Schedule:
        Expression: rate(5 minutes)
      Code:
        Handler: healthcheck.handler
        Script: |
          exports.handler = async () => {
            const response = await fetch('https://api.example.com/health');
            if (!response.ok) throw new Error('Health check failed');
          };
```

## Security Best Practices

### Secrets Management

**DO NOT** store secrets in `transire.yaml`:

```yaml
# ❌ BAD - Secrets in config
env:
  - name: prod
    variables:
      DB_PASSWORD: mysecretpassword  # Never do this!
```

**DO** use AWS Secrets Manager:

```yaml
# ✓ GOOD - Reference secrets
env:
  - name: prod
    secrets:
      - DB_PASSWORD: /myapp/prod/db_password
```

**Store secrets:**

```bash
aws secretsmanager create-secret \
  --name /myapp/prod/db_password \
  --secret-string "secure-password-here"
```

### Cross-Environment Access

**Prevent cross-environment access:**

```hcl
# IAM policy preventing cross-environment access
resource "aws_iam_policy" "lambda_restricted" {
  name = "${var.service}-${var.environment}-restricted"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["sqs:*"]
        Resource = "arn:aws:sqs:*:*:${var.service}-${var.environment}-*"
      },
      {
        Effect = "Deny"
        Action = ["sqs:*"]
        Resource = "arn:aws:sqs:*:*:${var.service}-prod-*"
        Condition = {
          StringNotEquals = {
            "aws:ResourceTag/Environment" = var.environment
          }
        }
      }
    ]
  })
}
```

## Troubleshooting

### Wrong Environment Deployed

**Verify current environment:**

```bash
# Check deployed environment
aws lambda get-function --function-name myapp-prod-http | jq .Tags.Environment
```

**Verify workspace:**

```bash
cd infra
tofu workspace show
```

### Environment Variables Not Applied

**Check Lambda environment variables:**

```bash
aws lambda get-function-configuration \
  --function-name myapp-prod-http \
  | jq .Environment
```

**Update environment variables:**

```bash
# After changing transire.yaml
transire deploy --env prod
```

### Cross-Environment Resource Access

**Symptom:** Dev environment accessing prod resources

**Solution:** Review IAM policies and resource names

```bash
# Check Lambda IAM role
aws lambda get-function \
  --function-name myapp-dev-http \
  | jq .Configuration.Role

# View role policies
aws iam list-attached-role-policies \
  --role-name myapp-dev-http-role
```

## Best Practices

1. **Consistent naming** - Use same environment names everywhere
2. **Isolate resources** - Never share resources between environments
3. **Separate accounts** - Consider separate AWS accounts for prod
4. **Tag everything** - Enable cost allocation and tracking
5. **Test promotion** - Always test in dev/staging before prod
6. **Document differences** - Keep track of environment-specific config
7. **Automate deployments** - Use CI/CD for consistency
8. **Monitor all environments** - Don't ignore non-prod alerts
9. **Limit production access** - Restrict who can deploy to prod
10. **Regular cleanup** - Delete old dev/staging resources

## See Also

- [Deployment Guide](/guides/deployment.md) - Deployment workflow
- [OpenTofu Workspaces](/iac/workspaces.md) - Workspace management
- [GitHub Actions CI/CD](/ci/github-actions.md) - Automated environments
- [Config Schema](/reference/config-schema.md) - Configuration reference
