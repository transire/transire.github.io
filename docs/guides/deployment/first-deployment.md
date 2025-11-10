---
title: First Deployment Guide
description: Step-by-step guide to deploying your first Transire application to AWS
category: guide
subcategory: deployment
complexity: beginner
duration: 30 minutes
prerequisites:
  - Completed Hello World tutorial
  - AWS account created
  - AWS CLI installed and configured
mcp_use: guide
mcp_operations:
  - verify_prerequisites
  - configure_aws
  - deploy_application
  - test_deployment
features_covered:
  - AWS setup
  - First deployment
  - Testing deployed app
  - Viewing logs
  - Cleanup
code_blocks: true
last_updated: 2025-11-10
---

# First Deployment Guide

> **Deploy your first Transire application to AWS in 30 minutes**

## What You'll Deploy

Transform this local app into production:

```
Local Development               →    AWS Production
────────────────                     ─────────────
HTTP server (:8080)             →    API Gateway + Lambda
In-memory queue                 →    SQS + Lambda
Fixed-rate scheduler            →    EventBridge + Lambda
```

**Time:** 30 minutes • **Complexity:** Beginner

---

## Prerequisites

### Required

- [x] Completed [Hello World Tutorial](../../learn/tutorials/01-hello-world/)
- [x] AWS account ([Create one →](https://aws.amazon.com/free/))
- [x] AWS CLI installed ([Install guide →](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- [x] Go 1.22+ installed
- [x] Transire CLI installed

### Verify Setup

```bash
# Check Go
$ go version
go version go1.22.0 darwin/arm64

# Check AWS CLI
$ aws --version
aws-cli/2.13.0

# Check Transire CLI
$ transire version
transire version 0.1.0

# Check AWS credentials
$ aws sts get-caller-identity
{
    "UserId": "AIDAI...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/yourname"
}
```

---

## Step 1: Create Simple Application

Create a minimal Transire app:

### Project Structure

```bash
mkdir my-first-app
cd my-first-app
go mod init my-first-app
```

### Install SDK

```bash
go get github.com/transire/transire-sdk-go
```

### Create main.go

```go
package main

import (
    "net/http"

    "github.com/transire/transire-sdk-go"
    "github.com/transire/transire-sdk-go/response"
)

func main() {
    app := transire.New()

    // Health check endpoint
    app.GET("/health", func(w http.ResponseWriter, r *http.Request) {
        response.OK(w, map[string]string{
            "status": "healthy",
            "app":    "my-first-app",
        })
    })

    // Hello endpoint
    app.GET("/hello", func(w http.ResponseWriter, r *http.Request) {
        response.OK(w, map[string]string{
            "message": "Hello from Transire!",
        })
    })

    // API info endpoint
    app.GET("/", func(w http.ResponseWriter, r *http.Request) {
        response.OK(w, map[string]interface{}{
            "app":     "my-first-app",
            "version": "1.0.0",
            "endpoints": []string{
                "/",
                "/health",
                "/hello",
            },
        })
    })

    app.Run()
}
```

---

## Step 2: Test Locally

Verify app works locally:

```bash
# Run locally
$ go run main.go

✓ Starting HTTP server on :8080
✓ Queue emulator: 0 queues
→ Ready: http://localhost:8080

# In another terminal, test endpoints
$ curl http://localhost:8080/health
{"status":"healthy","app":"my-first-app"}

$ curl http://localhost:8080/hello
{"message":"Hello from Transire!"}

$ curl http://localhost:8080/
{
  "app": "my-first-app",
  "version": "1.0.0",
  "endpoints": ["/", "/health", "/hello"]
}
```

**✓ Local testing successful!**

---

## Step 3: Configure AWS Credentials

Set up AWS credentials for deployment:

### Option A: AWS Configure

```bash
$ aws configure

AWS Access Key ID [None]: YOUR_ACCESS_KEY
AWS Secret Access Key [None]: YOUR_SECRET_KEY
Default region name [None]: us-east-1
Default output format [None]: json
```

### Option B: Environment Variables

```bash
export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
export AWS_REGION="us-east-1"
```

### Option C: AWS Profile

```bash
# ~/.aws/credentials
[transire]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

# Use profile
export AWS_PROFILE=transire
```

### Verify Credentials

```bash
$ aws sts get-caller-identity

{
    "UserId": "AIDAI...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/yourname"
}
```

---

## Step 4: Create Configuration

Create `transire.yaml`:

```yaml
version: 1
service: my-first-app
runtime: go
cloud: aws

# Deployment configuration
deploy:
  region: us-east-1
  arch: arm64              # ARM64 for cost savings
  memory_mb: 256           # Start small
  timeout_s: 30

# HTTP configuration
http:
  cors:
    enabled: true
    allow_origins: ["*"]

# Observability
observability:
  logging:
    level: info
    format: json
```

**Key settings:**
- `service` - Your app name (must be unique in your AWS account)
- `region` - AWS region to deploy to
- `arch` - ARM64 is 20% cheaper than x86_64
- `memory_mb` - Start with 256MB, tune later

---

## Step 5: Initialize Infrastructure Backend

One-time setup per AWS account:

```bash
$ transire init --backend

Initializing Transire infrastructure backend...

Creating resources:
  ✓ S3 bucket: transire-state-123456789012-us-east-1
  ✓ DynamoDB table: transire-state-locks
  ✓ Encryption: Enabled
  ✓ Versioning: Enabled

Backend configuration saved to:
  infra/backend.tf

✅ Backend initialized successfully!
```

**What this creates:**
- **S3 bucket** - Stores Terraform state
- **DynamoDB table** - Locks state for concurrent deploys
- **Encryption** - State is encrypted at rest
- **Versioning** - Can rollback state changes

**Note:** Only run this once per AWS account. Subsequent projects use the same backend.

---

## Step 6: Generate Manifest

Create deployment manifest:

```bash
$ transire gen

Analyzing Go code...
  ✓ Found 3 HTTP handlers
  ✓ Found 0 queue handlers
  ✓ Found 0 scheduled jobs

Validating handlers...
  ✓ All handler signatures valid

Generating manifest...
  ✓ Manifest generated: transire_manifest.json

Build tags: lambda.norpc
```

**Review manifest:**

```bash
$ cat transire_manifest.json
```

```json
{
  "service": "my-first-app",
  "runtime": "go",
  "handlers": {
    "http": [
      {
        "method": "GET",
        "path": "/",
        "handler": "main.main.func1"
      },
      {
        "method": "GET",
        "path": "/health",
        "handler": "main.main.func2"
      },
      {
        "method": "GET",
        "path": "/hello",
        "handler": "main.main.func3"
      }
    ]
  }
}
```

---

## Step 7: Deploy to AWS

Deploy your application:

```bash
$ transire deploy

Building application...
  ✓ go build -tags lambda.norpc
  ✓ Binary size: 8.2 MB
  ✓ Compressed: 2.8 MB

Packaging handlers...
  ✓ HTTP handler: my-first-app-http.zip

Generating infrastructure...
  ✓ Generated: infra/main.tf
  ✓ Generated: infra/http.tf
  ✓ Generated: infra/permissions.tf

Deploying with OpenTofu...
  ✓ tofu init
  ✓ tofu plan

Plan: 7 resources to create
  + AWS Lambda function
  + API Gateway HTTP API
  + API Gateway stage
  + API Gateway integration
  + API Gateway route (x3)
  + IAM role
  + IAM role policy

Apply? (yes/no): yes

  ✓ tofu apply

Deployment complete! (45 seconds)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 Your app is live!

Endpoint:
  https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev

Resources created:
  Lambda:      my-first-app-dev-http
  API Gateway: my-first-app-dev
  IAM Role:    my-first-app-dev-execution-role

Next steps:
  • Test: curl https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev/health
  • Logs: transire logs
  • Update: transire deploy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**🎉 Congratulations! Your app is deployed!**

---

## Step 8: Test Deployed Application

Test your live endpoint:

### Health Check

```bash
$ curl https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev/health

{
  "status": "healthy",
  "app": "my-first-app"
}
```

### Hello Endpoint

```bash
$ curl https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev/hello

{
  "message": "Hello from Transire!"
}
```

### Root Endpoint

```bash
$ curl https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev/

{
  "app": "my-first-app",
  "version": "1.0.0",
  "endpoints": ["/", "/health", "/hello"]
}
```

### Test with Browser

Open in browser:
```
https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev/health
```

**✓ All endpoints working!**

---

## Step 9: View Logs

Check application logs:

```bash
# Tail logs
$ transire logs --follow

2025-11-10 15:23:45 START RequestId: abc-123
2025-11-10 15:23:45 [INFO] GET /health
2025-11-10 15:23:45 END RequestId: abc-123
2025-11-10 15:23:45 REPORT RequestId: abc-123
  Duration: 12.34 ms
  Billed Duration: 13 ms
  Memory Size: 256 MB
  Max Memory Used: 45 MB
```

### Filter Logs

```bash
# Last hour
$ transire logs --since 1h

# Search for errors
$ transire logs --filter ERROR

# Specific time range
$ transire logs --since "2025-11-10 15:00:00"
```

---

## Step 10: View Metrics

Check application metrics:

```bash
$ transire metrics

My First App - Metrics (Last 24 hours)
════════════════════════════════════════

HTTP Metrics:
  Invocations:     156
  Errors:          0 (0%)
  Duration (avg):  12ms
  Duration (p99):  45ms
  Cold Starts:     3

Cost Estimate:
  Lambda:          $0.02
  API Gateway:     $0.01
  Total:           $0.03

Status: ✅ Healthy
```

---

## Step 11: Update Application

Make changes and redeploy:

### Update Code

```go
// main.go - Add new endpoint
app.GET("/info", func(w http.ResponseWriter, r *http.Request) {
    response.OK(w, map[string]string{
        "version":     "1.1.0",
        "environment": "production",
        "region":      "us-east-1",
    })
})
```

### Redeploy

```bash
$ transire deploy

Building application...
  ✓ go build

Packaging handlers...
  ✓ HTTP handler updated

Deploying with OpenTofu...
  ✓ tofu plan

Plan: 0 to add, 1 to change, 0 to destroy
  ~ Lambda function (code updated)

Apply? (yes/no): yes

  ✓ tofu apply

✅ Update complete! (12 seconds)
```

### Test New Endpoint

```bash
$ curl https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev/info

{
  "version": "1.1.0",
  "environment": "production",
  "region": "us-east-1"
}
```

---

## Step 12: Clean Up (Optional)

Remove all resources:

```bash
$ transire destroy

⚠️  This will DELETE all resources for: my-first-app-dev

Resources to destroy:
  - Lambda function
  - API Gateway
  - IAM role and policies
  - CloudWatch log groups

Continue? (yes/no): yes

Destroying resources...
  ✓ Deleting Lambda function
  ✓ Deleting API Gateway
  ✓ Deleting IAM role
  ✓ Deleting log groups

✅ All resources destroyed
```

**Note:** This does NOT delete:
- S3 backend bucket
- DynamoDB state table
- CloudWatch logs (retained 7 days by default)

---

## Understanding AWS Resources

### Lambda Function

**What:** Serverless compute running your code

**Configuration:**
- Runtime: Custom (Go binary)
- Memory: 256 MB
- Timeout: 30 seconds
- Architecture: ARM64

**View in AWS Console:**
```
Services → Lambda → Functions → my-first-app-dev-http
```

### API Gateway

**What:** HTTP API routing requests to Lambda

**Configuration:**
- Type: HTTP API (cheaper than REST)
- Stage: dev
- Integration: Lambda proxy

**View in AWS Console:**
```
Services → API Gateway → APIs → my-first-app-dev
```

### IAM Role

**What:** Permissions for Lambda execution

**Permissions:**
- CloudWatch Logs (write)
- X-Ray tracing (if enabled)

**View in AWS Console:**
```
Services → IAM → Roles → my-first-app-dev-execution-role
```

---

## Troubleshooting

### Deployment Failed

**Error:** `Access Denied` or `Insufficient Permissions`

**Solution:** Verify AWS credentials:
```bash
aws sts get-caller-identity
```

Ensure your user has these permissions:
- Lambda (create, update, delete)
- API Gateway (create, update, delete)
- IAM (create roles, policies)
- CloudWatch Logs (create groups)

---

**Error:** `Service already exists`

**Solution:** Change service name in `transire.yaml`:
```yaml
service: my-first-app-v2  # Make unique
```

---

**Error:** `Backend not initialized`

**Solution:** Run backend init:
```bash
transire init --backend
```

---

### Endpoint Not Working

**Error:** 404 Not Found

**Check:**

1. **Verify endpoint URL:**
   ```bash
   transire info --output json | jq '.endpoint'
   ```

2. **Check routes deployed:**
   ```bash
   aws apigatewayv2 get-routes --api-id <API_ID>
   ```

3. **View Lambda logs:**
   ```bash
   transire logs --filter ERROR
   ```

---

**Error:** 502 Bad Gateway

**Causes:**
- Lambda timeout (increase in `transire.yaml`)
- Lambda error (check logs)
- Handler panic (add recovery)

**Solution:**
```bash
# Check logs for errors
transire logs --filter ERROR

# Increase timeout
# transire.yaml
deploy:
  timeout_s: 60
```

---

### Cold Start Latency

**Issue:** First request slow (~500ms)

**Why:** Lambda "cold start" - initializing runtime

**Solutions:**

1. **Accept it** - Cold starts are normal, 2-5% of requests

2. **Increase traffic** - More requests = fewer cold starts

3. **Provisioned concurrency** (costs more):
   ```yaml
   deploy:
     provisioned_concurrency: 1
   ```

4. **Optimize binary size:**
   ```bash
   go build -ldflags="-s -w"  # Strip debug info
   ```

---

## Cost Analysis

### Free Tier (First 12 Months)

- **Lambda:** 1M requests/month, 400,000 GB-seconds/month
- **API Gateway:** 1M requests/month

### After Free Tier

**Example: 10,000 requests/day**

| Service | Usage | Cost |
|---------|-------|------|
| Lambda (ARM64, 256MB, 20ms avg) | 300k req/month | $0.60 |
| API Gateway HTTP | 300k req/month | $0.30 |
| **Total** | | **$0.90/month** |

**Extremely cheap for low-medium traffic!**

---

## Next Steps

### Add More Features

1. **Add Queue Processing:**
   - [Queue Tutorial →](../../learn/tutorials/03-queue-processing/)

2. **Add Scheduled Jobs:**
   - [Schedule Tutorial →](../../learn/tutorials/04-scheduled-jobs/)

3. **Add Database:**
   - [DI Tutorial →](../../learn/tutorials/05-dependency-injection/)

4. **Add Authentication:**
   - [Middleware Tutorial →](../../learn/tutorials/06-middleware-auth/)

### Deploy to Production

1. **Multiple Environments:**
   ```yaml
   # transire.yaml
   environments:
     dev:
       deploy:
         memory_mb: 256
     prod:
       deploy:
         memory_mb: 512
   ```

   Deploy:
   ```bash
   transire deploy --env dev
   transire deploy --env prod
   ```

2. **Custom Domain:**
   - [Custom Domain Guide →](custom-domain/)

3. **CI/CD Pipeline:**
   - [CI/CD Setup →](ci-cd-setup/)

### Learn More

- [Production Checklist →](production-checklist/)
- [Monitoring Guide →](../../guides/observability/monitoring/)
- [Troubleshooting →](../../guides/troubleshooting/)

---

## Summary

Congratulations! You've successfully:

- ✅ Created a Transire application
- ✅ Configured AWS credentials
- ✅ Deployed to AWS Lambda + API Gateway
- ✅ Tested live endpoints
- ✅ Viewed logs and metrics
- ✅ Updated and redeployed

**Your application is live on AWS!** 🎉

---

## Quick Reference

```bash
# Deploy
transire deploy

# Deploy to specific environment
transire deploy --env prod

# View logs
transire logs
transire logs --follow

# View metrics
transire metrics

# Update deployment
transire deploy

# Destroy all resources
transire destroy
```

---

## See Also

- [Production Deployment Tutorial](../../learn/tutorials/07-production-deployment/) - Advanced deployment
- [Production Checklist](production-checklist/) - Pre-launch checklist
- [AWS Provider Docs](../../plugins/cloud/aws/) - AWS-specific details
- [Troubleshooting Guide](../../guides/troubleshooting/) - Common issues

