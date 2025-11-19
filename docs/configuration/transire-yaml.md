---
title: "transire.yaml Reference"
description: "Complete reference for the Transire configuration file"
keywords:
  - transire.yaml
  - configuration
  - config file
  - yaml
  - settings
  - resource naming
  - environment support
  - multi-environment
category: configuration
difficulty: all
estimated_time: 10 minutes
prerequisites:
  - "Basic YAML knowledge"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Configuring project settings"
    - "Understanding config options"
    - "Customizing behavior"
    - "Resource naming configuration"
    - "Environment-specific settings"
  common_questions:
    - "What goes in transire.yaml?"
    - "What config options are available?"
    - "How do I customize settings?"
    - "How are resources named across environments?"
    - "How does the name field affect resource naming?"
---

# transire.yaml Reference

Complete reference for the Transire configuration file.

!!! tip "TL;DR"
    `transire.yaml` configures your project metadata, Lambda settings, VPC, existing resources, and development environment. Located in project root.

---

## File Location

**Default:** `transire.yaml` in project root

**Override with CLI flag:**
```bash
transire run -c custom.yaml
transire build --config custom.yaml
transire deploy --config custom.yaml
```

---

## Full Example

```yaml
# Project metadata
name: my-api
language: go
cloud: aws
runtime: lambda
iac: cdk
ci: github

# Lambda defaults
lambda:
  architecture: arm64
  timeout_seconds: 30
  memory_mb: 128

# Function groups (optional - advanced)
functions:
  main:
    include:
      - http_handlers: "*"
      - queue_handlers: "*"
      - schedule_handlers: "*"

# Environment variables
environment:
  LOG_LEVEL: info
  DATABASE_URL: ${DATABASE_URL}

# VPC configuration (optional)
vpc:
  subnet_ids:
    - subnet-abc123
    - subnet-def456
  security_group_ids:
    - sg-xyz789

# Existing resources (optional)
existing_resources:
  dynamodb_tables:
    - name: users-table
      arn: "arn:aws:dynamodb:us-east-1:123456789012:table/users"
      permissions: ["read", "write"]
  s3_buckets:
    - name: uploads-bucket
      arn: "arn:aws:s3:::my-uploads-bucket"
      permissions: ["read", "write"]
  secrets:
    - name: api-key
      arn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:api-key"
      permissions: ["read"]

# Per-queue configuration (optional)
queues:
  email-queue:
    visibility_timeout_seconds: 30
    max_receive_count: 3
    batch_size: 10

# Per-schedule configuration (optional)
schedules:
  daily-cleanup:
    timezone: "UTC"
    enabled: true

# CDK extensions (optional)
cdk_extensions:
  - file: "extensions/database.ts"

# Development settings
development:
  http_port: 3000
  queue_port: 4000
  auto_reload: true
  log_level: debug
```

---

## Field Reference

### Project Metadata

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | – | Project name (used as AppName in `{AppName}-{Environment}-{ResourceName}` naming) |
| `language` | string | No | `go` | Programming language (only `go` supported in MVP) |
| `cloud` | string | No | `aws` | Cloud provider (only `aws` supported in MVP) |
| `runtime` | string | No | `lambda` | Runtime platform (only `lambda` supported in MVP) |
| `iac` | string | No | `cdk` | Infrastructure as Code tool (only `cdk` supported in MVP) |
| `ci` | string | No | `github` | CI/CD platform (only `github` supported in MVP) |

Source: [`pkg/transire/config.go:12-31`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

---

### Resource Naming & Environment Support

Transire automatically names all AWS resources using the pattern:
```
{AppName}-{Environment}-{ResourceName}
```

**How it works:**
- **AppName**: Derived from the `name` field in `transire.yaml`
- **Environment**: Specified via CLI flag `--environment` (defaults to `dev`)
- **ResourceName**: Specific to resource type (e.g., `main`, `email-queue`, `daily-cleanup`)

**Examples:**

```yaml
# transire.yaml
name: my-api
```

```bash
# Commands produce different resource names
transire deploy --environment dev
# → Stack: my-api-dev
# → Lambda: my-api-dev-main
# → API: my-api-dev-api
# → Queue: my-api-dev-email-queue

transire deploy --environment prod
# → Stack: my-api-prod
# → Lambda: my-api-prod-main
# → API: my-api-prod-api
# → Queue: my-api-prod-email-queue
```

This ensures complete resource isolation between environments.

Source: [`internal/cli/commands/build.go:87-91`](https://github.com/transire/transire/blob/main/internal/cli/commands/build.go), [`internal/providers/aws/cdk_generator.go`](https://github.com/transire/transire/blob/main/internal/providers/aws/cdk_generator.go)

---

### Lambda Configuration

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `lambda.architecture` | string | No | `arm64` | CPU architecture (only `arm64` supported) |
| `lambda.timeout_seconds` | int | No | `30` | Default function timeout (1-900 seconds) |
| `lambda.memory_mb` | int | No | `128` | Default function memory (128-10240 MB) |

Source: [`pkg/transire/config.go:33-38`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

**Recommendations:**
- **Architecture:** Use `arm64` for 20% cost savings
- **Timeout:** Set based on your longest handler duration (API: 30s, queue: 300s, schedule: 900s)
- **Memory:** More memory = more CPU. Start with 128MB, increase if needed (256MB is good default)

See also: [Lambda Configuration](lambda.md)

---

### Function Groups (Optional)

```yaml
functions:
  web:
    include:
      - http_handlers: "*"
    memory_mb: 256
    timeout_seconds: 30
  background:
    include:
      - queue_handlers: "*"
      - schedule_handlers: "*"
    memory_mb: 512
    timeout_seconds: 300
```

Splits handlers into multiple Lambda functions for optimized resource allocation.

See also: [Multi-Function Architecture](../guides/multi-function-architecture.md)

---

### Environment Variables

```yaml
environment:
  KEY: value                 # Literal value
  SECRET: ${ENV_VAR}         # From environment variable
  RESOURCE: !Ref MyResource  # CloudFormation reference (in CDK)
```

Environment variables are passed to Lambda functions and available via `os.Getenv()`.

**Best practices:**
- Use `${VAR}` syntax for secrets (read from local environment or AWS Secrets Manager)
- Never commit secrets to `transire.yaml`
- Use AWS Secrets Manager or Parameter Store for production secrets

See also: [Environment Variables](environment.md)

---

### VPC Configuration (Optional)

```yaml
vpc:
  subnet_ids:
    - subnet-abc123
    - subnet-def456
  security_group_ids:
    - sg-xyz789
```

Places Lambda functions in specified VPC subnets with security groups.

**Use cases:**
- Access RDS databases in private subnets
- Access ElastiCache clusters
- Access internal APIs without public endpoints

**Important:**
- Requires NAT Gateway for Lambda to access AWS APIs
- Increases cold start time (~1-2 seconds)
- Security groups must allow egress to AWS services

Source: [`pkg/transire/config.go:49-53`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

See also: [VPC Configuration](vpc-existing.md)

---

### Existing Resources (Optional)

```yaml
existing_resources:
  dynamodb_tables:
    - name: users-table
      arn: "arn:aws:dynamodb:us-east-1:123456789012:table/users"
      permissions: ["read", "write"]
  s3_buckets:
    - name: uploads-bucket
      arn: "arn:aws:s3:::my-uploads-bucket"
      permissions: ["read", "write"]
  secrets:
    - name: api-key
      arn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:api-key"
      permissions: ["read"]
```

Grants Lambda IAM permissions to access existing AWS resources.

**Permission Values:**
- `"read"` – Read-only access
- `"write"` – Write-only access
- `["read", "write"]` – Full access

Source: [`pkg/transire/config.go:55-67`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

See also: [Existing Resources](vpc-existing.md)

---

### Per-Queue Configuration (Optional)

```yaml
queues:
  email-queue:
    visibility_timeout_seconds: 30
    max_receive_count: 3
    batch_size: 10
  notification-queue:
    visibility_timeout_seconds: 60
    max_receive_count: 5
    batch_size: 5
```

Overrides queue settings per-queue. Values here override `QueueConfig` from your `QueueHandler`.

See also: [Queue Configuration](queues.md), [Queue Handlers](../core-concepts/queue-handlers.md)

---

### Per-Schedule Configuration (Optional)

```yaml
schedules:
  daily-cleanup:
    timezone: "UTC"
    enabled: true
  hourly-report:
    timezone: "America/New_York"
    enabled: false
```

Configure individual schedules. Use `enabled: false` to temporarily disable a schedule without removing the handler.

See also: [Schedule Configuration](schedules.md), [Schedule Handlers](../core-concepts/schedule-handlers.md)

---

### CDK Extensions (Optional)

```yaml
cdk_extensions:
  - file: "extensions/database.ts"
  - file: "extensions/monitoring.ts"
```

Reference TypeScript files that extend the generated CDK stack with custom resources.

**Extension file format:**

```typescript
// extensions/database.ts
import * as cdk from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';

export function extend(stack: cdk.Stack, functions: Map<string, lambda.Function>) {
  // Add RDS database
  const db = new rds.DatabaseInstance(stack, 'Database', {
    engine: rds.DatabaseInstanceEngine.postgres({ version: rds.PostgresEngineVersion.VER_15 }),
    instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
  });

  // Grant access to Lambda
  const mainFunction = functions.get('main');
  db.connections.allowFrom(mainFunction, ec2.Port.tcp(5432));
}
```

Source: [`pkg/transire/config.go:69-72`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

See also: [Custom CDK Extensions](../guides/custom-cdk.md)

---

### Development Settings

```yaml
development:
  http_port: 3000              # HTTP server port
  queue_port: 4000             # Queue simulator port
  scheduler_port: 5000         # Schedule simulator port
  auto_reload: true            # Enable hot reload
  log_level: debug             # Log verbosity (debug, info, warn, error)
  mock_aws_services: false     # Mock AWS services (future)
```

Controls local development behavior with `transire run`.

Source: [`pkg/transire/config.go:74-82`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

See also: [transire run](../cli-reference/transire-run.md), [Local Development](../guides/local-development.md)

---

## Validation

Configuration is validated on load. Errors will prevent app from starting.

**Common validation errors:**

**Missing required field:**
```
Error: configuration validation failed: name is required
```

**Invalid value:**
```
Error: invalid language: only 'go' is supported in current version
```

**Invalid Lambda settings:**
```
Error: lambda.memory_mb must be between 128 and 10240
Error: lambda.timeout_seconds must be between 1 and 900
```

**Empty function groups:**
```
Error: function 'web' has no handlers included
```

Validation logic source: [`pkg/transire/config.go:200-245`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

---

## Configuration Loading Order

Transire loads configuration in this order (later overrides earlier):

1. **Defaults** from code (`pkg/transire/config.go`)
2. **`transire.yaml`** file
3. **CLI flags** (if applicable, e.g., `--region`)

---

## Minimal Configuration

The absolute minimum `transire.yaml`:

```yaml
name: my-api
```

All other fields have sensible defaults.

---

## Next Steps

### Deep-Dive Topics

- [Lambda Configuration](lambda.md) – Memory, timeout, architecture settings
- [Queue Configuration](queues.md) – Per-queue SQS settings
- [Schedule Configuration](schedules.md) – Per-schedule EventBridge settings
- [VPC Configuration](vpc-existing.md) – Networking and security groups
- [Environment Variables](environment.md) – Secrets and configuration
- [Existing Resources](vpc-existing.md) – Connect to existing AWS infrastructure

### Guides

- [Multi-Function Architecture](../guides/multi-function-architecture.md) – Split handlers across functions
- [Custom CDK Extensions](../guides/custom-cdk.md) – Extend generated infrastructure
- [Deploying to AWS](../guides/deploying-to-aws.md) – Complete deployment walkthrough

---

## See Also

- [Quickstart](../getting-started/quickstart.md) – Get started in 5 minutes
- [transire init](../cli-reference/transire-init.md) – Initialize a new project
- [Application & Runtime](../core-concepts/application-runtime.md) – How Transire works
