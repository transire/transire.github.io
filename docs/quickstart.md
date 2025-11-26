---
title: Quickstart | Transire
description: Install the Transire CLI, scaffold a Go app, run locally with live reload, and deploy to AWS in minutes.
keywords:
  - transire quickstart
  - go webapp scaffold
  - serverless go deploy
  - chi router
  - aws lambda api gateway
---
# Quickstart

Short path for Go developers who want to see Transire working end-to-end.

## Prerequisites

- Go 1.25+ for your project.
- Node.js/npm for AWS CDK deployment.
- AWS CLI credentials with a bootstrapped CDK account (any profile name works).

## Install the CLI

```shell
go install github.com/transire/transire/cmd/transire@latest
```

## Scaffold a new app

```shell
transire init my-app
cd my-app
```

The scaffold gives you:

- `cmd/app/main.go` that wires the chi router, handlers, and dispatcher auto-selection.
- HTTP handler that enqueues work, queue handlers that chain into an audit queue, and a heartbeat schedule.
- `transire.yaml` with an app name and an example `dev` environment (optionally pin an AWS profile per env; regions use the AWS SDK default chain).
- `cmd/app` is required for `transire run|build|deploy`; if you started with an older layout, move your entrypoint to `./cmd/app`.

## Run locally

```shell
transire run --port 8080   # defaults to --watch
```

- Hit HTTP: `curl "http://localhost:8080/?msg=hi"` (enqueues a queue message).
- Send directly to a queue: `transire send work "manual message"`.
- Trigger the schedule: `transire trigger heartbeat`.

If you change the port, set `TRANSIRE_PORT` before calling `transire send` or `transire trigger` so the CLI hits the right host.

`--watch` is on by default; change Go or YAML files and Transire restarts the app.

## Deploy to AWS

```shell
transire deploy --profile <aws-profile> --env dev
```

What happens:

1. `transire build` compiles a Lambda bootstrap for `linux/amd64` and generates a CDK app under `dist/aws/cdk`.
2. CDK provisions API Gateway v2, an SQS queue per discovered handler, EventBridge schedules, and a single Lambda that fans events into your handlers.
3. Outputs include the API endpoint, queue URLs, and schedule names.

Fetch endpoints and queues after deploy:

```shell
transire info --env dev --profile <aws-profile>
```

Use `transire send` and `transire trigger` with `--env dev` to hit AWS resources directly.
All AWS commands follow the AWS SDK region resolution (profile default or `AWS_REGION`/`AWS_DEFAULT_REGION`).
