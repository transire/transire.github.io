---
title: Core Concepts
category: introduction
complexity: beginner
duration: 10 minutes
mcp_use: reference
features_covered:
  - Handler types
  - Registration patterns
  - Build-time manifest
  - Local vs cloud runtime
  - Dependency injection
---

# Core Concepts

This guide explains the fundamental concepts behind Transire's architecture and programming model.

## Handler Types

Transire supports three types of handlers, each with a specific purpose:

### HTTP Handlers

Standard Go HTTP handlers for RESTful APIs:

```go
func getOrder(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")
    // ... fetch order
    response.OK(w, order)
}

app.GET("/orders/{id}", getOrder)
```

**Signature:** `func(w http.ResponseWriter, r *http.Request)`

**Key Points:**
- Uses standard Go `net/http` patterns - works with the entire Go ecosystem
- Chi router for path parameters (`{id}`, `{path+}`)
- Compatible with all Go HTTP middleware
- One Lambda handles all HTTP routes (mono-Lambda architecture)

### Queue Handlers

Type-safe batch processing for asynchronous work:

```go
func processOrders(ctx context.Context, orders []Order) error {
    for _, order := range orders {
        if err := process(ctx, order); err != nil {
            return err
        }
    }
    return nil
}

app.RegisterQueue("process-orders", processOrders)
```

**Signature:** `func(ctx context.Context, msgs []T) error`

**Key Points:**
- Always processes messages in batches (default batch size: 10)
- Type-safe: message type `T` is inferred at build time
- Automatic serialization/deserialization (JSON)
- Supports partial batch failures (per-message success/failure)
- Dead-letter queue (DLQ) for failed messages after max retries

### Scheduled Handlers

Cron-style scheduled jobs for periodic tasks:

```go
func generateReport(ctx context.Context) error {
    // Generate daily report
    return createReport(ctx)
}

app.Schedule("daily-report", "@daily 09:00", generateReport)
```

**Signature:** `func(ctx context.Context) error`

**Key Points:**
- Supports cron syntax and shorthand (`@hourly`, `@daily`, `@daily HH:MM`)
- Non-overlapping execution (local mode skips if previous run still active)
- Timezone-aware (configured in `transire.yaml`)
- Idempotent by design (no arguments, stateless)

## Registration Patterns

Transire uses **explicit registration** at application startup. No magic, no reflection at runtime.

### App-Based Architecture

All handlers register with a `transire.App` instance:

```go
package main

import (
    "github.com/transire/transire-sdk-go"
    "log"
)

func main() {
    // Create application
    app := transire.New()

    // Register handlers
    app.GET("/health", healthCheck)
    app.POST("/orders", createOrder)
    app.RegisterQueue("process-orders", processOrders)
    app.Schedule("daily-report", "@daily 09:00", generateReport)

    // Start application
    if err := app.Run(); err != nil {
        log.Fatal(err)
    }
}
```

### Registration Rules (MVP)

To ensure build-time analysis works correctly:

1. ✅ All registrations must be in `func main()` of `package main`
2. ✅ Handler functions must be defined in `package main`
3. ❌ No registrations in `init()` functions
4. ❌ No registrations in conditional blocks
5. ❌ No registrations in loops or closures

**Why these constraints?** Transire uses static analysis (Go AST) to discover handlers at build time. This enables type safety, validation, and infrastructure generation without runtime reflection.

## Build-Time Manifest

Transire analyzes your code at build time to generate a manifest:

### Generating the Manifest

```bash
$ transire gen
✓ Analyzed package main
✓ Found 5 HTTP routes
✓ Found 2 queue handlers
✓ Found 1 scheduled job
✓ Validated handler signatures
✓ Generated transire_manifest.json
```

### Manifest Structure

```json
{
  "version": "1.0",
  "service": "orders",
  "http_routes": [
    {
      "method": "GET",
      "path": "/orders/{id}",
      "handler": "getOrder"
    },
    {
      "method": "POST",
      "path": "/orders",
      "handler": "createOrder"
    }
  ],
  "queues": [
    {
      "key": "process-orders",
      "message_type": "github.com/acme/orders.Order",
      "handler": "processOrders",
      "batch_size": 10,
      "visibility_timeout_s": 30,
      "max_receive_count": 3
    }
  ],
  "schedules": [
    {
      "key": "daily-report",
      "schedule": "cron(0 9 * * ? *)",
      "handler": "generateReport",
      "timezone": "America/New_York"
    }
  ],
  "dependencies": ["OrderService", "PaymentService"],
  "permissions": ["sqs:SendMessage", "sqs:ReceiveMessage"]
}
```

### What the Manifest Enables

- **Type safety:** Validates handler signatures at build time
- **Infrastructure generation:** Automatically creates Lambda, API Gateway, SQS, EventBridge
- **IAM policies:** Generates least-privilege permissions
- **Local emulation:** Configures queue workers and schedulers
- **Documentation:** Self-documenting API from code

## Local vs. Cloud Runtime

Transire applications run in two modes with the **same code**:

### Local Mode (`transire run`)

```bash
$ transire run
✓ Starting HTTP server on :8080
✓ Queue emulator: 2 queues, 1 worker per queue
✓ Scheduler: 1 job (next run: 09:00 tomorrow)
→ Ready: http://localhost:8080
```

**Local Runtime:**
- **HTTP:** Chi HTTP server on `localhost:8080`
- **Queues:** In-memory queue with configurable workers (default: 1 per queue)
- **Scheduler:** Fixed-rate, non-overlapping execution
- **Purpose:** Development and testing

### Cloud Mode (`transire deploy`)

```bash
$ transire deploy
✓ Packaged 5 handlers
✓ Generated OpenTofu configuration
✓ Applied infrastructure
→ API URL: https://abc123.execute-api.us-east-1.amazonaws.com
```

**Cloud Runtime:**
- **HTTP:** API Gateway v2 (HTTP API) → Lambda with Chi router
- **Queues:** SQS → Lambda per queue (batch invocation)
- **Scheduler:** EventBridge rules → Lambda per schedule
- **Purpose:** Production deployment

### Parity Guarantees

Transire ensures key behaviors match between local and cloud:

| Feature | Local | Cloud | Parity |
|---------|-------|-------|--------|
| **Routing** | Chi router | Chi router in Lambda | ✅ Identical |
| **Message format** | JSON with `__type` | JSON with `__type` | ✅ Identical |
| **Error handling** | Panic recovery | Panic recovery | ✅ Identical |
| **Middleware** | Full chain | Full chain | ✅ Identical |
| **Context cancellation** | `ctx.Done()` | `ctx.Done()` | ✅ Identical |
| **Concurrency** | N workers | Auto-scaling | ⚠️ Different (by design) |
| **DLQ** | Logged | Real DLQ | ⚠️ Different (by design) |
| **Timeouts** | Graceful | Hard kill | ⚠️ Different (by design) |

**Philosophy:** Local is for development, cloud is source of truth. Use local for rapid iteration, cloud for production testing.

## Dependency Injection

Transire includes a simple, explicit DI system for managing services:

### Singleton Services

Created once per process (local) or cold start (cloud):

```go
package main

import (
    "github.com/transire/transire-sdk-go"
)

func main() {
    // Provide singleton
    transire.Provide(func(cfg *Config) (*OrderService, error) {
        db, err := connectDB(cfg.DatabaseURL)
        if err != nil {
            return nil, err
        }
        return &OrderService{DB: db}, nil
    })

    app := transire.New()
    // ... register handlers
    app.Run()
}

func getOrder(w http.ResponseWriter, r *http.Request) {
    // Access singleton
    svc := transire.MustGet[*OrderService](r.Context())
    order, err := svc.GetOrder(r.Context(), id)
    // ...
}
```

**Use cases:** Database connections, external API clients, shared caches

### Request-Scoped Services

Created once per invocation:

```go
// Provide request-scoped
transire.ProvideRequest(func(ctx context.Context, r *http.Request) (*RequestID, error) {
    id := transire.Header(r, "X-Request-ID")
    if id == "" {
        id = generateID()
    }
    return &RequestID{ID: id}, nil
})

func createOrder(w http.ResponseWriter, r *http.Request) {
    // Access request-scoped
    reqID := transire.MustGet[*RequestID](r.Context())
    log.Printf("Processing request %s", reqID.ID)
    // ...
}
```

**Use cases:** Request IDs, user context, per-request configuration

### Scope Lifetimes

| Scope | HTTP | Queue | Scheduled |
|-------|------|-------|-----------|
| **Singleton** | Once per process/cold start | Once per process/cold start | Once per process/cold start |
| **Request** | Once per request | Once per batch | Once per trigger |

**Important:** Queue handlers process batches, so request-scoped services are created **once per batch**, not per message.

## Type Safety

Transire enforces type safety at build time and runtime:

### Build-Time Validation

`transire gen` validates:

- ✅ Handler signatures match expected types
- ✅ Queue message types are concrete (no interfaces)
- ✅ HTTP paths are valid Chi syntax
- ✅ Schedule expressions are valid cron
- ✅ Dependencies are resolvable

**Example validation errors:**

```
E1001: Handler 'processOrders' not found in package main
E1002: Invalid signature for queue handler 'processOrders'
       Expected: func(ctx context.Context, msgs []Order) error
       Got:      func(ctx context.Context, msgs []*Order) error
E1005: Cannot infer message type for queue handler (interface type not supported)
```

### Runtime Type Safety

Queue messages include a `__type` field:

```json
{
  "__type": "github.com/acme/orders.Order",
  "order_id": "123",
  "amount": 99.99
}
```

**Type validation flow:**

1. Producer enqueues message → `__type` added automatically
2. Consumer receives message → validates `__type` matches handler's `T`
3. **Match:** Message processed normally
4. **Mismatch:** Message moved to DLQ with logged error

This prevents wrong-type enqueues and handles message schema evolution gracefully.

## Configuration

Transire uses a single `transire.yaml` file:

```yaml
version: 1
service: orders
runtime: go
cloud: aws
iac: opentofu
ci: github
timezone: America/New_York

deploy:
  arch: arm64
  memory_mb: 256
  timeout_s: 30

http:
  simulate_apigw_limits: true
  cors:
    enabled: true
    allow_origins: ["https://app.example.com"]

queues:
  max_batch_size: 10
  batch_window_s: 5
  visibility_timeout_s: 30
  max_receive_count: 3

observability:
  logging:
    level: info
    format: json
  tracing:
    enabled: false

env:
  - name: dev
    workspace: dev
    variables:
      DB_URL: postgres://localhost/orders_dev
  - name: prod
    workspace: prod
    variables:
      DB_URL: postgres://prod-db/orders
```

See [Config Schema Reference](../reference/config-schema.md) for complete schema.

## Next Steps

Now that you understand Transire's core concepts:

**[Quick Start →](../getting-started/quickstart.md){ .md-button .md-button--primary }**

Deploy your first app in 15 minutes with the Quick Start guide.

## See Also

- [HTTP Handlers](../sdk/http.md) - Complete HTTP handler reference
- [Queue Handlers](../sdk/queue.md) - Queue processing patterns
- [Scheduled Jobs](../sdk/schedule.md) - Scheduling and cron syntax
- [Dependency Injection](../sdk/di.md) - DI patterns and best practices
- [Config Schema](../reference/config-schema.md) - Complete configuration reference
