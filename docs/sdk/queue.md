---
title: "Queue Handlers"
category: sdk
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - Go 1.22+
  - Understanding of HTTP handlers
  - Basic knowledge of message queues
mcp_use: reference
mcp_operations:
  - add_queue_handler
  - extract_queue_patterns
  - enqueue_messages
features_covered:
  - Queue handler registration
  - Message enqueuing
  - Batch processing
  - Partial batch failures
  - Type safety
code_blocks: true
last_updated: 2025-10-30
---

# Queue Handlers

## Overview

Queue handlers enable asynchronous, decoupled message processing in Transire. They're perfect for:

- **Background processing** - Long-running tasks that shouldn't block HTTP responses
- **Event-driven workflows** - React to events from other parts of your system
- **Reliability** - Built-in retries and dead-letter queues
- **Scalability** - Process messages in parallel with automatic scaling

**Key features:**
- Type-safe message handling with compile-time validation
- Batch processing for efficiency
- Granular partial failure handling
- Automatic retries with exponential backoff
- Dead-letter queues for failed messages

## Handler Signature

Queue handlers process batches of messages:

```go
func(ctx context.Context, msgs []T) error
```

Where `T` is your message type (any Go struct).

**Important:** Queue handlers ALWAYS receive a slice, even if batch size is 1. A single message will be passed as a slice of length 1.

## Registering Queue Handlers

Register queue handlers using `app.RegisterQueue`:

```go
package main

import (
    "context"
    "log"
    "github.com/transire/sdk-go"
)

type OrderCreated struct {
    OrderID string  `json:"order_id"`
    UserID  string  `json:"user_id"`
    Total   float64 `json:"total"`
}

func main() {
    app := transire.New()

    // Register queue handler
    err := app.RegisterQueue("OrderCreated", processOrderCreated)
    if err != nil {
        log.Fatal("Failed to register queue:", err)
    }

    app.Run()
}

// Queue handler - processes batches of OrderCreated messages
func processOrderCreated(ctx context.Context, msgs []OrderCreated) error {
    for _, msg := range msgs {
        log.Printf("Processing order %s for user %s", msg.OrderID, msg.UserID)

        // Your business logic here
        if err := sendOrderConfirmation(ctx, msg); err != nil {
            log.Printf("Failed to send confirmation for order %s: %v", msg.OrderID, err)
            return err  // Will retry entire batch
        }
    }

    return nil
}
```

### Queue Keys

The first argument to `RegisterQueue` is the **queue key** - a logical name for your queue:

- Use PascalCase: `"OrderCreated"`, `"PaymentProcessed"`
- Keys are unique per application
- Physical queue names are generated as `${service}-${env}-${normalized(key)}`

## Enqueuing Messages

Enqueue messages from HTTP handlers or other code using `app.Enqueue`:

```go
import "github.com/transire/sdk-go"

func createOrder(w http.ResponseWriter, r *http.Request) {
    // Create order in database
    order, err := db.CreateOrder(r.Context(), ...)
    if err != nil {
        response.InternalServerError(w, "Failed to create order")
        return
    }

    // Enqueue message for async processing
    msg := OrderCreated{
        OrderID: order.ID,
        UserID:  order.UserID,
        Total:   order.Total,
    }

    if err := app.Enqueue(r.Context(), "OrderCreated", msg); err != nil {
        log.Printf("Warning: Failed to enqueue order created event: %v", err)
        // Order is created, but notification may not be sent
        // Consider your error handling strategy here
    }

    response.Created(w, order)
}
```

### Batch Enqueuing

For efficiency, you can enqueue multiple messages at once:

```go
func processBulkOrders(w http.ResponseWriter, r *http.Request) {
    // Create multiple orders
    orders, err := db.CreateBulkOrders(r.Context(), ...)
    if err != nil {
        response.InternalServerError(w, "Failed to create orders")
        return
    }

    // Build batch of messages
    var msgs []interface{}
    for _, order := range orders {
        msgs = append(msgs, OrderCreated{
            OrderID: order.ID,
            UserID:  order.UserID,
            Total:   order.Total,
        })
    }

    // Enqueue as batch
    if err := app.EnqueueBatch(r.Context(), "OrderCreated", msgs); err != nil {
        log.Printf("Warning: Failed to enqueue bulk order events: %v", err)
    }

    response.OK(w, orders)
}
```

## Type Safety

Transire ensures type safety for queue messages:

1. **Build-time validation:** `transire gen` extracts the message type `T` from your handler signature
2. **Runtime validation:** Each message includes a `__type` field (e.g., `"github.com/acme/orders.OrderCreated"`)
3. **Automatic type checking:** Messages with wrong types are moved to DLQ with logged errors

**This prevents:**
- Enqueuing wrong message types
- Schema evolution issues (old messages in queue with different structure)
- Silent failures from type mismatches

## Batch Processing

Queue handlers always process messages in batches for efficiency:

```go
func processPayments(ctx context.Context, msgs []PaymentRequest) error {
    log.Printf("Processing batch of %d payments", len(msgs))

    // Process batch efficiently
    results, err := paymentGateway.ProcessBatch(ctx, msgs)
    if err != nil {
        return err  // Retry entire batch
    }

    // Handle individual results
    for i, result := range results {
        if result.Success {
            log.Printf("Payment %s succeeded", msgs[i].PaymentID)
        } else {
            log.Printf("Payment %s failed: %s", msgs[i].PaymentID, result.Error)
        }
    }

    return nil
}
```

### Configuring Batch Size

Configure batch size in `transire.yaml`:

```yaml
queues:
  max_batch_size: 10      # Maximum messages per batch
  batch_window_s: 5       # Wait up to 5 seconds to fill batch
  visibility_timeout_s: 30 # Time before message visible again
  max_receive_count: 3    # Retries before moving to DLQ
```

## Error Handling and Retries

Queue handlers use a simple error-based pattern. The Transire runtime automatically handles retries and dead-letter queue routing based on your handler's return value.

### Recommended Pattern: Fail Fast (Recommended)

Return an error if any message fails processing:

```go
func handler(ctx context.Context, msgs []Order) error {
    for _, msg := range msgs {
        if err := processOrder(ctx, msg); err != nil {
            // Log the error
            log.Printf("Failed to process order %s: %v", msg.OrderID, err)
            // Return error - runtime will retry the entire batch
            return err
        }
    }

    // All messages processed successfully
    return nil
}
```

**How it works:**
- If you return `nil`: All messages are acknowledged and removed from the queue
- If you return an `error`: The entire batch is retried according to your retry configuration
- After max retries: Failed messages are automatically moved to the dead-letter queue

**Pros:**
- Simple and explicit
- No complex batch result tracking
- Framework handles all retry logic
- Ensures atomicity within batches

### Alternative: Best Effort Processing

Process all messages and log failures without failing the batch:

```go
func handler(ctx context.Context, msgs []Order) error {
    for _, msg := range msgs {
        if err := processOrder(ctx, msg); err != nil {
            // Log but continue - this message is lost
            log.Printf("ERROR: Failed to process order %s: %v", msg.OrderID, err)
            continue
        }
    }

    // Return nil even if some messages failed
    // All messages are acknowledged and removed
    return nil
}
```

**Use when:**
- Messages are completely independent
- Failures are rare and acceptable
- You have alternative error tracking (monitoring, DLQ analysis)

**Warning:** Failed messages are permanently acknowledged and removed from the queue. Only use this pattern if you have robust error monitoring in place.

## Error Handling

### Retries

Failed messages are automatically retried with exponential backoff:

1. Message fails processing
2. Returns to queue after `visibility_timeout`
3. Retried up to `max_receive_count` times
4. Moved to DLQ after max retries

### Dead-Letter Queues (DLQ)

Messages that fail after all retries are moved to a DLQ:

- DLQ name: `${queue}-dlq`
- Messages preserved for inspection
- Manual reprocessing or analysis

**Monitoring DLQs:** Always monitor DLQ depth in production. Messages in DLQ indicate issues requiring attention.

### Context Cancellation

Always respect `ctx.Done()` for graceful shutdown:

```go
func processLongRunning(ctx context.Context, msgs []Task) error {
    for i, msg := range msgs {
        // Check for cancellation
        select {
        case <-ctx.Done():
            // Return error to retry remaining messages
            return ctx.Err()
        default:
        }

        if err := processTask(ctx, msg); err != nil {
            // Log error but continue processing
            log.Printf("Failed to process task %d: %v", i, err)
            continue
        }
    }

    return nil
}
```

## Complete Example

Here's a complete example of an order processing system:

```go
package main

import (
    "context"
    "encoding/json"
    "log"
    "net/http"
    "github.com/transire/sdk-go"
    "github.com/transire/sdk-go/response"
)

// Message types
type OrderCreated struct {
    OrderID   string  `json:"order_id"`
    UserID    string  `json:"user_id"`
    Total     float64 `json:"total"`
    Items     []Item  `json:"items"`
}

type Item struct {
    ProductID string  `json:"product_id"`
    Quantity  int     `json:"quantity"`
    Price     float64 `json:"price"`
}

type PaymentCompleted struct {
    OrderID   string `json:"order_id"`
    PaymentID string `json:"payment_id"`
    Status    string `json:"status"`
}

func main() {
    app := transire.New()

    // HTTP endpoints
    app.POST("/orders", createOrder)

    // Queue handlers
    app.RegisterQueue("OrderCreated", processOrderCreated)
    app.RegisterQueue("PaymentCompleted", processPaymentCompleted)

    app.Run()
}

// HTTP handler - creates order and enqueues for processing
func createOrder(w http.ResponseWriter, r *http.Request) {
    var req struct {
        UserID string  `json:"user_id"`
        Items  []Item  `json:"items"`
    }

    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        response.BadRequest(w, "Invalid JSON")
        return
    }

    // Validate
    if req.UserID == "" {
        response.BadRequest(w, "user_id is required")
        return
    }

    // Create order in database
    order, err := db.CreateOrder(r.Context(), req.UserID, req.Items)
    if err != nil {
        response.InternalServerError(w, "Failed to create order")
        return
    }

    // Enqueue for async processing
    msg := OrderCreated{
        OrderID: order.ID,
        UserID:  order.UserID,
        Total:   order.Total,
        Items:   order.Items,
    }

    if err := app.Enqueue(r.Context(), "OrderCreated", msg); err != nil {
        log.Printf("ERROR: Failed to enqueue order %s: %v", order.ID, err)
        // Consider your strategy: rollback order? Mark as pending? Alert?
    }

    response.Created(w, order)
}

// Queue handler - processes order creation
func processOrderCreated(ctx context.Context, msgs []OrderCreated) error {
    for i, msg := range msgs {
        log.Printf("Processing order %s", msg.OrderID)

        // Check inventory
        if err := reserveInventory(ctx, msg.Items); err != nil {
            log.Printf("Failed to reserve inventory for order %s: %v", msg.OrderID, err)
            continue
        }

        // Send to payment processing
        paymentReq := PaymentRequest{
            OrderID: msg.OrderID,
            UserID:  msg.UserID,
            Amount:  msg.Total,
        }

        if err := initiatePayment(ctx, paymentReq); err != nil {
            // Rollback inventory
            releaseInventory(ctx, msg.Items)
            log.Printf("Failed to initiate payment for order %s: %v", msg.OrderID, err)
            continue
        }

        log.Printf("Successfully processed order %s", msg.OrderID)
    }

    return nil
}

// Queue handler - processes payment completion
func processPaymentCompleted(ctx context.Context, msgs []PaymentCompleted) error {
    for i, msg := range msgs {
        log.Printf("Processing payment %s for order %s", msg.PaymentID, msg.OrderID)

        if msg.Status == "succeeded" {
            // Update order status
            if err := db.UpdateOrderStatus(ctx, msg.OrderID, "paid"); err != nil {
                log.Printf("Failed to update order %s: %v", msg.OrderID, err)
                continue
            }

            // Send confirmation email
            if err := sendConfirmationEmail(ctx, msg.OrderID); err != nil {
                // Log but don't fail - email is best-effort
                log.Printf("Warning: Failed to send confirmation for order %s: %v", msg.OrderID, err)
            }
        } else {
            // Payment failed - cancel order
            if err := cancelOrder(ctx, msg.OrderID); err != nil {
                log.Printf("Failed to cancel order %s: %v", msg.OrderID, err)
                continue
            }

            // Send failure notification
            sendPaymentFailureEmail(ctx, msg.OrderID)
        }

        log.Printf("Successfully processed payment for order %s", msg.OrderID)
    }

    return nil
}
```

## Local vs Cloud

Queue behavior differs between local development and cloud deployment:

### Local Development

When running `transire run`, queues are emulated in-memory:

- **In-memory queue** - Messages stored in process memory
- **Configurable workers** - Control concurrency (default: 1 per queue)
- **Simulated retries** - Retry logic mimics cloud behavior
- **Logged failures** - DLQ events logged to console (not persisted)

```bash
# Start local development server
transire run
```

### Cloud Deployment

When deployed, queues use your cloud provider's native queue service:

- **Persistent queues** - Messages survive restarts
- **Auto-scaling** - Handles thousands of concurrent messages
- **Physical DLQ** - Failed messages stored for inspection
- **Exponential backoff** - Configurable retry with increasing delays

See your cloud provider's documentation for specific implementation details.

## Testing

Test queue handlers using the testkit:

```go
package main

import (
    "context"
    "testing"
    "github.com/transire/sdk-go/testkit"
)

func TestProcessOrderCreated(t *testing.T) {
    // Create test messages
    msgs := []OrderCreated{
        {OrderID: "order-1", UserID: "user-1", Total: 99.99},
        {OrderID: "order-2", UserID: "user-2", Total: 149.99},
    }

    // Call handler
    err := processOrderCreated(context.Background(), msgs)
    if err != nil {
        t.Fatalf("Handler failed: %v", err)
    }

    // Verify results
    // ... check database, mock calls, etc.
}

func TestQueueIntegration(t *testing.T) {
    app := testkit.App()
    app.RegisterQueue("OrderCreated", processOrderCreated)

    // Start test server
    server := app.Start(t)
    defer server.Stop()

    // Enqueue message
    msg := OrderCreated{OrderID: "test-1", UserID: "user-1", Total: 99.99}
    server.Enqueue("OrderCreated", msg)

    // Wait for processing
    server.DrainQueue("OrderCreated")

    // Verify results
    // ...
}
```

## Best Practices

### Idempotency

Always design queue handlers to be idempotent:

```go
func processPayment(ctx context.Context, msgs []PaymentRequest) error {
    

    for i, msg := range msgs {
        // Check if already processed (idempotency check)
        if exists, _ := db.PaymentExists(ctx, msg.PaymentID); exists {
            log.Printf("Payment %s already processed, skipping", msg.PaymentID)
            continue  // Not a failure, skip
        }

        // Process payment
        if err := processPayment(ctx, msg); err != nil {
            
        }
    }

    return nil
}
```

### Message Size

Keep messages small for optimal performance:

- **Recommended:** < 10KB
- **Maximum:** Check your cloud provider's limits (typically 256KB)
- Store large data externally (object storage, database), pass references only

```go
// ❌ BAD: Large payload in message
type OrderCreated struct {
    OrderID       string
    FullOrderData Order  // Could be many KB
    UserProfile   User   // Could be many KB
    ProductImages []byte // Large binary data
}

// ✅ GOOD: Reference to data
type OrderCreated struct {
    OrderID string  // Fetch full data from database/storage
    UserID  string  // Fetch user profile separately if needed
}
```

### Error Logging

Always log detailed errors:

```go
func handler(ctx context.Context, msgs []T) error {
    

    for i, msg := range msgs {
        if err := process(ctx, msg); err != nil {
            // Log with context
            log.Printf("ERROR: Failed to process message %d: %+v, error: %v",
                i, msg, err)
            
        }
    }

    return nil
}
```

### Monitoring

Monitor queue metrics in production:

- **Queue depth** - Messages waiting to be processed
- **DLQ depth** - Failed messages requiring attention
- **Processing time** - Handler execution duration
- **Failure rate** - Percentage of failed messages

## See Also

- [HTTP Handlers](/docs/sdk/http.md) - Enqueuing from HTTP endpoints
- [Scheduled Jobs](/docs/sdk/schedule.md) - Time-based execution
- [Dependency Injection](/docs/sdk/di.md) - Injecting services into handlers
- [Testing](/docs/sdk/testkit.md) - Testing queue handlers
- [Error Handling](/docs/sdk/errors.md) - Error handling patterns
- [Configuration Reference](/docs/reference/config-schema.md) - Queue configuration options
