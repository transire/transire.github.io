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
If you run the dev server on a port other than 8080, set `TRANSIRE_PORT` before calling `transire send` or `transire trigger` so the CLI talks to the right localhost address.

## hello

- Path: `examples/hello`
- Purpose: scaffold output from `transire init` showing HTTP, queue, and schedule handlers that all enqueue work.
- Try it: `transire run --port 8080`, then `curl "http://localhost:8080/?msg=hi"`, `transire send work "manual message"`, `transire trigger heartbeat`.

## handlers-guide

- Path: `examples/handlers-guide`
- Purpose: doc-aligned walkthrough where HTTP, queue, and schedule handlers all enqueue to show queue sending from every handler type.
- Local: `transire run --port 8080`, `curl "http://localhost:8080/?msg=hi"`, `transire send work "manual message"`, `transire trigger heartbeat` (add `TRANSIRE_PORT` if you changed the port).
- AWS: `AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1 transire deploy --env dev --profile transire-sandbox`, fetch outputs with `transire info --env dev --profile transire-sandbox` (use the same region env if your AWS profile has no default), then curl the API endpoint and run `transire send ... --env dev --profile transire-sandbox` plus `transire trigger heartbeat --env dev --profile transire-sandbox` (optional: `aws logs tail /aws/lambda/transire-handlers-guide-lambda-dev --since 5m --profile transire-sandbox` to watch the queue chain).

## all-handlers

- Path: `examples/all-handlers`
- Purpose: exercises every handler type. HTTP enqueues work; queue handlers fan into `notifications` and `notification-log`; the heartbeat schedule also enqueues work.
- Try it: `transire run --port 8080`, `curl "http://localhost:8080/?msg=hello-local"`, watch logs for chained queue deliveries.

## all-handlers-cli

- Path: `examples/all-handlers-cli`
- Purpose: same flow as `all-handlers`, with CLI-driven docs for hitting HTTP, queues, and schedules from both local and AWS.
- Local: `transire run --port 8080`, then `curl "http://localhost:8080/?msg=hello-local"`, `transire send work-events '{"source":"cli","detail":"local send"}'`, and `transire trigger heartbeat`.
- AWS: `AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1 transire deploy --env dev --profile transire-sandbox`, fetch outputs with `transire info --env dev --profile transire-sandbox`, then call the API endpoint and use `transire send ... --env dev --profile transire-sandbox` plus `transire trigger heartbeat ...` to exercise queues and schedules (omit the env vars if your profile already has a default region).

## handler-chaining

- Path: `examples/handler-chaining`
- Purpose: demonstrates queue fan-out. HTTP, queue, and schedule handlers all enqueue `work`, which flows to `summary-log` and `log-stream`.
- Try it: `curl "http://localhost:8080/?msg=hi"` or `transire send work "manual message"`, then tail logs to watch the fan-out.
