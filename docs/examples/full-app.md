---
title: "Full Application Example"
description: "Production-ready application with all Transire features"
keywords:
  - example
  - full application
  - production
  - complete
  - advanced
category: examples
difficulty: advanced
estimated_time: 45 minutes
prerequisites:
  - "Completed other examples"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Production patterns"
    - "Complete feature set"
    - "Best practices"
  common_questions:
    - "Show me a production app"
    - "What does a complete app look like?"
    - "What are best practices?"
---

# Full App Example

Reference for building production-grade applications with Transire.

!!! tip "TL;DR"
    The full-app example demonstrates enterprise-grade patterns including multi-function architecture, comprehensive error handling, observability, testing, and production deployment strategies.

---

## Overview

The **full-app** example showcases:

- **Multi-Function Architecture** – Split handlers across functions
- **Advanced Queue Patterns** – Idempotency, DLQ handling, priority queues
- **Comprehensive Testing** – Unit, integration, and E2E tests
- **Observability** – Structured logging, metrics, tracing
- **Security** – Authentication, authorization, rate limiting
- **Performance** – Connection pooling, caching, optimizations
- **Production Deployment** – Multi-environment, CI/CD, monitoring

**Location:** [`examples/full-app/`](https://github.com/transire/transire/tree/main/examples/full-app)

---

## Architecture

### Multi-Function Split

```yaml
# transire.yaml
functions:
  web:
    include:
      - http_handlers: "*"
    memory_mb: 512
    timeout_seconds: 30
    reserved_concurrent_executions: 100

  high-priority-workers:
    include:
      - queue_handlers: "order-processing"
      - queue_handlers: "payment-processing"
    memory_mb: 1024
    timeout_seconds: 60
    reserved_concurrent_executions: 20

  low-priority-workers:
    include:
      - queue_handlers: "analytics"
      - queue_handlers: "reports"
    memory_mb: 512
    timeout_seconds: 300
    reserved_concurrent_executions: 5

  schedulers:
    include:
      - schedule_handlers: "*"
    memory_mb: 2048
    timeout_seconds: 900
    reserved_concurrent_executions: 1
```

---

## Advanced Patterns

### 1. Idempotent Queue Processing

```go
// From queues/order_processor.go
type OrderProcessor struct {
    db    *sql.DB
    cache *redis.Client
}

func (p *OrderProcessor) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        // Check if already processed (in cache)
        processed, err := p.cache.Get(ctx, fmt.Sprintf("order:processed:%s", msg.ID())).Result()
        if err == nil && processed == "true" {
            log.Printf("Order %s already processed, skipping", msg.ID())
            continue
        }

        var order OrderMessage
        if err := json.Unmarshal(msg.Body(), &order); err != nil {
            log.Printf("Invalid message format: %v", err)
            continue
        }

        // Process with database transaction
        tx, err := p.db.BeginTx(ctx, nil)
        if err != nil {
            failedIDs = append(failedIDs, msg.ID())
            continue
        }

        // Check idempotency key in database
        var exists bool
        err = tx.QueryRowContext(ctx,
            "SELECT EXISTS(SELECT 1 FROM orders WHERE idempotency_key = $1)",
            order.IdempotencyKey,
        ).Scan(&exists)

        if err != nil {
            tx.Rollback()
            failedIDs = append(failedIDs, msg.ID())
            continue
        }

        if exists {
            tx.Rollback()
            log.Printf("Order with key %s already exists", order.IdempotencyKey)
            continue
        }

        // Process order
        if err := p.processOrder(ctx, tx, order); err != nil {
            tx.Rollback()
            if isTransientError(err) {
                failedIDs = append(failedIDs, msg.ID())
            }
            continue
        }

        if err := tx.Commit(); err != nil {
            failedIDs = append(failedIDs, msg.ID())
            continue
        }

        // Mark as processed in cache (24h TTL)
        p.cache.Set(ctx, fmt.Sprintf("order:processed:%s", msg.ID()), "true", 24*time.Hour)
    }

    return failedIDs, nil
}
```

---

### 2. Circuit Breaker for External APIs

```go
// From services/payment_service.go
type PaymentService struct {
    breaker *CircuitBreaker
    client  *http.Client
}

type CircuitBreaker struct {
    mu              sync.Mutex
    failureCount    int
    lastFailureTime time.Time
    threshold       int
    timeout         time.Duration
    isOpen          bool
}

func (s *PaymentService) ProcessPayment(ctx context.Context, payment Payment) error {
    return s.breaker.Call(func() error {
        return s.callPaymentAPI(ctx, payment)
    })
}

func (cb *CircuitBreaker) Call(fn func() error) error {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    // Check if circuit is open
    if cb.isOpen {
        if time.Since(cb.lastFailureTime) < cb.timeout {
            return ErrCircuitBreakerOpen
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

    // Success - reset counter
    cb.failureCount = 0
    return nil
}
```

---

### 3. Structured Logging with Context

```go
// From observability/logging.go
import "log/slog"

func LogWithContext(ctx context.Context, level slog.Level, msg string, args ...any) {
    // Extract request context
    requestID := ctx.Value("requestID")
    userID := ctx.Value("userID")
    traceID := ctx.Value("traceID")

    // Build structured log
    attrs := []slog.Attr{
        slog.String("msg", msg),
    }

    if requestID != nil {
        attrs = append(attrs, slog.String("request_id", requestID.(string)))
    }
    if userID != nil {
        attrs = append(attrs, slog.String("user_id", userID.(string)))
    }
    if traceID != nil {
        attrs = append(attrs, slog.String("trace_id", traceID.(string)))
    }

    // Add custom args
    for i := 0; i < len(args); i += 2 {
        if i+1 < len(args) {
            key := fmt.Sprint(args[i])
            value := args[i+1]
            attrs = append(attrs, slog.Any(key, value))
        }
    }

    slog.LogAttrs(ctx, level, msg, attrs...)
}
```

---

### 4. Metrics Collection

```go
// From observability/metrics.go
import "github.com/prometheus/client_golang/prometheus"

type Metrics struct {
    requestDuration prometheus.HistogramVec
    requestCount    prometheus.CounterVec
    queueDepth      prometheus.GaugeVec
    errorCount      prometheus.CounterVec
}

func NewMetrics() *Metrics {
    m := &Metrics{
        requestDuration: *prometheus.NewHistogramVec(
            prometheus.HistogramOpts{
                Name:    "http_request_duration_seconds",
                Help:    "HTTP request duration in seconds",
                Buckets: prometheus.DefBuckets,
            },
            []string{"method", "path", "status"},
        ),
        requestCount: *prometheus.NewCounterVec(
            prometheus.CounterOpts{
                Name: "http_requests_total",
                Help: "Total HTTP requests",
            },
            []string{"method", "path", "status"},
        ),
    }

    // Register metrics
    prometheus.MustRegister(m.requestDuration)
    prometheus.MustRegister(m.requestCount)

    return m
}

func (m *Metrics) RecordRequest(method, path string, status int, duration time.Duration) {
    statusStr := strconv.Itoa(status)
    m.requestDuration.WithLabelValues(method, path, statusStr).Observe(duration.Seconds())
    m.requestCount.WithLabelValues(method, path, statusStr).Inc()
}
```

---

### 5. Comprehensive Error Handling

```go
// From errors/errors.go
type AppError struct {
    Code       string
    Message    string
    StatusCode int
    Internal   error
    Retryable  bool
}

func (e *AppError) Error() string {
    if e.Internal != nil {
        return fmt.Sprintf("%s: %v", e.Message, e.Internal)
    }
    return e.Message
}

// Predefined errors
var (
    ErrNotFound = &AppError{
        Code:       "NOT_FOUND",
        Message:    "Resource not found",
        StatusCode: 404,
        Retryable:  false,
    }

    ErrDatabaseError = &AppError{
        Code:       "DATABASE_ERROR",
        Message:    "Database operation failed",
        StatusCode: 500,
        Retryable:  true,
    }

    ErrRateLimited = &AppError{
        Code:       "RATE_LIMITED",
        Message:    "Rate limit exceeded",
        StatusCode: 429,
        Retryable:  true,
    }
)

// Error middleware
func ErrorHandler(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                log.Printf("Panic recovered: %v", err)
                writeErrorResponse(w, ErrInternalServer)
            }
        }()

        next.ServeHTTP(w, r)
    })
}
```

---

## Testing Strategy

### Unit Tests

```go
// From handlers/orders_test.go
func TestCreateOrder(t *testing.T) {
    // Setup mock database
    db, mock, err := sqlmock.New()
    require.NoError(t, err)
    defer db.Close()

    // Setup expectations
    mock.ExpectBegin()
    mock.ExpectQuery("INSERT INTO orders").
        WithArgs("order-123", sqlmock.AnyArg()).
        WillReturnRows(sqlmock.NewRows([]string{"id"}).AddRow("order-123"))
    mock.ExpectCommit()

    // Create handler
    handler := NewOrderHandler(db)

    // Create test request
    body := `{"idempotency_key":"key-123","amount":100}`
    req := httptest.NewRequest("POST", "/orders", strings.NewReader(body))
    w := httptest.NewRecorder()

    // Execute handler
    handler.ServeHTTP(w, req)

    // Assert
    assert.Equal(t, http.StatusCreated, w.Code)
    assert.NoError(t, mock.ExpectationsWereMet())
}
```

### Integration Tests

```go
// From integration_test.go
func TestOrderFlow(t *testing.T) {
    // Start test database
    db := setupTestDatabase(t)
    defer db.Close()

    // Start app
    app := transire.New()
    setupRoutes(app, db)

    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    go app.Run(ctx)
    time.Sleep(100 * time.Millisecond)

    // Test order creation
    resp, err := http.Post("http://localhost:3000/orders", "application/json",
        strings.NewReader(`{"amount":100,"currency":"USD"}`))
    require.NoError(t, err)
    assert.Equal(t, http.StatusCreated, resp.StatusCode)

    // Verify database state
    var count int
    err = db.QueryRow("SELECT COUNT(*) FROM orders").Scan(&count)
    require.NoError(t, err)
    assert.Equal(t, 1, count)
}
```

---

## Production Deployment

### Multi-Environment Configuration

```yaml
# transire.prod.yaml
name: full-app-prod

lambda:
  architecture: arm64
  memory_mb: 1024
  timeout_seconds: 30

functions:
  web:
    memory_mb: 512
    reserved_concurrent_executions: 200

environment:
  ENV: production
  LOG_LEVEL: info
  DATABASE_URL: ${DATABASE_URL}

vpc:
  subnet_ids:
    - subnet-prod-1
    - subnet-prod-2
  security_group_ids:
    - sg-prod

cdk_extensions:
  - file: "extensions/database.ts"
  - file: "extensions/cache.ts"
  - file: "extensions/monitoring.ts"
  - file: "extensions/alarms.ts"
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go test -v -cover ./...

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
      - run: go install github.com/transire/transire/cmd/transire@latest
      - run: transire build --config transire.prod.yaml
      - uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/download-artifact@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install -g aws-cdk
      - run: transire deploy --config transire.prod.yaml
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

---

## Key Learnings

### 1. Multi-Function Benefits
- **Cost optimization** – Pay only for resources you use
- **Independent scaling** – Each function scales independently
- **Better cold starts** – Smaller functions = faster starts
- **Clear boundaries** – Logical separation of concerns

### 2. Production Patterns
- **Idempotency** – Essential for reliable message processing
- **Circuit breakers** – Protect against cascading failures
- **Structured logging** – Critical for debugging in production
- **Metrics** – Understand system behavior
- **Error handling** – Distinguish transient vs permanent errors

### 3. Testing Approach
- **Unit tests** – Test business logic in isolation
- **Integration tests** – Test with real database
- **E2E tests** – Test full request flow
- **Load tests** – Verify performance under load

### 4. Deployment Strategy
- **Multi-environment** – Separate dev/staging/prod configs
- **CI/CD** – Automated testing and deployment
- **Monitoring** – Dashboards and alarms
- **Rollback plan** – Quick recovery from issues

---

## Next Steps

- **[Multi-Function Architecture Guide](../guides/multi-function-architecture.md)** – Advanced patterns
- **[Testing Guide](../guides/testing.md)** – Comprehensive testing strategies
- **[Deploying to AWS](../guides/deploying-to-aws.md)** – Production deployment guide

---

## See Also

- [Full App Source Code](https://github.com/transire/transire/tree/main/examples/full-app)
- [Simple API Example](simple-api.md)
- [Todo App Example](todo-app.md)
