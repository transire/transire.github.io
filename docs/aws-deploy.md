---
title: Deploy to AWS | Transire
description: Build Lambda and CDK assets, configure transire.yaml, and deploy Transire apps to API Gateway, SQS, and EventBridge.
keywords:
  - transire deploy
  - aws cdk
  - go lambda
  - api gateway v2
  - sqs queues
  - eventbridge schedules
---
# Deploy to AWS

Transire builds and deploys AWS assets with a single CLI. The output is a Lambda bootstrap plus a CDK app that provisions API Gateway, SQS, and EventBridge.

## Prerequisites

- AWS credentials and a bootstrapped CDK environment.
- Node.js/npm available for `npm install` and `npx cdk`.

## transire.yaml

`transire.yaml` captures only names and regions:

```yaml
app:
  name: my-app
aws:
  region: us-east-1
envs:
  dev:
    profile: transire-sandbox
    region: us-east-1
```

- `app.name` drives the CloudFormation stack name (`<name>-stack`) and resource names (`<app>-<queue>-<env>` for queues, schedules, and API).
- Each `env` can override AWS profile and region. You choose which env to deploy via `--env`.

## Build assets

```shell
transire build --manifest transire.yaml
```

Outputs under `dist/aws`:

- `lambda/bootstrap` and `lambda/bootstrap.zip` compiled for `linux/amd64`.
- `cdk/` with `package.json`, `cdk.json`, and TypeScript sources describing the stack.

## Deploy

```shell
transire deploy --env dev --profile <aws-profile>
```

What deploy does:

1. Runs the same build as `transire build`.
2. Runs `npm install` inside `dist/aws/cdk` (once per environment) then `npx cdk deploy --require-approval never` with your chosen profile and env context.

> `--env` is required. Defaults: `--profile transire-sandbox`, region falls back to `aws.region` in `transire.yaml` unless overridden by `--region`.

## Inspect outputs

After deploy, fetch endpoints, queue URLs, and schedule names:

```shell
transire info --env dev --profile <aws-profile> --region <region>
```

`transire send` and `transire trigger` use these outputs automatically when targeting AWS.

## Runtime wiring

- Environment variables `TRANSIRE_QUEUE_<NAME>_URL` and `TRANSIRE_QUEUE_<NAME>_NAME` are injected for each discovered queue; schedules get `TRANSIRE_SCHEDULE_<NAME>_NAME`.
- The AWS dispatcher resolves API Gateway events through chi, maps SQS records back to logical queue names, and adapts EventBridge schedule invocations to your handlers.
- Override dispatcher choice with `TRANSIRE_DISPATCHER=aws` when testing Lambda locally.
