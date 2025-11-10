---
title: Queue API Reference
description: Complete reference for Transire queue handlers, batch processing, and message patterns
category: reference
subcategory: sdk
complexity: beginner
mcp_use: reference
features_covered:
  - Queue handlers
  - Batch processing
  - Partial failures
  - Dead-letter queues
  - Type safety
  - Message enqueueing
code_blocks: true
last_updated: 2025-11-10
---

# Queue API Reference

> **Complete reference** for async queue processing with Transire

## Table of Contents

- [Queue Registration](#queue-registration)
- [Handler Signatures](#handler-signatures)
- [Message Types](#message-types)
- [Enqueueing Messages](#enqueueing-messages)
- [Batch Processing](#batch-processing)
- [Error Handling](#error-handling)
- [Partial Batch Failures](#partial-batch-failures)
- [Dead-Letter Queues](#dead-letter-queues)
- [Configuration](#configuration)
- [Testing](#testing)

---

## Queue Registration

### Basic Registration

Register a queue handler:

```go
app.RegisterQueue(key string, handler QueueHandler)
```

**Parameters:**
- `key` - Unique queue identifier
- `handler` - Function to process messages

**Example:**

```go
func main() {
    app := transire.New()

    // Register queue handler
    app.RegisterQueue("fulfill-orders", fulfillOrders)

    app.Run()
}
```

### Multiple Queues

```go
func main() {
    app := transire.New()

    // Order fulfillment
    app.RegisterQueue("fulfill-orders", fulfillOrders)

    // Email notifications
    app.RegisterQueue("send-emails", sendEmails)

    // Inventory sync
    app.RegisterQueue("sync-inventory", syncInventory)

    app.Run()
}
```

---

## Handler Signatures

### Basic Handler

Process batch of messages:

```go
func(ctx context.Context, messages []T) error
```

**Example:**

```go
func fulfillOrders(ctx context.Context, orders []Order) error {
    for _, order := range orders {
        // Process each order
        if err := processOrder(ctx, order); err != nil {
            return err
        }
    }
    return nil
}
```

### Handler with Dependencies

Inject services:

```go
func(ctx context.Context, messages []T, deps ...interface{}) error
```

**Example:**

```go
func fulfillOrders(ctx context.Context, orders []Order, db *Database, logger *Logger) error {
    logger.Info(fmt.Sprintf("Processing %d orders", len(orders)))

    for _, order := range orders {
        if err := processOrder(ctx, order, db); err != nil {
            logger.Error("Failed to process order", err)
            return err
        }
    }

    return nil
}
```

---

## Message Types

### Type Definition

Messages are strongly typed:

```go
type Order struct {
    ID       string    `json:"id"`
    Product  string    `json:"product"`
    Quantity int       `json:"quantity"`
    Price    float64   `json:"price"`
    Status   string    `json:"status"`
    UserID   string    `json:"user_id"`
}

// Handler receives []Order
func fulfillOrders(ctx context.Context, orders []Order) error {
    // orders is []Order, not []interface{}
    for _, order := range orders {
        // Type-safe access
        fmt.Printf("Processing order %s: %s", order.ID, order.Product)
    }
    return nil
}
```

### Runtime Type Safety

Transire adds `__type` field to messages:

```json
{
  "__type": "main.Order",
  "id": "ORD-123",
  "product": "Widget",
  "quantity": 5,
  "price": 99.99
}
```

**Type validation:**
- If message type doesn't match handler type → moves to DLQ
- Prevents wrong-type messages from being processed
- Enables schema evolution

---

## Enqueueing Messages

### Enqueue Single Message

```go
app.Enqueue(ctx context.Context, queueKey string, message interface{}) error
```

**Example:**

```go
func createOrder(app *transire.App) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        order := &Order{
            ID:      generateID(),
            Product: "Widget",
            Status:  "pending",
        }

        // Save to database
        db.CreateOrder(r.Context(), order)

        // Enqueue for async processing
        if err := app.Enqueue(r.Context(), "fulfill-orders", *order); err != nil {
            log.Printf("WARNING: Failed to enqueue: %v", err)
            // Order still created, can retry fulfillment later
        }

        response.Created(w, order)
    }
}
```

### Enqueue Batch

```go
app.EnqueueBatch(ctx context.Context, queueKey string, messages []interface{}) error
```

**Example:**

```go
func scheduleOrdersFulfillment(app *transire.App) func(ctx context.Context, orders []Order) error {
    return func(ctx context.Context, orders []Order) error {
        // Convert to []interface{}
        messages := make([]interface{}, len(orders))
        for i, order := range orders {
            messages[i] = order
        }

        return app.EnqueueBatch(ctx, "fulfill-orders", messages)
    }
}
```

### Enqueue with Delay

```go
app.EnqueueDelayed(ctx context.Context, queueKey string, message interface{}, delay time.Duration) error
```

**Example:**

```go
// Send reminder after 24 hours
reminder := Reminder{
    OrderID: order.ID,
    UserID:  order.UserID,
    Message: "Your order is ready!",
}

app.EnqueueDelayed(ctx, "send-reminders", reminder, 24*time.Hour)
```

---

## Batch Processing

### Understanding Batches

Queue handlers receive **batches** of messages:

```go
func fulfillOrders(ctx context.Context, orders []Order) error {
    // orders is a batch, typically 1-10 messages
    log.Printf("Processing batch of %d orders", len(orders))

    for _, order := range orders {
        // Process each message in batch
        processOrder(ctx, order)
    }

    return nil
}
```

**Batch size configuration:**

```yaml
# transire.yaml
queues:
  max_batch_size: 10       # Max messages per batch
  batch_window_s: 5        # Wait 5s to collect batch
```

**How batching works:**

1. Messages arrive at queue
2. Transire waits up to `batch_window_s` seconds
3. Collects up to `max_batch_size` messages
4. Invokes handler with batch
5. Repeats for next batch

### Batch Processing Patterns

#### Pattern 1: Process Each Independently

```go
func fulfillOrders(ctx context.Context, orders []Order, db *Database) error {
    br := transire.NewBatchResult(len(orders))

    for i, order := range orders {
        if err := db.FulfillOrder(ctx, order.ID); err != nil {
            br.Fail(i, err)
            continue
        }
    }

    return br.ToCloudPartialBatchResponse()
}
```

#### Pattern 2: Parallel Processing

```go
func fulfillOrders(ctx context.Context, orders []Order, db *Database) error {
    br := transire.NewBatchResult(len(orders))

    // Process in parallel with limit
    sem := make(chan struct{}, 5) // Max 5 concurrent
    var wg sync.WaitGroup

    for i, order := range orders {
        wg.Add(1)
        go func(idx int, o Order) {
            defer wg.Done()

            sem <- struct{}{}        // Acquire
            defer func() { <-sem }() // Release

            if err := db.FulfillOrder(ctx, o.ID); err != nil {
                br.Fail(idx, err)
            }
        }(i, order)
    }

    wg.Wait()
    return br.ToCloudPartialBatchResponse()
}
```

#### Pattern 3: Batch Database Operations

```go
func fulfillOrders(ctx context.Context, orders []Order, db *Database) error {
    // Collect all IDs
    ids := make([]string, len(orders))
    for i, order := range orders {
        ids[i] = order.ID
    }

    // Single batch update
    if err := db.UpdateOrderStatusBatch(ctx, ids, "fulfilled"); err != nil {
        return err // All messages will retry
    }

    return nil
}
```

---

## Error Handling

### All-or-Nothing Errors

Return error to retry entire batch:

```go
func fulfillOrders(ctx context.Context, orders []Order, db *Database) error {
    for _, order := range orders {
        if err := db.FulfillOrder(ctx, order.ID); err != nil {
            // Return error - ALL messages in batch will retry
            return err
        }
    }
    return nil
}
```

**When to use:**
- Atomic operations (all succeed or all fail)
- Database transactions
- Critical processing where partial success is unacceptable

**Retry behavior:**
- Entire batch goes back to queue
- Retries up to `max_receive_count` (default: 3)
- After max retries → moves to DLQ

### Idempotent Processing

Make handlers safe to retry:

```go
func fulfillOrders(ctx context.Context, orders []Order, db *Database) error {
    for _, order := range orders {
        // Check if already processed
        existing, _ := db.GetOrder(ctx, order.ID)
        if existing.Status == "fulfilled" {
            log.Printf("Order %s already fulfilled, skipping", order.ID)
            continue
        }

        // Process order
        if err := db.FulfillOrder(ctx, order.ID); err != nil {
            return err
        }
    }
    return nil
}
```

---

## Partial Batch Failures

### BatchResult API

Handle failures per-message:

```go
import "github.com/transire/sdk-go"

func fulfillOrders(ctx context.Context, orders []Order, db *Database) error {
    // Create batch result tracker
    br := transire.NewBatchResult(len(orders))

    for i, order := range orders {
        // Check context cancellation
        if ctx.Err() != nil {
            // Mark remaining as failed
            for j := i; j < len(orders); j++ {
                br.Fail(j, ctx.Err())
            }
            break
        }

        // Process order
        if err := db.FulfillOrder(ctx, order.ID); err != nil {
            log.Printf("Order %s failed: %v", order.ID, err)
            br.Fail(i, err)  // Mark this message as failed
            continue          // Try next message
        }

        // Success - automatically tracked by BatchResult
    }

    log.Printf("Batch complete: %d succeeded, %d failed",
        br.SuccessCount(), br.FailureCount())

    // Return partial batch response
    return br.ToCloudPartialBatchResponse()
}
```

### BatchResult Methods

#### NewBatchResult

Create tracker:

```go
br := transire.NewBatchResult(batchSize int)
```

#### Fail

Mark message as failed:

```go
br.Fail(index int, err error)
```

#### SuccessCount

Get number of successful messages:

```go
count := br.SuccessCount()  // int
```

#### FailureCount

Get number of failed messages:

```go
count := br.FailureCount()  // int
```

#### ToCloudPartialBatchResponse

Convert to cloud provider response:

```go
return br.ToCloudPartialBatchResponse()  // error
```

**Cloud behavior:**
- AWS SQS: Returns `batchItemFailures` with failed message IDs
- Failed messages: Retry independently
- Successful messages: Deleted from queue

---

## Dead-Letter Queues

### Automatic DLQ

Transire creates DLQ automatically:

```yaml
# AWS Example
Queue: orders-api-dev-fulfill-orders
DLQ:   orders-api-dev-fulfill-orders-dlq

# Messages go to DLQ after:
# - max_receive_count retries exceeded
# - Type mismatch (wrong message type)
# - Handler not found
```

### Monitoring DLQ

Check DLQ for failed messages:

```bash
# AWS
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123/orders-api-dev-fulfill-orders-dlq \
  --attribute-names ApproximateNumberOfMessages

# Output
{
  "Attributes": {
    "ApproximateNumberOfMessages": "3"
  }
}
```

### Processing DLQ Messages

Create handler for DLQ:

```go
func main() {
    app := transire.New()

    // Normal queue
    app.RegisterQueue("fulfill-orders", fulfillOrders)

    // DLQ handler
    app.RegisterQueue("fulfill-orders-dlq", handleFailedOrders)

    app.Run()
}

func handleFailedOrders(ctx context.Context, orders []Order, logger *Logger) error {
    for _, order := range orders {
        logger.Error("Order failed after max retries", fmt.Errorf("order: %s", order.ID))

        // Notify ops team
        notifyOps(order)

        // Log for investigation
        logFailure(order)
    }

    return nil
}
```

### Replaying from DLQ

Move messages back to main queue:

```bash
# AWS: Redrive DLQ to main queue
aws sqs start-message-move-task \
  --source-arn arn:aws:sqs:us-east-1:123:orders-api-dev-fulfill-orders-dlq \
  --destination-arn arn:aws:sqs:us-east-1:123:orders-api-dev-fulfill-orders
```

---

## Configuration

### Queue Settings

Configure in `transire.yaml`:

```yaml
queues:
  # Batch configuration
  max_batch_size: 10              # Max messages per invocation
  batch_window_s: 5               # Wait 5s to collect batch

  # Visibility & retries
  visibility_timeout_s: 30        # Hide message while processing
  max_receive_count: 3            # Retries before DLQ

  # Message retention
  message_retention_s: 345600     # 4 days (AWS default)

  # DLQ configuration
  dlq_enabled: true               # Auto-create DLQ (default)
  dlq_max_receive_count: 1        # Messages in DLQ after 1 receive

  # Concurrency (local mode)
  workers: 1                      # Number of concurrent workers
```

### Per-Queue Configuration

Override settings per queue:

```yaml
queues:
  # Global defaults
  max_batch_size: 10
  visibility_timeout_s: 30

  # Per-queue overrides
  fulfill-orders:
    max_batch_size: 5
    visibility_timeout_s: 60      # Longer timeout for complex processing

  send-emails:
    max_batch_size: 25
    visibility_timeout_s: 10      # Quick processing
```

---

## Testing

### Unit Testing Handlers

```go
func TestFulfillOrders(t *testing.T) {
    ctx := context.Background()

    // Mock database
    mockDB := &MockDatabase{
        FulfillFunc: func(ctx context.Context, id string) error {
            if id == "fail" {
                return errors.New("fulfillment failed")
            }
            return nil
        },
    }

    // Test batch
    orders := []Order{
        {ID: "1", Product: "Widget A"},
        {ID: "fail", Product: "Widget B"},
        {ID: "2", Product: "Widget C"},
    }

    // Call handler
    err := fulfillOrders(ctx, orders, mockDB)

    // Assert BatchResult returned
    if err == nil {
        t.Fatal("Expected BatchResult error")
    }

    // Verify correct messages failed
    // (Would inspect BatchResult details in real implementation)
}
```

### Integration Testing with Testkit

```go
import "github.com/transire/sdk-go/testkit"

func TestQueueProcessing(t *testing.T) {
    tk := testkit.New(t)

    // Setup test database
    db := setupTestDB(t)
    defer db.Close()

    transire.Provide(func() *Database { return db })

    // Register queue
    tk.Queue("fulfill-orders", fulfillOrders)

    // Enqueue message
    order := Order{ID: "1", Product: "Widget", Status: "pending"}
    tk.Enqueue("fulfill-orders", order)

    // Wait for processing
    tk.DrainQueue("fulfill-orders")

    // Verify result
    processed, _ := db.GetOrder(context.Background(), "1")
    if processed.Status != "fulfilled" {
        t.Errorf("Expected fulfilled, got %s", processed.Status)
    }
}
```

### Testing Partial Failures

```go
func TestPartialBatchFailure(t *testing.T) {
    ctx := context.Background()

    mockDB := &MockDatabase{
        FulfillFunc: func(ctx context.Context, id string) error {
            if id == "2" {
                return errors.New("temporary failure")
            }
            return nil
        },
    }

    orders := []Order{
        {ID: "1", Product: "A"},
        {ID: "2", Product: "B"},  // Will fail
        {ID: "3", Product: "C"},
    }

    err := fulfillOrders(ctx, orders, mockDB)

    // Should return BatchResult
    if err == nil {
        t.Fatal("Expected error with BatchResult")
    }

    // Verify 2 succeeded, 1 failed
    if mockDB.FulfillCount != 3 {
        t.Errorf("Expected 3 attempts, got %d", mockDB.FulfillCount)
    }
}
```

---

## Common Patterns

### Pattern: Conditional Processing

```go
func processOrders(ctx context.Context, orders []Order, db *Database) error {
    br := transire.NewBatchResult(len(orders))

    for i, order := range orders {
        // Skip if already processed
        existing, _ := db.GetOrder(ctx, order.ID)
        if existing.Status == "fulfilled" {
            log.Printf("Order %s already processed", order.ID)
            continue
        }

        // Skip if cancelled
        if existing.Status == "cancelled" {
            log.Printf("Order %s was cancelled", order.ID)
            continue
        }

        // Process
        if err := db.FulfillOrder(ctx, order.ID); err != nil {
            br.Fail(i, err)
            continue
        }
    }

    return br.ToCloudPartialBatchResponse()
}
```

### Pattern: External API Calls

```go
func sendEmails(ctx context.Context, emails []Email, emailSvc *EmailService) error {
    br := transire.NewBatchResult(len(emails))

    for i, email := range emails {
        // Add timeout per email
        emailCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
        defer cancel()

        if err := emailSvc.Send(emailCtx, email); err != nil {
            log.Printf("Failed to send email to %s: %v", email.To, err)
            br.Fail(i, err)
            continue
        }

        log.Printf("Sent email to %s", email.To)
    }

    return br.ToCloudPartialBatchResponse()
}
```

### Pattern: Transactional Processing

```go
func processPayments(ctx context.Context, payments []Payment, db *Database) error {
    for _, payment := range payments {
        // Each payment in its own transaction
        tx, err := db.BeginTx(ctx, nil)
        if err != nil {
            return err
        }

        if err := processPayment(ctx, tx, payment); err != nil {
            tx.Rollback()
            return err
        }

        if err := tx.Commit(); err != nil {
            return err
        }
    }

    return nil
}
```

### Pattern: Deduplicate Messages

```go
type DeduplicationService struct {
    redis *redis.Client
}

func (d *DeduplicationService) IsProcessed(ctx context.Context, id string) bool {
    result, _ := d.redis.SetNX(ctx, "processed:"+id, "1", 24*time.Hour).Result()
    return !result // true if key already existed
}

func processOrders(ctx context.Context, orders []Order, dedup *DeduplicationService) error {
    br := transire.NewBatchResult(len(orders))

    for i, order := range orders {
        if dedup.IsProcessed(ctx, order.ID) {
            log.Printf("Order %s already processed (duplicate)", order.ID)
            continue
        }

        if err := fulfillOrder(ctx, order); err != nil {
            br.Fail(i, err)
            continue
        }
    }

    return br.ToCloudPartialBatchResponse()
}
```

---

## Performance Optimization

### 1. Tune Batch Size

```yaml
# Small batches - faster processing, more invocations
queues:
  max_batch_size: 1
  batch_window_s: 0

# Large batches - fewer invocations, better throughput
queues:
  max_batch_size: 100
  batch_window_s: 10
```

### 2. Parallel Processing

```go
func processOrders(ctx context.Context, orders []Order) error {
    br := transire.NewBatchResult(len(orders))

    // Process in parallel
    var wg sync.WaitGroup
    sem := make(chan struct{}, 10) // Limit concurrency

    for i, order := range orders {
        wg.Add(1)
        go func(idx int, o Order) {
            defer wg.Done()

            sem <- struct{}{}
            defer func() { <-sem }()

            if err := processOrder(ctx, o); err != nil {
                br.Fail(idx, err)
            }
        }(i, order)
    }

    wg.Wait()
    return br.ToCloudPartialBatchResponse()
}
```

### 3. Connection Pooling

```go
// Reuse HTTP client
var httpClient = &http.Client{
    Timeout: 30 * time.Second,
    Transport: &http.Transport{
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 10,
        IdleConnTimeout:     90 * time.Second,
    },
}

func callAPI(ctx context.Context, order Order) error {
    req, _ := http.NewRequestWithContext(ctx, "POST", apiURL, nil)
    resp, err := httpClient.Do(req)
    // ...
}
```

---

## Monitoring

### CloudWatch Metrics (AWS)

Key metrics to monitor:

- **ApproximateNumberOfMessages** - Queue depth
- **ApproximateNumberOfMessagesVisible** - Available messages
- **ApproximateNumberOfMessagesNotVisible** - In-flight messages
- **ApproximateAgeOfOldestMessage** - Oldest message age
- **NumberOfMessagesSent** - Enqueue rate
- **NumberOfMessagesDeleted** - Success rate
- **NumberOfMessagesReceived** - Processing rate

### Custom Metrics

```go
import "github.com/prometheus/client_golang/prometheus"

var (
    messagesProcessed = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "queue_messages_processed_total",
            Help: "Total messages processed",
        },
        []string{"queue", "status"},
    )

    processingDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "queue_processing_duration_seconds",
            Help:    "Message processing duration",
            Buckets: prometheus.ExponentialBuckets(0.001, 2, 10),
        },
        []string{"queue"},
    )
)

func processOrders(ctx context.Context, orders []Order) error {
    start := time.Now()
    defer func() {
        processingDuration.WithLabelValues("fulfill-orders").Observe(
            time.Since(start).Seconds(),
        )
    }()

    br := transire.NewBatchResult(len(orders))

    for i, order := range orders {
        if err := processOrder(ctx, order); err != nil {
            br.Fail(i, err)
            messagesProcessed.WithLabelValues("fulfill-orders", "failed").Inc()
            continue
        }
        messagesProcessed.WithLabelValues("fulfill-orders", "success").Inc()
    }

    return br.ToCloudPartialBatchResponse()
}
```

---

## Troubleshooting

### Messages Not Processing

**Check:**

1. **Is queue registered?**
   ```go
   app.RegisterQueue("fulfill-orders", handler)
   ```

2. **Are messages being enqueued?**
   ```bash
   aws sqs get-queue-attributes --queue-url $QUEUE_URL \
     --attribute-names ApproximateNumberOfMessages
   ```

3. **Check Lambda logs:**
   ```bash
   transire logs --env dev --handler queue
   ```

4. **Verify message type matches:**
   ```go
   // Enqueue: Order
   app.Enqueue(ctx, "queue", Order{})

   // Handler: []Order
   func handler(ctx context.Context, orders []Order) error
   ```

### Messages Going to DLQ

**Causes:**
- Handler returning errors
- Type mismatch
- Timeout exceeded
- Max retries reached

**Fix:**

1. **Check DLQ messages:**
   ```bash
   aws sqs receive-message --queue-url $DLQ_URL
   ```

2. **Review handler logs:**
   ```bash
   transire logs --env dev --handler queue --filter ERROR
   ```

3. **Increase timeout:**
   ```yaml
   deploy:
     timeout_s: 60  # Increase from 30s
   ```

4. **Fix type mismatch:**
   ```go
   // Ensure enqueue and handler types match
   type Order struct { ... }
   app.Enqueue(ctx, "queue", Order{})  // Order, not *Order
   func handler(ctx context.Context, orders []Order) error
   ```

### Slow Processing

**Solutions:**

1. **Increase batch size:**
   ```yaml
   queues:
     max_batch_size: 50
   ```

2. **Add parallel processing:**
   ```go
   // Use goroutines with semaphore
   ```

3. **Increase Lambda memory:**
   ```yaml
   deploy:
     memory_mb: 1024
   ```

4. **Optimize handler:**
   - Use batch database operations
   - Implement connection pooling
   - Cache frequently accessed data

---

## See Also

- [Queue Tutorial](../../learn/tutorials/03-queue-processing/) - Build queue handlers
- [HTTP API Reference](http-api/) - Enqueue from HTTP
- [Error Handling Guide](../../guides/patterns/error-handling/) - Error patterns
- [Testing Guide](../../guides/testing/) - Test queue handlers
- [AWS SQS Details](../../plugins/cloud/aws/queues/) - AWS-specific info

