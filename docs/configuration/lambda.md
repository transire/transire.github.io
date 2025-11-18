---
title: "Lambda Settings"
description: "Configure AWS Lambda function settings for your Transire application"
keywords:
  - lambda
  - aws lambda
  - function settings
  - memory
  - timeout
  - architecture
category: configuration
difficulty: intermediate
estimated_time: 10 minutes
prerequisites:
  - "Basic Lambda knowledge"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Configuring Lambda resources"
    - "Optimizing performance"
    - "Setting timeouts"
  common_questions:
    - "How do I configure Lambda?"
    - "What memory should I use?"
    - "How do I set timeout?"
---

# Lambda Configuration

Detailed configuration options for AWS Lambda functions in Transire.

!!! tip "TL;DR"
    Configure Lambda memory, timeout, and architecture in `transire.yaml` under the `lambda:` key. Defaults: ARM64, 128MB, 30s timeout. Override per-function in `functions:` section.

---

## Overview

Transire generates AWS Lambda functions from your application. The `lambda` configuration section sets defaults for all functions, which can be overridden per-function.

Source: [`pkg/transire/config.go:33-38`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

---

## Configuration Fields

### Architecture

```yaml
lambda:
  architecture: arm64
```

**Type:** `string`
**Default:** `arm64`
**Allowed values:** `arm64` (only option in current version)

**Why ARM64:**
- **20% cost savings** compared to x86_64
- **Better performance** for most workloads
- **Graviton2 processors** are faster and more efficient
- **Same Go binary** compiles for ARM64 with zero code changes

**Future:** `x86_64` support planned but not yet implemented.

---

### Timeout

```yaml
lambda:
  timeout_seconds: 30
```

**Type:** `int`
**Default:** `30`
**Range:** `1` to `900` (15 minutes)
**Unit:** Seconds

**Recommendations by handler type:**

| Handler Type | Recommended Timeout | Reason |
|--------------|---------------------|---------|
| HTTP (API) | 30s | API Gateway timeout is 30s max |
| Queue | 300s (5min) | Batch processing may take longer |
| Schedule | 900s (15min) | Long-running maintenance tasks |

**Example:** Different timeouts per function group:

```yaml
lambda:
  timeout_seconds: 30  # Default

functions:
  web:
    include:
      - http_handlers: "*"
    timeout_seconds: 30

  background:
    include:
      - queue_handlers: "*"
      - schedule_handlers: "*"
    timeout_seconds: 300  # 5 minutes
```

---

### Memory

```yaml
lambda:
  memory_mb: 256
```

**Type:** `int`
**Default:** `128`
**Range:** `128` to `10240` (10 GB)
**Increments:** Must be in multiples of 1 MB

**How memory affects Lambda:**

1. **Memory = CPU:** More memory = more CPU power (proportional allocation)
2. **Cost:** Higher memory = higher cost per invocation
3. **Performance:** May reduce cold starts and execution time

**Memory recommendations:**

| Use Case | Memory | Notes |
|----------|--------|-------|
| Simple API | 128-256 MB | Sufficient for most HTTP handlers |
| Database queries | 512-1024 MB | Faster query processing |
| Image processing | 1024-3008 MB | CPU-intensive tasks |
| Video processing | 3008-10240 MB | Maximum for heavy workloads |

**Finding the right memory:**

1. Start with 128 MB
2. Monitor CloudWatch Logs for "Max Memory Used"
3. Increase if using >80% of allocated memory
4. Test performance with different memory settings

Example from CloudWatch Logs:
```
REPORT RequestId: abc123
Duration: 250ms
Billed Duration: 251ms
Memory Size: 256 MB
Max Memory Used: 180 MB  ← Monitor this
```

**Cost vs Performance Trade-off:**

Sometimes **increasing memory reduces cost** by reducing execution time:

- 128 MB @ 1000ms = $0.0000002083 per invocation
- 512 MB @ 250ms = $0.0000002083 per invocation (same cost, 4x faster!)

Source: AWS Lambda pricing as of 2024

---

### Reserved Concurrency (Per-Function)

```yaml
functions:
  web:
    include:
      - http_handlers: "*"
    memory_mb: 256
    timeout_seconds: 30
    reserved_concurrency: 100  # Max 100 concurrent executions
```

**Type:** `int`
**Default:** Unreserved (uses account limit)
**Range:** `0` to account limit (default: 1000)

**Use cases:**

- **Rate limiting:** Prevent a function from consuming all account concurrency
- **Cost control:** Limit maximum concurrent executions
- **Downstream protection:** Avoid overwhelming databases or APIs

**Important:**
- Setting this **reserves** concurrency from your account pool
- Other functions cannot use this reserved capacity
- `reserved_concurrency: 0` **disables** the function entirely

---

## Complete Example

```yaml
name: my-api
language: go
cloud: aws
runtime: lambda
iac: cdk

# Lambda defaults
lambda:
  architecture: arm64
  timeout_seconds: 30
  memory_mb: 128

# Per-function overrides
functions:
  web:
    include:
      - http_handlers: "*"
    memory_mb: 256        # More memory for API
    timeout_seconds: 30   # API Gateway max
    reserved_concurrency: 100

  background:
    include:
      - queue_handlers: "*"
      - schedule_handlers: "*"
    memory_mb: 512        # More memory for batch jobs
    timeout_seconds: 300  # 5 minutes for processing
```

Source: Example adapted from [`examples/simple-api/transire.yaml`](https://github.com/transire/transire/blob/main/examples/simple-api/transire.yaml)

---

## Lambda Runtime

Transire uses the **`provided.al2023`** runtime (Amazon Linux 2023) with a custom Go bootstrap.

**Technical details:**
- **Runtime:** `provided.al2023`
- **Handler:** `bootstrap`
- **Architecture:** ARM64
- **Go version:** 1.21+ (specified in your `go.mod`)

**Deployment package structure:**
```
function.zip
└── bootstrap  # Your compiled Go binary (ARM64)
```

The binary is compiled with:
```bash
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o bootstrap -ldflags="-s -w" .
```

Source: [`internal/providers/aws/lambda_builder.go`](https://github.com/transire/transire/blob/main/internal/providers/aws/lambda_builder.go)

---

## Monitoring Lambda Configuration

### Check Function Configuration

```bash
aws lambda get-function-configuration \
  --function-name my-api-stack-WebFunction-ABC123
```

Output:
```json
{
  "FunctionName": "my-api-stack-WebFunction-ABC123",
  "Runtime": "provided.al2023",
  "MemorySize": 256,
  "Timeout": 30,
  "Architectures": ["arm64"]
}
```

### View CloudWatch Metrics

Monitor your Lambda functions:

- **Duration:** Execution time per invocation
- **Memory:** Max memory used
- **Concurrency:** Concurrent executions
- **Throttles:** Rate-limited invocations
- **Errors:** Failed invocations

---

## Common Configuration Patterns

### Cost-Optimized Configuration

```yaml
lambda:
  architecture: arm64  # 20% savings
  memory_mb: 128       # Minimum
  timeout_seconds: 30  # Prevent runaway costs
```

Use for: Simple APIs, low-traffic applications

### Performance-Optimized Configuration

```yaml
lambda:
  architecture: arm64
  memory_mb: 1024      # More CPU power
  timeout_seconds: 60
```

Use for: Database-heavy applications, complex business logic

### Batch Processing Configuration

```yaml
lambda:
  architecture: arm64
  memory_mb: 512
  timeout_seconds: 900  # Maximum
```

Use for: Queue handlers, data processing, scheduled jobs

---

## Troubleshooting

### "Task timed out after X seconds"

**Cause:** Function execution exceeded `timeout_seconds`.

**Solution:**
1. Increase timeout in `transire.yaml`
2. Optimize code to run faster
3. Consider splitting into smaller functions

### "Lambda at or near maximum capacity"

**Cause:** Account concurrency limit reached.

**Solution:**
1. Request limit increase from AWS Support
2. Add `reserved_concurrency` to critical functions
3. Optimize code to reduce execution time

### "Memory Size: X MB Max Memory Used: Y MB"

**Problem:** Using >80% of allocated memory.

**Solution:**
Increase `memory_mb` in `transire.yaml`:
```yaml
lambda:
  memory_mb: 512  # Was 256
```

### "Function failed during initialization"

**Cause:** Out of memory during cold start.

**Solution:**
- Increase `memory_mb`
- Reduce dependencies in `go.mod`
- Use build tags to exclude unnecessary code

---

## Next Steps

- [Multi-Function Architecture](../guides/multi-function-architecture.md) – Split handlers across functions
- [transire.yaml Reference](transire-yaml.md) – Complete configuration reference
- [Deploying to AWS](../guides/deploying-to-aws.md) – Deploy your configured functions

---

## See Also

- [Queue Configuration](queues.md) – Configure SQS queues
- [Schedule Configuration](schedules.md) – Configure EventBridge schedules
- [VPC Configuration](vpc-existing.md) – Networking and existing resources
