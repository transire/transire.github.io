---
title: "Multi-Function Architecture"
description: "Split your application into multiple Lambda functions for optimal resource usage"
keywords:
  - multi-function
  - architecture
  - optimization
  - lambda functions
  - resource allocation
category: guides
difficulty: advanced
estimated_time: 30 minutes
prerequisites:
  - "Understanding of Lambda architecture"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Optimizing resource usage"
    - "Scaling specific handlers"
    - "Reducing cold start times"
  common_questions:
    - "When should I use multiple functions?"
    - "How do I split my application?"
    - "What are the benefits?"
---

# Multi-Function Architecture

Learn how to split your application into multiple Lambda functions for optimized resource allocation, scaling, and cost efficiency.

!!! tip "TL;DR"
    Split handlers into separate Lambda functions to optimize memory, timeout, and concurrency per use case. Configure via `functions` in `transire.yaml` for better performance and lower costs.

---

## Overview

### Single vs Multi-Function

**Single Function (Default):**
- One Lambda function handles all requests (HTTP, queues, schedules)
- Simple deployment
- Good for small applications
- One-size-fits-all resource allocation

**Multi-Function Architecture:**
- Separate Lambda functions for different workloads
- Optimized resources per function
- Better scaling and cost control
- More complex deployment

---

## Why Use Multi-Function?

### 1. Resource Optimization

Different workloads have different needs:

| Workload | Memory | Timeout | Concurrency |
|----------|--------|---------|-------------|
| **API Handlers** | 256 MB | 30s | High |
| **Queue Workers** | 512 MB | 300s | Medium |
| **Schedulers** | 1024 MB | 900s | Low |

Single function = worst case for all = higher cost

---

### 2. Scaling Independence

**Problem with single function:**
```
High API traffic → scales up function
→ More queue/schedule invocations
→ Unnecessary scaling and cost
```

**With multi-function:**
```
High API traffic → scales web function only
Queue processing → independent scaling
Schedules → fixed concurrency
```

---

### 3. Cold Start Optimization

Smaller functions = faster cold starts:

| Function Type | Code Size | Cold Start |
|---------------|-----------|------------|
| **Monolith** | 50 MB | 2-3s |
| **Web only** | 10 MB | 500ms |
| **Queue only** | 15 MB | 800ms |

---

### 4. Cost Optimization

**Example calculation:**

```
Single function (512 MB, 30s timeout):
- API: 10,000 requests × 100ms = 1,000s
- Queue: 1,000 messages × 5s = 5,000s
- Schedule: 24 runs × 60s = 1,440s
Total: 7,440s × 512 MB = 3,809,280 MB-seconds

Multi-function:
- API (256 MB): 10,000 × 100ms = 1,000s × 256 MB = 256,000 MB-seconds
- Queue (512 MB): 1,000 × 5s = 5,000s × 512 MB = 2,560,000 MB-seconds
- Schedule (1024 MB): 24 × 60s = 1,440s × 1024 MB = 1,474,560 MB-seconds
Total: 4,290,560 MB-seconds

Savings: ~11% (plus better performance)
```

---

## Configuration

### Basic Multi-Function Setup

```yaml
name: my-api

# Define function groups
functions:
  web:
    include:
      - http_handlers: "*"
    memory_mb: 256
    timeout_seconds: 30
    reserved_concurrent_executions: 100

  workers:
    include:
      - queue_handlers: "*"
    memory_mb: 512
    timeout_seconds: 300
    reserved_concurrent_executions: 10

  schedulers:
    include:
      - schedule_handlers: "*"
    memory_mb: 1024
    timeout_seconds: 900
    reserved_concurrent_executions: 1
```

---

### Include Patterns

**All handlers of a type:**
```yaml
functions:
  web:
    include:
      - http_handlers: "*"
```

**Specific handlers by name:**
```yaml
functions:
  high-priority:
    include:
      - queue_handlers: "email-queue"
      - queue_handlers: "notification-queue"

  low-priority:
    include:
      - queue_handlers: "analytics-queue"
      - queue_handlers: "cleanup-queue"
```

**Multiple types in one function:**
```yaml
functions:
  background:
    include:
      - queue_handlers: "*"
      - schedule_handlers: "*"
```

---

## Deployment Patterns

### Pattern 1: Web + Background Split

**Best for:** Most applications

```yaml
functions:
  # Frontend: API Gateway
  web:
    include:
      - http_handlers: "*"
    memory_mb: 256
    timeout_seconds: 30
    reserved_concurrent_executions: 100

  # Backend: Async processing
  background:
    include:
      - queue_handlers: "*"
      - schedule_handlers: "*"
    memory_mb: 512
    timeout_seconds: 300
```

**Benefits:**
- Simple: Only 2 functions
- Clear separation of sync/async
- Easy to monitor and debug

**Use when:**
- Application has clear sync/async split
- Queue and schedule workloads are similar

---

### Pattern 2: Fine-Grained Split

**Best for:** Large applications with diverse workloads

```yaml
functions:
  web:
    include:
      - http_handlers: "*"
    memory_mb: 256
    timeout_seconds: 30

  queue-high-priority:
    include:
      - queue_handlers: "email-queue"
      - queue_handlers: "notification-queue"
    memory_mb: 512
    timeout_seconds: 60

  queue-low-priority:
    include:
      - queue_handlers: "analytics-queue"
      - queue_handlers: "reports-queue"
    memory_mb: 256
    timeout_seconds: 300

  schedulers:
    include:
      - schedule_handlers: "*"
    memory_mb: 1024
    timeout_seconds: 900
```

**Benefits:**
- Maximum optimization
- Independent scaling per workload
- Better resource utilization

**Use when:**
- Different queues have very different requirements
- Cost optimization is critical
- Application is large and stable

---

### Pattern 3: Per-Queue Functions

**Best for:** Queue-heavy applications

```yaml
functions:
  web:
    include:
      - http_handlers: "*"

  email-worker:
    include:
      - queue_handlers: "email-queue"
    memory_mb: 512
    timeout_seconds: 60

  image-processor:
    include:
      - queue_handlers: "image-processing-queue"
    memory_mb: 2048
    timeout_seconds: 300

  analytics-worker:
    include:
      - queue_handlers: "analytics-queue"
    memory_mb: 256
    timeout_seconds: 120
```

**Benefits:**
- Precise resource allocation
- Independent monitoring per queue
- Isolated failures

**Use when:**
- Queues have very different characteristics
- Some queues process heavy workloads (images, videos)
- Need independent scaling per queue

---

## Generated Infrastructure

### CloudFormation Resources

`transire build` generates separate resources for each function:

```typescript
// Generated CDK code

// Web function
const webFunction = new lambda.Function(this, 'WebFunction', {
  runtime: lambda.Runtime.PROVIDED_AL2023,
  handler: 'bootstrap',
  code: lambda.Code.fromAsset('../dist/web-function.zip'),
  memorySize: 256,
  timeout: cdk.Duration.seconds(30),
  reservedConcurrentExecutions: 100,
});

const api = new apigatewayv2.HttpApi(this, 'HttpApi', {
  defaultIntegration: new HttpLambdaIntegration('WebIntegration', webFunction),
});

// Workers function
const workersFunction = new lambda.Function(this, 'WorkersFunction', {
  runtime: lambda.Runtime.PROVIDED_AL2023,
  handler: 'bootstrap',
  code: lambda.Code.fromAsset('../dist/workers-function.zip'),
  memorySize: 512,
  timeout: cdk.Duration.seconds(300),
  reservedConcurrentExecutions: 10,
});

// SQS queues trigger workers function
const emailQueue = new sqs.Queue(this, 'EmailQueue');
workersFunction.addEventSource(new SqsEventSource(emailQueue, {
  batchSize: 10,
}));
```

---

### Build Artifacts

Each function gets separate deployment package:

```bash
transire build

# Output:
dist/
  web-function.zip         # Only HTTP handler code
  workers-function.zip     # Only queue/schedule handler code
```

Smaller packages = faster deployments and cold starts

---

## Best Practices

### 1. Start Simple, Split Later

**Initial deployment:**
```yaml
# No functions section = single function
name: my-api
```

**After profiling:**
```yaml
# Split when you identify bottlenecks
functions:
  web:
    include:
      - http_handlers: "*"
    memory_mb: 256

  background:
    include:
      - queue_handlers: "*"
      - schedule_handlers: "*"
    memory_mb: 512
```

**When to split:**
- Application is stable
- Have usage metrics
- Identified resource bottlenecks
- Cost optimization needed

---

### 2. Group Similar Workloads

**Good grouping:**
```yaml
functions:
  # Similar resource needs
  notifications:
    include:
      - queue_handlers: "email-queue"
      - queue_handlers: "sms-queue"
      - queue_handlers: "push-notification-queue"
    memory_mb: 512
```

**Bad grouping:**
```yaml
functions:
  # Very different resource needs
  mixed:
    include:
      - queue_handlers: "email-queue"        # Fast, 512 MB
      - queue_handlers: "video-encoding-queue"  # Slow, 3 GB
```

---

### 3. Set Reserved Concurrency

Prevent runaway costs and queue backlog:

```yaml
functions:
  web:
    reserved_concurrent_executions: 100  # Prevent DDoS cost spike

  workers:
    reserved_concurrent_executions: 10   # Control queue processing rate

  schedulers:
    reserved_concurrent_executions: 1    # One schedule at a time
```

---

### 4. Monitor Per-Function Metrics

```yaml
# Use function name in logs and metrics
functions:
  web:
    environment:
      FUNCTION_NAME: web

  workers:
    environment:
      FUNCTION_NAME: workers
```

```go
// In code
slog.Info("Request processed",
    "function", os.Getenv("FUNCTION_NAME"),
    "duration_ms", duration.Milliseconds(),
)
```

---

### 5. Use Environment-Specific Config

```yaml
# transire.prod.yaml
functions:
  web:
    memory_mb: 512                         # More memory in prod
    reserved_concurrent_executions: 200    # Higher limit

# transire.dev.yaml
functions:
  web:
    memory_mb: 256                         # Less memory in dev
    reserved_concurrent_executions: 10     # Lower limit
```

---

## Migration Strategy

### Migrating from Single to Multi-Function

**Step 1: Profile current usage**
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=my-api-MainFunction \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average,Maximum
```

**Step 2: Add function configuration**
```yaml
# Start with simple split
functions:
  web:
    include:
      - http_handlers: "*"
    memory_mb: 256

  background:
    include:
      - queue_handlers: "*"
      - schedule_handlers: "*"
    memory_mb: 512
```

**Step 3: Deploy and monitor**
```bash
transire build
transire deploy

# Monitor for issues
aws logs tail /aws/lambda/my-api-WebFunction --follow
aws logs tail /aws/lambda/my-api-BackgroundFunction --follow
```

**Step 4: Optimize based on metrics**
```yaml
# Adjust memory/timeout based on CloudWatch metrics
functions:
  web:
    memory_mb: 512  # Increased after profiling
```

---

## Troubleshooting

### Function Not Receiving Requests

**Problem:** HTTP requests return 404

**Check:**
1. Verify function includes HTTP handlers:
   ```yaml
   functions:
     web:
       include:
         - http_handlers: "*"
   ```

2. Check API Gateway integration:
   ```bash
   aws apigatewayv2 get-integrations --api-id <api-id>
   ```

3. Verify Lambda permissions for API Gateway

---

### Queue Messages Not Processing

**Problem:** Messages stuck in queue

**Check:**
1. Verify function includes queue handler:
   ```yaml
   functions:
     workers:
       include:
         - queue_handlers: "email-queue"
   ```

2. Check event source mapping:
   ```bash
   aws lambda list-event-source-mappings \
     --function-name my-api-WorkersFunction
   ```

3. Verify SQS permissions for Lambda

---

### High Cold Start Times

**Problem:** Functions timing out on cold start

**Solutions:**
1. **Reduce memory** (paradoxically can help):
   ```yaml
   memory_mb: 256  # Smaller package, faster init
   ```

2. **Use ARM64 architecture:**
   ```yaml
   lambda:
     architecture: arm64  # 20% faster, 20% cheaper
   ```

3. **Enable provisioned concurrency** (costs more):
   ```yaml
   functions:
     web:
       provisioned_concurrent_executions: 2
   ```

---

### Deployment Too Slow

**Problem:** `transire deploy` takes too long

**Cause:** Deploying multiple functions sequentially

**Solution:** Deploy in parallel (future enhancement) or split into separate stacks

---

## Cost Analysis

### Calculate Costs Per Function

**Web function:**
```
Requests: 1M/month
Duration: 100ms average
Memory: 256 MB

Cost = (1M requests × $0.20/1M) + (1M × 0.1s × 256MB/1024MB × $0.0000166667)
     = $0.20 + $0.43 = $0.63/month
```

**Workers function:**
```
Requests: 100K/month
Duration: 5s average
Memory: 512 MB

Cost = (100K × $0.20/1M) + (100K × 5s × 512MB/1024MB × $0.0000166667)
     = $0.02 + $4.17 = $4.19/month
```

**Total: $4.82/month**

Compare to single function approach for your workload.

---

## Advanced Patterns

### Pattern 1: Canary Deployments

Deploy to subset of functions first:

```bash
# Deploy web function only
transire deploy --functions web

# Monitor metrics
# ...

# Deploy remaining functions
transire deploy --functions workers,schedulers
```

---

### Pattern 2: Cross-Function Communication

Functions can publish to queues consumed by other functions:

```go
// In web function
func createOrder(w http.ResponseWriter, r *http.Request) {
    // Process order...

    // Publish to queue for async processing
    sqs.SendMessage(ctx, "order-processing-queue", orderData)

    w.WriteHeader(http.StatusCreated)
}

// In workers function
type OrderProcessingHandler struct{}

func (h *OrderProcessingHandler) QueueName() string {
    return "order-processing-queue"
}

func (h *OrderProcessingHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    // Process orders asynchronously
}
```

---

### Pattern 3: Function-Specific IAM Permissions

```yaml
functions:
  web:
    include:
      - http_handlers: "*"
    existing_resources:
      dynamodb_tables:
        - name: users-table
          permissions: ["read"]  # Read-only

  workers:
    include:
      - queue_handlers: "*"
    existing_resources:
      dynamodb_tables:
        - name: users-table
          permissions: ["read", "write"]  # Full access
      s3_buckets:
        - name: uploads-bucket
          permissions: ["write"]
```

---

## Next Steps

- **[Configuration Reference](../configuration/transire-yaml.md)** – Complete configuration options
- **[Deploying to AWS](deploying-to-aws.md)** – Deployment walkthrough
- **[Cost Optimization](../guides/deploying-to-aws.md#cost-optimization)** – Save money

---

## See Also

- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Lambda Cold Start Optimization](https://aws.amazon.com/blogs/compute/operating-lambda-performance-optimization-part-1/)
