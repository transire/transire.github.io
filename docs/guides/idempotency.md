---
title: "Idempotency Guide"
category: guides
subcategory: null
complexity: advanced
duration: null
prerequisites:
  - HTTP and queue handler experience
  - Database knowledge
mcp_use: reference
features_covered:
  - Idempotent operations
  - Retry safety
  - Deduplication strategies
code_blocks: true
last_updated: 2025-10-31
---

# Idempotency Guide

This guide covers patterns for implementing idempotent operations in Transire applications.

## What is Idempotency?

An idempotent operation produces the same result when executed multiple times with the same input. This is crucial for:

- Handling retries safely
- Ensuring exactly-once semantics
- Preventing duplicate processing
- Building reliable distributed systems

## HTTP Idempotency

### Idempotency Keys

Use idempotency keys for POST requests:

```go
type Order struct {
    ID              string
    IdempotencyKey  string
    UserID          string
    Amount          float64
    Status          string
    CreatedAt       time.Time
}

func CreateOrder(w http.ResponseWriter, r *http.Request) {
    idempotencyKey := r.Header.Get("Idempotency-Key")
    if idempotencyKey == "" {
        response.BadRequest(w, "Idempotency-Key header required")
        return
    }

    db := transire.MustGet[*sql.DB](r.Context())

    // Check if order with this key exists
    existing, err := getOrderByIdempotencyKey(r.Context(), db, idempotencyKey)
    if err == nil {
        // Already processed - return existing result
        response.OK(w, existing)
        return
    }

    // Parse request
    var req CreateOrderRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        response.BadRequest(w, "Invalid JSON")
        return
    }

    // Create new order with idempotency key
    order := &Order{
        ID:             generateID(),
        IdempotencyKey: idempotencyKey,
        UserID:         req.UserID,
        Amount:         req.Amount,
        Status:         "pending",
        CreatedAt:      time.Now(),
    }

    if err := insertOrder(r.Context(), db, order); err != nil {
        if isDuplicateKeyError(err) {
            // Race condition - another request created it
            existing, _ := getOrderByIdempotencyKey(r.Context(), db, idempotencyKey)
            response.OK(w, existing)
            return
        }
        response.InternalServerError(w, "Failed to create order")
        return
    }

    response.Created(w, order)
}
```

### Database Schema

Add unique constraint on idempotency key:

```sql
CREATE TABLE orders (
    id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_orders_idempotency ON orders(idempotency_key);
```

### Idempotency Key Generation

Client generates idempotency key:

```javascript
// Client-side example
const idempotencyKey = generateUUID(); // Or use existing request ID

fetch('/orders', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Idempotency-Key': idempotencyKey
    },
    body: JSON.stringify(orderData)
});
```

## Queue Idempotency

### Message Deduplication

Use message IDs for deduplication:

```go
type ProcessedMessage struct {
    MessageID   string
    ProcessedAt time.Time
}

func ProcessOrders(ctx context.Context, msgs []Order) error {
    db := transire.MustGet[*sql.DB](ctx)
    br := transire.NewBatchResult(len(msgs))

    for i, order := range msgs {
        // Check if already processed
        alreadyProcessed, err := wasMessageProcessed(ctx, db, order.MessageID)
        if err != nil {
            br.Fail(i, err)
            continue
        }

        if alreadyProcessed {
            log.Printf("Order %s already processed (message %s), skipping",
                order.ID, order.MessageID)
            continue
        }

        // Process order
        if err := processOrder(ctx, db, order); err != nil {
            br.Fail(i, err)
            continue
        }

        // Mark as processed
        if err := markMessageProcessed(ctx, db, order.MessageID); err != nil {
            // Order processed but tracking failed
            // This might cause reprocessing, but order logic should be idempotent
            log.Printf("Warning: failed to mark message %s as processed: %v",
                order.MessageID, err)
        }
    }

    return br.ToError()
}

func wasMessageProcessed(ctx context.Context, db *sql.DB, messageID string) (bool, error) {
    var exists bool
    err := db.QueryRowContext(ctx,
        "SELECT EXISTS(SELECT 1 FROM processed_messages WHERE message_id = $1)",
        messageID,
    ).Scan(&exists)
    return exists, err
}

func markMessageProcessed(ctx context.Context, db *sql.DB, messageID string) error {
    _, err := db.ExecContext(ctx,
        "INSERT INTO processed_messages (message_id, processed_at) VALUES ($1, $2)",
        messageID, time.Now(),
    )
    return err
}
```

### Database Schema

Track processed messages:

```sql
CREATE TABLE processed_messages (
    message_id TEXT PRIMARY KEY,
    processed_at TIMESTAMP NOT NULL
);

-- Optional: Add expiration for cleanup
CREATE INDEX idx_processed_messages_expiration ON processed_messages(processed_at);
```

### Cleanup Old Records

Prevent unbounded growth:

```go
func CleanupProcessedMessages(ctx context.Context) error {
    db := transire.MustGet[*sql.DB](ctx)

    // Delete records older than 7 days
    _, err := db.ExecContext(ctx,
        "DELETE FROM processed_messages WHERE processed_at < NOW() - INTERVAL '7 days'",
    )

    if err != nil {
        log.Printf("Failed to cleanup processed messages: %v", err)
        return err
    }

    log.Println("Processed messages cleanup completed")
    return nil
}

func main() {
    app := transire.New()

    // Run cleanup daily
    app.RegisterScheduled("@daily", CleanupProcessedMessages)

    app.Run()
}
```

## Idempotent Operations

### Database Upserts

Use upsert operations for idempotency:

```go
func UpdateUserProfile(ctx context.Context, db *sql.DB, profile *UserProfile) error {
    _, err := db.ExecContext(ctx, `
        INSERT INTO user_profiles (user_id, name, email, updated_at)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id) DO UPDATE SET
            name = EXCLUDED.name,
            email = EXCLUDED.email,
            updated_at = EXCLUDED.updated_at
    `, profile.UserID, profile.Name, profile.Email, time.Now())

    return err
}
```

### Conditional Updates

Use optimistic locking:

```go
type User struct {
    ID      string
    Version int
    Name    string
}

func UpdateUser(ctx context.Context, db *sql.DB, user *User) error {
    result, err := db.ExecContext(ctx, `
        UPDATE users
        SET name = $1, version = version + 1
        WHERE id = $2 AND version = $3
    `, user.Name, user.ID, user.Version)

    if err != nil {
        return err
    }

    rows, err := result.RowsAffected()
    if err != nil {
        return err
    }

    if rows == 0 {
        return ErrVersionMismatch
    }

    user.Version++
    return nil
}
```

### Financial Transactions

Ensure exactly-once processing for payments:

```go
type Transaction struct {
    ID              string
    IdempotencyKey  string
    UserID          string
    Amount          float64
    Status          string
    ProcessedAt     *time.Time
}

func ProcessPayment(ctx context.Context, req *PaymentRequest) (*Transaction, error) {
    db := transire.MustGet[*sql.DB](ctx)

    // Start transaction
    tx, err := db.BeginTx(ctx, nil)
    if err != nil {
        return nil, err
    }
    defer tx.Rollback()

    // Check for existing transaction
    var existing Transaction
    err = tx.QueryRowContext(ctx, `
        SELECT id, idempotency_key, user_id, amount, status, processed_at
        FROM transactions
        WHERE idempotency_key = $1
        FOR UPDATE  -- Lock row
    `, req.IdempotencyKey).Scan(
        &existing.ID, &existing.IdempotencyKey,
        &existing.UserID, &existing.Amount,
        &existing.Status, &existing.ProcessedAt,
    )

    if err == nil {
        // Already processed
        if existing.Status == "completed" {
            return &existing, nil
        }
        // Still processing or failed - return error
        return nil, fmt.Errorf("transaction already exists with status: %s", existing.Status)
    }

    if err != sql.ErrNoRows {
        return nil, err
    }

    // Create new transaction
    txn := &Transaction{
        ID:             generateID(),
        IdempotencyKey: req.IdempotencyKey,
        UserID:         req.UserID,
        Amount:         req.Amount,
        Status:         "pending",
    }

    _, err = tx.ExecContext(ctx, `
        INSERT INTO transactions (id, idempotency_key, user_id, amount, status)
        VALUES ($1, $2, $3, $4, $5)
    `, txn.ID, txn.IdempotencyKey, txn.UserID, txn.Amount, txn.Status)

    if err != nil {
        return nil, err
    }

    // Process payment with external service
    if err := chargeCard(ctx, req.Amount, req.CardToken); err != nil {
        txn.Status = "failed"
        tx.ExecContext(ctx, "UPDATE transactions SET status = $1 WHERE id = $2", txn.Status, txn.ID)
        tx.Commit()
        return nil, fmt.Errorf("payment failed: %w", err)
    }

    // Mark as completed
    now := time.Now()
    txn.Status = "completed"
    txn.ProcessedAt = &now

    _, err = tx.ExecContext(ctx, `
        UPDATE transactions
        SET status = $1, processed_at = $2
        WHERE id = $3
    `, txn.Status, txn.ProcessedAt, txn.ID)

    if err != nil {
        return nil, err
    }

    if err := tx.Commit(); err != nil {
        return nil, err
    }

    return txn, nil
}
```

## Scheduled Task Idempotency

### Prevent Overlapping Executions

Use distributed locks:

```go
func DailyReport(ctx context.Context) error {
    db := transire.MustGet[*sql.DB](ctx)

    // Acquire lock
    locked, err := acquireLock(ctx, db, "daily_report", 10*time.Minute)
    if err != nil {
        return err
    }

    if !locked {
        log.Println("Daily report already running")
        return nil
    }

    defer releaseLock(ctx, db, "daily_report")

    // Generate report
    if err := generateReport(ctx); err != nil {
        return err
    }

    log.Println("Daily report completed")
    return nil
}

func acquireLock(ctx context.Context, db *sql.DB, lockName string, ttl time.Duration) (bool, error) {
    result, err := db.ExecContext(ctx, `
        INSERT INTO distributed_locks (lock_name, acquired_at, expires_at)
        VALUES ($1, NOW(), NOW() + $2)
        ON CONFLICT (lock_name) DO NOTHING
    `, lockName, ttl)

    if err != nil {
        return false, err
    }

    rows, err := result.RowsAffected()
    return rows > 0, err
}

func releaseLock(ctx context.Context, db *sql.DB, lockName string) error {
    _, err := db.ExecContext(ctx, "DELETE FROM distributed_locks WHERE lock_name = $1", lockName)
    return err
}
```

## Best Practices

1. **Generate idempotency keys client-side** - Client controls retry behavior
2. **Store idempotency keys with business entities** - Not in separate table
3. **Use unique constraints** - Let database enforce idempotency
4. **Return same response** - If duplicate detected, return original result
5. **Set expiration** - Clean up old idempotency records
6. **Use transactions** - Ensure atomicity of operations
7. **Handle race conditions** - Use locks or MVCC
8. **Log deduplication** - Track when duplicates are detected
9. **Test retry scenarios** - Simulate failures and retries
10. **Document retention policy** - How long to keep deduplication data

## Testing Idempotency

```go
func TestIdempotentOrderCreation(t *testing.T) {
    tk := testkit.New(t)

    // Setup
    idempotencyKey := "test-key-123"

    // First request
    resp1 := tk.POST("/orders", CreateOrderRequest{
        UserID: "user1",
        Amount: 100.0,
    }, map[string]string{
        "Idempotency-Key": idempotencyKey,
    })

    tk.AssertStatus(resp1, 201)

    var order1 Order
    json.Unmarshal(resp1.Body, &order1)

    // Retry with same key
    resp2 := tk.POST("/orders", CreateOrderRequest{
        UserID: "user1",
        Amount: 100.0,
    }, map[string]string{
        "Idempotency-Key": idempotencyKey,
    })

    tk.AssertStatus(resp2, 200)

    var order2 Order
    json.Unmarshal(resp2.Body, &order2)

    // Should return same order
    if order1.ID != order2.ID {
        t.Errorf("Expected same order ID, got %s and %s", order1.ID, order2.ID)
    }
}
```

## See Also

- [Queue Handlers](/docs/sdk/queue.md)
- [Error Handling](/docs/guides/error-handling.md)
- [Testing Guide](/docs/sdk/testkit.md)
- [AWS Queues](/docs/cloud/aws/queues.md)
