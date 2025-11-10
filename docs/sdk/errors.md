---
title: "Error Handling"
category: sdk
complexity: intermediate
duration: 15 minutes
prerequisites:
  - Basic understanding of HTTP handlers
  - Familiarity with Go error handling
mcp_use: reference
mcp_operations:
  - handle_errors
  - create_error_responses
features_covered:
  - HTTP errors
  - Queue error handling
  - Panic recovery
  - Error responses
code_blocks: true
last_updated: 2025-10-30
---

# Error Handling

## Overview

Transire provides consistent error handling across HTTP handlers, queue handlers, and scheduled jobs. This guide covers:

- **HTTP errors** - Return appropriate status codes and messages
- **Queue errors** - Retry failed messages, handle permanent failures
- **Panic recovery** - Catch panics and return proper errors
- **Error responses** - Standardized JSON error format
- **Logging** - Structured error logging

## HTTP Error Handling

### Basic Error Responses

Use standard `http.Error`:

```go
func getUser(w http.ResponseWriter, r *http.Request) {
    userID := transire.URLParam(r, "id")

    user, err := db.GetUser(r.Context(), userID)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            http.Error(w, "User not found", http.StatusNotFound)
            return
        }
        http.Error(w, "Internal server error", http.StatusInternalServerError)
        return
    }

    json.NewEncoder(w).Encode(user)
}
```

### Structured Error Responses

Return JSON errors for better client handling:

```go
import "github.com/transire/sdk-go/response"

type ErrorResponse struct {
    Error   string `json:"error"`
    Code    string `json:"code,omitempty"`
    Details string `json:"details,omitempty"`
}

func getUser(w http.ResponseWriter, r *http.Request) {
    userID := transire.URLParam(r, "id")

    user, err := db.GetUser(r.Context(), userID)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            response.JSON(w, http.StatusNotFound, ErrorResponse{
                Error:   "User not found",
                Code:    "USER_NOT_FOUND",
                Details: fmt.Sprintf("No user with ID: %s", userID),
            })
            return
        }

        log.Printf("Database error: %v", err)
        response.JSON(w, http.StatusInternalServerError, ErrorResponse{
            Error: "Internal server error",
            Code:  "INTERNAL_ERROR",
        })
        return
    }

    response.JSON(w, http.StatusOK, user)
}
```

### Error Helper Functions

Create reusable error handlers:

```go
func errorJSON(w http.ResponseWriter, status int, code string, message string) {
    response.JSON(w, status, ErrorResponse{
        Error: message,
        Code:  code,
    })
}

func getUser(w http.ResponseWriter, r *http.Request) {
    userID := transire.URLParam(r, "id")

    user, err := db.GetUser(r.Context(), userID)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            errorJSON(w, http.StatusNotFound, "USER_NOT_FOUND", "User not found")
            return
        }
        log.Printf("Error: %v", err)
        errorJSON(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Internal server error")
        return
    }

    response.JSON(w, http.StatusOK, user)
}
```

### Validation Errors

Return detailed validation failures:

```go
type ValidationError struct {
    Field   string `json:"field"`
    Message string `json:"message"`
}

type ValidationErrorResponse struct {
    Error  string            `json:"error"`
    Code   string            `json:"code"`
    Fields []ValidationError `json:"fields"`
}

func createUser(w http.ResponseWriter, r *http.Request) {
    var input CreateUserInput
    if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
        errorJSON(w, http.StatusBadRequest, "INVALID_JSON", "Invalid JSON")
        return
    }

    // Validate input
    validationErrors := validateUser(input)
    if len(validationErrors) > 0 {
        response.JSON(w, http.StatusBadRequest, ValidationErrorResponse{
            Error:  "Validation failed",
            Code:   "VALIDATION_ERROR",
            Fields: validationErrors,
        })
        return
    }

    // Create user...
}

func validateUser(input CreateUserInput) []ValidationError {
    var errors []ValidationError

    if input.Email == "" {
        errors = append(errors, ValidationError{
            Field:   "email",
            Message: "Email is required",
        })
    } else if !isValidEmail(input.Email) {
        errors = append(errors, ValidationError{
            Field:   "email",
            Message: "Invalid email format",
        })
    }

    if len(input.Password) < 8 {
        errors = append(errors, ValidationError{
            Field:   "password",
            Message: "Password must be at least 8 characters",
        })
    }

    return errors
}
```

### Custom Error Types

Define domain-specific errors:

```go
type AppError struct {
    Code       string
    Message    string
    HTTPStatus int
    Err        error
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

// Predefined errors
var (
    ErrUserNotFound = &AppError{
        Code:       "USER_NOT_FOUND",
        Message:    "User not found",
        HTTPStatus: http.StatusNotFound,
    }

    ErrUnauthorized = &AppError{
        Code:       "UNAUTHORIZED",
        Message:    "Unauthorized",
        HTTPStatus: http.StatusUnauthorized,
    }

    ErrForbidden = &AppError{
        Code:       "FORBIDDEN",
        Message:    "Forbidden",
        HTTPStatus: http.StatusForbidden,
    }
)

// Error handler middleware
func errorHandler(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Use custom response writer to capture errors
        rw := &errorResponseWriter{ResponseWriter: w}
        next.ServeHTTP(rw, r)
    })
}

// Handler can return AppError
func getUser(w http.ResponseWriter, r *http.Request) {
    userID := transire.URLParam(r, "id")

    user, err := db.GetUser(r.Context(), userID)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            handleError(w, ErrUserNotFound)
            return
        }
        handleError(w, &AppError{
            Code:       "INTERNAL_ERROR",
            Message:    "Internal server error",
            HTTPStatus: http.StatusInternalServerError,
            Err:        err,
        })
        return
    }

    response.JSON(w, http.StatusOK, user)
}

func handleError(w http.ResponseWriter, err *AppError) {
    // Log internal errors
    if err.HTTPStatus >= 500 {
        log.Printf("Internal error: %v", err)
    }

    response.JSON(w, err.HTTPStatus, ErrorResponse{
        Error: err.Message,
        Code:  err.Code,
    })
}
```

## Queue Error Handling

### Simple Error Pattern (Recommended)

Queue handlers should return an error when processing fails:

```go
func processOrders(ctx context.Context, msgs []ProcessOrder) error {
    for _, order := range msgs {
        if err := processOrder(ctx, order); err != nil {
            // Log error with context
            log.Printf("Failed to process order %s: %v", order.OrderID, err)

            // Return error - entire batch will be retried
            return fmt.Errorf("failed to process order %s: %w", order.OrderID, err)
        }

        log.Printf("Successfully processed order %s", order.OrderID)
    }

    // All messages processed successfully
    return nil
}
```

**How it works:**
- Return `nil`: All messages acknowledged and removed from queue
- Return `error`: Entire batch retried according to retry configuration
- After max retries: Failed messages moved to dead-letter queue automatically

### Transient vs Permanent Errors

Distinguish between retryable and non-retryable errors:

```go
type PermanentError struct {
    message string
}

func (e *PermanentError) Error() string {
    return e.message
}

func processOrder(ctx context.Context, order ProcessOrder) error {
    // Validation errors are permanent (won't fix on retry)
    if order.Total < 0 {
        return &PermanentError{message: "invalid order total"}
    }

    // User not found is permanent
    user, err := db.GetUser(ctx, order.UserID)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return &PermanentError{message: "user not found"}
        }
        // Database error is transient (may succeed on retry)
        return fmt.Errorf("database error: %w", err)
    }

    // Network errors are transient
    err = paymentService.Charge(ctx, order)
    if err != nil {
        return fmt.Errorf("payment failed: %w", err)
    }

    return nil
}

// Handler with permanent error handling
func processOrders(ctx context.Context, msgs []ProcessOrder) error {
    for _, order := range msgs {
        err := processOrder(ctx, order)
        if err != nil {
            var permErr *PermanentError
            if errors.As(err, &permErr) {
                // Permanent error: log and continue (don't retry)
                log.Printf("PERMANENT ERROR for order %s: %v", order.OrderID, err)
                // Consider: send alert, write to error log, etc.
                continue  // Skip this message, don't fail batch
            }

            // Transient error: return to retry entire batch
            log.Printf("Transient error for order %s: %v", order.OrderID, err)
            return err
        }
    }

    return nil
}
```

### Error Enrichment

Add context to errors:

```go
func processOrder(ctx context.Context, order ProcessOrder) error {
    // Add order context to all errors
    defer func() {
        if r := recover(); r != nil {
            log.Printf("Panic processing order %s: %v\n%s",
                order.OrderID, r, debug.Stack())
        }
    }()

    if err := chargePayment(ctx, order); err != nil {
        return fmt.Errorf("order %s: charge payment: %w", order.OrderID, err)
    }

    if err := sendConfirmation(ctx, order); err != nil {
        return fmt.Errorf("order %s: send confirmation: %w", order.OrderID, err)
    }

    return nil
}
```

### DLQ Monitoring

Monitor and alert on DLQ messages:

```go
// Scheduled job to check DLQ
func monitorDLQ(ctx context.Context) error {
    count, err := getDLQMessageCount(ctx)
    if err != nil {
        return err
    }

    if count > 0 {
        log.Printf("WARNING: %d messages in DLQ", count)

        // Send alert
        err = sendAlert(ctx, fmt.Sprintf("DLQ has %d messages", count))
        if err != nil {
            return err
        }
    }

    return nil
}
```

## Panic Recovery

### HTTP Handler Recovery

```go
import "runtime/debug"

func recoveryMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                log.Printf("Panic: %v\n%s", err, debug.Stack())

                // Return 500 error
                http.Error(w, "Internal server error", http.StatusInternalServerError)
            }
        }()

        next.ServeHTTP(w, r)
    })
}

// Usage
func main() {
    app := transire.New()
    app.Use(recoveryMiddleware)
    app.GET("/risky", riskyHandler)
    app.Run()
}

func riskyHandler(w http.ResponseWriter, r *http.Request) {
    panic("something went wrong!")
    // recoveryMiddleware catches this
}
```

### Queue Handler Recovery

```go
func processOrders(ctx context.Context, msgs []ProcessOrder) (err error) {
    // Catch panics for entire batch
    defer func() {
        if r := recover(); r != nil {
            log.Printf("Panic in queue handler: %v\n%s", r, debug.Stack())
            err = fmt.Errorf("panic: %v", r)
        }
    }()

    for _, order := range msgs {
        if err := processOrder(ctx, order); err != nil {
            // Log and return - batch will retry
            log.Printf("Error processing order %s: %v", order.OrderID, err)
            return err
        }
    }

    return nil
}
```

## Error Logging

### Structured Logging

```go
import (
    "encoding/json"
    "os"
)

type LogEntry struct {
    Timestamp int64                  `json:"timestamp"`
    Level     string                 `json:"level"`
    Message   string                 `json:"message"`
    Error     string                 `json:"error,omitempty"`
    Fields    map[string]interface{} `json:"fields,omitempty"`
}

func logError(message string, err error, fields map[string]interface{}) {
    entry := LogEntry{
        Timestamp: time.Now().Unix(),
        Level:     "error",
        Message:   message,
        Fields:    fields,
    }

    if err != nil {
        entry.Error = err.Error()
    }

    json.NewEncoder(os.Stdout).Encode(entry)
}

// Usage
func getUser(w http.ResponseWriter, r *http.Request) {
    userID := transire.URLParam(r, "id")

    user, err := db.GetUser(r.Context(), userID)
    if err != nil {
        logError("Failed to get user", err, map[string]interface{}{
            "user_id": userID,
            "method":  r.Method,
            "path":    r.URL.Path,
        })

        http.Error(w, "Internal server error", http.StatusInternalServerError)
        return
    }

    response.JSON(w, http.StatusOK, user)
}
```

### Error Context

Add request context to errors:

```go
type errorContext struct {
    RequestID  string `json:"request_id"`
    Method     string `json:"method"`
    Path       string `json:"path"`
    UserID     string `json:"user_id,omitempty"`
    RemoteAddr string `json:"remote_addr"`
}

func getErrorContext(r *http.Request) errorContext {
    ctx := errorContext{
        RequestID:  middleware.GetRequestID(r.Context()),
        Method:     r.Method,
        Path:       r.URL.Path,
        RemoteAddr: r.RemoteAddr,
    }

    if user, ok := getUser(r.Context()); ok {
        ctx.UserID = user.ID
    }

    return ctx
}

func logErrorWithContext(r *http.Request, message string, err error) {
    logEntry := map[string]interface{}{
        "timestamp": time.Now().Unix(),
        "level":     "error",
        "message":   message,
        "error":     err.Error(),
        "context":   getErrorContext(r),
    }

    json.NewEncoder(os.Stdout).Encode(logEntry)
}
```

## Error Response Patterns

### Standard Error Response

```go
type ErrorResponse struct {
    Error      string                 `json:"error"`
    Code       string                 `json:"code"`
    Message    string                 `json:"message,omitempty"`
    Details    map[string]interface{} `json:"details,omitempty"`
    RequestID  string                 `json:"request_id,omitempty"`
    Timestamp  int64                  `json:"timestamp"`
}

func sendError(w http.ResponseWriter, r *http.Request, status int, code string, message string) {
    resp := ErrorResponse{
        Error:     http.StatusText(status),
        Code:      code,
        Message:   message,
        RequestID: middleware.GetRequestID(r.Context()),
        Timestamp: time.Now().Unix(),
    }

    response.JSON(w, status, resp)
}
```

### Problem Details (RFC 7807)

```go
type ProblemDetail struct {
    Type     string                 `json:"type"`
    Title    string                 `json:"title"`
    Status   int                    `json:"status"`
    Detail   string                 `json:"detail,omitempty"`
    Instance string                 `json:"instance"`
    Extra    map[string]interface{} `json:"-"`
}

func (p ProblemDetail) MarshalJSON() ([]byte, error) {
    type Alias ProblemDetail
    m := make(map[string]interface{})

    // Marshal base fields
    b, _ := json.Marshal(Alias(p))
    json.Unmarshal(b, &m)

    // Add extra fields
    for k, v := range p.Extra {
        m[k] = v
    }

    return json.Marshal(m)
}

func sendProblemDetail(w http.ResponseWriter, r *http.Request, problem ProblemDetail) {
    problem.Instance = r.URL.Path
    if problem.Type == "" {
        problem.Type = "about:blank"
    }

    w.Header().Set("Content-Type", "application/problem+json")
    response.JSON(w, problem.Status, problem)
}

// Usage
func getUser(w http.ResponseWriter, r *http.Request) {
    userID := transire.URLParam(r, "id")

    user, err := db.GetUser(r.Context(), userID)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            sendProblemDetail(w, r, ProblemDetail{
                Title:  "User Not Found",
                Status: http.StatusNotFound,
                Detail: fmt.Sprintf("No user with ID: %s", userID),
                Extra: map[string]interface{}{
                    "user_id": userID,
                },
            })
            return
        }

        sendProblemDetail(w, r, ProblemDetail{
            Title:  "Internal Server Error",
            Status: http.StatusInternalServerError,
            Detail: "An unexpected error occurred",
        })
        return
    }

    response.JSON(w, http.StatusOK, user)
}
```

## Best Practices

### 1. Don't Leak Internal Errors

```go
// ❌ BAD: Exposes internal implementation
func getUser(w http.ResponseWriter, r *http.Request) {
    user, err := db.GetUser(r.Context(), userID)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        // Client sees: "pq: connection to database failed at 10.0.1.5:5432"
        return
    }
}

// ✅ GOOD: Generic message, log details
func getUser(w http.ResponseWriter, r *http.Request) {
    user, err := db.GetUser(r.Context(), userID)
    if err != nil {
        log.Printf("Database error: %v", err)  // Log full details
        http.Error(w, "Internal server error", http.StatusInternalServerError)  // Generic message
        return
    }
}
```

### 2. Use Appropriate Status Codes

```go
// 400 Bad Request - Client error (invalid input)
errorJSON(w, http.StatusBadRequest, "INVALID_INPUT", "Invalid user ID format")

// 401 Unauthorized - Missing/invalid authentication
errorJSON(w, http.StatusUnauthorized, "UNAUTHORIZED", "Authentication required")

// 403 Forbidden - Valid auth but insufficient permissions
errorJSON(w, http.StatusForbidden, "FORBIDDEN", "Insufficient permissions")

// 404 Not Found - Resource doesn't exist
errorJSON(w, http.StatusNotFound, "NOT_FOUND", "User not found")

// 422 Unprocessable Entity - Valid syntax but semantic errors
errorJSON(w, http.StatusUnprocessableEntity, "VALIDATION_ERROR", "Validation failed")

// 429 Too Many Requests - Rate limit exceeded
errorJSON(w, http.StatusTooManyRequests, "RATE_LIMIT", "Rate limit exceeded")

// 500 Internal Server Error - Server error
errorJSON(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Internal server error")

// 503 Service Unavailable - Temporary unavailability
errorJSON(w, http.StatusServiceUnavailable, "SERVICE_UNAVAILABLE", "Service temporarily unavailable")
```

### 3. Log Errors with Context

```go
// ❌ BAD: Insufficient context
log.Printf("Error: %v", err)

// ✅ GOOD: Include relevant context
log.Printf("Failed to get user: userID=%s, error=%v", userID, err)

// ✅ BETTER: Structured logging
logError("Failed to get user", err, map[string]interface{}{
    "user_id":    userID,
    "request_id": requestID,
    "method":     r.Method,
    "path":       r.URL.Path,
})
```

### 4. Handle Context Cancellation

```go
func processOrder(ctx context.Context, order ProcessOrder) error {
    // Check context before expensive operations
    select {
    case <-ctx.Done():
        return ctx.Err()  // context.Canceled or context.DeadlineExceeded
    default:
    }

    // Do work...

    // Check context again
    if ctx.Err() != nil {
        return ctx.Err()
    }

    return nil
}
```

## See Also

- [HTTP Handlers](/sdk/http.md) - HTTP handler basics
- [Queue Handlers](/sdk/queue.md) - Queue error handling
- [Middleware](/sdk/middleware.md) - Recovery middleware
- [Testing](/sdk/testkit.md) - Testing error cases
- [Error Codes Reference](/reference/error-codes.md) - Complete error code list
