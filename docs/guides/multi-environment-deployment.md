---
title: "Multi-Environment Deployment"
description: "Deploy Transire applications across dev, staging, and production environments with complete resource isolation"
keywords:
  - multi-environment
  - dev staging prod
  - environment isolation
  - deployment strategy
  - resource naming
  - environment-specific configuration
  - isolated deployments
category: guides
difficulty: intermediate
estimated_time: 15 minutes
prerequisites:
  - "Basic deployment knowledge"
  - "AWS account setup"
related_docs:
  - "guides/deploying-to-aws.md"
  - "cli-reference/transire-deploy.md"
  - "configuration/environment.md"
mcp_metadata:
  primary_use_cases:
    - "Setting up dev/staging/prod environments"
    - "Isolating resources across environments"
    - "Managing environment-specific configurations"
    - "Implementing deployment workflows"
    - "Understanding resource naming patterns"
  common_questions:
    - "How do I deploy to different environments?"
    - "How are resources isolated between environments?"
    - "How do I manage environment-specific settings?"
    - "What's the resource naming pattern?"
    - "How do I set up a deployment pipeline?"
    - "Can I deploy the same app to multiple environments?"
---

# Multi-Environment Deployment

Learn how to deploy your Transire application across development, staging, and production environments with complete resource isolation.

!!! tip "TL;DR"
    Use `--environment` flag to deploy to different environments. Transire automatically names all AWS resources as `{AppName}-{Environment}-{ResourceName}` ensuring complete isolation between dev/staging/prod deployments.

---

## Overview

Transire's multi-environment support enables you to deploy the same application to multiple isolated environments without resource conflicts. Each environment gets its own:

- **Lambda functions** with unique names
- **API Gateway endpoints** with separate URLs
- **SQS queues** with isolated message processing
- **EventBridge rules** with independent scheduling
- **CloudFormation stacks** for complete infrastructure separation

### Resource Naming Pattern

All AWS resources follow the consistent pattern:
```
{AppName}-{Environment}-{ResourceName}
```

**Examples:**
- Lambda: `my-api-dev-handler`, `my-api-prod-handler`
- SQS Queue: `my-api-staging-email-queue`
- API Gateway: `my-api-prod-api`
- EventBridge Rule: `my-api-dev-daily-cleanup`

---

## Environment Configuration

### Default Environment

If no environment is specified, Transire defaults to `dev`:

```bash
# These are equivalent
transire deploy
transire deploy --environment dev
```

### Supported Environments

While you can use any environment name, common patterns are:

- **`dev`** - Local development and testing
- **`staging`** - Pre-production testing and validation
- **`prod`** or **`production`** - Live production environment

```bash
# Deploy to development
transire deploy --environment dev

# Deploy to staging
transire deploy --environment staging

# Deploy to production
transire deploy --environment prod
```

---

## Complete Deployment Workflow

### 1. Development Environment

Set up your development environment for rapid iteration:

```bash
# Build for development
transire build --environment dev

# Deploy to development
transire deploy --environment dev
```

**Development characteristics:**
- Typically lower resource allocations
- More verbose logging
- Relaxed security for debugging
- Frequent deployments

### 2. Staging Environment

Create a production-like environment for testing:

```bash
# Build for staging
transire build --environment staging

# Deploy to staging
transire deploy --environment staging
```

**Staging characteristics:**
- Production-like configuration
- Performance testing
- Integration testing
- User acceptance testing

### 3. Production Environment

Deploy to your live production environment:

```bash
# Build for production
transire build --environment prod

# Deploy to production (with dry run first)
transire deploy --environment prod --dry-run
transire deploy --environment prod
```

**Production characteristics:**
- Optimized resource allocation
- Minimal logging
- Enhanced security
- Controlled deployment schedule

---

## Resource Isolation Examples

### Lambda Functions

Each environment gets its own Lambda functions:

```yaml
# Development
Function Name: my-api-dev-main
Log Group: /aws/lambda/my-api-dev-main

# Staging
Function Name: my-api-staging-main
Log Group: /aws/lambda/my-api-staging-main

# Production
Function Name: my-api-prod-main
Log Group: /aws/lambda/my-api-prod-main
```

### API Gateway Endpoints

Each environment gets a unique API endpoint:

```yaml
# Development
API Name: my-api-dev-api
URL: https://abc123.execute-api.us-east-1.amazonaws.com

# Staging
API Name: my-api-staging-api
URL: https://def456.execute-api.us-east-1.amazonaws.com

# Production
API Name: my-api-prod-api
URL: https://ghi789.execute-api.us-east-1.amazonaws.com
```

### SQS Queues

Queue isolation prevents cross-environment message processing:

```yaml
# Development
Queue: my-api-dev-email-queue
DLQ: my-api-dev-email-queue-dlq

# Staging
Queue: my-api-staging-email-queue
DLQ: my-api-staging-email-queue-dlq

# Production
Queue: my-api-prod-email-queue
DLQ: my-api-prod-email-queue-dlq
```

---

## Environment-Specific Configuration

### Environment Variables

Configure different settings per environment in `transire.yaml`:

```yaml
name: my-api

# Global environment variables
environment:
  SERVICE_NAME: my-api
  REGION: us-east-1

# Development-specific (set locally)
# LOG_LEVEL=debug transire deploy --environment dev
```

For environment-specific variables, use local environment variables:

```bash
# Development
export LOG_LEVEL=debug
export DATABASE_URL=postgres://localhost:5432/myapp_dev
transire deploy --environment dev

# Staging
export LOG_LEVEL=info
export DATABASE_URL=postgres://staging.db.com:5432/myapp
transire deploy --environment staging

# Production
export LOG_LEVEL=warn
export DATABASE_URL=postgres://prod.db.com:5432/myapp
transire deploy --environment prod
```

### Lambda Configuration

Customize Lambda settings per environment:

```yaml
# transire.yaml
lambda:
  memory: 256      # Development default
  timeout: 30      # Development default

# For production, consider higher allocations
# lambda:
#   memory: 1024   # Production
#   timeout: 60    # Production
```

---

## Multi-Region Deployments

Deploy the same environment to multiple regions:

```bash
# Deploy staging to multiple regions
transire deploy --environment staging --region us-east-1
transire deploy --environment staging --region eu-west-1
transire deploy --environment staging --region ap-southeast-1

# Deploy production globally
transire deploy --environment prod --region us-east-1
transire deploy --environment prod --region eu-west-1
```

Each region gets isolated resources:
- `my-api-prod-main` in us-east-1
- `my-api-prod-main` in eu-west-1
- `my-api-prod-main` in ap-southeast-1

---

## Deployment Strategies

### Manual Deployment

For small teams or simple applications:

```bash
# Developer workflow
git checkout feature-branch
# ... make changes ...
transire deploy --environment dev
# ... test changes ...

# Staging deployment
git checkout main
transire deploy --environment staging
# ... validate in staging ...

# Production deployment
transire deploy --environment prod
```

### CI/CD Pipeline

For automated deployments, use environment-specific secrets:

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Build and deploy to staging
        env:
          DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
          LOG_LEVEL: info
        run: |
          transire build --environment staging
          transire deploy --environment staging

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production  # Requires manual approval
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.PROD_AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.PROD_AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Build and deploy to production
        env:
          DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}
          LOG_LEVEL: warn
        run: |
          transire build --environment prod
          transire deploy --environment prod
```

---

## Monitoring and Management

### CloudFormation Stacks

Each environment creates a separate CloudFormation stack:

```bash
# List all stacks
aws cloudformation list-stacks

# View specific environment
aws cloudformation describe-stacks --stack-name my-api-dev
aws cloudformation describe-stacks --stack-name my-api-staging
aws cloudformation describe-stacks --stack-name my-api-prod
```

### CloudWatch Logs

Logs are isolated per environment:

```bash
# Development logs
aws logs tail /aws/lambda/my-api-dev-main --follow

# Staging logs
aws logs tail /aws/lambda/my-api-staging-main --follow

# Production logs
aws logs tail /aws/lambda/my-api-prod-main --follow
```

### Cost Management

Track costs per environment using AWS Cost Explorer with tags or by resource name patterns.

---

## Troubleshooting

### Environment Mismatch

**Problem:** Resources from wrong environment being accessed.

**Solution:** Verify environment flag and resource names:
```bash
# Check which environment you're targeting
echo $AWS_DEFAULT_REGION
aws sts get-caller-identity

# Verify deployment
transire deploy --environment staging --dry-run
```

### Cross-Environment Contamination

**Problem:** Development affecting production data.

**Solution:** Use separate AWS accounts or IAM boundaries:
```yaml
# Separate AWS accounts (recommended)
Development AWS Account: 111111111111
Staging AWS Account: 222222222222
Production AWS Account: 333333333333
```

### Resource Name Conflicts

**Problem:** Resources not properly isolated.

**Solution:** Ensure environment flag is used consistently:
```bash
# Always specify environment explicitly
transire build --environment prod
transire deploy --environment prod

# Never mix environments
❌ transire build --environment dev
❌ transire deploy --environment prod
```

---

## Best Practices

### 1. Environment Consistency

- Use the same `transire.yaml` across all environments
- Vary configuration through environment variables
- Test staging with production-like data volumes

### 2. Deployment Discipline

- Always deploy to `dev` first
- Validate in `staging` before production
- Use `--dry-run` for production deployments

### 3. Resource Management

- Monitor costs per environment
- Clean up unused development deployments
- Use separate AWS accounts for production isolation

### 4. Security

- Use different IAM roles per environment
- Restrict production access
- Audit environment deployments

---

## Next Steps

- [Configuration Reference](../configuration/transire-yaml.md) – Customize per-environment settings
- [Deploying to AWS](deploying-to-aws.md) – Complete AWS deployment guide
- [Environment Variables](../configuration/environment.md) – Manage secrets and config
- [CI/CD Integration](../examples/cicd-pipelines.md) – Automate deployments

---

## See Also

- [transire deploy](../cli-reference/transire-deploy.md) – Deploy command reference
- [transire build](../cli-reference/transire-build.md) – Build command reference
- [Custom CDK Extensions](custom-cdk.md) – Extend generated infrastructure