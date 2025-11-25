---
title: Concepts | Transire
description: Core Transire model: chi router, queue handlers, schedule handlers, dispatchers, and build-time discovery that keeps Go code portable.
keywords:
  - transire concepts
  - go dispatcher
  - queue handlers
  - schedule handlers
  - chi middleware
  - serverless go patterns
---
# Concepts

The Transire surface area is intentionally small. Everything revolves around a Go `App`, a dispatcher, and three handler types.

## App

`transire.New()` returns an `App` that owns a chi router, queue handlers, schedules, and a queue sender. You register handlers once and then let a dispatcher feed them.

```go
app := transire.New()
app.Router().Use(middleware.Logger)

handlers.RegisterHTTP(app)
handlers.RegisterQueues(app)
handlers.RegisterSchedules(app)

d, _ := dispatcher.Auto()
app.SetDispatcher(d)
_ = app.Run(context.Background())
```

## HTTP handlers

- Use the chi router you already know: `app.Router().Get(...)`.
- `InjectContext` middleware decorates requests with a Transire context so handlers can enqueue work.

```go
app.Router().Get("/", func(w http.ResponseWriter, r *http.Request) {
    ctx, ok := transire.RequestContext(r)
    if !ok {
        http.Error(w, "missing transire context", http.StatusInternalServerError)
        return
    }
    _ = ctx.Queues.Send(r.Context(), "work", []byte("hello"))
    w.WriteHeader(http.StatusAccepted)
})
```

## Queue handlers

Queue handlers are registered by name and receive `transire.Message` values. Handlers can enqueue more messages through the same `Queues.Send` interface.

```go
app.RegisterQueueHandler("work", func(ctx transire.Context, msg transire.Message) error {
    log.Printf("work: %s", msg.Body)
    return ctx.Queues.Send(ctx, "audit-log", []byte("audit:"+string(msg.Body)))
})
```

## Schedule handlers

Schedules run on a fixed cadence. `Every` is a Go `time.Duration` and is discovered at build time to create EventBridge rules.

```go
app.RegisterScheduleHandler("heartbeat", time.Minute, func(ctx transire.Context, at time.Time) error {
    log.Printf("heartbeat at %s", at.UTC())
    return ctx.Queues.Send(ctx, "work", []byte(at.UTC().Format(time.RFC3339)))
})
```

## Context propagation

Every handler receives a Transire `Context` that wraps `context.Context` and carries a `Queues` sender. HTTP handlers pull it from requests via `RequestContext`; queue and schedule handlers get it directly.

## Dispatchers

Dispatchers adapt a runtime to your handlers:

- **Local dispatcher** runs an HTTP server (default `:8080`), handles queue sends in-process via goroutines, and exposes `_transire/health`, `_transire/queues/{name}`, and `_transire/schedules/{name}` endpoints for the CLI.
- **AWS dispatcher** binds API Gateway v2, SQS, and EventBridge into a single Lambda. Queue and schedule names are mapped back to your logical names via environment variables.
- **Auto selection** picks AWS inside Lambda or honors `TRANSIRE_DISPATCHER=aws|local`.

## Discovery over config

`transire build` walks your Go packages to find `RegisterQueueHandler` and `RegisterScheduleHandler` calls. The discovered layout informs the CDK app and environment variable wiring—no extra YAML required beyond `transire.yaml` for app/env names.
