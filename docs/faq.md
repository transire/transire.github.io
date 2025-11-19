---
title: "FAQ"
description: "Frequently asked questions about Transire"
keywords:
  - faq
  - questions
  - troubleshooting
  - help
  - common issues
category: other
difficulty: all
estimated_time: 10 minutes
prerequisites:
  []
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Finding answers"
    - "Troubleshooting"
    - "Common questions"
  common_questions:
    - "Where can I find answers?"
    - "How do I troubleshoot?"
    - "What are common issues?"
---

# Frequently Asked Questions

Common questions about Transire and their answers.

---

## General

### What is Transire?

Transire is a cloud-agnostic Go framework for building production APIs that run seamlessly across local development and cloud platforms (currently AWS Lambda, with more platforms coming).

It provides:
- **Local development** with hot reload and simulators
- **Chi router** for HTTP routing
- **Queue handlers** for async processing
- **Schedule handlers** for cron jobs
- **Automatic AWS deployment** via CDK

---

### Why use Transire instead of X?

**vs. AWS Lambda directly:**
- Local dev experience with hot reload
- Built-in queue and schedule simulators
- No Lambda-specific code in your handlers
- Automatic CloudFormation/CDK generation

**vs. Serverless Framework:**
- Type-safe Go instead of YAML configuration
- Chi router (familiar Go patterns)
- Code generation (not runtime framework)
- Better local development experience

**vs. Standard Go server (net/http):**
- Automatic cloud deployment
- Queue and schedule handlers built-in
- Zero ops infrastructure management
- Cost-effective serverless scaling

**vs. SAM (Serverless Application Model):**
- Simpler configuration (one `transire.yaml`)
- Better local development tooling
- Chi router integration
- More Go-idiomatic patterns

---

### Is Transire production-ready?

Transire is in active development. Check the [GitHub releases](https://github.com/transire/transire/releases) for current version and stability information.

For production use:
- Review the release notes
- Test thoroughly in staging environment
- Monitor CloudWatch metrics
- Have rollback plan ready

---

### What's the difference between Transire and traditional frameworks?

Traditional frameworks (Express, Flask, Django) assume a long-running server. Transire is designed for **serverless** environments where functions start and stop frequently.

Key differences:
- **No global state** between requests
- **Connection pooling** optimized for Lambda
- **Event-driven** (HTTP, queues, schedules)
- **Pay-per-use** pricing (not per-hour)

---

## Development

### How do I debug my application?

**Local debugging:**
Use standard Go debugging tools (Delve, IDE debuggers) with `transire run`:

```bash
# Terminal
dlv debug

# VS Code
# Set breakpoints and press F5
```

**AWS debugging:**
- Use CloudWatch Logs for log output
- Use X-Ray for distributed tracing
- Use `slog` for structured logging

---

### Can I use custom middleware?

Yes! Transire uses Chi router, so all Chi middleware works:

```go
import "github.com/go-chi/chi/v5/middleware"

r := app.Router()
r.Use(middleware.Logger)
r.Use(middleware.Recoverer)
r.Use(middleware.RequestID)
r.Use(yourCustomMiddleware)
```

See: [HTTP Handlers](core-concepts/http-handlers.md)

---

### How do I connect to a database?

Use standard Go `database/sql` with connection pooling:

```go
import (
    "database/sql"
    _ "github.com/lib/pq"
)

db, err := sql.Open("postgres", os.Getenv("DATABASE_URL"))
db.SetMaxOpenConns(25)  // Limit for Lambda
db.SetMaxIdleConns(5)   // Keep warm
```

---

### Can I use environment variables?

Yes! Configure in `transire.yaml`:

```yaml
environment:
  DATABASE_URL: ${DATABASE_URL}  # From environment or Secrets Manager
  LOG_LEVEL: info                # Literal value
```

Access in code:
```go
dbURL := os.Getenv("DATABASE_URL")
```

See: [Configuration](core-concepts/configuration.md)

---

### How do I test my handlers?

Use standard Go testing with `httptest`:

```go
func TestHandler(t *testing.T) {
    req := httptest.NewRequest("GET", "/health", nil)
    w := httptest.NewRecorder()

    healthHandler(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
}
```

See: [Testing Guide](guides/testing.md)

---

### Can I use WebSockets?

Currently, Transire focuses on HTTP APIs. WebSocket support via API Gateway WebSocket APIs is planned for a future release.

---

### How do I handle file uploads?

Use standard Go `multipart/form-data` handling:

```go
func uploadHandler(w http.ResponseWriter, r *http.Request) {
    r.ParseMultipartForm(10 << 20) // 10 MB max

    file, header, err := r.FormFile("file")
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    defer file.Close()

    // Upload to S3 via AWS SDK
    // ...
}
```

See: [Custom CDK Extensions](guides/custom-cdk.md) for adding S3 buckets

---

## Deployment

### What AWS permissions do I need?

Full list in [Deploying to AWS](guides/deploying-to-aws.md#iam-permissions).

Minimum required:
- Lambda (create/update functions)
- IAM (create execution roles)
- API Gateway (create HTTP APIs)
- CloudFormation (deploy stacks)
- S3 (store deployment artifacts)
- SQS (create queues)
- EventBridge (create rules)

---

### Can I customize the generated CDK?

Yes! Two approaches:

**1. Edit generated CDK** (after `transire build`):
```typescript
// infrastructure/lib/my-api-dev.ts
// Add custom resources here
```

**2. Use CDK extensions** (before build):
```yaml
# transire.yaml
cdk_extensions:
  - file: "extensions/database.ts"
```

See: [Custom CDK Extensions](guides/custom-cdk.md)

---

### How much does it cost to run on AWS?

AWS Lambda pricing (as of 2025):
- **Requests**: $0.20 per 1M requests
- **Duration**: $0.0000166667 per GB-second (ARM64)
- **Free tier**: 1M requests + 400,000 GB-seconds/month

**Example costs:**

| Scenario | Requests/mo | Memory | Avg Duration | Cost |
|----------|-------------|--------|--------------|------|
| Small API | 100K | 256 MB | 100ms | Free tier |
| Medium API | 1M | 256 MB | 100ms | ~$5/mo |
| Large API | 10M | 512 MB | 200ms | ~$85/mo |

Additional costs:
- **API Gateway**: $1.00 per million requests
- **CloudWatch Logs**: $0.50 per GB ingested
- **RDS** (if used): Starting at ~$15/mo for db.t3.micro
- **NAT Gateway** (if VPC): $0.045/hour (~$32/mo)

See: [Deploying to AWS - Cost Optimization](guides/deploying-to-aws.md#cost-optimization)

---

### Can I use my existing VPC?

Yes! Configure in `transire.yaml`:

```yaml
vpc:
  subnet_ids:
    - subnet-abc123
    - subnet-def456
  security_group_ids:
    - sg-xyz789
```

See: [Custom CDK Extensions](guides/custom-cdk.md)

---

### Can I deploy to multiple regions?

Yes! Deploy separate stacks per region:

```bash
export AWS_REGION=us-east-1
transire deploy

export AWS_REGION=eu-west-1
transire deploy
```

Use different stack names in `transire.yaml` or via CLI flags.

---

### Can I deploy to other clouds?

Currently AWS Lambda only. Planned support:
- **GCP Cloud Run** - In development
- **Azure Functions** - Future consideration

Follow [GitHub discussions](https://github.com/transire/transire/discussions) for updates.

---

### How do I roll back a deployment?

**Via CloudFormation:**
```bash
aws cloudformation rollback-stack --stack-name my-api-dev
```

**Via CDK:**
```bash
cd .transire/cdk
cdk rollback
```

**Best practice**: Use CI/CD with staged deployments (dev → staging → prod).

---

## Performance

### Lambda cold starts are slow

Solutions:

**1. Use ARM64 architecture:**
```yaml
lambda:
  architecture: arm64  # 20% faster, 20% cheaper
```

**2. Increase memory (more CPU):**
```yaml
lambda:
  memory_mb: 512  # More memory = more CPU = faster cold start
```

**3. Use provisioned concurrency** (costs more):
```yaml
lambda:
  provisioned_concurrency: 2  # Keep 2 instances warm
```

**4. Optimize code size:**
- Remove unused dependencies
- Use multi-function architecture (smaller packages)

See: [Multi-Function Architecture](guides/multi-function-architecture.md)

---

### How do I optimize Lambda performance?

**Memory vs Duration tradeoff:**
- More memory = more CPU = faster execution
- But costs more per invocation
- Test different memory settings to find optimal

**Connection pooling:**
```go
db.SetMaxOpenConns(25)  // Prevent connection exhaustion
db.SetMaxIdleConns(5)   // Reuse connections across invocations
```

**Caching:**
- Use ElastiCache for frequently accessed data
- Cache responses at API Gateway level
- Use CDN (CloudFront) for static content

---

### Queue messages are processing slowly

Check:

**1. Batch size:**
```yaml
queues:
  my-queue:
    batch_size: 10  # Process more messages per invocation
```

**2. Reserved concurrency:**
```yaml
lambda:
  reserved_concurrent_executions: 10  # Limit parallelism
```

**3. Visibility timeout:**
```yaml
queues:
  my-queue:
    visibility_timeout_seconds: 300  # Must be > Lambda timeout
```

See: [Queue Processing](guides/queue-processing.md)

---

## Troubleshooting

### "transire: command not found"

Add `$GOPATH/bin` to your `$PATH`:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH=$PATH:$(go env GOPATH)/bin

# Verify
transire --version
```

See: [Installation](getting-started/installation.md#troubleshooting)

---

### Port already in use

Change ports in `transire.yaml`:

```yaml
development:
  http_port: 8080
  queue_port: 8081
  scheduler_port: 8082
```

Or kill process using the port:
```bash
# Find process
lsof -i :3000

# Kill process
kill -9 <PID>
```

---

### "Too many connections" to database

**Problem:** RDS max connections exceeded

**Solutions:**

1. **Reduce connection pool:**
```go
db.SetMaxOpenConns(10)  // Lower limit
```

2. **Use RDS Proxy:**
- Automatic connection pooling
- Prevents connection exhaustion

3. **Increase RDS instance size:**
- Larger instances have more max connections
- Check: `SHOW max_connections;` in PostgreSQL

---

### Lambda timeout errors

**Problem:** Function timing out

**Solutions:**

1. **Increase timeout:**
```yaml
lambda:
  timeout_seconds: 300  # Max 900 (15 minutes)
```

2. **Optimize slow operations:**
- Use X-Ray to identify bottlenecks
- Add database indexes
- Use caching
- Move heavy processing to queue handlers

3. **Use async processing:**
- Publish to queue instead of processing synchronously
- Return response immediately

---

### "Permission denied" errors in Lambda

**Problem:** Lambda can't access AWS resource

**Solutions:**

1. **Grant IAM permissions:**
```yaml
existing_resources:
  dynamodb_tables:
    - name: my-table
      permissions: ["read", "write"]
```

2. **Check security groups** (for VPC resources):
- Verify Lambda security group can access RDS/ElastiCache
- Check RDS security group allows Lambda ingress

3. **Verify resource ARNs** are correct in config

---

### Logs not appearing in CloudWatch

**Problem:** Logs missing from CloudWatch Logs

**Solutions:**

1. **Check IAM permissions:**
- Lambda execution role needs `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`

2. **Ensure writing to stdout/stderr:**
```go
// Good: Writes to stdout
log.Println("message")
slog.Info("message")

// Bad: Writing to file (won't appear in CloudWatch)
f, _ := os.Create("/tmp/log.txt")
```

3. **Check Lambda timeout:**
- If function times out, logs may not flush
- Increase timeout or optimize code

---

## More Questions?

Can't find your answer? Try these resources:

- **[GitHub Discussions](https://github.com/transire/transire/discussions)** – Ask questions, share ideas
- **[GitHub Issues](https://github.com/transire/transire/issues)** – Report bugs, request features
- **[Examples](https://github.com/transire/transire/tree/main/examples)** – See working code samples

---

## Next Steps

- **[Quickstart](getting-started/quickstart.md)** – Build your first app in 5 minutes
- **[Your First API](getting-started/your-first-api.md)** – Complete tutorial
- **[Core Concepts](core-concepts/application-runtime.md)** – Understand how Transire works
- **[Deploying to AWS](guides/deploying-to-aws.md)** – Production deployment guide
