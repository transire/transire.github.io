---
title: "AWS Deployment"
category: cloud
subcategory: aws
complexity: intermediate
duration: null
prerequisites:
  - AWS account
  - AWS CLI configured
  - OpenTofu installed
mcp_use: reference
features_covered:
  - AWS deployment process
  - Infrastructure provisioning
  - Lambda deployment
code_blocks: true
last_updated: 2025-10-31
---

# AWS Deployment

## Overview

Transire deploys to AWS using serverless services with infrastructure managed by OpenTofu.

## Architecture

When you deploy to AWS, Transire creates:

- **Lambda functions** - One per handler (HTTP, queue, scheduled)
- **API Gateway** - Routes HTTP requests to Lambda functions
- **SQS queues** - Message queues with DLQs
- **EventBridge rules** - Scheduled task triggers
- **IAM roles** - Least-privilege permissions per function

## Prerequisites

### 1. AWS Account

You need an AWS account with appropriate permissions to create:
- Lambda functions
- API Gateway resources
- SQS queues
- EventBridge rules
- IAM roles and policies
- S3 buckets (for OpenTofu state)

### 2. AWS CLI

Install and configure the AWS CLI:

```bash
# Install (macOS)
brew install awscli

# Configure credentials
aws configure
```

### 3. OpenTofu

Install OpenTofu:

```bash
# macOS
brew install opentofu

# Or use the install script
./install-opentofu.sh
```

## First-Time Setup

### Initialize Backend

Before your first deployment, initialize the OpenTofu backend:

```bash
transire init --backend
```

This creates:
- S3 bucket for OpenTofu state
- DynamoDB table for state locking
- Backend configuration

## Deployment Process

### 1. Generate Manifest

```bash
transire gen
```

This analyzes your code and generates `transire_manifest.json`.

### 2. Deploy

```bash
# Deploy to default (dev) environment
transire deploy

# Deploy to specific environment
transire deploy --env production
```

### What Happens During Deployment

1. **Manifest validation** - Checks for configuration errors
2. **Code packaging** - Builds Lambda deployment packages
3. **Infrastructure generation** - Creates OpenTofu configurations
4. **OpenTofu plan** - Shows what will be created/changed
5. **OpenTofu apply** - Creates/updates AWS resources
6. **Output generation** - Displays deployment URLs and resource info

## Configuration

### Deployment Settings

Configure deployment in `transire.yaml`:

```yaml
deploy:
  lambda:
    architecture: arm64  # arm64 or x86_64
    memory: 512         # MB
    timeout: 30         # seconds
    runtime: provided.al2023

cloud:
  provider: aws
  region: us-east-1
```

### Environment-Specific Configuration

Use environment variables for different environments:

```yaml
env:
  dev:
    LOG_LEVEL: debug
    DB_HOST: dev-db.example.com

  production:
    LOG_LEVEL: info
    DB_HOST: prod-db.example.com
```

## Deployment Outputs

After deployment, you'll see:

```
Deployment successful!

HTTP Endpoint: https://abc123.execute-api.us-east-1.amazonaws.com
API Gateway ID: abc123
Lambda Functions:
  - GetUsers: arn:aws:lambda:us-east-1:123456789012:function:myapp-GetUsers
  - CreateOrder: arn:aws:lambda:us-east-1:123456789012:function:myapp-CreateOrder

SQS Queues:
  - orders: https://sqs.us-east-1.amazonaws.com/123456789012/myapp-orders
```

## Testing Deployment

Test your deployed application:

```bash
# Test HTTP endpoint
curl https://abc123.execute-api.us-east-1.amazonaws.com/users

# Test with authentication
curl -H "Authorization: Bearer token" \
  https://abc123.execute-api.us-east-1.amazonaws.com/users
```

## Environments

Transire uses OpenTofu workspaces for environments:

```bash
# List environments
transire deploy --list

# Deploy to production
transire deploy --env production

# Switch between environments
transire deploy --env staging
```

See [Environments Guide](/docs/guides/environments.md) for details.

## Permissions

Transire generates least-privilege IAM policies for each function.

See [AWS Permissions](/docs/cloud/aws/permissions.md) for details on:
- Default permissions
- Custom permissions
- Security best practices

## Monitoring

Monitor your deployment:

```bash
# CloudWatch Logs
aws logs tail /aws/lambda/myapp-GetUsers --follow

# Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=myapp-GetUsers
```

## Updating Deployment

To update your deployment:

```bash
# Make code changes
# Regenerate manifest
transire gen

# Deploy updates
transire deploy
```

OpenTofu will only update changed resources.

## Rollback

To rollback a deployment:

```bash
# View deployment history
cd infra
tofu state list

# Rollback (manual process)
git checkout previous-version
transire deploy
```

## Cleanup

To destroy all resources:

```bash
cd infra
tofu destroy
```

**Warning:** This deletes all cloud resources including data in queues.

## Troubleshooting

### Deployment fails

1. **Check AWS credentials:**
   ```bash
   aws sts get-caller-identity
   ```

2. **Verify permissions:**
   - Ensure IAM user/role has necessary permissions
   - Check service quotas

3. **Review logs:**
   ```bash
   transire deploy --debug
   ```

### Function errors after deployment

1. **Check CloudWatch Logs:**
   ```bash
   aws logs tail /aws/lambda/function-name --follow
   ```

2. **Verify environment variables** in AWS Console

3. **Test function directly:**
   ```bash
   aws lambda invoke \
     --function-name myapp-GetUsers \
     --payload '{}' \
     response.json
   ```

For more troubleshooting, see the [Troubleshooting Guide](/docs/guides/troubleshooting.md).

## Best Practices

1. **Use separate AWS accounts** for dev/staging/prod
2. **Enable CloudWatch Logs** for all functions
3. **Set appropriate timeouts** based on function needs
4. **Use ARM64** for better price/performance
5. **Monitor costs** with AWS Cost Explorer
6. **Tag resources** for better organization

## See Also

- [AWS HTTP Handlers](/docs/cloud/aws/http.md)
- [AWS Queue Handlers](/docs/cloud/aws/queues.md)
- [AWS Scheduled Handlers](/docs/cloud/aws/schedules.md)
- [AWS Permissions](/docs/cloud/aws/permissions.md)
- [Environments Guide](/docs/guides/environments.md)
- [IaC Overview](/docs/iac/overview.md)
