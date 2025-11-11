---
title: "Dependency Injection"
category: sdk
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - Go 1.22+
  - Understanding of dependency injection concepts
mcp_use: reference
mcp_operations:
  - add_di_provider
  - inject_dependencies
features_covered:
  - Singleton dependencies
  - Request-scoped dependencies
  - Dependency access
  - Lifecycle management
code_blocks: true
last_updated: 2025-10-30
---

# Dependency Injection

## Overview

Transire provides a simple, type-safe dependency injection (DI) system for managing application dependencies. It supports two scopes:

- **Singleton** - Created once per process (local) or cold start (cloud)
- **Request-scoped** - Created per invocation (HTTP request, queue batch, or scheduled trigger)

**Key features:**
- Type-safe with Go generics
- Explicit provider functions (no magic, no reflection)
- Automatic lifecycle management
- Works with middleware and handlers

## Why Use DI?

Dependency injection helps you:

- **Avoid globals** - Pass dependencies explicitly
- **Enable testing** - Easily mock dependencies
- **Manage resources** - Centralize database connections, clients, etc.
- **Share state** - Request-scoped values (request ID, user context, etc.)

## Singleton Dependencies

Singletons are created once and shared across all invocations:

```go
import (
    "context"
    "os"
    "github.com/transire/sdk-go"
)

type OrderService struct {
    DB *Database
}

func main() {
    // Register singleton provider
    transire.Provide(func(ctx context.Context) (*OrderService, error) {
        db, err := connectDatabase(os.Getenv("DB_URL"))
        if err != nil {
            return nil, err
        }

        return &OrderService{DB: db}, nil
    })

    app := transire.New()
    app.GET("/orders", listOrders)
    app.Run()
}

func listOrders(w http.ResponseWriter, r *http.Request) {
    // Access singleton
    svc, err := transire.Get[*OrderService](r.Context())
    if err != nil {
        response.InternalServerError(w, "Failed to get service")
        return
    }

    orders, err := svc.ListOrders(r.Context())
    if err != nil {
        response.InternalServerError(w, "Failed to list orders")
        return
    }

    response.OK(w, orders)
}
```

### When to Use Singletons

Use singletons for:
- **Database connections** - Reuse connection pools
- **HTTP clients** - Reuse connections
- **Configuration** - Load once, use everywhere
- **Caches** - In-memory caches shared across requests
- **External service clients** - Third-party API clients, SDK clients, etc.

## Request-Scoped Dependencies

Request-scoped dependencies are created per invocation:

```go
import (
    "context"
    "net/http"
    "github.com/transire/sdk-go"
)

type RequestID struct {
    ID string
}

func main() {
    // Register request-scoped provider
    transire.ProvideRequest(func(ctx context.Context, r *http.Request) (*RequestID, error) {
        id := transire.Header(r, "X-Request-Id")
        if id == "" {
            id = generateUUID()
        }

        return &RequestID{ID: id}, nil
    })

    app := transire.New()
    app.GET("/orders", listOrders)
    app.Run()
}

func listOrders(w http.ResponseWriter, r *http.Request) {
    // Access request-scoped dependency
    reqID, err := transire.Get[*RequestID](r.Context())
    if err != nil {
        response.InternalServerError(w, "Failed to get request ID")
        return
    }

    log.Printf("[%s] Listing orders", reqID.ID)

    // ... business logic

    response.OK(w, orders)
}
```

### When to Use Request-Scoped

Use request-scoped dependencies for:
- **Request context** - Request ID, correlation ID, trace ID
- **User context** - Authenticated user, permissions
- **Request-specific clients** - Clients with request-specific headers
- **Scoped caches** - Request-local caching

### Request-Scoped Lifecycle

Request-scoped instances are created before middleware and handlers run:

| Handler Type | Scope |
|--------------|-------|
| **HTTP** | One instance per HTTP request |
| **Queue** | One instance per batch (NOT per message) |
| **Scheduled** | One instance per trigger |

**Important:** In queue handlers, all messages in a batch share the same request-scoped instances.

## Accessing Dependencies

Use `transire.Get` or `transire.MustGet` to access dependencies:

### Safe Access with `Get`

```go
// Returns (value, error)
svc, err := transire.Get[*OrderService](ctx)
if err != nil {
    // Handle missing dependency
    return err
}

// Use svc
orders, err := svc.ListOrders(ctx)
```

### Panic on Missing with `MustGet`

```go
// Panics if dependency is missing (panic is recovered and logged)
svc := transire.MustGet[*OrderService](ctx)

// Use svc directly
orders, err := svc.ListOrders(ctx)
```

**When to use `MustGet`:**
- When dependency is required for handler to function
- Cleaner code (no error handling)
- Panic is recovered by framework and logged as 500

## Complete Example

Here's a complete example with multiple dependencies:

```go
package main

import (
    "context"
    "encoding/json"
    "log"
    "net/http"
    "os"
    "github.com/transire/sdk-go"
    "github.com/transire/sdk-go/response"
)

// Singleton dependencies
type Database struct {
    // Database connection pool
}

type EmailService struct {
    // Email client
}

type OrderService struct {
    DB    *Database
    Email *EmailService
}

// Request-scoped dependencies
type RequestContext struct {
    RequestID string
    UserID    string
}

func main() {
    // Register singleton providers
    transire.Provide(func(ctx context.Context) (*Database, error) {
        db, err := connectDatabase(os.Getenv("DB_URL"))
        if err != nil {
            return nil, err
        }
        log.Println("Database connected")
        return db, nil
    })

    transire.Provide(func(ctx context.Context) (*EmailService, error) {
        email := &EmailService{
            APIKey: os.Getenv("EMAIL_API_KEY"),
        }
        log.Println("Email service initialized")
        return email, nil
    })

    transire.Provide(func(ctx context.Context) (*OrderService, error) {
        // Dependencies can depend on other dependencies
        db := transire.MustGet[*Database](ctx)
        email := transire.MustGet[*EmailService](ctx)

        return &OrderService{
            DB:    db,
            Email: email,
        }, nil
    })

    // Register request-scoped provider
    transire.ProvideRequest(func(ctx context.Context, r *http.Request) (*RequestContext, error) {
        requestID := transire.Header(r, "X-Request-Id")
        if requestID == "" {
            requestID = generateUUID()
        }

        // Extract user from auth token (example)
        userID := extractUserFromAuth(r)

        return &RequestContext{
            RequestID: requestID,
            UserID:    userID,
        }, nil
    })

    // Create app and register routes
    app := transire.New()
    app.POST("/orders", createOrder)
    app.GET("/orders/{id}", getOrder)
    app.Run()
}

func createOrder(w http.ResponseWriter, r *http.Request) {
    // Access dependencies
    svc := transire.MustGet[*OrderService](r.Context())
    reqCtx := transire.MustGet[*RequestContext](r.Context())

    log.Printf("[%s] Creating order for user %s", reqCtx.RequestID, reqCtx.UserID)

    // Parse request
    var req CreateOrderRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        response.BadRequest(w, "Invalid JSON")
        return
    }

    // Create order using service
    order, err := svc.CreateOrder(r.Context(), reqCtx.UserID, req.Items)
    if err != nil {
        log.Printf("[%s] ERROR: Failed to create order: %v", reqCtx.RequestID, err)
        response.InternalServerError(w, "Failed to create order")
        return
    }

    // Send confirmation email (async, best-effort)
    go func() {
        if err := svc.SendOrderConfirmation(context.Background(), order); err != nil {
            log.Printf("Warning: Failed to send confirmation email: %v", err)
        }
    }()

    log.Printf("[%s] Order created: %s", reqCtx.RequestID, order.ID)
    response.Created(w, order)
}

func getOrder(w http.ResponseWriter, r *http.Request) {
    svc := transire.MustGet[*OrderService](r.Context())
    reqCtx := transire.MustGet[*RequestContext](r.Context())

    orderID := transire.URLParam(r, "id")
    log.Printf("[%s] Fetching order %s", reqCtx.RequestID, orderID)

    order, err := svc.GetOrder(r.Context(), orderID)
    if err != nil {
        response.NotFound(w, "Order not found")
        return
    }

    // Verify user owns this order
    if order.UserID != reqCtx.UserID {
        response.Text(w, http.StatusForbidden, "Access denied")
        return
    }

    response.OK(w, order)
}

// OrderService methods
func (s *OrderService) CreateOrder(ctx context.Context, userID string, items []Item) (*Order, error) {
    // Create order in database
    order := &Order{
        ID:     generateUUID(),
        UserID: userID,
        Items:  items,
        Status: "pending",
    }

    if err := s.DB.Insert(ctx, order); err != nil {
        return nil, err
    }

    return order, nil
}

func (s *OrderService) GetOrder(ctx context.Context, orderID string) (*Order, error) {
    return s.DB.GetOrder(ctx, orderID)
}

func (s *OrderService) SendOrderConfirmation(ctx context.Context, order *Order) error {
    subject := "Order Confirmation"
    body := "Your order has been created successfully"
    return s.Email.Send(ctx, order.UserEmail, subject, body)
}
```

## Provider Chaining

Providers can depend on other dependencies:

```go
func main() {
    // Provider 1: Database
    transire.Provide(func(ctx context.Context) (*Database, error) {
        return connectDatabase(os.Getenv("DB_URL"))
    })

    // Provider 2: Cache (depends on Database)
    transire.Provide(func(ctx context.Context) (*Cache, error) {
        db := transire.MustGet[*Database](ctx)
        return newCache(db), nil
    })

    // Provider 3: Service (depends on both)
    transire.Provide(func(ctx context.Context) (*OrderService, error) {
        db := transire.MustGet[*Database](ctx)
        cache := transire.MustGet[*Cache](ctx)
        return &OrderService{DB: db, Cache: cache}, nil
    })
}
```

## Initialization Order

Singletons are initialized lazily on first access:

1. Handler calls `transire.Get[*OrderService](ctx)`
2. If `*OrderService` doesn't exist, run its provider
3. Provider calls `transire.Get[*Database](ctx)`
4. If `*Database` doesn't exist, run its provider
5. Return `*Database` to `*OrderService` provider
6. Return `*OrderService` to handler

**Circular dependencies are not detected and will cause a deadlock.**

## Resource Cleanup

Use `context.Context` for resource cleanup:

```go
transire.Provide(func(ctx context.Context) (*Database, error) {
    db, err := connectDatabase(os.Getenv("DB_URL"))
    if err != nil {
        return nil, err
    }

    // Cleanup on context cancellation
    go func() {
        <-ctx.Done()
        log.Println("Closing database connection")
        db.Close()
    }()

    return db, nil
})
```

For request-scoped resources, cleanup happens automatically after handler completion.

## Error Handling

If a provider returns an error:

```go
transire.Provide(func(ctx context.Context) (*Database, error) {
    db, err := connectDatabase(os.Getenv("DB_URL"))
    if err != nil {
        return nil, err  // Application fails to start
    }
    return db, nil
})
```

- **Singleton error:** Application fails to start
- **Request-scoped error:** Request fails with 500

## Testing

Mock dependencies in tests:

```go
package main

import (
    "context"
    "testing"
    "github.com/transire/sdk-go/testkit"
)

func TestCreateOrder(t *testing.T) {
    // Create mock database
    mockDB := &MockDatabase{
        orders: make(map[string]*Order),
    }

    // Register mock as singleton
    transire.Provide(func(ctx context.Context) (*Database, error) {
        return mockDB, nil
    })

    // Test handler
    app := testkit.App()
    app.POST("/orders", createOrder)

    server := app.Start(t)
    defer server.Stop()

    // Make request
    resp := server.POST("/orders", CreateOrderRequest{
        Items: []Item{{ProductID: "123", Quantity: 1}},
    })

    if resp.StatusCode != 201 {
        t.Errorf("Expected 201, got %d", resp.StatusCode)
    }
}

type MockDatabase struct {
    orders map[string]*Order
}

func (m *MockDatabase) Insert(ctx context.Context, order *Order) error {
    m.orders[order.ID] = order
    return nil
}

func (m *MockDatabase) GetOrder(ctx context.Context, id string) (*Order, error) {
    return m.orders[id], nil
}
```

## Best Practices

### Keep Providers Simple

```go
// ✅ GOOD: Simple provider
transire.Provide(func(ctx context.Context) (*Database, error) {
    return connectDatabase(os.Getenv("DB_URL"))
})

// ❌ BAD: Complex initialization
transire.Provide(func(ctx context.Context) (*Database, error) {
    db, _ := connectDatabase(os.Getenv("DB_URL"))
    // Don't do complex setup here
    db.RunMigrations()  // NO!
    db.SeedData()       // NO!
    return db, nil
})
```

### Avoid Side Effects in Request-Scoped Providers

```go
// ✅ GOOD: Read-only
transire.ProvideRequest(func(ctx context.Context, r *http.Request) (*RequestID, error) {
    id := transire.Header(r, "X-Request-Id")
    return &RequestID{ID: id}, nil
})

// ❌ BAD: Side effects
transire.ProvideRequest(func(ctx context.Context, r *http.Request) (*RequestID, error) {
    id := transire.Header(r, "X-Request-Id")
    db.LogRequest(id)  // NO! Side effect in provider
    return &RequestID{ID: id}, nil
})
```

### Use Interfaces for Testing

```go
// Define interface
type OrderRepository interface {
    CreateOrder(ctx context.Context, order *Order) error
    GetOrder(ctx context.Context, id string) (*Order, error)
}

// Production implementation
type PostgresOrderRepository struct {
    DB *Database
}

func (r *PostgresOrderRepository) CreateOrder(ctx context.Context, order *Order) error {
    return r.DB.Insert(ctx, order)
}

// Provide interface
transire.Provide(func(ctx context.Context) (OrderRepository, error) {
    db := transire.MustGet[*Database](ctx)
    return &PostgresOrderRepository{DB: db}, nil
})

// Easy to mock in tests
type MockOrderRepository struct {
    orders map[string]*Order
}

func (m *MockOrderRepository) CreateOrder(ctx context.Context, order *Order) error {
    m.orders[order.ID] = order
    return nil
}
```

### Don't Over-DI

Not everything needs DI:

```go
// ✅ GOOD: Simple function, no DI needed
func validateEmail(email string) bool {
    return strings.Contains(email, "@")
}

// ❌ BAD: Unnecessary DI
type EmailValidator struct{}
func (v *EmailValidator) Validate(email string) bool {
    return strings.Contains(email, "@")
}
transire.Provide(func(ctx context.Context) (*EmailValidator, error) {
    return &EmailValidator{}, nil  // Pointless
})
```

Use DI for:
- Resources with lifecycle (connections, clients)
- Stateful services
- Things you want to mock in tests

## Common Patterns

### Database Connection

```go
transire.Provide(func(ctx context.Context) (*Database, error) {
    db, err := sql.Open("postgres", os.Getenv("DB_URL"))
    if err != nil {
        return nil, err
    }

    if err := db.Ping(); err != nil {
        return nil, err
    }

    return &Database{DB: db}, nil
})
```

### HTTP Client with Retry

```go
transire.Provide(func(ctx context.Context) (*PaymentClient, error) {
    client := &http.Client{
        Timeout: 30 * time.Second,
        Transport: &retryTransport{
            MaxRetries: 3,
        },
    }

    return &PaymentClient{
        BaseURL: os.Getenv("PAYMENT_API_URL"),
        Client:  client,
    }, nil
})
```

### User Context from Auth Token

```go
transire.ProvideRequest(func(ctx context.Context, r *http.Request) (*UserContext, error) {
    token := transire.Header(r, "Authorization")
    if token == "" {
        return nil, errors.New("missing auth token")
    }

    user, err := validateToken(token)
    if err != nil {
        return nil, err
    }

    return &UserContext{
        UserID: user.ID,
        Email:  user.Email,
        Roles:  user.Roles,
    }, nil
})
```

## See Also

- [HTTP Handlers](/sdk/http.md) - Using DI in HTTP handlers
- [Queue Handlers](/sdk/queue.md) - Using DI in queue handlers
- [Scheduled Jobs](/sdk/schedule.md) - Using DI in scheduled jobs
- [Middleware](/sdk/middleware.md) - Using DI in middleware
- [Testing](/sdk/testkit.md) - Mocking dependencies in tests
