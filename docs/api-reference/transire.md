---
title: "Package transire"
description: "Core Transire package with App, Runtime, and main types"
keywords:
  - package transire
  - App
  - Runtime
  - core types
  - api
category: api-reference
difficulty: intermediate
estimated_time: 10 minutes
prerequisites:
  - "Go basics"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Using core APIs"
    - "Understanding App"
    - "Runtime detection"
  common_questions:
    - "What is in package transire?"
    - "How do I use App?"
    - "What types are available?"
---

# Package transire

Main application API for creating and running Transire applications.

!!! tip "TL;DR"
    Create apps with `New()`, get the Chi router with `Router()`, register handlers with `RegisterQueueHandler()` and `RegisterScheduleHandler()`, then start with `Run()`.

---

## App

```go
type App struct {
    // contains filtered or unexported fields
}
```

The `App` type is the main application container. It holds:
- Chi router for HTTP routes
- Registered queue handlers
- Registered schedule handlers
- Application configuration
- Cloud provider (if configured)
- Runtime implementation

**Source:** [`pkg/transire/app.go:10-18`](https://github.com/transire/transire/blob/main/pkg/transire/app.go#L10-L18)

---

## New

```go
func New(opts ...Option) *App
```

Creates a new Transire application with optional configuration.

**Parameters:**
- `opts` – Variadic options for configuring the app

**Returns:** New `*App` instance

**Example:**
```go
// Basic app
app := transire.New()

// With config
app := transire.New(
    transire.WithConfig(myConfig),
)

// With provider
app := transire.New(
    transire.WithProvider(awsProvider),
)
```

**Source:** [`pkg/transire/app.go:21-32`](https://github.com/transire/transire/blob/main/pkg/transire/app.go#L21-L32)

---

## Option

```go
type Option func(*App)
```

Option is a function that configures an `App` instance.

### WithConfig

```go
func WithConfig(config *Config) Option
```

Sets the application configuration.

**Example:**
```go
config := &transire.Config{
    Name: "my-api",
    Lambda: transire.LambdaConfig{
        MemoryMB: 512,
        TimeoutSeconds: 30,
    },
}

app := transire.New(transire.WithConfig(config))
```

**Source:** [`pkg/transire/interfaces.go:104-108`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go#L104-L108)

### WithProvider

```go
func WithProvider(provider Provider) Option
```

Sets the cloud provider.

**Example:**
```go
provider := aws.NewProvider()
app := transire.New(transire.WithProvider(provider))
```

**Source:** [`pkg/transire/interfaces.go:97-101`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go#L97-L101)

---

## Router

```go
func (a *App) Router() *chi.Mux
```

Returns the Chi router for HTTP route registration. The returned router is a standard `chi.Mux` instance from `github.com/go-chi/chi/v5`.

**Returns:** `*chi.Mux` – Chi router instance

**Example:**
```go
app := transire.New()
r := app.Router()

// Use standard Chi methods
r.Use(middleware.Logger)
r.Get("/health", healthHandler)
r.Post("/users", createUserHandler)
```

**Source:** [`pkg/transire/app.go:35-37`](https://github.com/transire/transire/blob/main/pkg/transire/app.go#L35-L37)

---

## RegisterQueueHandler

```go
func (a *App) RegisterQueueHandler(handler QueueHandler)
```

Registers a queue handler for message processing.

**Parameters:**
- `handler` – Implementation of `QueueHandler` interface

**Example:**
```go
type EmailHandler struct{}

func (h *EmailHandler) QueueName() string {
    return "email-queue"
}

func (h *EmailHandler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        BatchSize: 10,
        VisibilityTimeoutSeconds: 30,
    }
}

func (h *EmailHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    // Process messages
    return nil, nil
}

app := transire.New()
app.RegisterQueueHandler(&EmailHandler{})
```

**Source:** [`pkg/transire/app.go:40-42`](https://github.com/transire/transire/blob/main/pkg/transire/app.go#L40-L42)

---

## RegisterScheduleHandler

```go
func (a *App) RegisterScheduleHandler(handler SchedulerHandler)
```

Registers a schedule handler for cron-based execution.

**Parameters:**
- `handler` – Implementation of `SchedulerHandler` interface

**Example:**
```go
type CleanupHandler struct{}

func (h *CleanupHandler) Name() string {
    return "daily-cleanup"
}

func (h *CleanupHandler) Schedule() string {
    return "0 2 * * *"  // Daily at 2 AM
}

func (h *CleanupHandler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        Timezone: "UTC",
        Enabled: true,
    }
}

func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    // Execute scheduled task
    return nil
}

app := transire.New()
app.RegisterScheduleHandler(&CleanupHandler{})
```

**Source:** [`pkg/transire/app.go:45-47`](https://github.com/transire/transire/blob/main/pkg/transire/app.go#L45-L47)

---

## Run

```go
func (a *App) Run(ctx context.Context) error
```

Starts the application in the detected runtime environment (local or cloud).

**Parameters:**
- `ctx` – Context for cancellation and timeout

**Returns:** `error` – Error if startup fails

**Behavior:**
1. Detects runtime environment (local vs Lambda vs other cloud)
2. Creates appropriate runtime adapter
3. Starts HTTP server (local) or Lambda handler (cloud)
4. Routes requests to registered handlers
5. Blocks until context is cancelled or error occurs

**Example:**
```go
app := transire.New()

// Register routes and handlers
r := app.Router()
r.Get("/health", healthHandler)
app.RegisterQueueHandler(&EmailHandler{})

// Start application
if err := app.Run(context.Background()); err != nil {
    log.Fatalf("Application failed: %v", err)
}
```

**Graceful Shutdown:**
```go
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

// Start app in goroutine
go func() {
    if err := app.Run(ctx); err != nil && err != context.Canceled {
        log.Printf("Application error: %v", err)
    }
}()

// Wait for interrupt signal
sigCh := make(chan os.Signal, 1)
signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)
<-sigCh

// Cancel context to trigger shutdown
cancel()
```

**Source:** [`pkg/transire/app.go:95-107`](https://github.com/transire/transire/blob/main/pkg/transire/app.go#L95-L107)

---

## Stop

```go
func (a *App) Stop(ctx context.Context) error
```

Gracefully stops the application.

**Parameters:**
- `ctx` – Context for timeout

**Returns:** `error` – Error if shutdown fails

**Example:**
```go
app := transire.New()

// Start app
go app.Run(context.Background())

// Stop app after some time
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

if err := app.Stop(ctx); err != nil {
    log.Printf("Shutdown error: %v", err)
}
```

**Source:** [`pkg/transire/app.go:110-115`](https://github.com/transire/transire/blob/main/pkg/transire/app.go#L110-L115)

---

## FindQueueHandler

```go
func (a *App) FindQueueHandler(queueName string) QueueHandler
```

Returns the handler for the specified queue name. Used internally by the runtime.

**Parameters:**
- `queueName` – Queue name to find

**Returns:** `QueueHandler` – Handler instance or `nil` if not found

**Source:** [`pkg/transire/app.go:50-57`](https://github.com/transire/transire/blob/main/pkg/transire/app.go#L50-L57)

---

## FindScheduleHandler

```go
func (a *App) FindScheduleHandler(scheduleName string) SchedulerHandler
```

Returns the handler for the specified schedule name. Used internally by the runtime.

**Parameters:**
- `scheduleName` – Schedule name to find

**Returns:** `SchedulerHandler` – Handler instance or `nil` if not found

**Source:** [`pkg/transire/app.go:60-67`](https://github.com/transire/transire/blob/main/pkg/transire/app.go#L60-L67)

---

## GetQueueHandlers

```go
func (a *App) GetQueueHandlers() []QueueHandler
```

Returns all registered queue handlers. Used by build tools for handler discovery.

**Returns:** `[]QueueHandler` – Slice of all queue handlers

**Source:** [`pkg/transire/app.go:70-72`](https://github.com/transire/transire/blob/main/pkg/transire/app.go#L70-L72)

---

## GetScheduleHandlers

```go
func (a *App) GetScheduleHandlers() []SchedulerHandler
```

Returns all registered schedule handlers. Used by build tools for handler discovery.

**Returns:** `[]SchedulerHandler` – Slice of all schedule handlers

**Source:** [`pkg/transire/app.go:75-77`](https://github.com/transire/transire/blob/main/pkg/transire/app.go#L75-L77)

---

## GetConfig

```go
func (a *App) GetConfig() *Config
```

Returns the application configuration.

**Returns:** `*Config` – Current configuration

**Source:** [`pkg/transire/app.go:80-82`](https://github.com/transire/transire/blob/main/pkg/transire/app.go#L80-L82)

---

## Next Steps

- **[Handler Interfaces](handlers.md)** – QueueHandler and SchedulerHandler
- **[Message Types](messages.md)** – Message and ScheduleEvent
- **[Configuration](config.md)** – Config structs
- **[Examples](../examples/)** – Code examples
