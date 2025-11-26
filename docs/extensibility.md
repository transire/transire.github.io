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

## Add custom AWS infrastructure

Transire auto-generates CDK for Lambda, API Gateway, SQS, and EventBridge. To provision additional resources or customize Lambda settings, create `infra/extend.ts` in your project root with two optional exports:

### Configure Lambda settings

Use `configure` to customize the Lambda before it's created—set VPC, memory, timeout, or add environment variables:

```typescript
// infra/extend.ts
import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as lambda from "aws-cdk-lib/aws-lambda";

export function configure(stack: cdk.Stack, env: string): Partial<lambda.FunctionProps> {
  const vpc = new ec2.Vpc(stack, "AppVpc", { maxAzs: 2 });

  return {
    vpc,
    vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
    memorySize: 1024,
    timeout: cdk.Duration.seconds(60),
    environment: {
      DATABASE_URL: `postgres://db.${env}.internal:5432/app`,
    },
  };
}
```

The returned config is merged with Transire's defaults. User-provided `environment` variables are merged with Transire's queue/schedule env vars.

### Add resources after Lambda creation

Use `extend` to provision additional resources and grant permissions to the Lambda:

```typescript
// infra/extend.ts
import * as cdk from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as lambda from "aws-cdk-lib/aws-lambda";

export function extend(stack: cdk.Stack, fn: lambda.Function, env: string) {
  const table = new dynamodb.Table(stack, "UsersTable", {
    tableName: `myapp-users-${env}`,
    partitionKey: { name: "pk", type: dynamodb.AttributeType.STRING },
    billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
  });

  table.grantReadWriteData(fn);
  fn.addEnvironment("USERS_TABLE", table.tableName);
}
```

### Both exports are optional

You can export just `configure`, just `extend`, or both. Transire calls them if they exist:

- `configure(stack, env)` → called before Lambda creation, returns config properties
- `extend(stack, fn, env)` → called after Lambda creation, for additional resources

### Complete example

Here's a full `infra/extend.ts` that provisions a VPC with private subnets, increases Lambda resources, and adds a DynamoDB table:

```typescript
// infra/extend.ts
import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as lambda from "aws-cdk-lib/aws-lambda";

export function configure(stack: cdk.Stack, env: string): Partial<lambda.FunctionProps> {
  const vpc = new ec2.Vpc(stack, "AppVpc", {
    maxAzs: 2,
    natGateways: 1,
  });

  return {
    vpc,
    vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
    memorySize: 1024,
    timeout: cdk.Duration.seconds(60),
    environment: {
      CUSTOM_ENV_VAR: `custom-value-${env}`,
    },
  };
}

export function extend(stack: cdk.Stack, fn: lambda.Function, env: string) {
  const table = new dynamodb.Table(stack, "UsersTable", {
    tableName: `myapp-users-${env}`,
    partitionKey: { name: "pk", type: dynamodb.AttributeType.STRING },
    sortKey: { name: "sk", type: dynamodb.AttributeType.STRING },
    billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    removalPolicy: cdk.RemovalPolicy.DESTROY,
  });

  table.grantReadWriteData(fn);
  fn.addEnvironment("USERS_TABLE", table.tableName);
}
```

The `infra/` directory is yours to organize—add constructs, utilities, or whatever CDK patterns you need.

Generated CDK stays in `dist/` (gitignored); your `infra/` code is source-controlled.

## Override environments

Use `TRANSIRE_DISPATCHER=aws|local` to force dispatcher selection, and keep `transire.yaml` lean with only names (plus optional env profiles). Everything else is discovered from your Go code, so adding new queues or schedules is as simple as registering another handler.
