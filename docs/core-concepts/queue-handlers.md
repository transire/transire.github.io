---
title: "Queue Handlers"
description: "Process SQS messages in batches with Transire's QueueHandler interface"
keywords:
  - queue handlers
  - sqs
  - message processing
  - batch processing
  - async processing
  - QueueHandler interface
  - retries
category: core-concepts
difficulty: intermediate
estimated_time: 15 minutes
prerequisites:
  - "Understanding of message queues"
  - "Basic async concepts"
related_docs:
  - path: "/guides/queue-processing/"
    relationship: "deep_dive"
  - path: "/configuration/queues/"
    relationship: "related"
  - path: "/examples/simple-api/"
    relationship: "related"
mcp_metadata:
  primary_use_cases:
    - "Processing async tasks"
    - "Handling background jobs"
    - "Understanding queue patterns"
  common_questions:
    - "How do I process queue messages?"
    - "How do I handle failed messages?"
    - "How do I configure retries?"
    - "How do I test queues locally?"
---

# Queue Handlers

Learn how to process SQS messages in batches with Transire's QueueHandler interface, including retry semantics and configuration.

!!! tip "TL;DR"
    Queue handlers process messages from queues (SQS in AWS) in batches. Locally, Transire simulates queues for testing. Implement the `QueueHandler` interface, return failed message IDs, and Transire handles retries automatically.

---

## The `QueueHandler` Interface

Defined in [`pkg/transire/interfaces.go`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go):

```go
type QueueHandler interface {
    QueueName() string
    Config() QueueConfig
    HandleMessages(ctx context.Context, messages []Message) ([]string, error)
}
```

---

## Method Breakdown

### `QueueName() string`

Returns the logical queue name (e.g., `"email-queue"`).

**This name is used:**

- **Locally**: to test with `transire dev queues send email-queue '{message}'`
- **AWS**: to generate the SQS queue resource in CDK

### `Config() QueueConfig`

Returns configuration for the queue.

**QueueConfig structure** ([`pkg/transire/interfaces.go:QueueConfig`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go)):

```go
type QueueConfig struct {
    VisibilityTimeoutSeconds int    // How long messages are invisible after delivery
    MaxReceiveCount          int    // Max delivery attempts before DLQ
    BatchSize                int    // Max messages per batch (1-10 for SQS)
    WaitTimeSeconds          int    // Long polling wait time
}
```

**Field descriptions:**

- **`VisibilityTimeoutSeconds`**: After a message is received, it's hidden from other consumers for this duration. If processing fails, the message becomes visible again.
- **`MaxReceiveCount`**: If a message fails this many times, it's moved to the Dead Letter Queue (DLQ).
- **`BatchSize`**: Maximum number of messages delivered in a single batch (SQS limit: 1-10).
- **`WaitTimeSeconds`**: Long polling duration. Higher values reduce API calls but increase latency.

### `HandleMessages(ctx context.Context, messages []Message) ([]string, error)`

Processes a batch of messages.

**Returns:**
- **`[]string`**: Message IDs that **failed** and should be retried
- **`error`**: Only return an error if the entire batch should be retried

**Retry semantics:**
- Messages with IDs in the returned slice are retried (up to `MaxReceiveCount`)
- After `MaxReceiveCount` failures, messages go to the DLQ
- Use SQS partial batch failure response ([`pkg/transire/lambda_runtime.go`](https://github.com/transire/transire/blob/main/pkg/transire/lambda_runtime.go))

---

## The `Message` Interface

Messages are delivered as this interface ([`pkg/transire/interfaces.go:Message`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go)):

```go
type Message interface {
    ID() string
    Body() []byte
    Attributes() map[string]string
}
```

**Methods:**

- **`ID()`**: Unique message identifier (for tracking failures)
- **`Body()`**: Message payload (raw bytes)
- **`Attributes()`**: Metadata key-value pairs

---

## Example: Email Queue Handler

From [`examples/simple-api/handlers.go:13-51`](https://github.com/transire/transire/blob/main/examples/simple-api/handlers.go):

```go
package main

import (
    "context"
    "encoding/json"
    "log"

    "github.com/transire/transire/pkg/transire"
)

// EmailQueueHandler processes email sending requests
type EmailQueueHandler struct{}

func (h *EmailQueueHandler) QueueName() string {
    return "email-queue"
}

func (h *EmailQueueHandler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        VisibilityTimeoutSeconds: 30,
        MaxReceiveCount:          3,
        BatchSize:                10,
        WaitTimeSeconds:          5, // Long polling
    }
}

func (h *EmailQueueHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    log.Printf("Processing %d email messages", len(messages))

    var failedIDs []string

    for _, msg := range messages {
        var emailReq EmailRequest
        if err := json.Unmarshal(msg.Body(), &emailReq); err != nil {
            log.Printf("Failed to parse email request from message %s: %v", msg.ID(), err)
            // Skip malformed messages (don't retry)
            continue
        }

        if err := sendEmail(emailReq); err != nil {
            log.Printf("Failed to send email for message %s: %v", msg.ID(), err)
            failedIDs = append(failedIDs, msg.ID())
        } else {
            log.Printf("Successfully sent email to %s (message %s)", emailReq.To, msg.ID())
        }
    }

    return failedIDs, nil
}

type EmailRequest struct {
    To      string `json:"to"`
    Subject string `json:"subject"`
    Body    string `json:"body"`
}

func sendEmail(req EmailRequest) error {
    // Email sending logic here
    return nil
}
```

### Key patterns

1. **Unmarshal body**: Parse `msg.Body()` into your struct
2. **Process each message**: Handle messages individually in a loop
3. **Track failures**: Collect `msg.ID()` for failed messages
4. **Return failed IDs**: Transire handles retry logic automatically
5. **Don't retry malformed messages**: If a message is invalid, skip it (don't add to `failedIDs`)

---

## Local Testing

Transire simulates queues locally ([`pkg/transire/local_runtime.go`](https://github.com/transire/transire/blob/main/pkg/transire/local_runtime.go)).

### Send a test message

```bash
transire dev queues send email-queue '{"to":"test@example.com","subject":"Test","body":"Hello"}'
```

Your `HandleMessages()` method will be called with the message.

### Check logs

```
[INFO] Processing 1 email messages
[INFO] Successfully sent email to test@example.com (message msg-abc123)
```

---

## AWS Integration

In AWS Lambda, Transire:

1. **Routes SQS events** to the correct `QueueHandler` based on queue name
2. **Uses partial batch failure** ([`pkg/transire/lambda_runtime.go`](https://github.com/transire/transire/blob/main/pkg/transire/lambda_runtime.go))
   - Failed message IDs are returned in SQS batch response
   - SQS automatically retries those messages
3. **Moves to DLQ** after `MaxReceiveCount` failures

### Generated CDK code

From [`internal/providers/aws/cdk_generator.go:92-175`](https://github.com/transire/transire/blob/main/internal/providers/aws/cdk_generator.go):

```typescript
// SQS Queue: email-queue
const emailQueue = new sqs.Queue(this, 'EmailQueueQueue', {
  queueName: 'email-queue',
  visibilityTimeout: cdk.Duration.seconds(30),
  deadLetterQueue: {
    queue: new sqs.Queue(this, 'EmailQueueDLQ'),
    maxReceiveCount: 3,
  },
});

// SQS -> Lambda event source
mainFunctionAlias.addEventSource(
  new SqsEventSource(emailQueue, {
    batchSize: 10,
    reportBatchItemFailures: true, // Enables partial batch failure
  })
);
```

**Key features:**

- **Dead Letter Queue (DLQ)** is created automatically
- **`reportBatchItemFailures: true`** enables partial batch failure support
- **Batch size** comes from your `QueueConfig.BatchSize`

---

## Configuration in `transire.yaml`

Override queue settings per-queue in [`transire.yaml`](https://github.com/transire/transire/blob/main/examples/simple-api/transire.yaml):

```yaml
queues:
  email-queue:
    visibility_timeout_seconds: 60
    max_receive_count: 5
    batch_size: 10
  notification-queue:
    visibility_timeout_seconds: 30
    max_receive_count: 3
    batch_size: 5
```

Config file values **override** the values from `Config()` method.

From [`examples/simple-api/transire.yaml:30-38`](https://github.com/transire/transire/blob/main/examples/simple-api/transire.yaml).

---

## Best Practices

### 1. Idempotency

Messages may be delivered more than once. Make your handler idempotent:

```go
func (h *EmailQueueHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    for _, msg := range messages {
        // Check if already processed (e.g., in database)
        if alreadyProcessed(msg.ID()) {
            log.Printf("Message %s already processed, skipping", msg.ID())
            continue
        }

        // Process message
        if err := processMessage(msg); err != nil {
            return []string{msg.ID()}, nil
        }

        // Mark as processed
        markProcessed(msg.ID())
    }
    return nil, nil
}
```

### 2. Error Handling

**Transient errors** (network timeouts, rate limits):
- Return message ID for retry

**Permanent errors** (invalid data, authorization failed):
- Skip the message (don't add to `failedIDs`)
- Log for manual review

```go
if err := processMessage(msg); err != nil {
    if isTransientError(err) {
        // Retry this message
        failedIDs = append(failedIDs, msg.ID())
    } else {
        // Permanent error - don't retry
        log.Printf("Permanent error for message %s: %v", msg.ID(), err)
    }
}
```

### 3. Timeouts

Set context deadlines to prevent hanging:

```go
func (h *EmailQueueHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    // Set timeout for entire batch
    ctx, cancel := context.WithTimeout(ctx, 25*time.Second)
    defer cancel()

    for _, msg := range messages {
        // Check context before processing each message
        if ctx.Err() != nil {
            // Timeout - return remaining messages for retry
            return getRemainingIDs(messages, processed), nil
        }

        processMessage(ctx, msg)
    }
    return nil, nil
}
```

### 4. Structured Logging

Log with context for debugging:

```go
log.Printf("[Queue: %s] [MessageID: %s] Processing email to %s",
    h.QueueName(), msg.ID(), emailReq.To)
```

---

## Advanced: Message Attributes

Use message attributes for routing or filtering:

```go
func (h *EmailQueueHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    for _, msg := range messages {
        // Check attribute
        priority := msg.Attributes()["priority"]
        if priority == "high" {
            // Process with higher priority
        }

        // Process message
        // ...
    }
    return nil, nil
}
```

Send messages with attributes (locally):

```bash
transire dev queues send email-queue '{
  "body": {"to":"user@example.com","subject":"Hi","body":"Hello"},
  "attributes": {"priority":"high"}
}'
```

---

## Troubleshooting

### Messages not being processed

**Check:**
1. Queue handler is registered: `app.RegisterQueueHandler(&EmailQueueHandler{})`
2. `QueueName()` matches the queue you're sending to
3. Message format is correct JSON

### Messages going to DLQ immediately

**Check:**
1. `MaxReceiveCount` is not too low (should be ≥ 3)
2. Handler is not panicking (check logs)
3. Handler is returning correct failed IDs

### High latency

**Solutions:**
1. Increase `BatchSize` to process more messages per invocation
2. Enable long polling with `WaitTimeSeconds` > 0
3. Use parallel processing within `HandleMessages()` (carefully)

---

## Next Steps

### Learn About Schedule Handlers

Similar pattern for cron jobs:

[:octicons-arrow-right-24: Schedule Handlers](schedule-handlers.md)

### Explore Queue Processing Patterns

Deep-dive into advanced patterns:

[:octicons-arrow-right-24: Queue Processing Guide](../guides/queue-processing.md)

### Configure Queues

Learn all configuration options:

[:octicons-arrow-right-24: Queue Configuration](../configuration/queues.md)

### Test Queue Handlers

Write unit tests for your handlers:

[:octicons-arrow-right-24: Testing Guide](../guides/testing.md)
