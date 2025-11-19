---
title: "transire deploy"
description: "Deploy Transire application to AWS"
keywords:
  - transire deploy
  - deployment
  - aws
  - cdk
  - cloudformation
  - multi-environment
  - environment-isolation
  - dev staging prod
category: cli-reference
difficulty: intermediate
estimated_time: 10 minutes
prerequisites:
  - "AWS CLI configured"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Deploying to AWS"
    - "Updating deployment"
    - "Production deployment"
    - "Multi-environment deployment"
    - "Environment isolation"
  common_questions:
    - "How do I deploy to AWS?"
    - "How do I update?"
    - "What does deploy do?"
    - "How do I deploy to different environments?"
    - "How are environments isolated?"
    - "What's the resource naming pattern?"
---

# transire deploy

Deploy your Transire application to AWS using CDK.

!!! tip "TL;DR"
    `transire deploy` validates artifacts, applies CDK infrastructure, uploads Lambda packages, and configures cloud resources. Run `transire build` first.

---

## Synopsis

```bash
transire deploy [flags]
```

---

## Description

The `transire deploy` command:

1. Validates that artifacts have been built (`transire build`)
2. Applies the generated AWS CDK infrastructure
3. Uploads Lambda deployment packages
4. Configures cloud resources (Lambda, API Gateway, SQS, EventBridge)
5. Sets up IAM permissions and networking

**Important:** Run `transire build` before deploying.

Source: [`internal/cli/commands/deploy.go:13-106`](https://github.com/transire/transire/blob/main/internal/cli/commands/deploy.go)

---

## Prerequisites

1. **Built artifacts:** Run `transire build` first
2. **AWS credentials:** Configured via `aws configure` or environment variables
3. **Node.js 18+:** For running CDK CLI
4. **AWS CDK CLI:** Installed via `npm install -g aws-cdk`

---

## Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `-c, --config` | string | `transire.yaml` | Path to configuration file |
| `-e, --environment` | string | `dev` | Deployment environment (dev, staging, prod) |
| `--dry-run` | bool | `false` | Preview changes without applying |
| `-r, --region` | string | `$AWS_DEFAULT_REGION` | AWS region (defaults to env var or `us-east-1`) |

Source: [`internal/cli/commands/deploy.go:97-100`](https://github.com/transire/transire/blob/main/internal/cli/commands/deploy.go)

---

## Examples

### Deploy to default region

```bash
transire deploy
```

Output:
```
🚀 Deploying Transire application: my-api
🌎 Target: aws/lambda in us-east-1

[CDK output...]

✅ Deployment completed successfully
🎯 Stack: my-api-dev
🌍 Region: us-east-1
📊 API Endpoint: https://abc123.execute-api.us-east-1.amazonaws.com
```

### Deploy to specific region

```bash
transire deploy --region us-west-2
```

### Preview changes (dry run)

```bash
transire deploy --dry-run
```

Shows CloudFormation diff without applying changes.

### Deploy to specific environments

```bash
# Deploy to development (default)
transire deploy
# or explicitly
transire deploy --environment dev

# Deploy to staging
transire deploy --environment staging

# Deploy to production
transire deploy --environment prod

# Combine with region for multi-region deployments
transire deploy --environment prod --region us-west-2
```

Environment isolation ensures resources are named `{AppName}-{Environment}-{ResourceName}` preventing conflicts across environments.

---

## Deployment Process

### 1. CDK Bootstrap (First-Time Setup)

On first deployment in a region, CDK requires bootstrapping:

```bash
cd infrastructure
cdk bootstrap aws://ACCOUNT-ID/REGION
```

This creates S3 bucket and IAM roles for CDK deployments.

Transire will prompt you if bootstrapping is needed.

### 2. CDK Synthesis

CDK synthesizes CloudFormation templates from TypeScript:

```bash
cd infrastructure
cdk synth
```

### 3. CDK Deployment

CDK applies CloudFormation stack:

```bash
cd infrastructure
cdk deploy
```

Transire automates these steps via [`internal/providers/aws/cdk_deployer.go`](https://github.com/transire/transire/blob/main/internal/providers/aws/cdk_deployer.go).

---

## Deployed Resources

After successful deployment:

**Lambda Functions:**
- One or more Lambda functions (named `{AppName}-{Environment}-{HandlerName}`)
- Lambda aliases (`live`) for each function
- IAM execution roles with necessary permissions

**API Gateway (if HTTP handlers present):**
- HTTP API v2 (named `{AppName}-{Environment}-api`)
- Default integration to Lambda function
- Publicly accessible endpoint

**SQS (if queue handlers present):**
- One queue per `QueueHandler` (named `{AppName}-{Environment}-{QueueName}`)
- Dead Letter Queue (DLQ) for each queue (named `{AppName}-{Environment}-{QueueName}-dlq`)
- Lambda event source mappings

**EventBridge (if schedule handlers present):**
- One rule per `SchedulerHandler` (named `{AppName}-{Environment}-{RuleName}`)
- Lambda targets for each rule

**VPC (if configured):**
- Lambda functions placed in specified subnets
- Security groups attached

**Existing Resources (if configured):**
- IAM permissions to access DynamoDB tables, S3 buckets, Secrets

---

## CloudFormation Stack Outputs

After deployment, view outputs:

```bash
cd infrastructure
cdk outputs
```

Example outputs:
```
my-api-dev.ApiEndpoint = https://abc123.execute-api.us-east-1.amazonaws.com
my-api-dev.FunctionName = my-api-dev-MainFunction-ABC123
```

Or via AWS Console:
CloudFormation → Stacks → `my-api-dev` → Outputs

---

## Troubleshooting

### "No such file: dist/function.zip"

**Solution:**
Run `transire build` before deploying.

### "CDK not found"

**Solution:**
Install AWS CDK:
```bash
npm install -g aws-cdk
```

### "Unable to resolve AWS account"

**Solution:**
Configure AWS credentials:
```bash
aws configure
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### "Require bootstrap stack version X"

**Solution:**
Run CDK bootstrap in the target region:
```bash
cd infrastructure
cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/us-east-1
```

### "Deployment failed" (CloudFormation error)

**Solution:**
- Check CloudFormation Events in AWS Console for detailed error
- Common issues:
  - IAM permissions (ensure deploying role has adequate permissions)
  - Resource limits (Lambda concurrent executions, API Gateway quotas)
  - Invalid configuration (check VPC subnet IDs, security group IDs)

---

## Updating an Existing Deployment

To update:

1. Make code changes
2. Run `transire build` (regenerates artifacts and CDK code)
3. Run `transire deploy` (applies changes)

CDK will show a diff of changes before applying:
```
Stack my-api-dev
Resources
[~] AWS::Lambda::Function MainFunction
 └─ [~] Code
     └─ [~] .S3Key:
         ├─ [-] old-hash.zip
         └─ [+] new-hash.zip
```

---

## Deleting a Deployment

To delete all resources:

```bash
cd infrastructure
cdk destroy
```

**Warning:** This deletes Lambda functions, API Gateway, queues, and all data. This action cannot be undone.

---

## Monitoring Deployment

### View CloudFormation Stack

```bash
aws cloudformation describe-stacks --stack-name my-api-dev
```

### View Lambda Function

```bash
aws lambda get-function --function-name my-api-dev-MainFunction-ABC123
```

### View API Gateway

```bash
aws apigatewayv2 get-apis
```

### View CloudWatch Logs

```bash
aws logs tail /aws/lambda/my-api-dev-MainFunction-ABC123 --follow
```

---

## Next Steps

- [Deploying to AWS Guide](../guides/deploying-to-aws.md) – Detailed deployment walkthrough
- [Multi-Function Architecture](../guides/multi-function-architecture.md) – Advanced function grouping
- [Custom CDK Extensions](../guides/custom-cdk.md) – Extend generated infrastructure
- [Configuration Reference](../configuration/transire-yaml.md) – Customize deployment settings

---

## See Also

- [transire build](transire-build.md) – Build deployment artifacts
- [transire run](transire-run.md) – Run locally with hot reload
