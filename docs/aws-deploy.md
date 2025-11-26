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

`transire.yaml` captures only the app name and optional per-env AWS profiles:

```yaml
app:
  name: my-app
envs:
  dev:
    profile: transire-sandbox
```

- `app.name` drives the CloudFormation stack name (`<name>-stack`) and resource names (`<app>-<queue>-<env>` for queues, schedules, and API).
- Each `env` can override AWS profile. You choose which env to deploy via `--env`. Regions come from the AWS SDK default chain (env vars, shared config, profile defaults).

## Build assets

```shell
transire build --manifest transire.yaml
```

Outputs under `dist/aws`:

- `lambda/bootstrap` and `lambda/bootstrap.zip` compiled for `linux/amd64`.
- `cdk/` with `package.json`, `cdk.json`, and TypeScript sources describing the stack.

If `infra/extend.ts` exists in your project root, the generated CDK imports and calls your `configure` and `extend` functions to customize Lambda settings or add resources like DynamoDB tables. See [Extensibility: Add custom AWS infrastructure](extensibility.md#add-custom-aws-infrastructure) for details.

## Deploy

```shell
transire deploy --env dev --profile <aws-profile>
```

What deploy does:

1. Runs the same build as `transire build`.
2. Runs `npm install` inside `dist/aws/cdk` (once per environment) then `npx cdk deploy --require-approval never` with your chosen profile and env context.

> `--env` is required. Deploy uses the AWS SDK default region resolution (env vars, shared config, or the profile default). There is no `--region` flag; set the region in your AWS config or export `AWS_REGION`/`AWS_DEFAULT_REGION` before running deploy.

The same AWS SDK region resolution is used by `transire info`, `transire send`, and `transire trigger` when `--env` points at AWS.

If you hit `SSM parameter /cdk-bootstrap/hnb659fds/version not found`, bootstrap the target account/region once from `dist/aws/cdk`:

```shell
AWS_REGION=<region> AWS_DEFAULT_REGION=<region> npx cdk bootstrap --profile <aws-profile>
```

## Inspect outputs

After deploy, fetch endpoints, queue URLs, and schedule names:

```shell
transire info --env dev --profile <aws-profile>
```

`transire send` and `transire trigger` use these outputs automatically when targeting AWS.

## Runtime wiring

- Environment variables `TRANSIRE_QUEUE_<NAME>_URL` and `TRANSIRE_QUEUE_<NAME>_NAME` are injected for each discovered queue; schedules get `TRANSIRE_SCHEDULE_<NAME>_NAME`.
- The AWS dispatcher resolves API Gateway events through chi, maps SQS records back to logical queue names, and adapts EventBridge schedule invocations to your handlers.
- Override dispatcher choice with `TRANSIRE_DISPATCHER=aws` when testing Lambda locally.
