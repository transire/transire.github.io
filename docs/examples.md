---
title: Examples | Transire
description: Reference Transire example apps covering scaffold output, all handlers, CLI-driven flows, and queue fan-out.
keywords:
  - transire examples
  - go webapp samples
  - queue handler demos
  - schedule handler demos
---
# Examples

These examples live in the main repository under `examples/`.

## hello

- Path: `examples/hello`
- Purpose: scaffold output from `transire init` showing HTTP, queue, and schedule handlers that all enqueue work.
- Try it: `transire run --port 8080`, then `curl "http://localhost:8080/?msg=hi"`, `transire send work "manual message"`, `transire trigger heartbeat`.

## all-handlers

- Path: `examples/all-handlers`
- Purpose: exercises every handler type. HTTP enqueues work; queue handlers fan into `notifications` and `notification-log`; the heartbeat schedule also enqueues work.
- Try it: `transire run --port 8080`, `curl "http://localhost:8080/?msg=hello-local"`, watch logs for chained queue deliveries.

## all-handlers-cli

- Path: `examples/all-handlers-cli`
- Purpose: same flow as `all-handlers`, with CLI-driven docs for hitting HTTP, queues, and schedules from both local and AWS.
- Try it: `transire send work-events '{"source":"cli","detail":"local send"}'` and `transire trigger heartbeat` while the app is running locally.

## handler-chaining

- Path: `examples/handler-chaining`
- Purpose: demonstrates queue fan-out. HTTP, queue, and schedule handlers all enqueue `work`, which flows to `summary-log` and `log-stream`.
- Try it: `curl "http://localhost:8080/?msg=hi"` or `transire send work "manual message"`, then tail logs to watch the fan-out.
