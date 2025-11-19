---
title: "Queue Configuration"
description: "Configure SQS queue settings for message processing"
keywords:
  - queue configuration
  - sqs
  - batch size
  - visibility timeout
  - dlq
category: configuration
difficulty: intermediate
estimated_time: 10 minutes
prerequisites:
  - "Understanding of queues"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Configuring queue behavior"
    - "Setting batch sizes"
    - "Configuring retries"
  common_questions:
    - "How do I configure queues?"
    - "What is visibility timeout?"
    - "How do I set batch size?"
---

# Queue Configuration

Configure AWS SQS queues for your Transire queue handlers.

!!! tip "TL;DR"
    Queue configuration comes from two sources: 1) `QueueConfig` struct in your `QueueHandler` implementation, 2) per-queue overrides in `transire.yaml`. Use `transire.yaml` to adjust settings without code changes.

---

## Overview

Transire automatically creates SQS queues for each registered `QueueHandler`. Queue behavior is configured in two places:

1. **Default configuration:** In your `QueueHandler.Config()` method (code)
2. **Per-queue overrides:** In `transire.yaml` under `queues:` key (config file)

Values in `transire.yaml` override values from code.

---

## QueueConfig Struct (Code)

Define default queue configuration in your handler:

```go
func (h *EmailQueueHandler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        VisibilityTimeoutSeconds: 30,
        MaxReceiveCount:          3,
        BatchSize:                10,
        WaitTimeSeconds:          5,
    }
}
```

Source: [`pkg/transire/interfaces.go`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go), example from [`examples/simple-api/handlers.go:20-27`](https://github.com/transire/transire/blob/main/examples/simple-api/handlers.go)

---

## Configuration Fields

### Visibility Timeout

```go
VisibilityTimeoutSeconds: 30
```

**Type:** `int`
**Default:** `30`
**Range:** `0` to `43200` (12 hours)
**Unit:** Seconds

**What it does:**
After a message is delivered to a consumer, it becomes invisible to other consumers for this duration. If the consumer doesn't delete the message within this time, it becomes visible again for redelivery.

**How to set it:**
Set to **1.5x to 2x your handler's expected duration**.

**Example calculation:**
- Handler takes 10 seconds → Set visibility timeout to 20-30 seconds
- Handler takes 60 seconds → Set visibility timeout to 90-120 seconds

**Too short:**
- Messages redelivered while still processing
- Duplicate processing
- Wasted Lambda invocations

**Too long:**
- Failed messages take longer to retry
- Longer recovery time after errors

---

### Max Receive Count

```go
MaxReceiveCount: 3
```

**Type:** `int`
**Default:** `3`
**Range:** `1` to `1000`

**What it does:**
Maximum number of times a message can be received before moving to Dead Letter Queue (DLQ).

**Recommendations:**

| Failure Type | Max Receive Count | Reason |
|--------------|-------------------|--------|
| Transient errors | 3-5 | Give network/service time to recover |
| Malformed data | 1-2 | Won't succeed on retry |
| External API | 5-10 | Allow multiple retry attempts |

**Important:**
- Every queue automatically gets a DLQ
- Messages in DLQ should be investigated and fixed manually
- Monitor DLQ depth as a key metric

---

### Batch Size

```go
BatchSize: 10
```

**Type:** `int`
**Default:** `10`
**Range:** `1` to `10` (SQS maximum)

**What it does:**
Number of messages delivered to `HandleMessages()` in a single batch.

**Recommendations:**

| Use Case | Batch Size | Reason |
|----------|------------|--------|
| Fast processing | 10 | Maximize throughput |
| Slow processing | 1-5 | Avoid timeouts |
| Database writes | 5-10 | Batch inserts |
| External API calls | 1-3 | Rate limiting |

**Trade-offs:**

**Larger batches (8-10):**
- ✅ Better throughput
- ✅ Lower Lambda invocation cost
- ❌ Longer processing time
- ❌ Higher risk of timeout

**Smaller batches (1-3):**
- ✅ Faster per-message processing
- ✅ Lower timeout risk
- ❌ More Lambda invocations
- ❌ Higher cost

**Partial batch failures:**
Transire returns failed message IDs from your handler, and SQS automatically retries only those messages.

```go
func (h *EmailQueueHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        if err := processMessage(msg); err != nil {
            failedIDs = append(failedIDs, msg.ID())  // Mark for retry
        }
    }

    return failedIDs, nil  // Only failed messages are retried
}
```

Source: [`pkg/transire/lambda_runtime.go`](https://github.com/transire/transire/blob/main/pkg/transire/lambda_runtime.go) uses SQS partial batch responses

---

### Wait Time (Long Polling)

```go
WaitTimeSeconds: 5
```

**Type:** `int`
**Default:** `0`
**Range:** `0` to `20` seconds

**What it does:**
Enables long polling. SQS waits up to this duration for messages before returning empty response.

**Benefits:**
- ✅ Reduces empty receives
- ✅ Lower cost (fewer API calls)
- ✅ Lower Lambda invocations for empty queues

**Recommendation:**
- Use `5-20` seconds for all queues
- Higher values (15-20) for low-traffic queues
- Lower values (5-10) for high-traffic queues

**Important:**
- `0` = short polling (not recommended, more expensive)
- `20` = maximum long polling (most cost-effective)

---

## Per-Queue Overrides (YAML)

Override queue settings in `transire.yaml` without changing code:

```yaml
queues:
  email-queue:
    visibility_timeout_seconds: 60  # Override: Was 30 in code
    max_receive_count: 5            # Override: Was 3 in code
    batch_size: 10                  # Same as code

  notification-queue:
    visibility_timeout_seconds: 120
    max_receive_count: 5
    batch_size: 5
```

**When to use overrides:**

✅ **Good use cases:**
- Environment-specific settings (dev vs prod)
- Tuning performance without redeploying code
- Testing different configurations

❌ **Avoid overrides for:**
- Essential handler behavior
- Values coupled to code logic
- Settings that should always match

---

## Complete Example

### In Code

```go
// handlers.go
package main

import (
    "context"
    "encoding/json"
    "log"

    "github.com/transire/transire/pkg/transire"
)

type EmailQueueHandler struct{}

func (h *EmailQueueHandler) QueueName() string {
    return "email-queue"
}

func (h *EmailQueueHandler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        VisibilityTimeoutSeconds: 30,
        MaxReceiveCount:          3,
        BatchSize:                10,
        WaitTimeSeconds:          5,
    }
}

func (h *EmailQueueHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    log.Printf("Processing %d email messages", len(messages))

    var failedIDs []string

    for _, msg := range messages {
        if err := sendEmail(msg); err != nil {
            log.Printf("Failed to send email: %v", err)
            failedIDs = append(failedIDs, msg.ID())
        }
    }

    return failedIDs, nil
}
```

Source: Example adapted from [`examples/simple-api/handlers.go:13-51`](https://github.com/transire/transire/blob/main/examples/simple-api/handlers.go)

### In Configuration

```yaml
# transire.yaml
name: my-api

# ... other configuration ...

queues:
  email-queue:
    # Production settings - override code defaults
    visibility_timeout_seconds: 60   # Longer timeout for production
    max_receive_count: 5             # More retries for transient failures
    batch_size: 10                   # Keep default
```

Source: Example adapted from [`examples/simple-api/transire.yaml:30-38`](https://github.com/transire/transire/blob/main/examples/simple-api/transire.yaml)

---

## Generated SQS Resources

When you run `transire build`, CDK generates:

```typescript
// infrastructure/lib/my-api-dev.ts (generated)

// SQS Queue + DLQ
const emailQueue = new sqs.Queue(this, 'EmailQueue', {
  queueName: 'my-api-dev-email-queue',
  visibilityTimeout: cdk.Duration.seconds(30),
  deadLetterQueue: {
    queue: new sqs.Queue(this, 'EmailQueueDLQ', {
      queueName: 'my-api-dev-email-queue-dlq',
    }),
    maxReceiveCount: 3,
  },
});

// Lambda event source
mainFunctionAlias.addEventSource(
  new SqsEventSource(emailQueue, {
    batchSize: 10,
    reportBatchItemFailures: true,  // Enables partial batch failures
  })
);
```

Source: CDK template from [`internal/providers/aws/cdk_generator.go:92-175`](https://github.com/transire/transire/blob/main/internal/providers/aws/cdk_generator.go)

---

## Local Testing

Test queues locally with `transire run`:

```bash
# Start app
transire run

# In another terminal, send a test message
transire dev queues send email-queue '{
  "to": "test@example.com",
  "subject": "Test Email",
  "body": "Hello from Transire!"
}'
```

Your `HandleMessages` method processes the message immediately.

Source: Queue simulator in [`pkg/transire/local_runtime.go`](https://github.com/transire/transire/blob/main/pkg/transire/local_runtime.go)

---

## Monitoring Queues

### CloudWatch Metrics

Key metrics to monitor:

| Metric | Description | Alert On |
|--------|-------------|----------|
| `ApproximateNumberOfMessagesVisible` | Messages waiting | High backlog |
| `ApproximateAgeOfOldestMessage` | Oldest message age | Processing lag |
| `NumberOfMessagesSent` | Messages sent to queue | Unexpected spikes |
| `NumberOfMessagesDeleted` | Successfully processed | Low rate |
| `ApproximateNumberOfMessagesNotVisible` | Messages in flight | Stuck messages |

### Dead Letter Queue (DLQ)

**Critical:** Always monitor your DLQ:

```bash
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/my-api-dev-email-queue-dlq \
  --attribute-names ApproximateNumberOfMessages
```

**Set up CloudWatch Alarm:**
```yaml
# CloudFormation/CDK
DLQAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: ApproximateNumberOfMessagesVisible
    Namespace: AWS/SQS
    Threshold: 1
    ComparisonOperator: GreaterThanThreshold
    # Alert when ANY message in DLQ
```

---

## Common Configuration Patterns

### Fast, Simple Processing

```go
transire.QueueConfig{
    VisibilityTimeoutSeconds: 30,
    MaxReceiveCount:          3,
    BatchSize:                10,
    WaitTimeSeconds:          20,  // Long polling
}
```

Use for: Notifications, simple data transforms

### Slow, External API Calls

```go
transire.QueueConfig{
    VisibilityTimeoutSeconds: 300,  // 5 minutes
    MaxReceiveCount:          5,    // More retries
    BatchSize:                1,    // One at a time
    WaitTimeSeconds:          10,
}
```

Use for: Third-party API integration, webhooks

### Batch Database Inserts

```go
transire.QueueConfig{
    VisibilityTimeoutSeconds: 120,  // 2 minutes
    MaxReceiveCount:          3,
    BatchSize:                10,   // Batch for DB efficiency
    WaitTimeSeconds:          15,
}
```

Use for: Bulk inserts, analytics processing

---

## Troubleshooting

### Messages processed multiple times

**Cause:** Visibility timeout too short.

**Solution:**
Increase `visibility_timeout_seconds`:
```yaml
queues:
  my-queue:
    visibility_timeout_seconds: 120  # Was 30
```

### Messages moving to DLQ immediately

**Cause:** `max_receive_count` too low or persistent errors.

**Solution:**
1. Check DLQ messages for error patterns
2. Fix code errors
3. Increase `max_receive_count` if transient:
```yaml
queues:
  my-queue:
    max_receive_count: 5  # Was 3
```

### High Lambda costs with low traffic

**Cause:** Short polling (frequent empty receives).

**Solution:**
Enable long polling:
```go
WaitTimeSeconds: 20  // Maximum long polling
```

### Handler timing out

**Cause:** Batch too large or visibility timeout too short.

**Solution:**
Reduce batch size:
```yaml
queues:
  my-queue:
    batch_size: 5  # Was 10
```

---

## Next Steps

- [Queue Handlers](../core-concepts/queue-handlers.md) – Implement queue handlers
- [Queue Processing Guide](../guides/queue-processing.md) – Best practices and patterns
- [transire.yaml Reference](transire-yaml.md) – Complete configuration reference

---

## See Also

- [Schedule Configuration](schedules.md) – Configure EventBridge schedules
- [Lambda Configuration](lambda.md) – Function memory and timeout
- [Local Development](../guides/local-development.md) – Test queues locally
