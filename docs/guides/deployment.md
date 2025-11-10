---
title: "Deployment Guide"
category: guides
subcategory: null
complexity: intermediate
duration: 20 minutes
prerequisites:
  - AWS account with appropriate permissions
  - AWS CLI configured
  - Transire project with transire.yaml
  - Application tested locally
mcp_use: reference
mcp_operations:
  - deploy_to_cloud
  - setup_backend
features_covered:
  - First deployment
  - Backend initialization
  - Multi-environment deployment
  - Rollback strategies
  - Monitoring deployments
code_blocks: true
last_updated: 2025-10-30
---

# Deployment Guide

## Overview

Deploying a Transire application involves generating infrastructure-as-code, packaging your handlers, and provisioning cloud resources. This guide walks through the complete deployment workflow from initial setup to production.

**Deployment flow:**
1. Generate manifest (`transire gen`)
2. Initialize backend (first time only)
3. Deploy to cloud (`transire deploy`)
4. Verify deployment
5. Monitor and maintain

## Prerequisites

Before deploying, ensure you have:

### AWS Account Setup

**1. Create AWS account:**
- Sign up at [aws.amazon.com](https://aws.amazon.com)
- Complete identity verification
- Add payment method

**2. Create IAM user with deployment permissions:**

```bash
# Create IAM user
aws iam create-user --user-name transire-deployer

# Attach policies
aws iam attach-user-policy \
  --user-name transire-deployer \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# Create access key
aws iam create-access-key --user-name transire-deployer
```

**3. Configure AWS CLI:**

```bash
aws configure
# AWS Access Key ID: [Your access key]
# AWS Secret Access Key: [Your secret key]
# Default region name: us-east-1
# Default output format: json
```

**Verify configuration:**

```bash
aws sts get-caller-identity
```

### Local Setup

**Install Transire CLI:**

```bash
# macOS
brew install transire/tap/transire

# Linux
curl -L https://github.com/transire/cli/releases/latest/download/transire-linux-amd64 -o transire
chmod +x transire
sudo mv transire /usr/local/bin/

# Verify installation
transire version
```

**Configure your project:**

Ensure you have a valid `transire.yaml`:

```yaml
version: 1
service: myapp
runtime: go
cloud: aws
iac: opentofu

deploy:
  arch: arm64
  memory_mb: 256
  timeout_s: 30

infra:
  backend:
    type: s3
    bucket: myapp-tf-state
    dynamodb_table: tf-locks
    key_prefix: myapp/
```

## First Deployment

### Step 1: Generate Manifest

Generate the build-time manifest:

```bash
transire gen
```

This creates `transire_manifest.json` with all routes, queues, and schedules.

**Verify manifest:**

```bash
cat transire_manifest.json | jq .
```

### Step 2: Initialize Backend

**First deployment only** - Bootstrap OpenTofu backend:

```bash
transire init --backend
```

This creates:
- S3 bucket for Terraform state (`myapp-tf-state`)
- DynamoDB table for state locking (`tf-locks`)
- Proper bucket policies and encryption

**What happens:**
```
Creating S3 bucket: myapp-tf-state
Enabling versioning on bucket
Enabling encryption (AES-256)
Creating DynamoDB table: tf-locks
Setting up table with LockID partition key
✓ Backend initialized successfully
```

**Manual backend setup (alternative):**

If you prefer to create resources manually:

```bash
# Create S3 bucket
aws s3api create-bucket \
  --bucket myapp-tf-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket myapp-tf-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table
aws dynamodb create-table \
  --table-name tf-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### Step 3: Deploy Application

Deploy to AWS:

```bash
transire deploy
```

**Deployment process:**

```
Generating manifest...
✓ Manifest generated

Packaging handlers...
  ✓ HTTP handler packaged: myapp-dev-http.zip
  ✓ Queue handler packaged: myapp-dev-queue-ProcessedOrder.zip
  ✓ Scheduled handler packaged: myapp-dev-scheduled-dailyReport.zip

Generating infrastructure...
  ✓ Generated: infra/backend.tf
  ✓ Generated: infra/api_gateway.tf
  ✓ Generated: infra/lambdas/http.tf
  ✓ Generated: infra/lambdas/queues.tf
  ✓ Generated: infra/lambdas/scheduled.tf
  ✓ Generated: infra/iam.tf

Initializing OpenTofu...
  ✓ Initialized backend (s3://myapp-tf-state/myapp/dev)

Planning changes...
  Plan: 15 to add, 0 to change, 0 to destroy

Applying changes...
  ✓ Created: IAM role (myapp-dev-http-role)
  ✓ Created: Lambda function (myapp-dev-http)
  ✓ Created: API Gateway (myapp-dev-api)
  ✓ Created: SQS queue (myapp-dev-ProcessedOrder)
  ✓ Created: EventBridge rule (myapp-dev-dailyReport)

✓ Deployment complete!

API Gateway URL: https://abc123.execute-api.us-east-1.amazonaws.com
```

### Step 4: Verify Deployment

**Test HTTP endpoint:**

```bash
curl https://abc123.execute-api.us-east-1.amazonaws.com/orders
```

**View Lambda logs:**

```bash
aws logs tail /aws/lambda/myapp-dev-http --follow
```

**Check infrastructure:**

```bash
# List created resources
aws lambda list-functions | grep myapp-dev
aws sqs list-queues | grep myapp-dev
aws events list-rules | grep myapp-dev
```

## Environment-Specific Deployment

Deploy to different environments (dev, staging, prod):

### Configure Environments

In `transire.yaml`:

```yaml
env:
  - name: dev
    workspace: dev
    variables:
      LOG_LEVEL: debug
      DB_URL: postgres://dev.example.com

  - name: staging
    workspace: staging
    variables:
      LOG_LEVEL: info
      DB_URL: postgres://staging.example.com

  - name: prod
    workspace: prod
    variables:
      LOG_LEVEL: warn
      DB_URL: postgres://prod.example.com
```

### Deploy to Specific Environment

```bash
# Deploy to dev (default)
transire deploy

# Deploy to staging
transire deploy --env staging

# Deploy to production
transire deploy --env prod
```

**Each environment gets isolated resources:**
- Lambda functions: `myapp-{env}-http`
- SQS queues: `myapp-{env}-ProcessedOrder`
- API Gateway: separate endpoint per environment
- OpenTofu workspace: separate state per environment

## Updating Deployments

### Code Changes

**1. Modify your handlers:**

```go
func getOrder(w http.ResponseWriter, r *http.Request) {
    // Updated handler logic
}
```

**2. Regenerate manifest:**

```bash
transire gen
```

**3. Deploy changes:**

```bash
transire deploy
```

**What happens:**
- Code changes → Lambda functions are updated
- New routes/queues → Infrastructure is created
- Removed routes/queues → Infrastructure is destroyed (with confirmation)

### Configuration Changes

**Update `transire.yaml`:**

```yaml
deploy:
  memory_mb: 512  # Increased from 256
  timeout_s: 60   # Increased from 30
```

**Deploy configuration changes:**

```bash
transire deploy
```

Lambda functions are updated with new configuration.

### Infrastructure Changes

**Add custom infrastructure** in `infra/overrides/`:

```hcl
# infra/overrides/custom.tf
resource "aws_s3_bucket" "uploads" {
  bucket = "${var.service}-${var.environment}-uploads"

  tags = var.tags
}

# Grant Lambda access to bucket
resource "aws_iam_role_policy_attachment" "http_s3" {
  role       = aws_iam_role.http_lambda.name
  policy_arn = aws_iam_policy.s3_uploads.arn
}

resource "aws_iam_policy" "s3_uploads" {
  name = "${var.service}-${var.environment}-s3-uploads"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.uploads.arn}/*"
      }
    ]
  })
}
```

**Deploy custom infrastructure:**

```bash
transire deploy
```

Files in `infra/overrides/` are never overwritten by `transire gen`.

## Rolling Back

### Rollback Strategies

**1. Redeploy previous version (recommended):**

```bash
# Checkout previous version
git checkout v1.2.3

# Regenerate manifest
transire gen

# Deploy
transire deploy
```

**2. Manual rollback via AWS Console:**

- Navigate to Lambda console
- Select function
- **Versions** → Select previous version
- **Aliases** → Update alias to point to previous version

**3. Rollback via AWS CLI:**

```bash
# List function versions
aws lambda list-versions-by-function --function-name myapp-prod-http

# Update alias to previous version
aws lambda update-alias \
  --function-name myapp-prod-http \
  --name live \
  --function-version 42
```

### Disaster Recovery

**If deployment fails mid-apply:**

```bash
# Check OpenTofu state
cd infra
tofu state list

# Unlock state if locked
aws dynamodb delete-item \
  --table-name tf-locks \
  --key '{"LockID": {"S": "myapp/prod/terraform.tfstate"}}'

# Attempt recovery
tofu apply
```

**If state is corrupted:**

```bash
# Pull state from S3
aws s3 cp s3://myapp-tf-state/myapp/prod/terraform.tfstate ./

# Restore previous version
aws s3api list-object-versions --bucket myapp-tf-state --prefix myapp/prod/

# Download specific version
aws s3api get-object \
  --bucket myapp-tf-state \
  --key myapp/prod/terraform.tfstate \
  --version-id {VERSION_ID} \
  terraform.tfstate.backup
```

## Monitoring Deployments

### CloudWatch Logs

**View Lambda logs:**

```bash
# Tail HTTP handler logs
aws logs tail /aws/lambda/myapp-prod-http --follow --format short

# View logs from last hour
aws logs tail /aws/lambda/myapp-prod-http --since 1h

# Filter by error
aws logs tail /aws/lambda/myapp-prod-http --filter-pattern "ERROR"
```

### CloudWatch Metrics

**View Lambda metrics:**

```bash
# Invocation count
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=myapp-prod-http \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Error count
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=myapp-prod-http \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### X-Ray Tracing

**Enable tracing** in `transire.yaml`:

```yaml
observability:
  tracing:
    enabled: true
    provider: aws-xray
```

**View traces in AWS Console:**
- Navigate to AWS X-Ray console
- View service map
- Analyze trace details
- Identify bottlenecks

### CloudWatch Alarms

**Create alarm for errors:**

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name myapp-prod-http-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=myapp-prod-http \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts
```

## Deployment Checklist

### Pre-Deployment

- [ ] All tests pass locally (`go test ./...`)
- [ ] Application runs locally (`transire run`)
- [ ] Manifest generates without errors (`transire gen`)
- [ ] Code reviewed and approved
- [ ] Environment variables configured
- [ ] Dependencies updated (`go mod tidy`)

### Deployment

- [ ] Backend initialized (first time only)
- [ ] Deploy to staging first
- [ ] Verify staging deployment
- [ ] Run smoke tests
- [ ] Deploy to production
- [ ] Verify production deployment

### Post-Deployment

- [ ] Test critical endpoints
- [ ] Monitor CloudWatch logs for errors
- [ ] Check CloudWatch metrics
- [ ] Verify queues are processing
- [ ] Verify scheduled jobs run
- [ ] Update documentation if needed
- [ ] Notify team of deployment

## Troubleshooting

### Deployment Fails

**Error: State lock timeout**

```
Error: acquiring state lock
```

**Solution:** Another deployment is in progress. Wait or manually unlock:

```bash
aws dynamodb delete-item \
  --table-name tf-locks \
  --key '{"LockID": {"S": "myapp/prod/terraform.tfstate"}}'
```

**Error: Insufficient permissions**

```
Error: AccessDenied
```

**Solution:** Verify IAM user has required permissions:

```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/transire-deployer \
  --action-names lambda:CreateFunction lambda:UpdateFunctionCode
```

**Error: Resource already exists**

```
Error: resource already exists
```

**Solution:** Import existing resource into state:

```bash
cd infra
tofu import aws_lambda_function.http myapp-prod-http
```

### Lambda Errors After Deployment

**Cold start timeouts:**

Increase timeout in `transire.yaml`:

```yaml
deploy:
  timeout_s: 60  # Increase from 30
```

**Out of memory:**

Increase memory in `transire.yaml`:

```yaml
deploy:
  memory_mb: 512  # Increase from 256
```

**Permission errors:**

Add required permissions in `infra/overrides/`:

```hcl
resource "aws_iam_role_policy_attachment" "http_s3" {
  role       = aws_iam_role.http_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}
```

## Best Practices

1. **Test locally first** - Always run `transire run` before deploying
2. **Deploy to staging** - Test in staging before production
3. **Use version control** - Tag releases for easy rollback
4. **Monitor deployments** - Watch CloudWatch logs during deployment
5. **Incremental changes** - Deploy small changes frequently
6. **Backup state** - S3 versioning protects OpenTofu state
7. **Use CI/CD** - Automate deployments via GitHub Actions
8. **Document changes** - Keep changelog updated
9. **Plan changes** - Review OpenTofu plan before applying
10. **Have rollback plan** - Know how to revert quickly

## Next Steps

- [Environments Guide](/docs/guides/environments.md) - Multi-environment setup
- [GitHub Actions CI/CD](/docs/ci/github-actions.md) - Automated deployments
- [OpenTofu Backend](/docs/iac/backend.md) - Backend state management
- [AWS Overview](/docs/cloud/aws/overview.md) - AWS-specific details
- [Troubleshooting](/docs/guides/troubleshooting.md) - Common issues

## See Also

- [Quick Start](/docs/getting-started/quickstart.md) - Initial setup
- [Local vs Cloud](/docs/guides/local-vs-cloud.md) - Environment parity
- [Testing Guide](/docs/guides/testing.md) - Pre-deployment testing
