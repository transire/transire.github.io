---
title: CLI Reference | Transire
description: Commands for the Transire CLI including init, run, build, deploy, info, send, trigger, and version.
keywords:
  - transire cli
  - go serverless commands
  - transire run
  - transire deploy
  - transire send
  - transire trigger
---
# CLI Reference

Transire ships a single binary, `transire`, built with Cobra. All commands honor `--verbose` for extra logging.

## init

```shell
transire init [path] --module <module-path>
```

- Creates a new Transire project in `path` (default: current directory).
- Fills in `cmd/app`, handler stubs, `transire.yaml`, and `go.mod` (module defaults to the directory name unless overridden).

## run

```shell
transire run [--port 8080] [--watch=true]
```

- Runs `go run ./cmd/app` with the local dispatcher.
- `--port` sets HTTP listen address (also honors `TRANSIRE_HTTP_ADDR`, `PORT`, `TRANSIRE_PORT`).
- `--watch` (default: true) restarts on Go/YAML changes.

## build

```shell
transire build [--manifest transire.yaml]
```

- Discovers queues and schedules by scanning your Go code.
- Compiles a Lambda bootstrap (`linux/amd64`) and writes a CDK app under `dist/aws`.
- Requires a main package at `./cmd/app`; move your entrypoint there if migrating an older project.

## deploy

```shell
transire deploy --env <name> [--profile transire-sandbox] [--manifest transire.yaml]
```

- Runs the build, installs CDK dependencies in `dist/aws/cdk`, and executes `npx cdk deploy --require-approval never`.
- `--env` is required; defaults to profile `transire-sandbox` and uses manifest regions unless overridden by `--region`.

## info

```shell
transire info [--env <name>] [--profile transire-sandbox]
```

- Always prints discovered queues and schedules from your code.
- When `--env` is provided, fetches CloudFormation outputs (API endpoint, queue URLs, schedule names) using the given profile/region.

## send

```shell
transire send <queue> <message> [--env local] [--base64]
```

- Validates the queue exists in the current project.
- Local/default: POSTs to `/_transire/queues/{name}` on the dev server.
- AWS: resolves queue URL from stack outputs and sends via SQS.
- `--base64` decodes the message before sending.

## trigger

```shell
transire trigger <schedule> [--env local]
```

- Validates the schedule exists in the project.
- Local/default: POSTs to `/_transire/schedules/{name}`.
- AWS: invokes the deployed Lambda with a fabricated EventBridge payload; schedule names come from stack outputs.

## version

```shell
transire version
```

Prints the CLI version string.
