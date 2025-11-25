---
title: Extensibility | Transire
description: Extend Transire with chi middleware, custom queue senders, handler chaining, and your own dispatcher implementations.
keywords:
  - transire extensibility
  - chi middleware
  - go queue sender
  - dispatcher interface
  - handler chaining
---
# Extensibility

Transire stays close to idiomatic Go so you can extend it without ceremony.

## Use chi middleware and routes

`App.Router()` returns a real chi router. Add middleware, sub-routers, and route patterns as you would in any chi project.

```go
app := transire.New()
app.Router().Use(middleware.Logger, middleware.Recoverer)
app.Router().Route("/api", func(r chi.Router) {
    r.Get("/ping", func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte("pong"))
    })
})
```

## Chain work across handlers

Because every handler gets a `Queues` sender, you can compose flows:

- HTTP handlers enqueue background jobs.
- Queue handlers can emit to other queues for fan-out or auditing.
- Schedule handlers can seed periodic work or cleanup tasks.

Queue sends are asynchronous locally (goroutines) and durable in AWS (SQS), but the handler signatures stay identical.

## Swap queue senders

If you need to intercept or customize queue delivery (metrics, retries, alternate brokers), provide your own `QueueSender` and set it on the app:

```go
type metricsSender struct { next transire.QueueSender }
func (m metricsSender) Send(ctx context.Context, queue string, payload []byte) error {
    started := time.Now()
    err := m.next.Send(ctx, queue, payload)
    recordMetric(queue, time.Since(started), err)
    return err
}

app.SetQueueSender(metricsSender{next: app.QueueSender()})
```

## Build your own dispatcher

Dispatchers are small adapters with a `Run` method. The built-in ones cover local dev and AWS. If you need to target another runtime, implement the `Dispatcher` interface and wire it via `app.SetDispatcher`.

## Override environments

Use `TRANSIRE_DISPATCHER=aws|local` to force dispatcher selection, and keep `transire.yaml` lean with only names and regions. Everything else is discovered from your Go code, so adding new queues or schedules is as simple as registering another handler.
