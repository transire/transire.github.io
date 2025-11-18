---
title: "Configuration System"
description: "Understanding Transire's configuration with transire.yaml and environment variables"
keywords:
  - configuration
  - transire.yaml
  - config
  - environment variables
  - settings
  - configuration merging
category: core-concepts
difficulty: intermediate
estimated_time: 10 minutes
prerequisites:
  - "Basic YAML knowledge"
  - "Understanding of environment variables"
related_docs:
  - path: "/configuration/transire-yaml/"
    relationship: "deep_dive"
  - path: "/configuration/environment/"
    relationship: "related"
  - path: "/guides/deploying-to-aws/"
    relationship: "related"
mcp_metadata:
  primary_use_cases:
    - "Configuring Transire applications"
    - "Understanding configuration precedence"
    - "Managing environment-specific settings"
  common_questions:
    - "How do I configure my app?"
    - "What goes in transire.yaml?"
    - "How do environment variables work?"
    - "What is configuration merging?"
---

# Configuration

Learn how Transire's configuration system works and how to customize your application behavior.

!!! tip "TL;DR"
    Configure your app via `transire.yaml` in your project root. Settings control development environment, Lambda deployment, queues, schedules, and VPC networking.

---

## Overview

Transire uses a **declarative configuration** approach via `transire.yaml`:

- **Project metadata** – Name, language, cloud provider
- **Development settings** – Local ports, hot reload, logging
- **Lambda configuration** – Memory, timeout, architecture
- **Queue configuration** – Visibility timeout, batch size, retries
- **Schedule configuration** – Timezone, enabled/disabled
- **VPC configuration** – Subnets, security groups
- **Environment variables** – Runtime configuration
- **Existing resources** – IAM permissions for AWS resources

Source: [`pkg/transire/config.go`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

---

## Configuration File

### Location

**Default:** `transire.yaml` in project root

**Override via CLI:**
```bash
transire run -c custom.yaml
transire build --config staging.yaml
transire deploy --config production.yaml
```

---

### Minimal Configuration

The absolute minimum configuration:

```yaml
name: my-api
```

All other fields have sensible defaults:
- **Language:** `go`
- **Cloud:** `aws`
- **Runtime:** `lambda`
- **HTTP port:** `3000`
- **Memory:** `128 MB`
- **Timeout:** `30 seconds`
- **Architecture:** `arm64`

---

## Configuration Sections

### 1. Project Metadata

Basic project information:

```yaml
name: my-api
language: go        # Only 'go' supported in MVP
cloud: aws          # Only 'aws' supported in MVP
runtime: lambda     # Only 'lambda' supported in MVP
iac: cdk            # Only 'cdk' supported in MVP
ci: github          # Only 'github' supported in MVP
```

**Used for:**
- CloudFormation stack naming (`my-api-stack`)
- IAM role naming
- Resource tagging

---

### 2. Development Settings

Controls local development with `transire run`:

```yaml
development:
  http_port: 3000              # HTTP server port
  queue_port: 4000             # Queue simulator port
  scheduler_port: 5000         # Schedule simulator port
  auto_reload: true            # Enable hot reload
  log_level: debug             # Log verbosity (debug, info, warn, error)
```

**Key features:**
- **Hot reload**: Automatically rebuilds on file changes
- **Simulators**: Test queues and schedules locally via REST APIs
- **Flexible ports**: Avoid conflicts with other services

See: [Local Development Guide](../guides/local-development.md)

---

### 3. Lambda Configuration

AWS Lambda deployment settings:

```yaml
lambda:
  architecture: arm64          # CPU architecture (arm64 only in MVP)
  timeout_seconds: 30          # Function timeout (1-900 seconds)
  memory_mb: 128               # Function memory (128-10240 MB)
  reserved_concurrent_executions: 10  # Optional: limit concurrency
```

**Recommendations:**
- **Architecture:** Use `arm64` for 20% cost savings
- **Timeout:** Set based on longest handler (API: 30s, queue: 300s, schedule: 900s)
- **Memory:** More memory = more CPU. Start at 128MB, increase if needed
- **Concurrency:** Set limits to prevent runaway costs

See: [Deploying to AWS](../guides/deploying-to-aws.md)

---

### 4. Environment Variables

Pass configuration to Lambda functions:

```yaml
environment:
  LOG_LEVEL: info                      # Literal value
  DATABASE_URL: ${DATABASE_URL}        # From environment variable
  API_KEY: !Ref MySecret              # CloudFormation reference
```

**Best practices:**
- Use `${VAR}` for secrets (read from local environment or AWS Secrets Manager)
- Never commit secrets to `transire.yaml`
- Use AWS Secrets Manager for production secrets

**Access in code:**
```go
logLevel := os.Getenv("LOG_LEVEL")
dbURL := os.Getenv("DATABASE_URL")
```

---

### 5. Queue Configuration

Per-queue SQS settings:

```yaml
queues:
  email-queue:
    visibility_timeout_seconds: 30    # How long message is invisible after delivery
    max_receive_count: 3              # Max retries before moving to DLQ
    batch_size: 10                    # Messages per Lambda invocation

  notification-queue:
    visibility_timeout_seconds: 60
    max_receive_count: 5
    batch_size: 5
```

**Overrides** `QueueConfig` from your `QueueHandler` implementation.

See: [Queue Handlers](queue-handlers.md)

---

### 6. Schedule Configuration

Per-schedule EventBridge settings:

```yaml
schedules:
  daily-cleanup:
    timezone: "UTC"
    enabled: true

  hourly-report:
    timezone: "America/New_York"
    enabled: true

  weekly-backup:
    enabled: false  # Temporarily disabled
```

**Use `enabled: false`** to disable a schedule without removing code.

See: [Schedule Handlers](schedule-handlers.md)

---

### 7. VPC Configuration

Place Lambda functions in VPC for private resource access:

```yaml
vpc:
  subnet_ids:
    - subnet-abc123
    - subnet-def456
  security_group_ids:
    - sg-xyz789
```

**Use cases:**
- Access RDS databases in private subnets
- Access ElastiCache clusters
- Access internal APIs without public endpoints

**Trade-offs:**
- Increases cold start time (~1-2 seconds)
- Requires NAT Gateway for AWS API access
- Additional cost for NAT Gateway

---

### 8. Existing Resources

Grant IAM permissions to existing AWS resources:

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

**Permission values:**
- `"read"` – Read-only access
- `"write"` – Write-only access
- `["read", "write"]` – Full access

**Generated IAM policies** are attached to Lambda execution role.

---

## Configuration Loading

Transire loads configuration in this order (later overrides earlier):

1. **Defaults** from code ([`pkg/transire/config.go`](https://github.com/transire/transire/blob/main/pkg/transire/config.go))
2. **`transire.yaml`** file
3. **CLI flags** (e.g., `--region`, `--environment`)

---

## Multi-Environment Configuration

### Strategy 1: Separate Files

Create environment-specific config files:

```bash
transire.yaml           # Default/development
transire.staging.yaml   # Staging
transire.prod.yaml      # Production
```

**Use with CLI:**
```bash
transire deploy --config transire.staging.yaml
transire deploy --config transire.prod.yaml
```

---

### Strategy 2: Environment Variables

Use environment variable substitution:

```yaml
name: my-api
environment:
  DATABASE_URL: ${DATABASE_URL}
  LOG_LEVEL: ${LOG_LEVEL:-info}  # Default to 'info'
```

**Set per environment:**
```bash
# Staging
export DATABASE_URL=postgres://staging-db:5432/myapp
transire deploy

# Production
export DATABASE_URL=postgres://prod-db:5432/myapp
transire deploy
```

---

### Strategy 3: CDK Context

Use CDK context values for environment-specific settings:

```yaml
# transire.yaml
name: my-api

# CDK extensions can access context
cdk_extensions:
  - file: "extensions/environment.ts"
```

```typescript
// extensions/environment.ts
export function extend(stack: cdk.Stack, functions: Map<string, lambda.Function>) {
  const env = stack.node.tryGetContext('environment') || 'development';
  const dbUrl = stack.node.tryGetContext('databaseUrl');

  functions.get('main')?.addEnvironment('ENV', env);
  functions.get('main')?.addEnvironment('DATABASE_URL', dbUrl);
}
```

**Deploy with context:**
```bash
cdk deploy -c environment=staging -c databaseUrl=postgres://staging-db/myapp
```

---

## Configuration Validation

Transire validates configuration on load. Common errors:

### Missing Required Field

```
Error: configuration validation failed: name is required
```

**Fix:** Add `name` field to `transire.yaml`

---

### Invalid Value

```
Error: invalid language: only 'go' is supported in current version
```

**Fix:** Use `language: go` (or omit, defaults to `go`)

---

### Invalid Lambda Settings

```
Error: lambda.memory_mb must be between 128 and 10240
Error: lambda.timeout_seconds must be between 1 and 900
```

**Fix:** Use values within valid ranges

---

### Empty Function Groups

```
Error: function 'web' has no handlers included
```

**Fix:** Ensure function groups include at least one handler pattern

---

## Advanced Configuration

### Multi-Function Architecture

Split handlers across multiple Lambda functions for optimized resource allocation:

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

**Benefits:**
- Optimize memory/timeout per use case
- Reduce cold start time for web handlers
- Better cost optimization

See: [Multi-Function Architecture Guide](../guides/multi-function-architecture.md)

---

### CDK Extensions

Extend generated infrastructure with custom TypeScript:

```yaml
cdk_extensions:
  - file: "extensions/database.ts"
  - file: "extensions/monitoring.ts"
```

**Extension format:**
```typescript
import * as cdk from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';

export function extend(stack: cdk.Stack, functions: Map<string, lambda.Function>) {
  // Add custom resources...
  const db = new rds.DatabaseInstance(stack, 'Database', {
    engine: rds.DatabaseInstanceEngine.postgres({ version: rds.PostgresEngineVersion.VER_15 }),
  });

  // Grant access to Lambda
  const mainFunction = functions.get('main');
  db.connections.allowFrom(mainFunction, ec2.Port.tcp(5432));
}
```

See: [Custom CDK Extensions Guide](../guides/custom-cdk.md)

---

## Configuration Best Practices

### 1. Use Defaults When Possible

Don't specify every field. Trust the defaults:

```yaml
# Good: Minimal config
name: my-api

# Avoid: Over-specifying
name: my-api
language: go
cloud: aws
runtime: lambda
lambda:
  architecture: arm64  # Already the default
  timeout_seconds: 30  # Already the default
```

---

### 2. Separate Secrets from Config

Never commit secrets:

```yaml
# Bad: Hardcoded secret
environment:
  API_KEY: sk_live_abc123

# Good: Environment variable
environment:
  API_KEY: ${API_KEY}
```

---

### 3. Document Custom Settings

Add comments explaining non-obvious choices:

```yaml
lambda:
  timeout_seconds: 300  # Long timeout for PDF generation
  memory_mb: 1024       # More memory for image processing
```

---

### 4. Use Consistent Naming

Follow naming conventions:

```yaml
# Good: Consistent kebab-case
queues:
  email-queue: {}
  notification-queue: {}

schedules:
  daily-cleanup: {}
  hourly-report: {}
```

---

### 5. Version Control Configuration

Commit `transire.yaml` to git (without secrets):

```bash
git add transire.yaml
git commit -m "Add transire configuration"
```

Add secrets to `.gitignore`:
```
.env
transire.*.yaml  # If using environment-specific files with secrets
```

---

## Configuration Reference

For complete field documentation, see:

- **[transire.yaml Reference](../configuration/transire-yaml.md)** – Complete field reference with examples

### Configuration Sub-Pages

- [Lambda Configuration](../configuration/lambda.md) – Memory, timeout, architecture
- [Queue Configuration](../configuration/queues.md) – Per-queue SQS settings
- [Schedule Configuration](../configuration/schedules.md) – Per-schedule EventBridge settings
- [VPC Configuration](../configuration/vpc-existing.md) – Networking and security groups
- [Environment Variables](../configuration/environment.md) – Runtime configuration
- [Existing Resources](../configuration/vpc-existing.md) – IAM permissions

---

## Next Steps

- [Application & Runtime](application-runtime.md) – Understand how Transire works
- [Local Development](../guides/local-development.md) – Test with local configuration
- [Deploying to AWS](../guides/deploying-to-aws.md) – Deploy your configured app
- [Multi-Function Architecture](../guides/multi-function-architecture.md) – Advanced function splitting

---

## See Also

- [YAML Syntax](https://yaml.org/spec/1.2.2/)
- [AWS Lambda Configuration](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-common.html)
- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/)
