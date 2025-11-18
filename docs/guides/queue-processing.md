# Queue Processing Patterns

Advanced patterns and best practices for processing messages with Transire queues.

!!! tip "TL;DR"
    Master batch processing, idempotency, partial failures, retries, and DLQ handling. Use patterns like deduplication, parallel processing, and circuit breakers for robust queue handlers.

---

## Overview

This guide covers advanced queue processing patterns for production systems:

- **Batch processing** – Handle multiple messages efficiently
- **Idempotency** – Process same message multiple times safely
- **Partial failures** – Handle individual message failures in batches
- **Error handling** – Retries, exponential backoff, DLQs
- **Performance** – Parallel processing, connection pooling
- **Monitoring** – Metrics, logging, alerting

---

## Partial Batch Failure Pattern

### The Problem

When processing a batch of 10 messages, if 1 fails, you don't want to retry all 10.

### The Solution

Return failed message IDs for selective retry:

```go
func (h *EmailHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        if err := h.processMessage(ctx, msg); err != nil {
            log.Printf("Failed to process message %s: %v", msg.ID(), err)
            failedIDs = append(failedIDs, msg.ID())
            continue  // Continue processing other messages
        }
    }

    // Only failed messages will be retried
    return failedIDs, nil
}
```

**Key points:**
- Continue processing remaining messages even if one fails
- Log failures for debugging
- SQS will only retry messages in `failedIDs`
- Successful messages are deleted from queue

Source: [`pkg/transire/queue_handler.go`](https://github.com/transire/transire/blob/main/pkg/transire/queue_handler.go)

---

## Idempotency Patterns

### Why Idempotency Matters

Messages can be delivered multiple times due to:
- Network failures
- Lambda timeouts
- Partial batch failures
- Manual retries

### Pattern 1: Deduplication Table

Track processed messages in database:

```go
type EmailHandler struct {
    db *sql.DB
}

func (h *EmailHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        // Check if already processed
        processed, err := h.isProcessed(ctx, msg.ID())
        if err != nil {
            failedIDs = append(failedIDs, msg.ID())
            continue
        }
        if processed {
            log.Printf("Message %s already processed, skipping", msg.ID())
            continue
        }

        // Process message
        if err := h.sendEmail(ctx, msg); err != nil {
            failedIDs = append(failedIDs, msg.ID())
            continue
        }

        // Mark as processed
        if err := h.markProcessed(ctx, msg.ID()); err != nil {
            log.Printf("Failed to mark message as processed: %v", err)
            // Don't add to failedIDs - email was sent successfully
        }
    }

    return failedIDs, nil
}

func (h *EmailHandler) isProcessed(ctx context.Context, messageID string) (bool, error) {
    var exists bool
    query := `SELECT EXISTS(SELECT 1 FROM processed_messages WHERE message_id = $1)`
    err := h.db.QueryRowContext(ctx, query, messageID).Scan(&exists)
    return exists, err
}

func (h *EmailHandler) markProcessed(ctx context.Context, messageID string) error {
    query := `INSERT INTO processed_messages (message_id, processed_at) VALUES ($1, NOW()) ON CONFLICT DO NOTHING`
    _, err := h.db.ExecContext(ctx, query, messageID)
    return err
}
```

**Schema:**
```sql
CREATE TABLE processed_messages (
    message_id VARCHAR(255) PRIMARY KEY,
    processed_at TIMESTAMP NOT NULL
);

-- Cleanup old entries periodically
CREATE INDEX idx_processed_at ON processed_messages(processed_at);
```

---

### Pattern 2: Idempotency Key in Payload

Include idempotency key in message payload:

```go
type OrderMessage struct {
    OrderID       string `json:"order_id"`
    IdempotencyKey string `json:"idempotency_key"`
    // ... other fields
}

func (h *OrderHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        var order OrderMessage
        if err := json.Unmarshal(msg.Body(), &order); err != nil {
            failedIDs = append(failedIDs, msg.ID())
            continue
        }

        // Use idempotency key to prevent duplicate processing
        if err := h.processOrder(ctx, order); err != nil {
            if !isIdempotencyError(err) {
                failedIDs = append(failedIDs, msg.ID())
            }
            // If idempotency error, message already processed - don't retry
        }
    }

    return failedIDs, nil
}

func (h *OrderHandler) processOrder(ctx context.Context, order OrderMessage) error {
    // Database constraint ensures idempotency
    query := `INSERT INTO orders (order_id, idempotency_key, ...) VALUES ($1, $2, ...)`
    _, err := h.db.ExecContext(ctx, query, order.OrderID, order.IdempotencyKey, ...)
    return err
}
```

---

### Pattern 3: Natural Idempotency

Design operations to be naturally idempotent:

```go
// Idempotent: Setting status to value
func updateStatus(ctx context.Context, orderID string, status string) error {
    query := `UPDATE orders SET status = $1 WHERE order_id = $2`
    _, err := db.ExecContext(ctx, query, status, orderID)
    return err
}

// NOT idempotent: Incrementing counter
func incrementCounter(ctx context.Context, orderID string) error {
    query := `UPDATE orders SET retry_count = retry_count + 1 WHERE order_id = $2`
    _, err := db.ExecContext(ctx, query, orderID)
    return err
}

// Idempotent version: Set to specific value
func setRetryCount(ctx context.Context, orderID string, count int) error {
    query := `UPDATE orders SET retry_count = $1 WHERE order_id = $2`
    _, err := db.ExecContext(ctx, query, count, orderID)
    return err
}
```

---

## Error Handling Patterns

### Pattern 1: Transient vs Permanent Errors

Distinguish between retryable and non-retryable errors:

```go
func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        if err := h.process(ctx, msg); err != nil {
            if isTransientError(err) {
                // Retry transient errors
                failedIDs = append(failedIDs, msg.ID())
                log.Printf("Transient error for message %s, will retry: %v", msg.ID(), err)
            } else {
                // Don't retry permanent errors - send to DLQ manually or log
                log.Printf("Permanent error for message %s, not retrying: %v", msg.ID(), err)
                h.sendToDLQ(ctx, msg, err)
            }
        }
    }

    return failedIDs, nil
}

func isTransientError(err error) bool {
    // Network timeouts
    if errors.Is(err, context.DeadlineExceeded) {
        return true
    }

    // Database connection errors
    if strings.Contains(err.Error(), "connection refused") {
        return true
    }

    // Rate limiting
    if strings.Contains(err.Error(), "rate limit") {
        return true
    }

    // HTTP 5xx errors
    if strings.Contains(err.Error(), "500") || strings.Contains(err.Error(), "503") {
        return true
    }

    return false
}
```

---

### Pattern 2: Circuit Breaker

Prevent cascading failures:

```go
type CircuitBreaker struct {
    mu              sync.Mutex
    failureCount    int
    lastFailureTime time.Time
    threshold       int
    timeout         time.Duration
    isOpen          bool
}

func (cb *CircuitBreaker) Call(fn func() error) error {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    // Check if circuit is open
    if cb.isOpen {
        if time.Since(cb.lastFailureTime) < cb.timeout {
            return errors.New("circuit breaker is open")
        }
        // Try to close circuit
        cb.isOpen = false
        cb.failureCount = 0
    }

    // Execute function
    err := fn()
    if err != nil {
        cb.failureCount++
        cb.lastFailureTime = time.Now()
        if cb.failureCount >= cb.threshold {
            cb.isOpen = true
            log.Printf("Circuit breaker opened after %d failures", cb.failureCount)
        }
        return err
    }

    // Success - reset failure count
    cb.failureCount = 0
    return nil
}

// Usage in handler
type Handler struct {
    breaker *CircuitBreaker
}

func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        err := h.breaker.Call(func() error {
            return h.callExternalAPI(ctx, msg)
        })

        if err != nil {
            failedIDs = append(failedIDs, msg.ID())
        }
    }

    return failedIDs, nil
}
```

---

## Performance Patterns

### Pattern 1: Parallel Processing

Process messages concurrently:

```go
func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var (
        mu        sync.Mutex
        failedIDs []string
        wg        sync.WaitGroup
    )

    // Limit concurrency
    sem := make(chan struct{}, 10) // Max 10 concurrent

    for _, msg := range messages {
        wg.Add(1)
        go func(msg transire.Message) {
            defer wg.Done()

            sem <- struct{}{}        // Acquire semaphore
            defer func() { <-sem }() // Release semaphore

            if err := h.process(ctx, msg); err != nil {
                mu.Lock()
                failedIDs = append(failedIDs, msg.ID())
                mu.Unlock()
            }
        }(msg)
    }

    wg.Wait()
    return failedIDs, nil
}
```

---

### Pattern 2: Connection Pooling

Reuse database connections:

```go
type Handler struct {
    db *sql.DB // Connection pool
}

func NewHandler() *Handler {
    db, _ := sql.Open("postgres", dsn)

    // Configure pool
    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(5)
    db.SetConnMaxLifetime(5 * time.Minute)

    return &Handler{db: db}
}

func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    // Connection is automatically managed by pool
    var failedIDs []string

    for _, msg := range messages {
        if err := h.saveToDatabase(ctx, msg); err != nil {
            failedIDs = append(failedIDs, msg.ID())
        }
    }

    return failedIDs, nil
}
```

---

### Pattern 3: Batch Database Operations

Use transactions and batch inserts:

```go
func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    // Start transaction
    tx, err := h.db.BeginTx(ctx, nil)
    if err != nil {
        // Fail entire batch
        var allIDs []string
        for _, msg := range messages {
            allIDs = append(allIDs, msg.ID())
        }
        return allIDs, err
    }
    defer tx.Rollback()

    // Prepare batch insert
    stmt, err := tx.PrepareContext(ctx, `
        INSERT INTO events (id, payload, created_at) VALUES ($1, $2, $3)
    `)
    if err != nil {
        var allIDs []string
        for _, msg := range messages {
            allIDs = append(allIDs, msg.ID())
        }
        return allIDs, err
    }
    defer stmt.Close()

    // Insert all messages
    for _, msg := range messages {
        if _, err := stmt.ExecContext(ctx, msg.ID(), msg.Body(), time.Now()); err != nil {
            log.Printf("Failed to insert message %s: %v", msg.ID(), err)
            // Individual failures - could track and retry
        }
    }

    // Commit transaction
    if err := tx.Commit(); err != nil {
        var allIDs []string
        for _, msg := range messages {
            allIDs = append(allIDs, msg.ID())
        }
        return allIDs, err
    }

    return nil, nil
}
```

---

## Monitoring Patterns

### Pattern 1: Structured Logging

```go
import "log/slog"

func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    start := time.Now()

    slog.Info("Processing message batch",
        "batch_size", len(messages),
        "queue", h.QueueName(),
    )

    var failedIDs []string
    for _, msg := range messages {
        if err := h.process(ctx, msg); err != nil {
            slog.Error("Message processing failed",
                "message_id", msg.ID(),
                "error", err,
                "queue", h.QueueName(),
            )
            failedIDs = append(failedIDs, msg.ID())
        }
    }

    duration := time.Since(start)
    slog.Info("Batch processing complete",
        "batch_size", len(messages),
        "failed", len(failedIDs),
        "duration_ms", duration.Milliseconds(),
        "queue", h.QueueName(),
    )

    return failedIDs, nil
}
```

---

### Pattern 2: Metrics Collection

```go
type Handler struct {
    processedCount prometheus.Counter
    failedCount    prometheus.Counter
    duration       prometheus.Histogram
}

func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    start := time.Now()
    defer func() {
        h.duration.Observe(time.Since(start).Seconds())
    }()

    var failedIDs []string
    for _, msg := range messages {
        if err := h.process(ctx, msg); err != nil {
            h.failedCount.Inc()
            failedIDs = append(failedIDs, msg.ID())
        } else {
            h.processedCount.Inc()
        }
    }

    return failedIDs, nil
}
```

---

## Dead Letter Queue Handling

### Pattern 1: Manual DLQ Processing

```go
func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        // Check receive count from message attributes
        receiveCount := getReceiveCount(msg)

        if receiveCount >= 3 { // Max retries reached
            // Process as DLQ message
            if err := h.handleDLQMessage(ctx, msg); err != nil {
                log.Printf("Failed to handle DLQ message: %v", err)
            }
            // Don't add to failedIDs - we've handled it
            continue
        }

        // Normal processing
        if err := h.process(ctx, msg); err != nil {
            failedIDs = append(failedIDs, msg.ID())
        }
    }

    return failedIDs, nil
}

func (h *Handler) handleDLQMessage(ctx context.Context, msg transire.Message) error {
    // Log to monitoring system
    log.Printf("Message sent to DLQ after max retries: %s", msg.ID())

    // Send alert
    h.alerting.Send("DLQ message", fmt.Sprintf("Message %s failed after max retries", msg.ID()))

    // Store for manual inspection
    return h.storeDLQMessage(ctx, msg)
}
```

---

### Pattern 2: DLQ Replay Handler

Create separate handler for DLQ replay:

```go
type DLQReplayHandler struct {
    originalHandler *OriginalHandler
}

func (h *DLQReplayHandler) QueueName() string {
    return "original-queue-dlq" // DLQ name
}

func (h *DLQReplayHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        // Investigate and fix issue
        if err := h.investigateAndFix(ctx, msg); err != nil {
            log.Printf("Still failing after investigation: %v", err)
            failedIDs = append(failedIDs, msg.ID())
            continue
        }

        // Replay to original handler
        if err := h.originalHandler.process(ctx, msg); err != nil {
            failedIDs = append(failedIDs, msg.ID())
        }
    }

    return failedIDs, nil
}
```

---

## Advanced Patterns

### Pattern 1: Message Deduplication Window

Track messages within time window:

```go
type Handler struct {
    recentMessages *sync.Map // message ID -> timestamp
    windowSize     time.Duration
}

func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        // Check if message was recently processed
        if lastSeen, ok := h.recentMessages.Load(msg.ID()); ok {
            if time.Since(lastSeen.(time.Time)) < h.windowSize {
                log.Printf("Duplicate message within window: %s", msg.ID())
                continue
            }
        }

        // Process message
        if err := h.process(ctx, msg); err != nil {
            failedIDs = append(failedIDs, msg.ID())
            continue
        }

        // Track message
        h.recentMessages.Store(msg.ID(), time.Now())
    }

    // Cleanup old entries periodically
    go h.cleanupOldEntries()

    return failedIDs, nil
}
```

---

### Pattern 2: Priority Queue Processing

```go
type PriorityMessage struct {
    transire.Message
    Priority int
}

func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    // Extract priority from message attributes
    priorityMessages := make([]PriorityMessage, len(messages))
    for i, msg := range messages {
        priority := extractPriority(msg)
        priorityMessages[i] = PriorityMessage{
            Message:  msg,
            Priority: priority,
        }
    }

    // Sort by priority (high to low)
    sort.Slice(priorityMessages, func(i, j int) bool {
        return priorityMessages[i].Priority > priorityMessages[j].Priority
    })

    // Process in priority order
    var failedIDs []string
    for _, pm := range priorityMessages {
        if err := h.process(ctx, pm.Message); err != nil {
            failedIDs = append(failedIDs, pm.Message.ID())
        }
    }

    return failedIDs, nil
}
```

---

## Best Practices Summary

### ✅ Do

- **Always return partial failures** – Don't fail entire batch
- **Implement idempotency** – Messages can be delivered multiple times
- **Use structured logging** – Include message ID, queue name, timing
- **Set appropriate timeouts** – Lambda timeout > visibility timeout
- **Monitor queue metrics** – Age, depth, DLQ size
- **Handle transient errors** – Distinguish from permanent errors
- **Use connection pooling** – Reuse database connections
- **Process in parallel** – When order doesn't matter
- **Track processed messages** – For idempotency

### ❌ Don't

- **Don't return errors for transient issues** – Use failedIDs instead
- **Don't process synchronously** – Use parallel processing when possible
- **Don't ignore DLQ** – Monitor and process regularly
- **Don't skip logging** – Essential for debugging
- **Don't forget context timeouts** – Respect Lambda timeout
- **Don't modify message payload** – Preserve original for retries
- **Don't batch insert without transactions** – Risk data inconsistency
- **Don't ignore visibility timeout** – Can cause duplicate processing

---

## Configuration Tips

### Queue Configuration

```yaml
queues:
  high-priority:
    visibility_timeout_seconds: 60   # 2x Lambda timeout
    max_receive_count: 3              # Retries before DLQ
    batch_size: 10                    # Balance throughput and latency

  low-priority:
    visibility_timeout_seconds: 300  # Longer timeout for slow processing
    max_receive_count: 5
    batch_size: 1                     # Process one at a time
```

### Lambda Configuration

```yaml
lambda:
  timeout_seconds: 30        # Must be < visibility timeout
  memory_mb: 512             # More memory = faster processing
  reserved_concurrent_executions: 10  # Prevent queue backlog
```

---

## Next Steps

- **[Queue Handlers Reference](../core-concepts/queue-handlers.md)** – Core concepts
- **[Queue Configuration](../configuration/queues.md)** – Configuration options
- **[Testing Guide](testing.md)** – Test queue handlers

---

## See Also

- [AWS SQS Best Practices](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-best-practices.html)
- [Idempotency Patterns](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
