# API Reference

Complete Go API documentation for the Transire framework.

!!! tip "TL;DR"
    The Transire API consists of the App type for creating applications, handler interfaces (QueueHandler, SchedulerHandler), message types, and configuration structs. All types are in `github.com/transire/transire/pkg/transire`.

---

## Package Overview

**Import path:** `github.com/transire/transire/pkg/transire`

```go
import "github.com/transire/transire/pkg/transire"
```

---

## Core Types

### Application

| Type | Description | Documentation |
|------|-------------|---------------|
| [`App`](transire.md#app) | Main application container | [View →](transire.md#app) |
| [`New()`](transire.md#new) | Create new application | [View →](transire.md#new) |
| [`Router()`](transire.md#router) | Get Chi router | [View →](transire.md#router) |
| [`Run()`](transire.md#run) | Start application | [View →](transire.md#run) |

### Handlers

| Interface | Description | Documentation |
|-----------|-------------|---------------|
| [`QueueHandler`](handlers.md#queuehandler) | Process queue messages | [View →](handlers.md#queuehandler) |
| [`SchedulerHandler`](handlers.md#schedulerhandler) | Handle scheduled events | [View →](handlers.md#schedulerhandler) |

### Messages & Events

| Type | Description | Documentation |
|------|-------------|---------------|
| [`Message`](messages.md#message) | Queue message interface | [View →](messages.md#message) |
| [`ScheduleEvent`](messages.md#scheduleevent) | Scheduled event struct | [View →](messages.md#scheduleevent) |

### Configuration

| Type | Description | Documentation |
|------|-------------|---------------|
| [`Config`](config.md#config) | Application configuration | [View →](config.md#config) |
| [`QueueConfig`](config.md#queueconfig) | Queue handler config | [View →](config.md#queueconfig) |
| [`ScheduleConfig`](config.md#scheduleconfig) | Schedule handler config | [View →](config.md#scheduleconfig) |
| [`LambdaConfig`](config.md#lambdaconfig) | Lambda function config | [View →](config.md#lambdaconfig) |

---

## Quick Reference

### Creating an Application

```go
// Basic app
app := transire.New()

// With options
app := transire.New(
    transire.WithConfig(config),
    transire.WithProvider(provider),
)
```

### Registering Handlers

```go
// HTTP routes (via Chi)
r := app.Router()
r.Get("/health", healthHandler)

// Queue handler
app.RegisterQueueHandler(&EmailHandler{})

// Schedule handler
app.RegisterScheduleHandler(&CleanupHandler{})
```

### Running the Application

```go
if err := app.Run(context.Background()); err != nil {
    log.Fatal(err)
}
```

---

## Handler Interfaces

### QueueHandler

```go
type QueueHandler interface {
    HandleMessages(ctx context.Context, messages []Message) ([]string, error)
    QueueName() string
    Config() QueueConfig
}
```

**[Full documentation →](handlers.md#queuehandler)**

### SchedulerHandler

```go
type SchedulerHandler interface {
    HandleSchedule(ctx context.Context, event ScheduleEvent) error
    Schedule() string
    Name() string
    Config() ScheduleConfig
}
```

**[Full documentation →](handlers.md#schedulerhandler)**

---

## Message Types

### Message

```go
type Message interface {
    ID() string
    Body() []byte
    Attributes() map[string]string
    DeliveryCount() int
    EnqueuedAt() time.Time
}
```

**[Full documentation →](messages.md#message)**

### ScheduleEvent

```go
type ScheduleEvent struct {
    ScheduledTime time.Time
    Name          string
    Payload       []byte
    EventID       string
}
```

**[Full documentation →](messages.md#scheduleevent)**

---

## Configuration Types

### QueueConfig

```go
type QueueConfig struct {
    VisibilityTimeoutSeconds int
    MaxReceiveCount          int
    BatchSize                int
    WaitTimeSeconds          int
    FIFO                     bool
}
```

**[Full documentation →](config.md#queueconfig)**

### ScheduleConfig

```go
type ScheduleConfig struct {
    Timezone       string
    Enabled        bool
    TimeoutSeconds int
    RetryAttempts  int
    RetryDelay     time.Duration
}
```

**[Full documentation →](config.md#scheduleconfig)**

---

## See Also

- **[Detailed API Documentation](transire.md)** – Complete API reference
- **[Examples](../examples/)** – Code examples
- **[Guides](../guides/)** – Usage guides
- **[Configuration Reference](../configuration/)** – YAML configuration

---

## Source Code

View the source code on GitHub:

- [`pkg/transire/app.go`](https://github.com/transire/transire/blob/main/pkg/transire/app.go)
- [`pkg/transire/interfaces.go`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go)
- [`pkg/transire/config.go`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)
