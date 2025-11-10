---
title: "Configuration Schema Reference"
category: reference
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - Basic YAML knowledge
  - Familiarity with Transire concepts
mcp_use: reference
mcp_operations:
  - extract_config
  - validate_config
  - generate_config
features_covered:
  - Configuration structure
  - Service metadata
  - Runtime settings
  - Deployment configuration
  - Cloud provider settings
  - Infrastructure configuration
code_blocks: true
last_updated: 2025-10-30
---

# Configuration Schema Reference

## Overview

The `transire.yaml` file is the central configuration file for your Transire application. It defines service metadata, runtime behavior, deployment settings, cloud provider configuration, and infrastructure requirements.

This document provides a complete reference for all configuration options with examples and best practices.

## Configuration Structure

```yaml
version: 1                    # Schema version (required)
service: string               # Service name (required)
runtime: string               # Runtime language (required, "go" for MVP)
cloud: string                 # Cloud provider (required, "aws" for MVP)
ci: string                    # CI provider (optional, "github")
iac: string                   # IaC provider (required, "opentofu" for MVP)
timezone: string              # Service timezone (optional, default "UTC")

deploy:                       # Deployment configuration
  arch: string
  memory_mb: int
  timeout_s: int

http:                         # HTTP configuration
  simulate_apigw_limits: bool
  cors: object
  rate_limit: object

queues:                       # Queue configuration
  max_batch_size: int
  batch_window_s: int
  visibility_timeout_s: int
  max_receive_count: int
  error_mode: string

scheduled:                    # Scheduled job configuration
  # (inherits timezone from service-level)

observability:                # Observability configuration
  logging: object
  tracing: object

infra:                        # Infrastructure configuration
  backend: object
  vpc: object
  route53: object
  tags: object

env:                          # Environment variables
  - name: string
    workspace: string
    variables: object
```

## Service Metadata

### version (required)

**Type:** `int`
**Default:** N/A
**Description:** Configuration schema version. Always set to `1` for current version.

```yaml
version: 1
```

### service (required)

**Type:** `string`
**Format:** `[a-z0-9-]+` (lowercase alphanumeric and hyphens only)
**Description:** Service name used for resource naming. This becomes part of all cloud resource names.

```yaml
service: orders
```

**Resource naming pattern:** `${service}-${env}-${resource}`

Examples:
- HTTP Lambda: `orders-prod-http`
- Queue: `orders-prod-queue-ProcessedOrder`
- DLQ: `orders-prod-queue-ProcessedOrder-dlq`

### runtime (required)

**Type:** `string`
**Valid values:** `go` (MVP only)
**Description:** Programming language runtime.

```yaml
runtime: go
```

### cloud (required)

**Type:** `string`
**Valid values:** `aws` (MVP only)
**Description:** Cloud provider for deployment.

```yaml
cloud: aws
```

### ci (optional)

**Type:** `string`
**Valid values:** `github` (MVP only)
**Default:** none
**Description:** CI/CD provider for workflow generation.

```yaml
ci: github
```

### iac (required)

**Type:** `string`
**Valid values:** `opentofu` (MVP only)
**Description:** Infrastructure-as-Code provider.

```yaml
iac: opentofu
```

### timezone (optional)

**Type:** `string`
**Format:** IANA timezone name (e.g., `America/New_York`, `Europe/London`, `UTC`)
**Default:** `UTC`
**Description:** Service-level timezone applied to all cron-based schedules. Individual schedules can override this.

```yaml
timezone: America/New_York
```

**Usage:**
- Applied to cron schedules with specific times (`@daily 09:00`)
- NOT applied to rate-based schedules (`@hourly`, `rate(1 hour)`)
- Can be overridden per schedule (`@daily 09:00 UTC`)

## Deployment Configuration

### deploy

**Type:** `object`
**Description:** Serverless function deployment settings.

```yaml
deploy:
  arch: arm64           # Architecture (arm64 or x86_64)
  memory_mb: 256        # Memory allocation in MB
  timeout_s: 30         # Function timeout in seconds
```

#### arch

**Type:** `string`
**Valid values:** `arm64`, `x86_64`
**Default:** `arm64`
**Description:** CPU architecture for Lambda functions. ARM64 offers better cost/performance ratio.

#### memory_mb

**Type:** `int`
**Range:** 128 - 10240
**Default:** 256
**Description:** Memory allocation in megabytes. CPU is allocated proportionally.

**Guidance:**
- 128 MB: Very lightweight handlers, minimal dependencies
- 256 MB: Default, suitable for most APIs
- 512 MB: Database queries, external API calls
- 1024+ MB: Heavy processing, large payloads

#### timeout_s

**Type:** `int`
**Range:** 1 - 900 (15 minutes)
**Default:** 30
**Description:** Maximum execution time in seconds. Also used as default graceful shutdown timeout locally.

**Guidance:**
- HTTP: 5-30s (API Gateway has 30s hard limit)
- Queue: 30-300s depending on batch processing time
- Scheduled: As needed for job duration

## HTTP Configuration

### http

**Type:** `object`
**Description:** HTTP server and API Gateway settings.

```yaml
http:
  simulate_apigw_limits: true
  cors:
    enabled: true
    allow_origins: ["https://app.example.com"]
    allow_methods: ["GET", "POST", "PUT", "DELETE"]
    allow_headers: ["Content-Type", "Authorization"]
  rate_limit:
    requests_per_minute: 100
    burst: 20
```

#### simulate_apigw_limits

**Type:** `bool`
**Default:** `true`
**Description:** Enforce API Gateway payload limits (6 MB) in local development.

**When to disable:**
- Testing with large payloads locally
- Using custom binary content types

#### cors

**Type:** `object`
**Description:** Cross-Origin Resource Sharing configuration.

```yaml
cors:
  enabled: bool
  allow_origins: []string
  allow_methods: []string
  allow_headers: []string
```

**Fields:**
- `enabled`: Enable/disable CORS middleware
- `allow_origins`: List of allowed origin domains (use `["*"]` for public APIs)
- `allow_methods`: List of allowed HTTP methods
- `allow_headers`: List of allowed request headers

#### rate_limit

**Type:** `object`
**Description:** Rate limiting configuration (local development only).

```yaml
rate_limit:
  requests_per_minute: int
  burst: int
```

**Note:** This is enforced locally only. For production rate limiting, use API Gateway throttling settings in custom IaC.

## Queue Configuration

### queues

**Type:** `object`
**Description:** Global queue behavior settings. Applied to all queue handlers.

```yaml
queues:
  max_batch_size: 10              # Messages per batch
  batch_window_s: 5               # Batch collection window
  visibility_timeout_s: 30        # Message visibility timeout
  max_receive_count: 3            # Retries before DLQ
  error_mode: partial             # Error handling mode
```

#### max_batch_size

**Type:** `int`
**Range:** 1 - 10 (SQS limit)
**Default:** 10
**Description:** Maximum messages per batch delivered to handler.

#### batch_window_s

**Type:** `int`
**Range:** 0 - 300
**Default:** 5
**Description:** Maximum time to wait for full batch before invoking handler.

#### visibility_timeout_s

**Type:** `int`
**Range:** 0 - 43200 (12 hours)
**Default:** 30
**Description:** Time a message is hidden after being received. Should be longer than handler timeout.

**Guidance:** Set to `timeout_s + 5` to allow for Lambda overhead.

#### max_receive_count

**Type:** `int`
**Range:** 1 - 1000
**Default:** 3
**Description:** Number of receive attempts before moving message to DLQ.

#### error_mode

**Type:** `string`
**Valid values:** `partial`
**Default:** `partial`
**Description:** Error handling mode for batch processing.

- `partial`: Per-message success/failure tracking using `BatchResult`

## Scheduled Jobs Configuration

### scheduled

**Type:** `object`
**Description:** Global scheduled job settings.

```yaml
scheduled:
  # Timezone inherited from service-level 'timezone' field
  # Individual schedules can override with syntax like "@daily 09:00 UTC"
```

**Note:** Configuration is inherited from service-level `timezone`. Individual schedules are defined in code and can override timezone inline.

## Observability Configuration

### observability

**Type:** `object`
**Description:** Logging, tracing, and metrics configuration.

```yaml
observability:
  logging:
    level: info           # Log level
    format: json          # Log format
  tracing:
    enabled: false        # Enable tracing
    provider: aws-xray    # Tracing provider
```

#### logging

**Type:** `object`
**Description:** Structured logging configuration.

```yaml
logging:
  level: string     # debug, info, warn, error
  format: string    # json, text
```

**level:**
- `debug`: Verbose logging, including request/response details
- `info`: Standard operational logs (default)
- `warn`: Warning messages
- `error`: Error messages only

**format:**
- `json`: Structured JSON logs (recommended for production)
- `text`: Human-readable logs (useful for local development)

#### tracing

**Type:** `object`
**Description:** Distributed tracing configuration.

```yaml
tracing:
  enabled: bool        # Enable/disable tracing
  provider: string     # Tracing provider (aws-xray, otel)
```

**Providers:**
- `aws-xray`: AWS X-Ray integration
- `otel`: OpenTelemetry (future)

**Note:** Tracing is opt-in to reduce overhead. Enable in production for debugging.

## Infrastructure Configuration

### infra

**Type:** `object`
**Description:** Infrastructure and IaC provider settings.

```yaml
infra:
  backend:
    type: s3
    bucket: transire-tf-state
    dynamodb_table: tf-locks
    key_prefix: orders/
  vpc:
    enabled: false
  route53:
    hosted_zone_id: null
  tags:
    env: dev
    service: orders
```

#### backend

**Type:** `object`
**Description:** OpenTofu/Terraform backend configuration for state storage.

```yaml
backend:
  type: string              # Backend type (s3 for AWS)
  bucket: string            # S3 bucket name
  dynamodb_table: string    # DynamoDB table for state locking
  key_prefix: string        # S3 key prefix for state files
```

**S3 Backend Example:**
```yaml
backend:
  type: s3
  bucket: my-company-terraform-state
  dynamodb_table: terraform-state-lock
  key_prefix: transire/orders/
```

**Setup:** Run `transire init --backend` to create required resources.

#### vpc

**Type:** `object`
**Description:** VPC configuration (advanced).

```yaml
vpc:
  enabled: bool
```

**Note:** VPC increases cold start time and incurs NAT Gateway costs. Only enable if accessing private resources.

#### route53

**Type:** `object`
**Description:** Route53 DNS configuration (advanced).

```yaml
route53:
  hosted_zone_id: string    # Route53 hosted zone ID
```

**Note:** Custom domains require additional IaC in `infra/overrides/`.

#### tags

**Type:** `object` (key-value pairs)
**Description:** Tags applied to all created resources.

```yaml
tags:
  env: dev
  service: orders
  team: backend
  cost-center: engineering
```

## Environment Variables

### env

**Type:** `array` of environment objects
**Description:** Environment-specific variable configuration for different deployment environments.

```yaml
env:
  - name: dev                    # Environment name
    workspace: dev               # OpenTofu workspace
    variables:                   # Environment variables
      DB_URL: postgres://dev-db.example.com/orders
      LOG_LEVEL: debug

  - name: prod
    workspace: prod
    variables:
      DB_URL: postgres://prod-db.example.com/orders
      LOG_LEVEL: info
```

**Fields:**
- `name`: Environment identifier (dev, staging, prod, etc.)
- `workspace`: OpenTofu workspace name (must match environment)
- `variables`: Key-value pairs injected as Lambda environment variables

**Usage:** Variables are injected at deployment time based on the active workspace.

## Complete Annotated Example

```yaml
version: 1
service: orders
runtime: go
cloud: aws
ci: github
iac: opentofu
timezone: America/New_York

# Deployment configuration for serverless functions
deploy:
  arch: arm64                      # Use ARM64 for better cost/performance
  memory_mb: 256                   # Allocate 256 MB per function
  timeout_s: 30                    # 30 second timeout (max for API Gateway)

# HTTP configuration
http:
  simulate_apigw_limits: true      # Enforce 6 MB limit locally
  cors:
    enabled: true
    allow_origins:
      - "https://app.example.com"
      - "https://admin.example.com"
    allow_methods:
      - GET
      - POST
      - PUT
      - PATCH
      - DELETE
    allow_headers:
      - Content-Type
      - Authorization
      - X-Request-ID
  rate_limit:
    requests_per_minute: 100       # Local rate limiting only
    burst: 20

# Queue configuration (applies to all queues)
queues:
  max_batch_size: 10               # 10 messages per batch (SQS max)
  batch_window_s: 5                # Wait up to 5s for full batch
  visibility_timeout_s: 35         # Hide for 35s (timeout + 5s buffer)
  max_receive_count: 3             # 3 retries before DLQ
  error_mode: partial              # Per-message failure tracking

# Scheduled jobs inherit timezone from service-level setting
scheduled:
  # All cron schedules use America/New_York unless overridden inline

# Observability configuration
observability:
  logging:
    level: info                    # Standard logging level
    format: json                   # Structured JSON logs
  tracing:
    enabled: false                 # Opt-in tracing (adds overhead)
    provider: aws-xray             # Use AWS X-Ray when enabled

# Infrastructure configuration
infra:
  backend:
    type: s3
    bucket: my-company-transire-state
    dynamodb_table: transire-locks
    key_prefix: orders/            # Separate state per service
  vpc:
    enabled: false                 # Disable VPC for faster cold starts
  route53:
    hosted_zone_id: null           # No custom domain (use API Gateway URL)
  tags:
    env: dev
    service: orders
    team: backend
    owner: platform-team
    cost-center: engineering

# Environment-specific variables
env:
  - name: dev
    workspace: dev
    variables:
      DB_URL: postgres://dev-db.internal.example.com:5432/orders
      REDIS_URL: redis://dev-cache.internal.example.com:6379
      LOG_LEVEL: debug
      FEATURE_FLAG_NEW_CHECKOUT: "true"

  - name: staging
    workspace: staging
    variables:
      DB_URL: postgres://staging-db.internal.example.com:5432/orders
      REDIS_URL: redis://staging-cache.internal.example.com:6379
      LOG_LEVEL: info
      FEATURE_FLAG_NEW_CHECKOUT: "true"

  - name: prod
    workspace: prod
    variables:
      DB_URL: postgres://prod-db.internal.example.com:5432/orders
      REDIS_URL: redis://prod-cache.internal.example.com:6379
      LOG_LEVEL: warn
      FEATURE_FLAG_NEW_CHECKOUT: "false"
```

## Configuration Validation

### Validation Timing

Configuration is validated at multiple stages:

1. **Syntax validation:** `transire gen`, `transire run`, `transire deploy`
   - Invalid YAML → immediate error with line/column

2. **Semantic validation:** `transire gen`, `transire deploy`
   - Invalid values (e.g., `timeout_s: -5`) → error
   - Suspicious values (e.g., `timeout_s: 1000`) → warning

3. **On failure:** Commands exit with code 1 and descriptive error

### Common Validation Errors

**Invalid service name:**
```
Error: service name "MyService" contains invalid characters
Expected: [a-z0-9-]+ (lowercase alphanumeric and hyphens only)
```

**Invalid timeout:**
```
Error: deploy.timeout_s must be between 1 and 900 seconds
Found: 1000
```

**Missing required field:**
```
Error: missing required field 'service'
File: transire.yaml
```

**Invalid timezone:**
```
Error: invalid timezone 'America/NewYork'
Did you mean: America/New_York?
```

## Common Patterns

### Development vs Production

Use separate configurations with different resource allocations:

```yaml
# Development: smaller, faster iterations
env:
  - name: dev
    workspace: dev
    variables:
      # ... dev vars

deploy:
  memory_mb: 256
  timeout_s: 30

# Production: tune for performance
env:
  - name: prod
    workspace: prod
    variables:
      # ... prod vars

# Consider per-handler overrides in future versions
```

### Multi-Region Deployment

Use workspace names that include region:

```yaml
env:
  - name: prod-us-east-1
    workspace: prod-us-east-1
    variables:
      REGION: us-east-1
      # ...

  - name: prod-eu-west-1
    workspace: prod-eu-west-1
    variables:
      REGION: eu-west-1
      # ...
```

### Feature Flags

Use environment variables for feature toggles:

```yaml
env:
  - name: dev
    workspace: dev
    variables:
      FEATURE_NEW_API: "true"
      FEATURE_BETA_CHECKOUT: "true"

  - name: prod
    workspace: prod
    variables:
      FEATURE_NEW_API: "true"
      FEATURE_BETA_CHECKOUT: "false"  # Gradual rollout
```

### Secrets Management

**DO NOT** store secrets in `transire.yaml`. Use placeholders and inject via CI/CD:

```yaml
env:
  - name: prod
    workspace: prod
    variables:
      DB_PASSWORD: ${DB_PASSWORD}        # Injected by CI
      API_KEY: ${API_KEY}                # Injected by CI
```

Configure secrets in your CI provider (GitHub Secrets, etc.) and inject at deploy time.

## See Also

- [Manifest Schema](/docs/reference/manifest-schema.md) - Generated manifest format
- [Error Codes](/docs/reference/error-codes.md) - Configuration error codes
- [Deployment Guide](/docs/guides/deployment.md) - Deploying with different configurations
- [Environments Guide](/docs/guides/environments.md) - Managing multiple environments
- [OpenTofu Backend](/docs/iac/backend.md) - Backend setup and configuration
