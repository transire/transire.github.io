# transire build

Build deployable artifacts and generate Infrastructure as Code definitions.

!!! tip "TL;DR"
    `transire build` compiles your Go app for Lambda (ARM64), excludes local-only code, and generates AWS CDK TypeScript infrastructure based on your handlers.

---

## Synopsis

```bash
transire build [flags]
```

---

## Description

The `transire build` command:

1. Compiles your Go application for AWS Lambda (ARM64 architecture)
2. Excludes local development code (via build tags `//go:build !local`)
3. Creates deployment packages (ZIP files)
4. Discovers registered handlers (HTTP, queue, schedule)
5. Generates AWS CDK TypeScript infrastructure code based on handlers

Source: [`internal/cli/commands/build.go:14-109`](https://github.com/transire/transire/blob/main/internal/cli/commands/build.go)

---

## Build Process

### 1. Handler Discovery

Transire scans your code to find:
- HTTP routes registered with `app.Router()`
- `QueueHandler` registrations via `app.RegisterQueueHandler()`
- `SchedulerHandler` registrations via `app.RegisterScheduleHandler()`

Discovery implementation: [`internal/cli/discovery/`](https://github.com/transire/transire/tree/main/internal/cli/discovery/)

### 2. Compilation

Cross-compiles Go code for Lambda:
- **GOOS:** `linux`
- **GOARCH:** `arm64`
- **CGO_ENABLED:** `0` (static binary)
- **Build tags:** Excludes code tagged with `//go:build local`
- **Optimizations:** Strips debug info (`-ldflags "-s -w"`)

Output: `dist/function.zip` (or per-function ZIPs for multi-function mode)

### 3. CDK Generation

Generates TypeScript CDK code in `infrastructure/lib/` including:
- Lambda functions with correct memory, timeout, environment
- API Gateway v2 HTTP API (if HTTP handlers present)
- SQS queues + DLQs (for queue handlers)
- EventBridge rules (for schedule handlers)
- IAM permissions
- VPC configuration (if specified)
- Existing resource imports (if specified)

CDK generation source: [`internal/providers/aws/cdk_generator.go`](https://github.com/transire/transire/blob/main/internal/providers/aws/cdk_generator.go)

---

## Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `-c, --config` | string | `transire.yaml` | Path to configuration file |
| `-o, --output` | string | `dist` | Output directory for artifacts |

Source: [`internal/cli/commands/build.go:104-105`](https://github.com/transire/transire/blob/main/internal/cli/commands/build.go)

---

## Examples

### Build with default settings

```bash
transire build
```

Output:
```
🔨 Building Transire application: my-api
📦 Building artifacts for aws/lambda
🏗️  Generating infrastructure definitions
✅ Build completed successfully
📁 Artifacts location: dist
🏗️  Infrastructure: infrastructure/
```

### Build with custom output directory

```bash
transire build --output ./build
```

### Build with custom config

```bash
transire build --config production-transire.yaml
```

---

## Output Artifacts

After building:

```
dist/
└── function.zip        # Lambda deployment package (ARM64 binary)

infrastructure/lib/
└── my-api-stack.ts    # Generated CDK stack definition
```

For multi-function configurations:
```
dist/
├── web-function.zip
└── background-function.zip
```

---

## Build Tags

Exclude code from Lambda builds using build tags:

```go
//go:build local

package main

// This file is only compiled for local development
// It is excluded from Lambda builds
```

Use this for:
- Local development utilities
- Test helpers
- Debug endpoints
- Development-only middleware

Example from [`examples/simple-api/`](https://github.com/transire/transire/tree/main/examples/simple-api/):

```go
//go:build local

package main

import (
    "log"
    "github.com/go-chi/chi/v5/middleware"
)

func init() {
    // Register debug middleware only for local development
    log.Println("Loading local-only middleware")
}
```

---

## Generated CDK Code

Example generated stack (simplified):

```typescript
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigatewayv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as events from 'aws-cdk-lib/aws-events';

export class MyApiStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string) {
    super(scope, id);

    // Lambda function
    const mainFunction = new lambda.Function(this, 'MainFunction', {
      runtime: lambda.Runtime.PROVIDED_AL2023,
      handler: 'bootstrap',
      code: lambda.Code.fromAsset('../dist/function.zip'),
      architecture: lambda.Architecture.ARM_64,
      memorySize: 256,
      timeout: cdk.Duration.seconds(30),
    });

    // API Gateway
    const api = new apigatewayv2.HttpApi(this, 'HttpApi', {
      defaultIntegration: new HttpLambdaIntegration(
        'DefaultIntegration',
        mainFunction
      ),
    });

    // SQS Queue + DLQ
    const emailQueue = new sqs.Queue(this, 'EmailQueue', {
      queueName: 'email-queue',
      visibilityTimeout: cdk.Duration.seconds(30),
      deadLetterQueue: {
        queue: new sqs.Queue(this, 'EmailQueueDLQ'),
        maxReceiveCount: 3,
      },
    });

    // EventBridge rule
    const dailyCleanup = new events.Rule(this, 'DailyCleanupRule', {
      schedule: events.Schedule.cron({ minute: '0', hour: '2' }),
    });
    dailyCleanup.addTarget(new LambdaFunction(mainFunction));
  }
}
```

Source: CDK template from [`internal/providers/aws/cdk_generator.go:92-175`](https://github.com/transire/transire/blob/main/internal/providers/aws/cdk_generator.go)

---

## Troubleshooting

### Build fails with "no Go files"

**Error:**
```
Error: no Go files in current directory
```

**Solution:**
- Ensure you have a `main.go` in the project root
- Check that `transire.yaml` is in the same directory
- Verify you're in the correct project directory

### CDK generation fails

**Error:**
```
Error: failed to generate infrastructure
```

**Solution:**
- Ensure Node.js 18+ is installed: `node --version`
- Run `npm install` in `infrastructure/` directory
- Check that `package.json` exists in `infrastructure/`

### Lambda package too large

**Error:**
```
Error: deployment package exceeds 50MB
```

**Solution:**
- Check for large dependencies in `go.mod`
- Use build tags to exclude non-production code
- Consider splitting into multiple functions (see [Multi-Function Architecture](../guides/multi-function-architecture.md))
- Remove unused dependencies: `go mod tidy`

### Cross-compilation errors

**Error:**
```
Error: build constraints exclude all Go files
```

**Solution:**
- Check your build tags syntax
- Ensure `//go:build local` is on its own line
- Verify you're not excluding required files

---

## Next Steps

After building, you're ready to deploy:

- [transire deploy](transire-deploy.md) – Deploy built artifacts to AWS
- [Multi-Function Architecture](../guides/multi-function-architecture.md) – Split handlers across functions
- [Configuration Reference](../configuration/transire-yaml.md) – Customize build settings
- [Deploying to AWS Guide](../guides/deploying-to-aws.md) – Complete deployment walkthrough

---

## See Also

- [transire deploy](transire-deploy.md) – Deploy to AWS
- [transire run](transire-run.md) – Run locally with hot reload
- [Custom CDK Extensions](../guides/custom-cdk.md) – Extend generated infrastructure
