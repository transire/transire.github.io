---
title: Transire | Go webapp framework for HTTP, queue, and schedule handlers
description: Cloud-agnostic Go framework that keeps chi routing, queue handlers, and schedule handlers portable between local dev and AWS.
keywords:
  - Go web framework
  - chi router
  - AWS Lambda
  - SQS queues
  - EventBridge schedules
  - serverless Go
  - queue handlers
  - schedule handlers
---
# Transire

<div class="hero">
  <p class="eyebrow">Go-native, cloud-agnostic webapp framework</p>
  <h1>Build HTTP, queue, and schedule handlers with three commands.</h1>
  <p class="lede">Zero boilerplate. Chi-compatible routing. Queues and schedules that stay portable across local dev and AWS. Ship the idiomatic Go you already write.</p>
  <div class="hero-actions">
    <a class="cta" href="quickstart/">Start now</a>
    <a class="ghost" href="concepts/">See how it works</a>
  </div>
</div>

## Three commands to production

```shell
transire init my-app
cd my-app
transire run --port 8080           # dev server + live reload
transire deploy --profile <aws-profile> --env dev
```

- **One runtime, two dispatchers.** Local HTTP + in-memory queues for fast feedback; the same code runs behind Lambda, API Gateway, SQS, and EventBridge when deployed.
- **No handler config files.** Transire discovers `RegisterQueueHandler` and `RegisterScheduleHandler` calls in your Go code at build time and wires AWS resources automatically.
- **Go-first ergonomics.** Bring your chi middleware, work with `context.Context`, and keep handlers small, testable functions.
- **Queue access everywhere.** Every handler receives a Transire `Context` that exposes `Queues.Send` so HTTP, queues, and schedules can chain work.
- **AWS ready.** `transire build` emits a Lambda bootstrap and CDK app; `transire deploy` drives CDK with your profiles and envs.

## A minimal app (real scaffold)

```go
// cmd/app/main.go
func main() {
    app := transire.New()
    app.Router().Use(middleware.Logger)

    app.Router().Get("/", func(w http.ResponseWriter, r *http.Request) {
        ctx, _ := transire.RequestContext(r)
        _ = ctx.Queues.Send(r.Context(), "work", []byte("hello from http"))
        w.WriteHeader(http.StatusAccepted)
    })

    app.RegisterQueueHandler("work", func(ctx transire.Context, msg transire.Message) error {
        log.Printf("work received: %s", msg.Body)
        return nil
    })

    app.RegisterScheduleHandler("heartbeat", time.Minute, func(ctx transire.Context, at time.Time) error {
        return ctx.Queues.Send(ctx, "work", []byte(at.UTC().Format(time.RFC3339)))
    })

    d, _ := dispatcher.Auto()
    app.SetDispatcher(d)
    _ = app.Run(context.Background())
}
```

One file, three handlers, zero config beyond the scaffolded `transire.yaml`. Add chi middleware, more routes, or more queues/schedules as you go.

Want to see it in action? Check `examples/hello` for the scaffold output or jump to [Examples](examples.md).
