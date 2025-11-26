---
title: Local Development | Transire
description: Run Transire locally with live reload, health endpoints, and in-process queues that mirror AWS behavior without extra tooling.
keywords:
  - transire local
  - go live reload
  - chi dev server
  - queue testing
  - dispatcher auto
---
# Local Development

Transire is tuned for fast feedback while keeping parity with AWS semantics.

## Run with live reload

```shell
transire run --port 8080 --watch=true
```

- Defaults to port 8080; override with `--port`, `TRANSIRE_PORT`, `PORT`, or `TRANSIRE_HTTP_ADDR`.
- `--watch` is enabled by default and restarts on Go/YAML changes (ignores `.git`, `dist`, `vendor`, `node_modules`).
- Runs `go run ./cmd/app`, so any code you add to `cmd/app` participates.
- `cmd/app` is required for `transire run|build|deploy`; if you started with an older layout, move your entrypoint to `./cmd/app`.

## Health and control endpoints

The local dispatcher mounts helpers under `/_transire`:

- `GET /_transire/health` — used by the CLI to confirm the dev server is running.
- `POST /_transire/queues/{name}` — sends a payload to a queue handler.
- `POST /_transire/schedules/{name}` — triggers a schedule handler immediately.

`transire send` and `transire trigger` call these for you when `--env` is omitted or set to `local`. They default to `http://localhost:8080`; if you run the dev server on another port, set `TRANSIRE_PORT` or `TRANSIRE_HTTP_ADDR` before calling the CLI so it hits the right place.

## Work with queues locally

Queue sends happen in-process using goroutines. That keeps logs close to your editor and mirrors production flow without needing Docker or localstack.

```shell
transire send work "manual message"
```

## Force dispatcher selection

By default, `dispatcher.Auto()` chooses local unless Lambda environment variables are present. Override when you need to mirror AWS behavior:

```shell
TRANSIRE_DISPATCHER=aws transire run
```

That forces the AWS dispatcher and expects Lambda-style environment variables to be set (e.g., `TRANSIRE_QUEUE_<NAME>_URL`).
