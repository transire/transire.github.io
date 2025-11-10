---
title: "Tutorial: Dependency Injection"
description: Manage service dependencies with singleton and request-scoped injection in 25 minutes
category: learn
subcategory: tutorial
complexity: beginner
duration: 25 minutes
prerequisites:
  - Completed Scheduled Jobs tutorial
  - Understanding of Go interfaces
  - Go 1.22+
mcp_use: template
mcp_operations:
  - add_singleton_service
  - add_request_scoped_service
  - inject_dependencies
features_covered:
  - Dependency injection
  - Singleton services
  - Request-scoped services
  - Database connections
  - Service resolution
  - Testing with DI
code_blocks: true
last_updated: 2025-11-10
---

# Tutorial: Dependency Injection

> **Quick Summary:** Add dependency injection to manage database connections, services, and request-scoped dependencies

## What You'll Build

Add DI to your orders API for better architecture:

```
Singleton Services (app lifetime)
  ↓
  Database Connection Pool
  Logger
  Configuration

Request-Scoped Services (per request)
  ↓
  Request ID
  User Context
  Transaction
```

**Time:** 25 minutes • **Difficulty:** Beginner

---

## Why Use Dependency Injection?

DI solves common problems:

- **Testability** - Easy to mock dependencies
- **Decoupling** - Services don't create their own dependencies
- **Lifecycle management** - Automatic cleanup
- **Configuration** - Single source of truth
- **Reusability** - Share services across handlers

**When to use:**
- Database connections
- External API clients
- Configuration objects
- Logging services
- Request-specific context

---

## Step 1: Define Services

Create service interfaces and implementations:

```go
package main

import (
    "context"
    "database/sql"
    "log"
    "time"
)

// Database service (singleton - shared across all requests)
type Database struct {
    DB *sql.DB
}

func NewDatabase(cfg *Config) (*Database, error) {
    db, err := sql.Open("postgres", cfg.DatabaseURL)
    if err != nil {
        return nil, err
    }

    // Configure connection pool
    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(5)
    db.SetConnMaxLifetime(5 * time.Minute)

    // Test connection
    if err := db.Ping(); err != nil {
        return nil, err
    }

    log.Println("✓ Database connected")
    return &Database{DB: db}, nil
}

func (d *Database) Close() error {
    return d.DB.Close()
}

// Configuration service (singleton - loaded at startup)
type Config struct {
    DatabaseURL string
    Port        int
    Environment string
}

func NewConfig() *Config {
    return &Config{
        DatabaseURL: getEnv("DATABASE_URL", "postgres://localhost/orders?sslmode=disable"),
        Port:        getEnvInt("PORT", 8080),
        Environment: getEnv("ENVIRONMENT", "development"),
    }
}

// Logger service (singleton - shared logger)
type Logger struct {
    prefix string
}

func NewLogger() *Logger {
    return &Logger{prefix: "[OrdersAPI]"}
}

func (l *Logger) Info(msg string) {
    log.Printf("%s INFO: %s", l.prefix, msg)
}

func (l *Logger) Error(msg string, err error) {
    log.Printf("%s ERROR: %s: %v", l.prefix, msg, err)
}
```

---

## Step 2: Register Singleton Services

Add to your `main()` function:

```go
import "github.com/transire/transire-sdk-go"

func main() {
    app := transire.New()

    // Register singleton services (created once at startup)

    // Config - loaded from environment
    transire.Provide(func() *Config {
        return NewConfig()
    })

    // Logger - single instance
    transire.Provide(func() *Logger {
        return NewLogger()
    })

    // Database - depends on Config
    transire.Provide(func(cfg *Config) (*Database, error) {
        return NewDatabase(cfg)
    })

    // HTTP routes
    app.GET("/orders", listOrders)
    app.GET("/orders/{id}", getOrder)
    app.POST("/orders", createOrder)

    app.Run()
}
```

**Key points:**
- `transire.Provide()` registers singleton providers
- Providers can depend on other services (DI graph)
- Services are created lazily on first request
- Returning `error` means provider can fail

---

## Step 3: Use Services in Handlers

Inject dependencies into handler functions:

```go
import "github.com/transire/transire-sdk-go/response"

// Handler with injected dependencies
func listOrders(w http.ResponseWriter, r *http.Request, db *Database, logger *Logger) {
    logger.Info("Listing all orders")

    // Query database
    rows, err := db.DB.QueryContext(r.Context(), "SELECT id, product, quantity, price, status FROM orders")
    if err != nil {
        logger.Error("Failed to query orders", err)
        response.InternalServerError(w, "Database error")
        return
    }
    defer rows.Close()

    // Scan results
    var orders []Order
    for rows.Next() {
        var order Order
        if err := rows.Scan(&order.ID, &order.Product, &order.Quantity, &order.Price, &order.Status); err != nil {
            logger.Error("Failed to scan order", err)
            continue
        }
        orders = append(orders, order)
    }

    logger.Info(fmt.Sprintf("Returned %d orders", len(orders)))
    response.OK(w, orders)
}

func getOrder(w http.ResponseWriter, r *http.Request, db *Database, logger *Logger) {
    id := transire.URLParam(r, "id")
    logger.Info(fmt.Sprintf("Getting order: %s", id))

    var order Order
    err := db.DB.QueryRowContext(r.Context(),
        "SELECT id, product, quantity, price, status FROM orders WHERE id = $1",
        id,
    ).Scan(&order.ID, &order.Product, &order.Quantity, &order.Price, &order.Status)

    if err == sql.ErrNoRows {
        logger.Info(fmt.Sprintf("Order not found: %s", id))
        response.NotFound(w, "Order not found")
        return
    }
    if err != nil {
        logger.Error("Database query failed", err)
        response.InternalServerError(w, "Database error")
        return
    }

    response.OK(w, order)
}

func createOrder(w http.ResponseWriter, r *http.Request, db *Database, logger *Logger) {
    var req CreateOrderRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        response.BadRequest(w, "Invalid JSON")
        return
    }

    if err := validateCreateOrder(&req); err != nil {
        response.BadRequest(w, err.Error())
        return
    }

    // Insert into database
    id := generateID()
    _, err := db.DB.ExecContext(r.Context(),
        "INSERT INTO orders (id, product, quantity, price, status) VALUES ($1, $2, $3, $4, $5)",
        id, req.Product, req.Quantity, req.Price, "pending",
    )
    if err != nil {
        logger.Error("Failed to insert order", err)
        response.InternalServerError(w, "Failed to create order")
        return
    }

    logger.Info(fmt.Sprintf("Created order: %s", id))

    order := Order{
        ID:       id,
        Product:  req.Product,
        Quantity: req.Quantity,
        Price:    req.Price,
        Status:   "pending",
    }

    w.Header().Set("Location", fmt.Sprintf("/orders/%s", id))
    response.Created(w, order)
}
```

**How it works:**
- Transire automatically injects `db` and `logger`
- Services are resolved from the DI container
- Same instances are reused across all requests (singleton)

---

## Step 4: Request-Scoped Services

For services that should be created per request:

```go
// RequestContext is created for each request
type RequestContext struct {
    RequestID string
    UserID    string
    StartTime time.Time
}

func main() {
    app := transire.New()

    // Singleton services (existing)
    transire.Provide(func() *Config { return NewConfig() })
    transire.Provide(func() *Logger { return NewLogger() })
    transire.Provide(func(cfg *Config) (*Database, error) {
        return NewDatabase(cfg)
    })

    // Request-scoped service (NEW)
    transire.ProvideRequest(func(ctx context.Context, r *http.Request) (*RequestContext, error) {
        requestID := r.Header.Get("X-Request-ID")
        if requestID == "" {
            requestID = generateID()
        }

        userID := r.Header.Get("X-User-ID")

        return &RequestContext{
            RequestID: requestID,
            UserID:    userID,
            StartTime: time.Now(),
        }, nil
    })

    // Routes (existing)
    app.GET("/orders", listOrders)
    app.Run()
}
```

**Key difference:**
- `transire.ProvideRequest()` creates service per request
- Gets access to `*http.Request`
- Fresh instance for each handler invocation

---

## Step 5: Use Request-Scoped Services

```go
func listOrders(
    w http.ResponseWriter,
    r *http.Request,
    db *Database,
    logger *Logger,
    reqCtx *RequestContext, // Request-scoped
) {
    logger.Info(fmt.Sprintf("[%s] Listing orders for user %s",
        reqCtx.RequestID, reqCtx.UserID))

    // Query database
    rows, err := db.DB.QueryContext(r.Context(),
        "SELECT id, product, quantity, price, status FROM orders WHERE user_id = $1",
        reqCtx.UserID,
    )
    if err != nil {
        logger.Error(fmt.Sprintf("[%s] Query failed", reqCtx.RequestID), err)
        response.InternalServerError(w, "Database error")
        return
    }
    defer rows.Close()

    // Scan results
    var orders []Order
    for rows.Next() {
        var order Order
        if err := rows.Scan(&order.ID, &order.Product, &order.Quantity, &order.Price, &order.Status); err != nil {
            continue
        }
        orders = append(orders, order)
    }

    elapsed := time.Since(reqCtx.StartTime)
    logger.Info(fmt.Sprintf("[%s] Returned %d orders in %v",
        reqCtx.RequestID, len(orders), elapsed))

    // Include request ID in response headers
    w.Header().Set("X-Request-ID", reqCtx.RequestID)
    response.OK(w, orders)
}
```

**Benefits:**
- Trace requests with unique IDs
- Track request duration
- User-scoped queries
- Correlation in logs

---

## Step 6: Service Resolution

Manually resolve services when needed:

```go
import "github.com/transire/transire-sdk-go"

func someFunction(ctx context.Context) {
    // Get service from DI container
    db, err := transire.Get[*Database](ctx)
    if err != nil {
        log.Fatal("Failed to resolve database:", err)
    }

    // Use service
    db.DB.QueryContext(ctx, "...")
}

// Or use MustGet (panics if not found)
func anotherFunction(ctx context.Context) {
    logger := transire.MustGet[*Logger](ctx)
    logger.Info("Using logger")
}
```

**When to use:**
- Queue handlers
- Scheduled jobs
- Helper functions
- Middleware

---

## Step 7: Queue Handlers with DI

Inject services into queue handlers:

```go
func main() {
    app := transire.New()

    // Register services (existing)
    transire.Provide(func() *Config { return NewConfig() })
    transire.Provide(func(cfg *Config) (*Database, error) { return NewDatabase(cfg) })
    transire.Provide(func() *Logger { return NewLogger() })

    // Queue handler with injected services
    app.RegisterQueue("fulfill-orders", fulfillOrders)

    app.Run()
}

// Queue handler with DI
func fulfillOrders(
    ctx context.Context,
    orderBatch []Order,
    db *Database,      // Injected
    logger *Logger,    // Injected
) error {
    logger.Info(fmt.Sprintf("Processing batch of %d orders", len(orderBatch)))

    br := transire.NewBatchResult(len(orderBatch))

    for i, order := range orderBatch {
        if ctx.Err() != nil {
            for j := i; j < len(orderBatch); j++ {
                br.Fail(j, ctx.Err())
            }
            break
        }

        // Update database
        _, err := db.DB.ExecContext(ctx,
            "UPDATE orders SET status = $1 WHERE id = $2",
            "fulfilled", order.ID,
        )
        if err != nil {
            logger.Error(fmt.Sprintf("Failed to fulfill order %s", order.ID), err)
            br.Fail(i, err)
            continue
        }

        logger.Info(fmt.Sprintf("Fulfilled order: %s", order.ID))
    }

    logger.Info(fmt.Sprintf("Batch complete: %d succeeded, %d failed",
        br.SuccessCount(), br.FailureCount()))

    return br.ToCloudPartialBatchResponse()
}
```

---

## Step 8: Scheduled Jobs with DI

```go
func main() {
    app := transire.New()

    // Register services
    transire.Provide(func() *Config { return NewConfig() })
    transire.Provide(func(cfg *Config) (*Database, error) { return NewDatabase(cfg) })
    transire.Provide(func() *Logger { return NewLogger() })

    // Scheduled job with injected services
    app.Schedule("daily-report", "@daily 09:00", generateDailyReport)

    app.Run()
}

func generateDailyReport(
    ctx context.Context,
    db *Database,   // Injected
    logger *Logger, // Injected
) error {
    logger.Info("Generating daily report...")

    // Query database
    var totalOrders int
    var totalSales float64

    err := db.DB.QueryRowContext(ctx, `
        SELECT COUNT(*), COALESCE(SUM(price * quantity), 0)
        FROM orders
        WHERE created_at >= NOW() - INTERVAL '1 day'
    `).Scan(&totalOrders, &totalSales)

    if err != nil {
        logger.Error("Report query failed", err)
        return err
    }

    report := fmt.Sprintf(`
Daily Report
============
Orders: %d
Sales:  $%.2f
`, totalOrders, totalSales)

    logger.Info(report)

    // In production: send email, save to S3, etc.

    return nil
}
```

---

## Service Lifecycle

Understanding when services are created and destroyed:

### Singleton Services

```go
transire.Provide(func() *Database {
    // Called ONCE at startup (lazy)
    // Shared across ALL requests
    return &Database{}
})
```

**Lifecycle:**
```
App Start → (wait for first use) → Create → Reuse → App Shutdown → Cleanup
```

### Request-Scoped Services

```go
transire.ProvideRequest(func(ctx context.Context, r *http.Request) *RequestContext {
    // Called ONCE per request
    // Unique instance per request
    return &RequestContext{}
})
```

**Lifecycle:**
```
Request Start → Create → Use in Handler → Request End → Garbage Collected
```

---

## Testing with DI

DI makes testing easier:

```go
package main

import (
    "testing"
    "github.com/transire/transire-sdk-go/testkit"
)

func TestListOrders(t *testing.T) {
    // Create test services
    mockDB := &MockDatabase{
        orders: []Order{
            {ID: "1", Product: "Widget", Quantity: 5, Price: 99.99},
        },
    }
    mockLogger := &MockLogger{}

    // Setup test kit
    tk := testkit.New(t)

    // Override services with test doubles
    transire.Provide(func() *Database { return mockDB })
    transire.Provide(func() *Logger { return mockLogger })

    // Register handler
    tk.GET("/orders", listOrders)

    // Test request
    resp := tk.Get("/orders")
    tk.AssertStatus(200)
    tk.AssertBodyContains("Widget")

    // Verify service calls
    if !mockLogger.Called("Listing all orders") {
        t.Fatal("Expected logger to be called")
    }
}

// Mock implementations
type MockDatabase struct {
    orders []Order
}

func (m *MockDatabase) Query() []Order {
    return m.orders
}

type MockLogger struct {
    calls []string
}

func (m *MockLogger) Info(msg string) {
    m.calls = append(m.calls, msg)
}

func (m *MockLogger) Called(msg string) bool {
    for _, call := range m.calls {
        if call == msg {
            return true
        }
    }
    return false
}
```

---

## Common Patterns

### Pattern 1: Database Transactions

```go
type Transaction struct {
    tx *sql.Tx
}

// Request-scoped transaction
transire.ProvideRequest(func(ctx context.Context, r *http.Request, db *Database) (*Transaction, error) {
    tx, err := db.DB.BeginTx(ctx, nil)
    if err != nil {
        return nil, err
    }

    // Register cleanup
    go func() {
        <-ctx.Done()
        if ctx.Err() != nil {
            tx.Rollback()
        }
    }()

    return &Transaction{tx: tx}, nil
})

func createOrder(w http.ResponseWriter, r *http.Request, tx *Transaction) {
    // Use transaction
    _, err := tx.tx.ExecContext(r.Context(), "INSERT INTO orders ...")
    if err != nil {
        // Transaction will auto-rollback on error
        response.InternalServerError(w, "Failed")
        return
    }

    // Commit transaction
    if err := tx.tx.Commit(); err != nil {
        response.InternalServerError(w, "Commit failed")
        return
    }

    response.Created(w, order)
}
```

### Pattern 2: External API Client

```go
type StripeClient struct {
    apiKey string
    client *http.Client
}

func NewStripeClient(cfg *Config) *StripeClient {
    return &StripeClient{
        apiKey: cfg.StripeAPIKey,
        client: &http.Client{Timeout: 30 * time.Second},
    }
}

func (s *StripeClient) ChargeCard(ctx context.Context, amount int, token string) error {
    // Call Stripe API...
    return nil
}

// Register
transire.Provide(func(cfg *Config) *StripeClient {
    return NewStripeClient(cfg)
})

// Use in handler
func processPayment(w http.ResponseWriter, r *http.Request, stripe *StripeClient) {
    if err := stripe.ChargeCard(r.Context(), 1000, "tok_visa"); err != nil {
        response.InternalServerError(w, "Payment failed")
        return
    }
    response.OK(w, map[string]string{"status": "paid"})
}
```

### Pattern 3: Service Initialization

```go
// Service with initialization
type EmailService struct {
    client *smtp.Client
}

func NewEmailService(cfg *Config) (*EmailService, error) {
    client, err := smtp.Dial(cfg.SMTPHost)
    if err != nil {
        return nil, fmt.Errorf("failed to connect to SMTP: %w", err)
    }

    log.Println("✓ Email service connected")
    return &EmailService{client: client}, nil
}

func (e *EmailService) Send(to, subject, body string) error {
    // Send email...
    return nil
}

// Register with error handling
transire.Provide(func(cfg *Config) (*EmailService, error) {
    return NewEmailService(cfg)
})
```

---

## Configuration

### Environment-Based Config

```go
import "os"

type Config struct {
    DatabaseURL  string
    Port         int
    Environment  string
    Debug        bool
    StripeAPIKey string
    SMTPHost     string
}

func NewConfig() *Config {
    return &Config{
        DatabaseURL:  getEnv("DATABASE_URL", "postgres://localhost/orders"),
        Port:         getEnvInt("PORT", 8080),
        Environment:  getEnv("ENVIRONMENT", "development"),
        Debug:        getEnvBool("DEBUG", false),
        StripeAPIKey: getEnv("STRIPE_API_KEY", ""),
        SMTPHost:     getEnv("SMTP_HOST", "localhost:25"),
    }
}

func getEnv(key, fallback string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return fallback
}

func getEnvInt(key string, fallback int) int {
    if value := os.Getenv(key); value != "" {
        if i, err := strconv.Atoi(value); err == nil {
            return i
        }
    }
    return fallback
}

func getEnvBool(key string, fallback bool) bool {
    if value := os.Getenv(key); value != "" {
        return value == "true" || value == "1"
    }
    return fallback
}
```

---

## Troubleshooting

### Service Not Found

**Issue:** `Failed to resolve service: *Database`

**Check:**
1. Is service registered?
   ```go
   transire.Provide(func() *Database { return &Database{} })
   ```

2. Is handler signature correct?
   ```go
   func handler(w http.ResponseWriter, r *http.Request, db *Database) {
       // db is injected
   }
   ```

3. Check for circular dependencies:
   ```go
   // ❌ Bad: A depends on B, B depends on A
   transire.Provide(func(b *ServiceB) *ServiceA { return &ServiceA{} })
   transire.Provide(func(a *ServiceA) *ServiceB { return &ServiceB{} })
   ```

### Provider Error

**Issue:** Service provider returns error

**Solution:**
```go
transire.Provide(func(cfg *Config) (*Database, error) {
    db, err := NewDatabase(cfg)
    if err != nil {
        // This error will be logged and app will fail to start
        return nil, fmt.Errorf("database init failed: %w", err)
    }
    return db, nil
})
```

### Service Lifecycle Issues

**Issue:** Service created multiple times

**Check:**
- Using `Provide()` for singletons (once)
- Using `ProvideRequest()` for per-request (each request)

```go
// ❌ Bad: Database created per request
transire.ProvideRequest(func(ctx context.Context, r *http.Request) *Database {
    return NewDatabase() // Opens new connection every request!
})

// ✅ Good: Database is singleton
transire.Provide(func() *Database {
    return NewDatabase() // Opens connection once
})
```

---

## Complete Code

```go
package main

import (
    "context"
    "database/sql"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "os"
    "strconv"
    "time"

    "github.com/transire/transire-sdk-go"
    "github.com/transire/transire-sdk-go/response"
    _ "github.com/lib/pq"
)

func main() {
    app := transire.New()

    // Register singleton services
    transire.Provide(func() *Config {
        return NewConfig()
    })

    transire.Provide(func() *Logger {
        return NewLogger()
    })

    transire.Provide(func(cfg *Config) (*Database, error) {
        return NewDatabase(cfg)
    })

    // Register request-scoped services
    transire.ProvideRequest(func(ctx context.Context, r *http.Request) (*RequestContext, error) {
        requestID := r.Header.Get("X-Request-ID")
        if requestID == "" {
            requestID = generateID()
        }

        return &RequestContext{
            RequestID: requestID,
            UserID:    r.Header.Get("X-User-ID"),
            StartTime: time.Now(),
        }, nil
    })

    // HTTP routes
    app.GET("/orders", listOrders)
    app.GET("/orders/{id}", getOrder)
    app.POST("/orders", createOrder)

    // Queue handler
    app.RegisterQueue("fulfill-orders", fulfillOrders)

    // Scheduled job
    app.Schedule("daily-report", "@daily 09:00", generateDailyReport)

    app.Run()
}

// Services
type Config struct {
    DatabaseURL string
    Port        int
    Environment string
}

func NewConfig() *Config {
    return &Config{
        DatabaseURL: getEnv("DATABASE_URL", "postgres://localhost/orders?sslmode=disable"),
        Port:        getEnvInt("PORT", 8080),
        Environment: getEnv("ENVIRONMENT", "development"),
    }
}

type Database struct {
    DB *sql.DB
}

func NewDatabase(cfg *Config) (*Database, error) {
    db, err := sql.Open("postgres", cfg.DatabaseURL)
    if err != nil {
        return nil, err
    }

    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(5)
    db.SetConnMaxLifetime(5 * time.Minute)

    if err := db.Ping(); err != nil {
        return nil, err
    }

    log.Println("✓ Database connected")
    return &Database{DB: db}, nil
}

type Logger struct {
    prefix string
}

func NewLogger() *Logger {
    return &Logger{prefix: "[OrdersAPI]"}
}

func (l *Logger) Info(msg string) {
    log.Printf("%s INFO: %s", l.prefix, msg)
}

func (l *Logger) Error(msg string, err error) {
    log.Printf("%s ERROR: %s: %v", l.prefix, msg, err)
}

type RequestContext struct {
    RequestID string
    UserID    string
    StartTime time.Time
}

// HTTP Handlers
func listOrders(
    w http.ResponseWriter,
    r *http.Request,
    db *Database,
    logger *Logger,
    reqCtx *RequestContext,
) {
    logger.Info(fmt.Sprintf("[%s] Listing orders", reqCtx.RequestID))

    rows, err := db.DB.QueryContext(r.Context(),
        "SELECT id, product, quantity, price, status FROM orders")
    if err != nil {
        logger.Error(fmt.Sprintf("[%s] Query failed", reqCtx.RequestID), err)
        response.InternalServerError(w, "Database error")
        return
    }
    defer rows.Close()

    var orders []Order
    for rows.Next() {
        var order Order
        if err := rows.Scan(&order.ID, &order.Product, &order.Quantity, &order.Price, &order.Status); err != nil {
            continue
        }
        orders = append(orders, order)
    }

    w.Header().Set("X-Request-ID", reqCtx.RequestID)
    response.OK(w, orders)
}

func getOrder(
    w http.ResponseWriter,
    r *http.Request,
    db *Database,
    logger *Logger,
) {
    id := transire.URLParam(r, "id")

    var order Order
    err := db.DB.QueryRowContext(r.Context(),
        "SELECT id, product, quantity, price, status FROM orders WHERE id = $1",
        id,
    ).Scan(&order.ID, &order.Product, &order.Quantity, &order.Price, &order.Status)

    if err == sql.ErrNoRows {
        response.NotFound(w, "Order not found")
        return
    }
    if err != nil {
        logger.Error("Query failed", err)
        response.InternalServerError(w, "Database error")
        return
    }

    response.OK(w, order)
}

func createOrder(
    w http.ResponseWriter,
    r *http.Request,
    db *Database,
    logger *Logger,
) {
    var req CreateOrderRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        response.BadRequest(w, "Invalid JSON")
        return
    }

    id := generateID()
    _, err := db.DB.ExecContext(r.Context(),
        "INSERT INTO orders (id, product, quantity, price, status) VALUES ($1, $2, $3, $4, $5)",
        id, req.Product, req.Quantity, req.Price, "pending",
    )
    if err != nil {
        logger.Error("Insert failed", err)
        response.InternalServerError(w, "Failed to create order")
        return
    }

    order := Order{
        ID:       id,
        Product:  req.Product,
        Quantity: req.Quantity,
        Price:    req.Price,
        Status:   "pending",
    }

    response.Created(w, order)
}

// Queue Handler
func fulfillOrders(
    ctx context.Context,
    orderBatch []Order,
    db *Database,
    logger *Logger,
) error {
    logger.Info(fmt.Sprintf("Processing batch of %d orders", len(orderBatch)))

    br := transire.NewBatchResult(len(orderBatch))

    for i, order := range orderBatch {
        _, err := db.DB.ExecContext(ctx,
            "UPDATE orders SET status = $1 WHERE id = $2",
            "fulfilled", order.ID,
        )
        if err != nil {
            br.Fail(i, err)
            continue
        }
    }

    return br.ToCloudPartialBatchResponse()
}

// Scheduled Job
func generateDailyReport(
    ctx context.Context,
    db *Database,
    logger *Logger,
) error {
    logger.Info("Generating daily report...")

    var totalOrders int
    var totalSales float64

    err := db.DB.QueryRowContext(ctx, `
        SELECT COUNT(*), COALESCE(SUM(price * quantity), 0)
        FROM orders
        WHERE created_at >= NOW() - INTERVAL '1 day'
    `).Scan(&totalOrders, &totalSales)

    if err != nil {
        logger.Error("Report query failed", err)
        return err
    }

    logger.Info(fmt.Sprintf("Daily Report: %d orders, $%.2f sales", totalOrders, totalSales))
    return nil
}

// Types
type Order struct {
    ID       string  `json:"id"`
    Product  string  `json:"product"`
    Quantity int     `json:"quantity"`
    Price    float64 `json:"price"`
    Status   string  `json:"status"`
}

type CreateOrderRequest struct {
    Product  string  `json:"product"`
    Quantity int     `json:"quantity"`
    Price    float64 `json:"price"`
}

// Helpers
func generateID() string {
    return fmt.Sprintf("ORD-%d", time.Now().UnixNano())
}

func getEnv(key, fallback string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return fallback
}

func getEnvInt(key string, fallback int) int {
    if value := os.Getenv(key); value != "" {
        if i, err := strconv.Atoi(value); err == nil {
            return i
        }
    }
    return fallback
}
```

---

## What You Learned

Congratulations! You've implemented dependency injection. You now know:

- ✅ How to define singleton services
- ✅ How to register services with `Provide()`
- ✅ How to create request-scoped services
- ✅ How to inject services into handlers
- ✅ How to use DI in queue handlers and scheduled jobs
- ✅ How to manually resolve services
- ✅ Service lifecycle management
- ✅ Testing with dependency injection

---

## Next Steps

### Add Middleware & Authentication

Continue to [Middleware Tutorial →](06-middleware-auth.md) to learn how to add cross-cutting concerns like authentication and logging.

### Enhance Services

```go
// Add caching layer
type Cache struct {
    client *redis.Client
}

transire.Provide(func(cfg *Config) (*Cache, error) {
    client := redis.NewClient(&redis.Options{
        Addr: cfg.RedisURL,
    })
    return &Cache{client: client}, nil
})

// Use in handler
func getOrder(w http.ResponseWriter, r *http.Request, cache *Cache, db *Database) {
    // Try cache first
    if cached, err := cache.Get(id); err == nil {
        response.OK(w, cached)
        return
    }

    // Fall back to database
    order := db.GetOrder(id)
    cache.Set(id, order)
    response.OK(w, order)
}
```

### Add Service Middleware

```go
// Timing middleware for services
type TimedDatabase struct {
    db     *Database
    logger *Logger
}

func (t *TimedDatabase) Query(ctx context.Context, query string) {
    start := time.Now()
    defer func() {
        t.logger.Info(fmt.Sprintf("Query took %v", time.Since(start)))
    }()
    return t.db.Query(ctx, query)
}
```

---

## See Also

- [DI API Reference](../../reference/sdk/di-api/) - Complete DI documentation
- [Testing Guide](../../guides/testing/) - Test with DI
- [Configuration Guide](../../guides/configuration/) - Manage config
- [Middleware Tutorial](06-middleware-auth.md) - Add cross-cutting concerns
- [Production Guide](../../guides/deployment/production-checklist/) - Production patterns

