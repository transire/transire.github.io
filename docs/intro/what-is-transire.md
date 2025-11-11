---
title: What is Transire?
category: introduction
complexity: beginner
duration: 5 minutes
mcp_use: reference
---

# What is Transire?

Transire is a cloud-native development framework for Go that lets you write your application once and run it anywhere—locally or in the cloud. No serverless complexity. No infrastructure boilerplate. Just code.

## The Problem

Building cloud-native applications typically requires:

- **Different code for local and cloud** - Separate logic for development and production
- **Infrastructure boilerplate** - Dozens of files for Lambda, API Gateway, SQS, EventBridge
- **Manual IaC management** - Writing and maintaining Terraform/CloudFormation templates
- **Complex deployment** - Multi-step processes for packaging and deploying
- **Limited local testing** - Difficult to test queues and schedules locally

## The Transire Solution

Transire eliminates this complexity with a **zero-boilerplate approach**:

```go
package main

import (
    "context"
    "github.com/transire/sdk-go"
    "github.com/transire/sdk-go/response"
)

func main() {
    app := transire.New()

    // HTTP endpoint - standard Go HTTP handler
    app.GET("/orders/{id}", getOrder)

    // Queue handler - type-safe, batch-optimized
    app.RegisterQueue("process-orders", processOrders)

    // Scheduled job - cron-style scheduling
    app.Schedule("daily-report", "@daily 09:00", generateReport)

    app.Run()
}

func getOrder(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")
    // ... fetch order from database
    response.OK(w, order)
}

func processOrders(ctx context.Context, orders []Order) error {
    // Process batch of orders
    for _, order := range orders {
        if err := process(ctx, order); err != nil {
            return err
        }
    }
    return nil
}

func generateReport(ctx context.Context) error {
    // Generate daily report
    return createReport(ctx)
}
```

**That's it!** This same code runs:

- **Locally:** Full HTTP server with in-memory queue and scheduler emulators
- **In the cloud:** Serverless functions (Lambda, API Gateway, SQS, EventBridge)

## Key Features

### Same Code, Anywhere

Write your application logic once. Transire automatically adapts to the runtime environment:

- **Local development:** Full HTTP server, in-memory queues, fixed-rate scheduler
- **Cloud deployment:** Serverless functions with managed infrastructure

### Zero Boilerplate

Transire handles all the infrastructure code:

- ✅ HTTP routing with path parameters and middleware
- ✅ Type-safe message queues with batch processing
- ✅ Cron-style scheduled jobs
- ✅ Dependency injection for services and databases
- ✅ Error handling, logging, and tracing
- ✅ OpenTofu infrastructure generation
- ✅ Deployment automation

### Build-Time Manifest

Transire uses **static analysis** (Go AST) to generate a manifest of your application at build time:

```bash
$ transire gen
✓ Analyzed package main
✓ Found 5 HTTP routes
✓ Found 2 queue handlers
✓ Found 1 scheduled job
✓ Generated transire_manifest.json
```

No runtime reflection. No magic. Just clear, explicit registration that's analyzed statically.

### Production Ready

Transire includes production features out of the box:

- **Graceful shutdown** - Respects context cancellation, 30s default timeout
- **Structured logging** - JSON logs with request context
- **Distributed tracing** - OTEL-compatible, opt-in
- **Partial batch failures** - Per-message success/failure tracking for queues
- **Dead-letter queues** - Automatic DLQ for failed messages
- **Least-privilege IAM** - Generated IAM roles with minimal permissions

### Cloud-Agnostic

Transire uses a pluggable provider system:

- **Cloud providers:** AWS (MVP), GCP/Azure (future)
- **IaC providers:** OpenTofu (MVP), Terraform (future)
- **CI providers:** GitHub Actions (MVP), GitLab CI (future)

Start with AWS, extend to any cloud or infrastructure tool.

## How It Works

### 1. Write Your Application

Use standard Go patterns for HTTP handlers. Add queue and schedule handlers using Transire's registration API.

### 2. Generate Manifest

Run `transire gen` to analyze your code and generate a manifest:

```json
{
  "http_routes": [
    {"method": "GET", "path": "/orders/{id}", "handler": "getOrder"}
  ],
  "queues": [
    {"key": "process-orders", "message_type": "Order", "handler": "processOrders"}
  ],
  "schedules": [
    {"key": "daily-report", "schedule": "@daily 09:00", "handler": "generateReport"}
  ]
}
```

### 3. Run Locally

Start the development server with full emulation:

```bash
$ transire run
✓ Starting HTTP server on :8080
✓ Queue emulator: 2 queues, 1 worker per queue
✓ Scheduler: 1 job
→ Ready: http://localhost:8080
```

### 4. Deploy to Cloud

Deploy with one command. Transire generates and applies all infrastructure:

```bash
$ transire deploy
✓ Packaged 5 handlers
✓ Generated OpenTofu configuration
✓ Created S3 backend
✓ Applied infrastructure
→ API URL: https://abc123.execute-api.us-east-1.amazonaws.com
```

## Design Philosophy

Transire is built on these principles:

### Developer Experience First

Minimal API surface, intuitive patterns, fast feedback loops. If it feels like fighting the framework, it's a bug.

### Zero Magic

No runtime reflection, explicit registration, clear behavior. You should always know what Transire is doing.

### Build-Time Analysis

Use Go's AST and type system for manifest generation. Catch errors at build time, not runtime.

### Production Ready

Observability, error handling, and graceful shutdown aren't afterthoughts—they're built-in.

### Cloud-Agnostic

Pluggable providers let you start with one cloud and expand to others without rewriting your application.

## When to Use Transire

Transire is ideal for:

- ✅ RESTful APIs with background processing
- ✅ Event-driven architectures with queues
- ✅ Scheduled jobs and cron workflows
- ✅ Microservices with HTTP + async messaging
- ✅ Cloud-native apps that need local development

Transire might not be the best fit for:

- ❌ Long-running processes (use containers/Kubernetes)
- ❌ Real-time streaming (use Kafka, Kinesis directly)
- ❌ GraphQL subscriptions (use purpose-built tools)
- ❌ Stateful applications (serverless is stateless)

## Comparisons

### vs. AWS Lambda + SAM/CDK

| Feature | Transire | Lambda + SAM/CDK |
|---------|----------|------------------|
| **Boilerplate** | Zero | High (separate handler files, IaC) |
| **Local development** | Full emulator | SAM local (limited) |
| **Type-safe queues** | Built-in | Manual marshaling |
| **HTTP routing** | Chi router in code | API Gateway config |
| **Deployment** | One command | Multi-step (build, package, deploy) |
| **Cloud-agnostic** | Yes (pluggable) | No (AWS-specific) |

### vs. Serverless Framework

| Feature | Transire | Serverless Framework |
|---------|----------|----------------------|
| **Language** | Go-native | Multi-language |
| **Configuration** | Minimal YAML | Large serverless.yml |
| **Local development** | Full emulator | Plugins required |
| **Type safety** | Compile-time | Runtime |
| **IaC generation** | Automatic | Manual templates |
| **Build-time analysis** | AST-based | Runtime conventions |

### vs. Traditional Frameworks (Gin, Echo, Fiber)

| Feature | Transire | Gin/Echo/Fiber |
|---------|----------|----------------|
| **Deployment target** | Serverless + local | Containers/VMs |
| **Queue handlers** | Built-in | External tools |
| **Scheduled jobs** | Built-in | External tools |
| **Infrastructure** | Auto-generated | Manual setup |
| **Scalability** | Automatic (serverless) | Manual (containers) |
| **Cost model** | Pay-per-request | Always-on |

## Next Steps

Ready to build your first Transire app?

**[Quick Start →](../getting-started/quickstart.md){ .md-button .md-button--primary }**

Or dive deeper into [core concepts](concepts.md) and architecture.

## See Also

- [Core Concepts](concepts.md) - Understand handlers, queues, schedules, and DI
- [Quick Start](../getting-started/quickstart.md) - Deploy your first app in 15 minutes
- [SDK Reference](../sdk/overview.md) - Complete API documentation
