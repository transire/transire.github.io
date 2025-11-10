---
title: "AWS Cloud Provider"
category: cloud
subcategory: aws
complexity: intermediate
duration: null
prerequisites:
  - AWS account
  - AWS CLI configured
  - Basic understanding of AWS services
mcp_use: reference
mcp_operations:
  - understand_aws_architecture
  - configure_aws_deployment
features_covered:
  - AWS Lambda
  - API Gateway
  - SQS
  - EventBridge
  - IAM
code_blocks: true
last_updated: 2025-10-30
---

# AWS Cloud Provider

## Overview

Transire's AWS provider deploys your application to AWS using serverless services. Your handlers run as Lambda functions, HTTP endpoints are exposed via API Gateway, queues use SQS, and schedules use EventBridge.

**AWS Services Used:**
- **Lambda** - Runs your handlers (HTTP, queue, schedule)
- **API Gateway HTTP API** - HTTP endpoint routing
- **SQS** - Queue message delivery
- **EventBridge** - Scheduled job triggers
- **IAM** - Least-privilege permissions
- **S3** - State storage (backend)
- **DynamoDB** - State locking (backend)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AWS Cloud                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐        ┌──────────────────────────┐  │
│  │  API Gateway │───────▶│  Lambda (HTTP Handlers)  │  │
│  │  HTTP API    │        │  - GET /orders           │  │
│  └──────────────┘        │  - POST /orders          │  │
│                          │  - PUT /orders/{id}      │  │
│                          └──────────────────────────┘  │
│                                                          │
│  ┌──────────────┐        ┌──────────────────────────┐  │
│  │  SQS Queue   │───────▶│  Lambda (Queue Handler)  │  │
│  │  + DLQ       │        │  - processOrderCreated   │  │
│  └──────────────┘        └──────────────────────────┘  │
│                                                          │
│  ┌──────────────┐        ┌──────────────────────────┐  │
│  │  EventBridge │───────▶│  Lambda (Scheduled Job)  │  │
│  │  Rule        │        │  - sendDailyReport       │  │
│  └──────────────┘        └──────────────────────────┘  │
│                                                          │
│  ┌──────────────┐        ┌──────────────────────────┐  │
│  │  IAM Roles   │───────▶│  Least-Privilege         │  │
│  │  & Policies  │        │  Permissions             │  │
│  └──────────────┘        └──────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Lambda Configuration

Transire deploys Lambda functions with these defaults (configurable in `transire.yaml`):

### Runtime

- **Runtime:** `provided.al2023` (custom runtime on Amazon Linux 2023)
- **Architecture:** ARM64 (Graviton2 - better price/performance)
- **Language:** Go (compiled to static binary)

### Resources

Configure in `transire.yaml`:

```yaml
deploy:
  arch: arm64              # arm64 or x86_64
  memory_mb: 256          # 128-10240 MB
  timeout_s: 30           # Max 900s (15 min)
```

**Recommendations:**
- **Memory:** Start with 256 MB, increase if OOM errors occur
- **Timeout:** Match your longest handler execution time
- **Architecture:** ARM64 (20% cheaper, similar performance)

## API Gateway HTTP API

HTTP handlers are exposed via API Gateway HTTP API v2:

### Features

- **Protocol:** HTTP/1.1 and HTTP/2
- **Methods:** GET, POST, PUT, PATCH, DELETE
- **Path parameters:** `/orders/{id}`
- **Query parameters:** `?status=pending&limit=10`
- **Headers:** All standard HTTP headers
- **Body:** JSON, form data, binary
- **Max request size:** 10 MB (payload)
- **Max response size:** 10 MB

### Generated Resources

For each HTTP handler, Transire creates:

- **Route:** Method + path (e.g., `GET /orders`)
- **Integration:** API Gateway → Lambda
- **Permissions:** Allow API Gateway to invoke Lambda

### CORS

Enable CORS in `transire.yaml`:

```yaml
http:
  cors:
    enabled: true
    allow_origins: ["https://app.example.com"]
    allow_methods: ["GET", "POST", "PUT", "DELETE"]
    allow_headers: ["Content-Type", "Authorization"]
```

Generated CORS configuration:
- Preflight (`OPTIONS`) handled automatically
- Headers: `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, etc.

### Custom Domain

Configure custom domain (requires Route53):

```yaml
infra:
  route53:
    hosted_zone_id: Z1234567890ABC
    domain: api.example.com
```

Transire creates:
- ACM certificate
- API Gateway custom domain
- Route53 alias record

## SQS Queues

Queue handlers use SQS for message delivery:

### Queue Configuration

Configure in `transire.yaml`:

```yaml
queues:
  max_batch_size: 10           # Messages per batch (1-10 for SQS)
  batch_window_s: 5            # Max seconds to wait for batch
  visibility_timeout_s: 30     # Time before message visible again
  max_receive_count: 3         # Retries before DLQ
```

### Generated Resources

For each queue handler, Transire creates:

- **SQS Queue:** `${service}-${env}-${queue_key}`
- **SQS DLQ:** `${service}-${env}-${queue_key}-dlq`
- **Lambda Event Source Mapping:** SQS → Lambda
- **IAM Permissions:** Lambda can receive/delete messages

### Message Attributes

Transire adds these attributes to each message:

- `__type` - Message type (e.g., `github.com/acme/orders.OrderCreated`)
- `traceparent` - W3C trace context (for distributed tracing)
- `tracestate` - W3C trace state (vendor-specific data)

### Batch Processing

SQS invokes Lambda with batches:

```json
{
  "Records": [
    {
      "messageId": "...",
      "body": "{\"order_id\":\"123\",\"user_id\":\"456\"}",
      "messageAttributes": {
        "__type": {"stringValue": "github.com/acme/orders.OrderCreated"}
      }
    }
  ]
}
```

Transire's adapter:
1. Parses SQS event
2. Validates message types
3. Deserializes messages
4. Calls your handler with `[]T`
5. Returns partial batch response for failures

## EventBridge Schedules

Scheduled jobs use EventBridge rules:

### Schedule Expressions

Transire converts shorthand to EventBridge cron:

| Transire Syntax | EventBridge Expression | Description |
|----------------|------------------------|-------------|
| `@hourly` | `rate(1 hour)` | Every hour |
| `@daily` | `rate(1 day)` | Every 24 hours |
| `@daily 09:00` | `cron(0 9 * * ? *)` | Daily at 9 AM |
| `cron(0 12 * * ? *)` | `cron(0 12 * * ? *)` | Pass-through |

### Generated Resources

For each scheduled job, Transire creates:

- **EventBridge Rule:** With cron/rate expression
- **Lambda Target:** Rule → Lambda
- **IAM Permissions:** EventBridge can invoke Lambda

### Timezone Handling

EventBridge uses UTC by default. Transire adjusts cron expressions based on service timezone:

```yaml
timezone: America/New_York  # Service-level timezone
```

```go
app.RegisterScheduled("@daily 09:00", handler)
// Converted to cron(0 14 * * ? *) in EventBridge (UTC)
```

## IAM Permissions

Transire generates least-privilege IAM roles:

### HTTP Handler Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": ["sqs:SendMessage"],
      "Resource": "arn:aws:sqs:*:*:orders-*"
    }
  ]
}
```

Allows:
- CloudWatch Logs (all handlers)
- Send to SQS (if handler enqueues messages)

### Queue Handler Role

```json
{
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["logs:*"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"],
      "Resource": "arn:aws:sqs:*:*:orders-dev-OrderCreated"
    }
  ]
}
```

Allows:
- CloudWatch Logs
- Receive/delete from specific queue

### Custom Permissions

Add custom permissions in `infra/overrides/`:

```hcl
resource "aws_iam_role_policy_attachment" "http_s3" {
  role       = aws_iam_role.http_lambda.name
  policy_arn = aws_iam_policy.s3_access.arn
}
```

## Deployment Workflow

`transire deploy` performs these steps:

### 1. Build Binaries

For each handler type:

```bash
# HTTP handlers (single binary with all routes)
GOOS=linux GOARCH=arm64 go build -o bootstrap-http cmd/http/main.go

# Queue handler
GOOS=linux GOARCH=arm64 go build -o bootstrap-queue-OrderCreated cmd/queue/OrderCreated/main.go

# Scheduled job
GOOS=linux GOARCH=arm64 go build -o bootstrap-schedule-dailyReport cmd/schedule/dailyReport/main.go
```

### 2. Package Binaries

Zip each binary:

```bash
zip http.zip bootstrap-http
zip queue-OrderCreated.zip bootstrap-queue-OrderCreated
zip schedule-dailyReport.zip bootstrap-schedule-dailyReport
```

### 3. Generate IaC

Create OpenTofu files:

```
infra/
├── generated/
│   ├── main.tf           # Provider config
│   ├── http.tf           # API Gateway + Lambda
│   ├── queues.tf         # SQS + Lambda + Event Source Mappings
│   ├── schedules.tf      # EventBridge + Lambda
│   ├── iam.tf            # Roles and policies
│   └── outputs.tf        # API URL, queue names, etc.
└── overrides/
    └── custom.tf         # Your custom resources
```

### 4. Apply Infrastructure

```bash
tofu init
tofu plan
tofu apply
```

## Costs

Rough AWS costs for a typical Transire app:

### Lambda

- **Requests:** $0.20 per million requests
- **Duration:** $0.0000166667 per GB-second
- **Example:** 1M requests/month @ 256MB, 100ms avg
  - Requests: $0.20
  - Duration: $0.42
  - **Total:** ~$0.62/month

### API Gateway

- **Requests:** $1.00 per million requests
- **Example:** 1M requests/month
  - **Total:** ~$1.00/month

### SQS

- **Requests:** $0.40 per million requests (after free tier)
- **Example:** 100K messages/month
  - **Total:** ~$0.04/month

### EventBridge

- **Invocations:** $1.00 per million invocations
- **Example:** 1K invocations/month (hourly job)
  - **Total:** ~$0.001/month

### Total Estimate

For 1M HTTP requests, 100K queue messages, hourly schedule:

**~$2/month** (excluding data transfer)

Add:
- **S3 (state):** ~$0.01/month
- **DynamoDB (locks):** ~$0.01/month
- **CloudWatch Logs:** ~$0.50/month (5GB logs)

**Grand Total: ~$2.50/month**

## Monitoring

AWS services provide built-in monitoring:

### CloudWatch Metrics

- **Lambda:** Invocations, errors, duration, throttles
- **API Gateway:** Request count, latency, errors
- **SQS:** Messages sent/received, age, dead-letter count
- **EventBridge:** Invocations, failed invocations

### CloudWatch Logs

Each Lambda function writes logs to CloudWatch Logs:

```
/aws/lambda/orders-dev-get-orders
/aws/lambda/orders-dev-processOrderCreated
/aws/lambda/orders-dev-sendDailyReport
```

### X-Ray Tracing

Enable tracing in `transire.yaml`:

```yaml
observability:
  tracing:
    enabled: true
    provider: aws-xray
```

Transire enables X-Ray for all Lambda functions.

## See Also

- [AWS HTTP (API Gateway)](/docs/cloud/aws/http.md) - HTTP endpoint details
- [AWS Queues (SQS)](/docs/cloud/aws/queues.md) - Queue implementation details
- [AWS Schedules (EventBridge)](/docs/cloud/aws/schedules.md) - Schedule implementation details
- [Deployment Guide](/docs/guides/deployment.md) - Deployment best practices
- [Configuration](/docs/reference/config-schema.md) - Configuration options
