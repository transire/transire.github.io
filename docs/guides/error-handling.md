---
title: "Error Handling Guide"
category: guides
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - Basic Go error handling
  - HTTP handler experience
mcp_use: reference
features_covered:
  - Error handling patterns
  - HTTP error responses
  - Queue error handling
  - Retry strategies
code_blocks: true
last_updated: 2025-10-31
---

# Error Handling Guide

This guide covers error handling patterns for Transire applications.

## HTTP Error Handling

### Basic Error Responses

Use the response package for standard HTTP errors:

```go
import "github.com/transire/transire-sdk-go/response"

func GetUser(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")

    user, err := db.GetUser(r.Context(), id)
    if err != nil {
        // Handle different error types
        switch {
        case errors.Is(err, ErrNotFound):
            response.NotFound(w, "User not found")
        case errors.Is(err, ErrUnauthorized):
            response.Text(w, http.StatusUnauthorized, "Unauthorized")
        default:
            log.Printf("Error fetching user %s: %v", id, err)
            response.InternalServerError(w, "Internal server error")
        }
        return
    }

    response.OK(w, user)
}
```

### Custom Error Types

Define domain-specific errors:

```go
type AppError struct {
    Code    string
    Message string
    Status  int
    Err     error
}

func (e *AppError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("%s: %v", e.Message, e.Err)
    }
    return e.Message
}

func (e *AppError) Unwrap() error {
    return e.Err
}

// Error constructors
func NewNotFoundError(message string) *AppError {
    return &AppError{
        Code:    "NOT_FOUND",
        Message: message,
        Status:  http.StatusNotFound,
    }
}

func NewValidationError(message string) *AppError {
    return &AppError{
        Code:    "VALIDATION_ERROR",
        Message: message,
        Status:  http.StatusBadRequest,
    }
}
```

### Centralized Error Handling

Use middleware for consistent error handling:

```go
func ErrorHandlerMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                log.Printf("Panic: %v\n%s", err, debug.Stack())
                response.InternalServerError(w, "Internal server error")
            }
        }()

        next.ServeHTTP(w, r)
    })
}

func main() {
    app := transire.New()
    app.Use(ErrorHandlerMiddleware)
    app.Run()
}
```

### Validation Errors

Handle input validation errors:

```go
type ValidationErrors struct {
    Errors map[string]string
}

func ValidateCreateUser(user *CreateUserRequest) *ValidationErrors {
    errs := &ValidationErrors{Errors: make(map[string]string)}

    if user.Email == "" {
        errs.Errors["email"] = "Email is required"
    }
    if !isValidEmail(user.Email) {
        errs.Errors["email"] = "Invalid email format"
    }
    if len(user.Password) < 8 {
        errs.Errors["password"] = "Password must be at least 8 characters"
    }

    if len(errs.Errors) > 0 {
        return errs
    }
    return nil
}

func CreateUser(w http.ResponseWriter, r *http.Request) {
    var req CreateUserRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        response.BadRequest(w, "Invalid JSON")
        return
    }

    if errs := ValidateCreateUser(&req); errs != nil {
        response.JSON(w, http.StatusUnprocessableEntity, errs)
        return
    }

    // Proceed with creation
}
```

## Queue Error Handling

### Partial Batch Failures

Handle failures for individual messages in a batch:

```go
func ProcessOrders(ctx context.Context, msgs []Order) error {
    br := transire.NewBatchResult(len(msgs))

    for i, order := range msgs {
        if err := processOrder(ctx, order); err != nil {
            log.Printf("Failed to process order %s: %v", order.ID, err)
            br.Fail(i, err)
        }
    }

    // Failed messages will be retried
    return br.ToError()
}
```

### Retry Logic

Implement exponential backoff:

```go
func ProcessOrder(ctx context.Context, msgs []Order) error {
    br := transire.NewBatchResult(len(msgs))

    for i, order := range msgs {
        err := retryWithBackoff(ctx, func() error {
            return processOrder(ctx, order)
        })

        if err != nil {
            br.Fail(i, err)
        }
    }

    return br.ToError()
}

func retryWithBackoff(ctx context.Context, fn func() error) error {
    maxRetries := 3
    backoff := time.Second

    for attempt := 0; attempt < maxRetries; attempt++ {
        if err := fn(); err != nil {
            if attempt == maxRetries-1 {
                return err
            }

            select {
            case <-time.After(backoff):
                backoff *= 2
            case <-ctx.Done():
                return ctx.Err()
            }
            continue
        }
        return nil
    }

    return fmt.Errorf("max retries exceeded")
}
```

### Dead Letter Queue Handling

Messages that fail repeatedly go to DLQ:

```go
// Monitor DLQ
func MonitorDLQ(ctx context.Context, msgs []FailedOrder) error {
    for _, order := range msgs {
        // Alert on critical failures
        if order.Retries > 5 {
            alertOps(order)
        }

        // Log for investigation
        log.Printf("Order %s failed %d times: %v",
            order.ID, order.Retries, order.LastError)
    }
    return nil
}

func main() {
    app := transire.New()

    // Register DLQ handler
    app.RegisterQueue("orders-dlq", MonitorDLQ)

    app.Run()
}
```

## Context Handling

### Timeout Handling

Respect context deadlines:

```go
func LongRunningHandler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()

    result := make(chan Result)
    go func() {
        // Long-running operation
        data, err := fetchData(ctx)
        result <- Result{Data: data, Err: err}
    }()

    select {
    case res := <-result:
        if res.Err != nil {
            if errors.Is(res.Err, context.DeadlineExceeded) {
                response.Text(w, http.StatusRequestTimeout, "Request timeout")
                return
            }
            response.InternalServerError(w, "Failed to fetch data")
            return
        }
        response.OK(w, res.Data)

    case <-ctx.Done():
        // Request was cancelled
        response.Text(w, 499, "Client closed request")
    }
}
```

### Context Cancellation

Check for cancellation in loops:

```go
func ProcessBatch(ctx context.Context, items []Item) error {
    for i, item := range items {
        // Check for cancellation
        select {
        case <-ctx.Done():
            return fmt.Errorf("processing cancelled after %d items: %w",
                i, ctx.Err())
        default:
        }

        if err := processItem(ctx, item); err != nil {
            return fmt.Errorf("failed to process item %d: %w", i, err)
        }
    }
    return nil
}
```

## Scheduled Handler Errors

### Error Recovery

Handle errors in scheduled tasks:

```go
func DailyCleanup(ctx context.Context) error {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("Panic in daily cleanup: %v\n%s", r, debug.Stack())
            // Alert ops team
            sendAlert("Daily cleanup panicked")
        }
    }()

    if err := cleanupOldData(ctx); err != nil {
        log.Printf("Cleanup failed: %v", err)
        // Alert but don't block future runs
        sendAlert(fmt.Sprintf("Cleanup error: %v", err))
        return err
    }

    log.Println("Cleanup completed successfully")
    return nil
}
```

## Error Logging

### Structured Logging

Log errors with context:

```go
type Logger struct {
    TraceID   string
    UserID    string
    RequestID string
}

func (l *Logger) Error(msg string, err error, fields map[string]interface{}) {
    entry := map[string]interface{}{
        "level":      "error",
        "message":    msg,
        "error":      err.Error(),
        "trace_id":   l.TraceID,
        "user_id":    l.UserID,
        "request_id": l.RequestID,
        "timestamp":  time.Now().UTC(),
    }

    for k, v := range fields {
        entry[k] = v
    }

    json.NewEncoder(os.Stdout).Encode(entry)
}

func Handler(w http.ResponseWriter, r *http.Request) {
    logger := transire.MustGet[*Logger](r.Context())

    user, err := db.GetUser(r.Context(), id)
    if err != nil {
        logger.Error("Failed to fetch user", err, map[string]interface{}{
            "user_id": id,
            "source":  "database",
        })
        response.InternalServerError(w, "Internal server error")
        return
    }
}
```

## Best Practices

1. **Return errors, don't panic** - Reserve panic for truly exceptional situations
2. **Wrap errors with context** - Use `fmt.Errorf("context: %w", err)`
3. **Log before responding** - Log details before sending generic error to client
4. **Use custom error types** - For errors that need special handling
5. **Handle partial failures** - In batch operations, track individual failures
6. **Respect context cancellation** - Check `ctx.Done()` in long operations
7. **Don't leak internal details** - Return generic messages to clients
8. **Monitor DLQs** - Set up alerts for messages in dead letter queues
9. **Implement retries with backoff** - For transient failures
10. **Test error paths** - Write tests for error scenarios

## Testing Error Handling

```go
func TestErrorHandling(t *testing.T) {
    tk := testkit.New(t)

    // Mock service that returns error
    tk.App.Provide(func() UserService {
        return &MockUserService{
            GetUserFunc: func(ctx context.Context, id string) (*User, error) {
                return nil, ErrNotFound
            },
        }
    })

    resp := tk.GET("/users/123")

    tk.AssertStatus(resp, 404)
    tk.AssertJSONContains(resp, `{"error": "User not found"}`)
}
```

## See Also

- [HTTP Handlers](/sdk/http.md)
- [Queue Handlers](/sdk/queue.md)
- [Testing Guide](/sdk/testkit.md)
- [DI Patterns](/guides/di-patterns.md)
- [Error Codes Reference](/reference/error-codes.md)
