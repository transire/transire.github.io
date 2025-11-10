---
title: "Tutorial: Production Deployment"
description: Deploy your application to AWS with infrastructure as code in 45 minutes
category: learn
subcategory: tutorial
complexity: beginner
duration: 45 minutes
prerequisites:
  - Completed Middleware tutorial
  - AWS account with CLI configured
  - Understanding of cloud basics
  - Go 1.22+
mcp_use: template
mcp_operations:
  - deploy_production
  - configure_environment
  - verify_deployment
features_covered:
  - Cloud deployment
  - Infrastructure as code
  - Environment configuration
  - Production checklist
  - Monitoring setup
code_blocks: true
last_updated: 2025-11-10
---

# Tutorial: Production Deployment

> **Quick Summary:** Deploy your complete orders API to AWS with monitoring and best practices

## What You'll Deploy

Transform local development into production:

```
Local (Development)
  ↓ transire deploy
AWS (Production)
  ├── API Gateway → Lambda (HTTP)
  ├── SQS → Lambda (Queue)
  ├── EventBridge → Lambda (Schedule)
  ├── RDS PostgreSQL (Database)
  └── CloudWatch (Monitoring)
```

**Time:** 45 minutes • **Difficulty:** Beginner

---

## Why Deploy to Cloud?

Production deployment provides:

- **Scalability** - Auto-scales with traffic
- **Reliability** - High availability
- **Cost efficiency** - Pay only for what you use
- **Global reach** - Deploy to multiple regions
- **Monitoring** - Built-in observability
- **Security** - Managed infrastructure

**When to deploy:**
- After local testing complete
- Feature ready for users
- Need production-grade reliability

---

## Prerequisites

### Required Tools

```bash
# Check Go version
go version  # Should be 1.22+

# Check Transire CLI
transire version

# Check AWS CLI
aws --version

# Configure AWS credentials
aws configure
AWS Access Key ID [None]: YOUR_ACCESS_KEY
AWS Secret Access Key [None]: YOUR_SECRET_KEY
Default region name [None]: us-east-1
Default output format [None]: json
```

### AWS Permissions Required

Your AWS user/role needs:
- Lambda (create, update, invoke)
- API Gateway (create, update)
- SQS (create, update)
- EventBridge (create, update)
- IAM (create roles, policies)
- CloudWatch Logs (create, write)
- S3 (for deployment artifacts)

---

## Step 1: Configure for Production

Create or update `transire.yaml`:

```yaml
version: 1
service: orders-api
runtime: go
cloud: aws

# Deployment configuration
deploy:
  region: us-east-1
  arch: arm64              # ARM64 (Graviton) for cost savings
  memory_mb: 512           # Increased for production
  timeout_s: 30            # 30 second timeout

# HTTP configuration
http:
  cors:
    enabled: true
    allow_origins:
      - "https://yourdomain.com"
      - "https://app.yourdomain.com"
    allow_methods: ["GET", "POST", "PUT", "DELETE"]
    allow_headers: ["Content-Type", "Authorization"]
  simulate_limits:
    enabled: true
    max_request_bytes: 1048576  # 1 MB

# Queue configuration
queues:
  max_batch_size: 10
  batch_window_s: 5
  visibility_timeout_s: 60    # Increased for complex processing
  max_receive_count: 3        # Retry 3 times before DLQ

# Observability
observability:
  logging:
    level: info               # info for production
    format: json              # JSON for log aggregation
  tracing:
    enabled: true
    sample_rate: 0.1          # Trace 10% of requests

# Environment-specific configuration
environments:
  dev:
    env:
      DATABASE_URL: "postgres://dev-host/orders?sslmode=require"
      ENVIRONMENT: "development"
      DEBUG: "true"

  prod:
    env:
      DATABASE_URL: "postgres://prod-host/orders?sslmode=require"
      ENVIRONMENT: "production"
      DEBUG: "false"
    deploy:
      memory_mb: 1024         # More memory in production
      timeout_s: 60           # Longer timeout
```

---

## Step 2: Initialize Infrastructure Backend

Set up Terraform/OpenTofu state management:

```bash
# Initialize backend (one-time setup per AWS account)
$ transire init --backend

✓ Creating S3 bucket: transire-state-123456789012-us-east-1
✓ Creating DynamoDB table: transire-state-locks
✓ Configuring encryption
✓ Backend initialized

Configuration saved to infra/backend.tf
```

**What this creates:**
- S3 bucket for Terraform state
- DynamoDB table for state locking
- Encryption enabled
- Versioning enabled

---

## Step 3: Generate Manifest

Build the deployment manifest:

```bash
# Generate manifest from code
$ transire gen

Analyzing Go code...
✓ Found 3 HTTP routes
✓ Found 1 queue handler
✓ Found 1 scheduled job
✓ Validating handler signatures
✓ Generating type metadata

Manifest saved to transire_manifest.json
```

**What's in the manifest:**

```json
{
  "service": "orders-api",
  "runtime": "go",
  "handlers": {
    "http": [
      {
        "method": "GET",
        "path": "/orders",
        "handler": "listOrders",
        "middleware": ["AuthMiddleware"]
      },
      {
        "method": "POST",
        "path": "/orders",
        "handler": "createOrder",
        "middleware": ["AuthMiddleware"]
      }
    ],
    "queue": [
      {
        "key": "fulfill-orders",
        "handler": "fulfillOrders",
        "message_type": "main.Order"
      }
    ],
    "schedule": [
      {
        "key": "daily-report",
        "schedule": "@daily 09:00",
        "handler": "generateDailyReport"
      }
    ]
  },
  "dependencies": [
    "github.com/transire/transire-sdk-go",
    "github.com/lib/pq"
  ]
}
```

---

## Step 4: Deploy to Development

Deploy to development environment first:

```bash
# Deploy to dev environment
$ transire deploy --env dev

Building application...
✓ go build -tags lambda.norpc
✓ Binary size: 12.4 MB

Packaging handlers...
✓ HTTP handler: orders-api-http.zip
✓ Queue handler: orders-api-queue.zip
✓ Schedule handler: orders-api-schedule.zip

Generating infrastructure...
✓ Generated: infra/main.tf
✓ Generated: infra/http.tf
✓ Generated: infra/queue.tf
✓ Generated: infra/schedule.tf
✓ Generated: infra/permissions.tf

Deploying with OpenTofu...
✓ tofu init
✓ tofu plan (12 resources to create)
✓ tofu apply

Deployment complete!

Endpoints:
  HTTP API: https://abc123.execute-api.us-east-1.amazonaws.com/dev

Resources created:
  - Lambda: orders-api-dev-http
  - Lambda: orders-api-dev-queue
  - Lambda: orders-api-dev-schedule
  - API Gateway: orders-api-dev
  - SQS Queue: orders-api-dev-fulfill-orders
  - SQS DLQ: orders-api-dev-fulfill-orders-dlq
  - EventBridge Rule: orders-api-dev-daily-report
  - IAM Role: orders-api-dev-execution-role

Next steps:
  - Test endpoint: curl https://abc123.execute-api.us-east-1.amazonaws.com/dev/health
  - View logs: transire logs --env dev
  - View metrics: transire metrics --env dev
```

---

## Step 5: Test Production Deployment

Verify the deployment works:

### Test HTTP Endpoint

```bash
# Health check
$ curl https://abc123.execute-api.us-east-1.amazonaws.com/dev/health
{
  "status": "healthy"
}

# Login (get token)
$ curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/dev/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
{
  "token": "eyJhbGciOiJIUzI1NiIs..."
}

# Create order (authenticated)
$ curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/dev/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "product": "Widget",
    "quantity": 5,
    "price": 99.99
  }'
{
  "id": "ORD-1699999999",
  "product": "Widget",
  "quantity": 5,
  "price": 99.99,
  "status": "pending"
}

# List orders
$ curl https://abc123.execute-api.us-east-1.amazonaws.com/dev/orders \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
[
  {
    "id": "ORD-1699999999",
    "product": "Widget",
    "status": "pending"
  }
]
```

### Test Queue Processing

```bash
# Check SQS queue
$ aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/orders-api-dev-fulfill-orders \
  --attribute-names ApproximateNumberOfMessages

{
  "Attributes": {
    "ApproximateNumberOfMessages": "1"
  }
}

# Check Lambda logs
$ transire logs --env dev --handler queue

2025-11-10 12:34:56 Processing batch of 1 orders
2025-11-10 12:34:56 Fulfilling order: ORD-1699999999
2025-11-10 12:34:57 Successfully processed 1 orders
```

### Test Scheduled Job

```bash
# Check EventBridge rule
$ aws events describe-rule --name orders-api-dev-daily-report

{
  "Name": "orders-api-dev-daily-report",
  "ScheduleExpression": "cron(0 9 * * ? *)",
  "State": "ENABLED"
}

# Trigger manually for testing
$ transire invoke --env dev --handler schedule --key daily-report

Invoking scheduled job: daily-report
✓ Execution successful

Logs:
2025-11-10 12:35:00 Generating daily report...
2025-11-10 12:35:01 Daily Report: 10 orders, $1,234.56 sales
```

---

## Step 6: Deploy to Production

After testing in dev, deploy to production:

```bash
# Deploy to production
$ transire deploy --env prod

⚠️  Production Deployment
   Environment: prod
   Region: us-east-1
   Service: orders-api

   This will create or update production resources.

   Continue? (yes/no): yes

Building application...
✓ go build -tags lambda.norpc
✓ Running tests... PASSED
✓ Binary size: 12.4 MB

Packaging handlers...
✓ HTTP handler: orders-api-http.zip
✓ Queue handler: orders-api-queue.zip
✓ Schedule handler: orders-api-schedule.zip

Generating infrastructure...
✓ Generated Terraform files

Deploying with OpenTofu...
✓ tofu init
✓ tofu plan (12 resources to create)

Plan summary:
  + 12 to create
  ~ 0 to change
  - 0 to destroy

Continue with apply? (yes/no): yes

✓ tofu apply

Deployment complete!

Production Endpoint:
  https://xyz789.execute-api.us-east-1.amazonaws.com/prod

⚠️  Post-Deployment Checklist:
  [ ] Test production endpoint
  [ ] Verify database connections
  [ ] Check CloudWatch metrics
  [ ] Review IAM permissions
  [ ] Update DNS records
  [ ] Configure custom domain
  [ ] Set up monitoring alerts
```

---

## Step 7: Configure Custom Domain

Map a friendly domain to your API:

### Register Domain in Route 53

```bash
# Create hosted zone (if not exists)
$ aws route53 create-hosted-zone \
  --name api.yourdomain.com \
  --caller-reference $(date +%s)
```

### Create SSL Certificate

```bash
# Request certificate
$ aws acm request-certificate \
  --domain-name api.yourdomain.com \
  --validation-method DNS \
  --region us-east-1

{
  "CertificateArn": "arn:aws:acm:us-east-1:123456789012:certificate/abc123..."
}

# Validate certificate (add DNS records shown in console)
```

### Configure Custom Domain in transire.yaml

```yaml
http:
  custom_domain:
    enabled: true
    domain_name: api.yourdomain.com
    certificate_arn: arn:aws:acm:us-east-1:123456789012:certificate/abc123...
    base_path: v1  # Optional: https://api.yourdomain.com/v1/orders
```

### Redeploy

```bash
$ transire deploy --env prod

✓ Creating custom domain mapping
✓ Updating Route 53 records

Custom domain configured:
  https://api.yourdomain.com
```

---

## Step 8: Set Up Monitoring

Configure CloudWatch alarms:

### Create Alarm Configuration

Add to `transire.yaml`:

```yaml
observability:
  alarms:
    enabled: true
    email: ops@yourdomain.com

    # Lambda errors
    lambda_errors:
      threshold: 10           # Alert if >10 errors
      period_minutes: 5

    # HTTP 5xx errors
    http_5xx:
      threshold: 5            # Alert if >5 errors
      period_minutes: 5

    # Queue DLQ messages
    dlq_messages:
      threshold: 1            # Alert on any DLQ message
      period_minutes: 5

    # Lambda duration
    lambda_duration:
      threshold_ms: 25000     # Alert if >25s (near timeout)
      period_minutes: 5
```

### Deploy Monitoring

```bash
$ transire deploy --env prod

✓ Creating SNS topic: orders-api-prod-alarms
✓ Creating subscription: ops@yourdomain.com
✓ Creating CloudWatch alarms (4 alarms)

Monitoring configured:
  - Lambda errors alarm
  - HTTP 5xx errors alarm
  - DLQ messages alarm
  - Lambda duration alarm

Confirmation email sent to: ops@yourdomain.com
```

---

## Step 9: View Logs and Metrics

Monitor your application:

### View Logs

```bash
# Tail all logs
$ transire logs --env prod --follow

# Filter by handler
$ transire logs --env prod --handler http
$ transire logs --env prod --handler queue
$ transire logs --env prod --handler schedule

# Filter by time
$ transire logs --env prod --since 1h
$ transire logs --env prod --since "2025-11-10 12:00:00"

# Search logs
$ transire logs --env prod --filter "ERROR"
$ transire logs --env prod --filter "user-123"
```

### View Metrics

```bash
# Dashboard
$ transire metrics --env prod

Orders API - Production Metrics (Last 24 hours)

HTTP Metrics:
  Invocations:     12,456
  Errors:          23 (0.18%)
  Duration (avg):  145ms
  Duration (p99):  890ms

Queue Metrics:
  Messages:        1,234
  Successes:       1,230 (99.7%)
  Failures:        4
  DLQ Messages:    0

Schedule Metrics:
  Executions:      24
  Successes:       24 (100%)
  Duration (avg):  2.3s

Cost Estimate:
  Lambda:          $12.34
  API Gateway:     $5.67
  SQS:             $0.12
  Total:           $18.13
```

---

## Production Checklist

### Pre-Deployment

- [x] All tests passing locally
- [x] Code reviewed
- [x] Environment variables configured
- [x] Database migrations ready
- [x] SSL certificate obtained
- [x] Custom domain configured
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Backup strategy defined

### Post-Deployment

- [ ] Health check endpoint responding
- [ ] All routes accessible
- [ ] Queue processing working
- [ ] Scheduled jobs triggering
- [ ] Logs appearing in CloudWatch
- [ ] Metrics being collected
- [ ] Alarms configured
- [ ] DNS propagated (if custom domain)
- [ ] Documentation updated

### Ongoing

- [ ] Monitor error rates
- [ ] Review CloudWatch dashboards
- [ ] Check DLQ messages
- [ ] Optimize Lambda memory
- [ ] Review costs
- [ ] Update dependencies
- [ ] Rotate credentials

---

## Rollback Strategy

If deployment fails or issues occur:

### Automatic Rollback

Transire keeps previous deployment artifacts:

```bash
# Rollback to previous version
$ transire rollback --env prod

⚠️  Rollback to Previous Version
   Current: v1.2.3 (deployed 2025-11-10 14:30:00)
   Previous: v1.2.2 (deployed 2025-11-09 10:15:00)

   Continue? (yes/no): yes

✓ Deploying previous version
✓ Updating Lambda functions
✓ Rollback complete

Rolled back to: v1.2.2
```

### Manual Rollback

```bash
# List deployments
$ transire deployments --env prod

Version  | Deployed At          | Status
---------|---------------------|--------
v1.2.3   | 2025-11-10 14:30:00 | FAILED
v1.2.2   | 2025-11-09 10:15:00 | SUCCESS
v1.2.1   | 2025-11-08 09:00:00 | SUCCESS

# Deploy specific version
$ transire deploy --env prod --version v1.2.2
```

---

## Cost Optimization

Reduce AWS costs:

### 1. Right-Size Lambda Memory

```bash
# Analyze Lambda metrics
$ transire analyze --env prod

Recommendations:
  - HTTP handler: Using 512MB, max usage 156MB → Reduce to 256MB (save 40%)
  - Queue handler: Using 512MB, max usage 380MB → Keep at 512MB
  - Schedule handler: Using 512MB, max usage 89MB → Reduce to 128MB (save 60%)

Apply recommendations? (yes/no): yes

✓ Updated Lambda configurations
Estimated savings: $8.50/month (45%)
```

### 2. Use ARM64 (Graviton)

Already configured in `transire.yaml`:

```yaml
deploy:
  arch: arm64  # 20% cost reduction vs x86_64
```

### 3. Optimize Queue Batch Size

```yaml
queues:
  max_batch_size: 10  # Process more messages per invocation
  batch_window_s: 5   # Wait longer to collect batch
```

### 4. Review CloudWatch Logs Retention

```yaml
observability:
  logging:
    retention_days: 7  # Default is 30 days
```

---

## Security Best Practices

### 1. Least Privilege IAM

Transire generates minimal IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage"
      ],
      "Resource": "arn:aws:sqs:us-east-1:123456789012:orders-api-prod-*"
    }
  ]
}
```

### 2. Encrypt Sensitive Data

```yaml
deploy:
  encryption:
    enabled: true
    kms_key_arn: arn:aws:kms:us-east-1:123456789012:key/abc123...
```

### 3. Use Secrets Manager

```go
import "github.com/aws/aws-sdk-go-v2/service/secretsmanager"

func NewConfig() *Config {
    // Get secret from AWS Secrets Manager
    secret := getSecret("orders-api/database")

    return &Config{
        DatabaseURL: secret["DATABASE_URL"],
    }
}
```

### 4. Enable VPC for Database

```yaml
deploy:
  vpc:
    enabled: true
    subnet_ids:
      - subnet-abc123
      - subnet-def456
    security_group_ids:
      - sg-abc123
```

---

## Troubleshooting Deployment

### Deployment Fails

**Issue:** `transire deploy` fails with Terraform error

**Check:**

```bash
# View detailed logs
$ transire deploy --env prod --verbose

# View Terraform state
$ cd infra && tofu show

# Validate configuration
$ transire validate
```

### Lambda Timeout

**Issue:** Lambda exceeds timeout (30s default)

**Solution:**

```yaml
deploy:
  timeout_s: 60  # Increase timeout

  # Or optimize code
  memory_mb: 1024  # More memory = faster CPU
```

### Cold Start Issues

**Issue:** First request after idle is slow

**Solutions:**

```yaml
deploy:
  provisioned_concurrency: 1  # Keep 1 instance warm (costs more)

# Or optimize binary size
deploy:
  optimize_binary: true  # Strip debug info
```

### Permission Denied

**Issue:** Lambda can't access SQS/EventBridge

**Check:**

```bash
# View IAM role
$ aws iam get-role --role-name orders-api-prod-execution-role

# View attached policies
$ aws iam list-attached-role-policies --role-name orders-api-prod-execution-role
```

---

## Complete Deployment Script

Automate deployments:

```bash
#!/bin/bash
# deploy.sh - Production deployment script

set -e  # Exit on error

ENV=${1:-dev}

echo "🚀 Deploying to $ENV environment..."

# 1. Run tests
echo "Running tests..."
go test ./...

# 2. Generate manifest
echo "Generating manifest..."
transire gen

# 3. Validate configuration
echo "Validating configuration..."
transire validate --env $ENV

# 4. Build
echo "Building..."
go build -o orders-api

# 5. Deploy
echo "Deploying..."
transire deploy --env $ENV

# 6. Test deployment
echo "Testing deployment..."
ENDPOINT=$(transire info --env $ENV --output json | jq -r '.endpoint')
curl -f "$ENDPOINT/health" || (echo "Health check failed!" && exit 1)

# 7. Success
echo "✅ Deployment successful!"
echo "Endpoint: $ENDPOINT"
```

Usage:

```bash
# Deploy to dev
./deploy.sh dev

# Deploy to prod
./deploy.sh prod
```

---

## What You Learned

Congratulations! You've deployed to production. You now know:

- ✅ How to configure production settings
- ✅ How to initialize infrastructure backend
- ✅ How to deploy to multiple environments
- ✅ How to test production deployments
- ✅ How to configure custom domains
- ✅ How to set up monitoring and alerts
- ✅ How to view logs and metrics
- ✅ How to rollback deployments
- ✅ Cost optimization strategies
- ✅ Security best practices
- ✅ Troubleshooting deployment issues

---

## Next Steps

### Set Up CI/CD

Automate deployments with GitHub Actions:

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
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v4
        with:
          go-version: '1.22'

      - name: Run tests
        run: go test ./...

      - name: Deploy
        run: transire deploy --env prod
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

### Advanced Topics

- **Multi-Region Deployment** - Deploy to multiple AWS regions
- **Blue-Green Deployment** - Zero-downtime deployments
- **Canary Releases** - Gradual rollout to subset of users
- **Database Migrations** - Automated schema updates
- **Load Testing** - Test at scale with k6 or Locust

---

## See Also

- [Deployment Guide](../../guides/deployment/first-deployment/) - Detailed deployment reference
- [Production Checklist](../../guides/deployment/production-checklist/) - Complete checklist
- [CI/CD Setup](../../guides/deployment/ci-cd-setup/) - Automated deployments
- [AWS Provider Docs](../../plugins/cloud/aws/) - AWS-specific details
- [Rollback Strategies](../../guides/deployment/rollback-strategies/) - Recovery procedures
- [Monitoring Guide](../../guides/observability/monitoring/) - Advanced monitoring

