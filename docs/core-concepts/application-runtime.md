---
title: "Application & Runtime"
description: "Understanding Transire's App abstraction and automatic runtime detection for local and cloud deployment"
keywords:
  - application
  - runtime
  - app
  - transire.New
  - runtime detection
  - local development
  - lambda
  - chi router
category: core-concepts
difficulty: intermediate
estimated_time: 10 minutes
prerequisites:
  - "Completed Quickstart"
  - "Basic Go knowledge"
related_docs:
  - path: "/getting-started/quickstart/"
    relationship: "prerequisite"
  - path: "/core-concepts/http-handlers/"
    relationship: "next_step"
  - path: "/guides/local-development/"
    relationship: "deep_dive"
mcp_metadata:
  primary_use_cases:
    - "Understanding how Transire apps work"
    - "Learning about runtime detection"
    - "Understanding local vs cloud execution"
  common_questions:
    - "How does Transire detect runtime?"
    - "What is the App abstraction?"
    - "How does the same code run locally and on Lambda?"
    - "What methods are available on App?"
---

# Application & Runtime

Learn how Transire's App abstraction and runtime detection enable your Go code to run locally and on AWS Lambda without changes.

!!! tip "TL;DR"
    The `transire.App` is your application container. It holds your Chi router, handlers, and configuration. When you call `app.Run()`, Transire automatically detects whether you're running locally or on Lambda and adapts accordingly.

---

## The `App` Abstraction

The `transire.App` is your application container. It holds your Chi router, queue handlers, schedule handlers, and configuration.

### Creating an App

```go
app := transire.New()
```

Source: [`pkg/transire/app.go:New`](https://github.com/transire/transire/blob/main/pkg/transire/app.go)

---

## Key Methods

| Method | Returns | Purpose | Source |
|--------|---------|---------|--------|
| `Router()` | `*chi.Mux` | Get the Chi router for HTTP route registration | [`pkg/transire/app.go:Router`](https://github.com/transire/transire/blob/main/pkg/transire/app.go) |
| `RegisterQueueHandler(QueueHandler)` | – | Register a queue message processor | [`pkg/transire/app.go:RegisterQueueHandler`](https://github.com/transire/transire/blob/main/pkg/transire/app.go) |
| `RegisterScheduleHandler(SchedulerHandler)` | – | Register a scheduled task | [`pkg/transire/app.go:RegisterScheduleHandler`](https://github.com/transire/transire/blob/main/pkg/transire/app.go) |
| `Run(context.Context)` | `error` | Start the app (detects runtime automatically) | [`pkg/transire/app.go:Run`](https://github.com/transire/transire/blob/main/pkg/transire/app.go) |

---

## Runtime Detection

Transire automatically detects where your app is running and adapts behavior accordingly.

### Detection Logic

From [`pkg/transire/runtime.go`](https://github.com/transire/transire/blob/main/pkg/transire/runtime.go):

1. **Check `AWS_LAMBDA_FUNCTION_NAME` environment variable**
   - If set → use `RuntimeAWSLambda`
2. **Check `K_SERVICE` environment variable**
   - If set → use `RuntimeGCPRun` (future support)
3. **Default**
   - Use `RuntimeLocal`

```go
// Simplified from pkg/transire/runtime.go
func detectRuntime() Runtime {
    if os.Getenv("AWS_LAMBDA_FUNCTION_NAME") != "" {
        return RuntimeAWSLambda
    }
    if os.Getenv("K_SERVICE") != "" {
        return RuntimeGCPRun
    }
    return RuntimeLocal
}
```

---

## Local Runtime

**Source:** [`pkg/transire/local_runtime.go`](https://github.com/transire/transire/blob/main/pkg/transire/local_runtime.go)

When running locally, Transire provides:

### HTTP Server
- Starts on port **3000** (configurable via `transire.yaml`)
- Uses your Chi router directly
- Supports all standard middleware and routing

### Queue Simulator
- Runs on port **4000** (configurable)
- Test queue handlers using the CLI:
  ```bash
  transire dev queues send {queue-name} '{json-message}'
  ```
- Messages are delivered to your `QueueHandler` implementations
- [:octicons-arrow-right-24: Learn more about queue testing](../cli-reference/transire-dev.md#queue-commands)

### Schedule Simulator
- Runs on port **5000** (configurable)
- Trigger scheduled tasks manually using the CLI:
  ```bash
  transire dev schedules execute {schedule-name}
  ```
- Useful for testing cron jobs without waiting
- [:octicons-arrow-right-24: Learn more about schedule testing](../cli-reference/transire-dev.md#schedule-commands)

### Hot Reload
- Watches `*.go` and `*.yaml` files for changes
- Automatically rebuilds and restarts your app
- Implemented via [`internal/cli/runner/`](https://github.com/transire/transire/blob/main/internal/cli/runner/) using [`github.com/fsnotify/fsnotify`](https://github.com/fsnotify/fsnotify)

---

## AWS Lambda Runtime

**Source:** [`pkg/transire/lambda_runtime.go`](https://github.com/transire/transire/blob/main/pkg/transire/lambda_runtime.go)

When running on AWS Lambda, Transire:

### Adapts Lambda Events

**API Gateway events** → Your Chi router:
- HTTP requests from API Gateway are converted to standard `http.Request`
- Routed through your Chi router
- Response converted back to API Gateway format

**SQS events** → Your `QueueHandler`:
- SQS batch events are converted to `[]Message`
- Delivered to the appropriate `QueueHandler` based on queue name
- Failed message IDs are returned for retry (partial batch failure support)

**EventBridge events** → Your `SchedulerHandler`:
- EventBridge scheduled events trigger your `SchedulerHandler`
- Event metadata (scheduled time, name) passed to your handler

### Event Routing

Transire examines the incoming Lambda event JSON and routes it automatically:

```go
// Simplified from pkg/transire/lambda_runtime.go
func (h *Handler) Handle(ctx context.Context, event json.RawMessage) (interface{}, error) {
    if isAPIGatewayEvent(event) {
        return h.handleHTTP(ctx, event)
    } else if isSQSEvent(event) {
        return h.handleQueue(ctx, event)
    } else if isEventBridgeEvent(event) {
        return h.handleSchedule(ctx, event)
    }
    return nil, fmt.Errorf("unknown event type")
}
```

---

## Example: Same Code, Different Runtimes

This single application works everywhere:

```go
// From examples/simple-api/main.go
package main

import (
    "context"
    "net/http"

    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
    "github.com/transire/transire/pkg/transire"
)

func main() {
    app := transire.New()
    r := app.Router()

    r.Use(middleware.Logger)
    r.Get("/health", healthHandler)

    app.RegisterQueueHandler(&EmailQueueHandler{})

    // This single line works everywhere
    app.Run(context.Background())
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("OK"))
}
```

### How it works

When you call `app.Run(context.Background())`, Transire:

1. **Detects the runtime** (local vs Lambda)
2. **Starts the appropriate adapter**
   - Local: Starts HTTP server + simulators
   - Lambda: Starts Lambda event handler
3. **Routes events to your handlers**
   - HTTP requests → Chi router
   - SQS messages → QueueHandler
   - EventBridge events → SchedulerHandler

**No code changes required** to move from local → Lambda.

---

## Configuration

Control runtime behavior via `transire.yaml`:

```yaml
# Development settings (local runtime only)
development:
  http_port: 3000
  queue_port: 4000
  auto_reload: true
  log_level: debug

# Lambda settings (cloud runtime only)
lambda:
  architecture: arm64
  timeout_seconds: 30
  memory_mb: 256
```

See the complete [Configuration Reference](../configuration/transire-yaml.md) for all options.

---

## Runtime Comparison

| Feature | Local Runtime | Lambda Runtime |
|---------|---------------|----------------|
| **HTTP** | HTTP server on port 3000 | API Gateway → Lambda |
| **Queues** | REST simulator on port 4000 | SQS → Lambda |
| **Schedules** | REST simulator on port 4000 | EventBridge → Lambda |
| **Hot Reload** | ✅ Yes (via fsnotify) | ❌ N/A |
| **Auto-scaling** | ❌ Single process | ✅ AWS handles it |
| **Cold starts** | ❌ N/A | ✅ Yes (minimize with ARM64) |
| **Cost** | $0 (runs locally) | AWS Lambda pricing |

---

## Next Steps

### Learn About Handlers

Now that you understand the App and Runtime, learn about the handler interfaces:

- [HTTP Handlers](http-handlers.md) – Using Chi router
- [Queue Handlers](queue-handlers.md) – Processing messages in batches
- [Schedule Handlers](schedule-handlers.md) – Running cron jobs

### Dive Into Guides

- [Local Development](../guides/local-development.md) – Best practices for local dev
- [Deploying to AWS](../guides/deploying-to-aws.md) – Deploy to Lambda
- [Testing](../guides/testing.md) – Test your application

### Explore API Reference

- [App API Reference](../api-reference/transire.md) – Complete API docs
- [Runtime Interface](../api-reference/transire.md#runtime) – Runtime interface details
