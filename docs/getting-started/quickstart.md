---
title: Quick Start
category: getting-started
complexity: beginner
duration: 15 minutes
prerequisites:
  - Go 1.22 or later
  - AWS Account
  - AWS CLI configured
mcp_use: template
mcp_operations:
  - scaffold_project
  - validate_setup
  - deploy
features_covered:
  - HTTP handlers
  - Queue handlers
  - Scheduled jobs
  - Local development
  - Cloud deployment
code_blocks: true
last_updated: 2025-10-30
---

# Quick Start

Deploy your first Transire application in 15 minutes. You'll build a simple orders API with HTTP endpoints, queue processing, and scheduled jobs—then deploy it to AWS.

## What You'll Build

A complete orders API with:

- ✅ **HTTP endpoints** - Create and retrieve orders
- ✅ **Queue processing** - Async order fulfillment
- ✅ **Scheduled job** - Daily report generation
- ✅ **Local development** - Full emulation with hot reload
- ✅ **Cloud deployment** - Serverless infrastructure on AWS

## Prerequisites

Before starting, ensure you have:

- [x] **Go 1.22 or later** - [Download](https://golang.org/dl/)
- [x] **Transire CLI** - [Installation guide](installation.md)

**Verify prerequisites:**

```bash
$ go version
go version go1.22.0 darwin/arm64

$ transire version
Transire CLI v1.0.0
```

**Optional (for cloud deployment):**
- Cloud provider account (AWS, Azure, GCP)
- Cloud provider CLI configured

See [Cloud Deployment](#step-7-deploy-to-cloud-optional) below for provider-specific setup.

## Step 1: Create Project

Create a new directory and initialize the project:

```bash
# Create project
mkdir orders-api
cd orders-api

# Initialize Go module
go mod init github.com/yourusername/orders-api

# Install Transire SDK
go get github.com/transire/sdk-go@latest
```

**Note:** Cloud provider packages (like `github.com/transire/cloud-aws`) are only needed when deploying. You don't need them for local development.

## Step 2: Create Application

Create `main.go`:

```go
package main

import (
    "context"
    "encoding/json"
    "log"
    "net/http"
    "time"

    "github.com/transire/sdk-go"
    "github.com/transire/sdk-go/response"
)

func main() {
    // Create Transire application
    app := transire.New()

    // HTTP handlers
    app.GET("/orders", listOrders)
    app.GET("/orders/{id}", getOrder)
    app.POST("/orders", createOrder(app))

    // Queue handler for async processing
    app.RegisterQueue("fulfill-orders", fulfillOrders)

    // Scheduled job - runs daily at 9 AM
    app.RegisterScheduled("@daily 09:00", generateDailyReport)

    // Start application
    if err := app.Run(); err != nil {
        log.Fatal(err)
    }
}

// Order represents an order in our system
type Order struct {
    ID        string    `json:"id"`
    Product   string    `json:"product"`
    Quantity  int       `json:"quantity"`
    Status    string    `json:"status"`
    CreatedAt time.Time `json:"created_at"`
}

// In-memory store (for demo purposes)
var orders = make(map[string]Order)

// listOrders returns all orders
func listOrders(w http.ResponseWriter, r *http.Request) {
    orderList := make([]Order, 0, len(orders))
    for _, order := range orders {
        orderList = append(orderList, order)
    }
    response.OK(w, orderList)
}

// getOrder returns a specific order by ID
func getOrder(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")

    order, exists := orders[id]
    if !exists {
        response.NotFound(w, "Order not found")
        return
    }

    response.OK(w, order)
}

// createOrder creates a new order and enqueues it for fulfillment
func createOrder(app *transire.App) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        var req struct {
            Product  string `json:"product"`
            Quantity int    `json:"quantity"`
        }

        if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
            response.BadRequest(w, "Invalid request body")
            return
        }

        // Validate input
        if req.Product == "" || req.Quantity <= 0 {
            response.BadRequest(w, "Product and quantity are required")
            return
        }

        // Create order
        order := Order{
            ID:        generateID(),
            Product:   req.Product,
            Quantity:  req.Quantity,
            Status:    "pending",
            CreatedAt: time.Now(),
        }

        orders[order.ID] = order

        // Enqueue for async fulfillment
        if err := app.Enqueue(r.Context(), "fulfill-orders", order); err != nil {
            log.Printf("Failed to enqueue order: %v", err)
            // Continue - order is created, we can retry fulfillment
        }

        response.Created(w, order)
    }
}

// fulfillOrders processes a batch of orders asynchronously
func fulfillOrders(ctx context.Context, orderBatch []Order) error {
    log.Printf("Processing batch of %d orders", len(orderBatch))

    for _, order := range orderBatch {
        // Simulate order fulfillment
        log.Printf("Fulfilling order %s: %d x %s", order.ID, order.Quantity, order.Product)

        // Update order status
        order.Status = "fulfilled"
        orders[order.ID] = order

        // In a real app, this would:
        // - Reserve inventory
        // - Process payment
        // - Create shipping label
        // - Send confirmation email
    }

    return nil
}

// generateDailyReport generates a daily report of all orders
func generateDailyReport(ctx context.Context) error {
    log.Printf("Generating daily report")

    totalOrders := len(orders)
    fulfilledCount := 0

    for _, order := range orders {
        if order.Status == "fulfilled" {
            fulfilledCount++
        }
    }

    log.Printf("Daily Report: %d total orders, %d fulfilled", totalOrders, fulfilledCount)

    // In a real app, this would:
    // - Generate PDF report
    // - Upload to S3
    // - Send email to admins
    // - Update analytics dashboard

    return nil
}

// generateID generates a simple order ID (use UUID in production)
func generateID() string {
    return fmt.Sprintf("ORD-%d", time.Now().UnixNano())
}
```

**What's happening here?**

- **Lines 100-117:** Create app and register handlers (note: createOrder uses a closure to access the app)
- **Lines 121-128:** Define `Order` model with JSON tags
- **Lines 133-153:** HTTP handlers for listing and retrieving orders
- **Lines 155-193:** HTTP handler closure for creating orders + enqueueing to fulfillment queue
- **Lines 195-214:** Queue handler that processes orders in batches
- **Lines 216-239:** Scheduled job that generates daily reports

## Step 3: Create Configuration

Create `transire.yaml`:

```yaml
version: 1
service: orders-api
runtime: go
cloud: aws
iac: opentofu
ci: github
timezone: America/New_York

deploy:
  arch: arm64
  memory_mb: 256
  timeout_s: 30

http:
  simulate_apigw_limits: true
  cors:
    enabled: true
    allow_origins: ["*"]

queues:
  max_batch_size: 10
  batch_window_s: 5
  visibility_timeout_s: 30
  max_receive_count: 3

observability:
  logging:
    level: info
    format: json

infra:
  backend:
    type: local  # Default: local state (perfect for development/testing)
    # For production, use S3:
    # type: s3
    # bucket: orders-api-tf-state  # Change this to a unique bucket name
    # dynamodb_table: tf-locks
    # key_prefix: orders-api/

env:
  - name: dev
    workspace: dev
```

**Note:** The default local backend stores state in `infra/terraform.tfstate`. This is perfect for development. For production, use S3 backend (see [Backend Setup guide](../iac/backend.md)).

## Step 4: Generate Manifest

Run `transire gen` to analyze your code:

```bash
$ transire gen
✓ Analyzed package main
✓ Found 3 HTTP routes
✓ Found 1 queue handler
✓ Found 1 scheduled job
✓ Validated handler signatures
✓ Inferred message type: Order
✓ Generated transire_manifest.json
```

View the generated manifest:

```bash
$ cat transire_manifest.json
{
  "version": "1.0",
  "service": "orders-api",
  "http_routes": [
    {"method": "GET", "path": "/orders", "handler": "listOrders"},
    {"method": "GET", "path": "/orders/{id}", "handler": "getOrder"},
    {"method": "POST", "path": "/orders", "handler": "createOrder"}
  ],
  "queues": [
    {
      "key": "fulfill-orders",
      "message_type": "main.Order",
      "handler": "fulfillOrders"
    }
  ],
  "schedules": [
    {
      "key": "daily-report",
      "schedule": "cron(0 9 * * ? *)",
      "handler": "generateDailyReport"
    }
  ]
}
```

## Step 5: Run Locally

Start the development server:

```bash
$ transire run
✓ Starting HTTP server on :8080
✓ Queue emulator: 1 queue (fulfill-orders), 1 worker
✓ Scheduler: 1 job (daily-report, next run: tomorrow at 09:00)
→ Ready: http://localhost:8080
```

## Step 6: Test Locally

Open a new terminal and test your API:

### Create an Order

```bash
$ curl -X POST http://localhost:8080/orders \
  -H "Content-Type: application/json" \
  -d '{
    "product": "Widget",
    "quantity": 5
  }'

{
  "id": "ORD-1234567890",
  "product": "Widget",
  "quantity": 5,
  "status": "pending",
  "created_at": "2025-10-30T10:30:00Z"
}
```

Check the server logs—you should see the fulfillment queue processing:

```
Processing batch of 1 orders
Fulfilling order ORD-1234567890: 5 x Widget
```

### List All Orders

```bash
$ curl http://localhost:8080/orders

[
  {
    "id": "ORD-1234567890",
    "product": "Widget",
    "quantity": 5,
    "status": "fulfilled",
    "created_at": "2025-10-30T10:30:00Z"
  }
]
```

### Get Specific Order

```bash
$ curl http://localhost:8080/orders/ORD-1234567890

{
  "id": "ORD-1234567890",
  "product": "Widget",
  "quantity": 5,
  "status": "fulfilled",
  "created_at": "2025-10-30T10:30:00Z"
}
```

### Test Error Handling

```bash
$ curl http://localhost:8080/orders/nonexistent

{
  "error": "Order not found"
}
```

**Everything works!** Your app is running locally with:
- ✅ HTTP server handling requests
- ✅ Queue processing orders asynchronously
- ✅ Scheduled job ready to run at 9 AM

## Step 7: Deploy to Cloud (Optional)

**Ready to deploy?** This quickstart shows AWS deployment as an example. Transire supports multiple cloud providers.

**Choose your provider:**
- **AWS** - Continue below for AWS deployment
- **Azure** - See [Azure Provider Guide](/docs/providers/azure/) (coming soon)
- **GCP** - See [GCP Provider Guide](/docs/providers/gcp/) (coming soon)

### AWS Deployment Example

**Prerequisites:**
1. Install AWS provider package:
   ```bash
   go get github.com/transire/cloud-aws@latest
   ```

2. Add import to `main.go`:
   ```go
   import _ "github.com/transire/cloud-aws" // Auto-registers AWS provider
   ```

3. Configure AWS CLI:
   ```bash
   aws configure
   ```

### Deploy (with Local State)

Deploy your application to AWS:

```bash
$ transire deploy --environment=dev
Using local backend - state will be stored in infra/terraform.tfstate
✓ Analyzing code
✓ Generating manifest
✓ Packaging handlers
  → HTTP handler: build/orders-api-dev-http.zip (5.2 MB)
  → Queue handler: build/orders-api-dev-queue-fulfill-orders.zip (5.1 MB)
  → Scheduled handler: build/orders-api-dev-scheduled-daily-report.zip (5.1 MB)
✓ Generating OpenTofu configuration
✓ Initializing Tofu backend (local)
✓ Applying infrastructure
  → Creating API Gateway HTTP API
  → Creating Lambda functions (3)
  → Creating SQS queue: orders-api-dev-fulfill-orders
  → Creating SQS DLQ: orders-api-dev-fulfill-orders-dlq
  → Creating EventBridge rule: orders-api-dev-daily-report
  → Creating IAM roles and policies
✓ Deployment complete!

→ API URL: https://abc123xyz.execute-api.us-east-1.amazonaws.com

Test your API:
  curl https://abc123xyz.execute-api.us-east-1.amazonaws.com/orders
```

**Deployment takes 2-3 minutes.** Transire automatically:

1. Packages your handlers into Lambda-compatible zips
2. Generates complete OpenTofu configuration
3. Stores state locally in `infra/terraform.tfstate`
4. Creates API Gateway, Lambda functions, SQS queues, EventBridge rules
5. Sets up least-privilege IAM roles
6. Deploys everything to AWS

**Note:** Local state is perfect for development. For team collaboration or production, use S3 backend (see below).

## Step 8: Test in Production

Test your deployed API:

### Create an Order

```bash
$ curl -X POST https://abc123xyz.execute-api.us-east-1.amazonaws.com/orders \
  -H "Content-Type: application/json" \
  -d '{
    "product": "Gadget",
    "quantity": 10
  }'

{
  "id": "ORD-9876543210",
  "product": "Gadget",
  "quantity": 10,
  "status": "pending",
  "created_at": "2025-10-30T10:35:00Z"
}
```

### List Orders

```bash
$ curl https://abc123xyz.execute-api.us-east-1.amazonaws.com/orders

[
  {
    "id": "ORD-9876543210",
    "product": "Gadget",
    "quantity": 10,
    "status": "fulfilled",
    "created_at": "2025-10-30T10:35:00Z"
  }
]
```

**It works!** Your application is now running serverless on AWS.

## View AWS Resources

Check the created resources in AWS Console:

### Lambda Functions

```bash
$ aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `orders-api-dev`)].FunctionName'

[
  "orders-api-dev-http",
  "orders-api-dev-queue-fulfill-orders",
  "orders-api-dev-scheduled-daily-report"
]
```

### SQS Queues

```bash
$ aws sqs list-queues --queue-name-prefix orders-api-dev

{
  "QueueUrls": [
    "https://sqs.us-east-1.amazonaws.com/123456789012/orders-api-dev-fulfill-orders",
    "https://sqs.us-east-1.amazonaws.com/123456789012/orders-api-dev-fulfill-orders-dlq"
  ]
}
```

### API Gateway

```bash
$ aws apigatewayv2 get-apis --query 'Items[?Name==`orders-api-dev`]'
```

## View Logs

View Lambda logs in CloudWatch:

```bash
$ aws logs tail /aws/lambda/orders-api-dev-http --follow
```

Or use the AWS Console: CloudWatch → Log Groups → `/aws/lambda/orders-api-dev-http`

## Architecture

Here's what Transire deployed:

```
┌─────────────────────────────────────────────────────────┐
│                      AWS Cloud                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐      ┌───────────────────────────┐   │
│  │ API Gateway  │─────▶│  orders-api-dev-http      │   │
│  │ HTTP API     │      │  (Lambda)                 │   │
│  └──────────────┘      │  • GET /orders            │   │
│                        │  • GET /orders/{id}       │   │
│                        │  • POST /orders           │   │
│                        └───────────┬───────────────┘   │
│                                    │ Enqueue            │
│                                    ▼                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │  SQS: orders-api-dev-fulfill-orders              │  │
│  └───────────┬──────────────────────────────────────┘  │
│              │ Batch invocation                        │
│              ▼                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  orders-api-dev-queue-fulfill-orders (Lambda)    │  │
│  │  • Process order batches                         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  EventBridge: orders-api-dev-daily-report        │  │
│  │  Rule: cron(0 9 * * ? *)                         │  │
│  └───────────┬──────────────────────────────────────┘  │
│              │ Trigger                                  │
│              ▼                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  orders-api-dev-scheduled-daily-report (Lambda)  │  │
│  │  • Generate daily report                         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Clean Up

To avoid AWS charges, destroy the deployed resources:

```bash
$ transire destroy
⚠ This will destroy all resources for orders-api-dev
Continue? (yes/no): yes

✓ Destroying infrastructure
  → Deleting Lambda functions
  → Deleting API Gateway
  → Deleting SQS queues
  → Deleting EventBridge rules
  → Deleting IAM roles
✓ Resources destroyed
```

**Note:** This does not delete the S3 backend bucket (to preserve state history).

## What's Next?

Congratulations! You've built and deployed a complete cloud-native application with Transire in 15 minutes.

### Learn More

- **[SDK Reference](../sdk/overview.md)** - Deep dive into HTTP, queue, and schedule handlers
- **[Testing Guide](../guides/testing.md)** - Write tests for your handlers
- **[Deployment Guide](../guides/deployment.md)** - Production deployment best practices
- **[Examples](../examples/orders.md)** - More complete example applications

### Add More Features

Try adding these features to your app:

- **Authentication** - Add middleware for JWT validation
- **Database** - Connect to RDS or DynamoDB
- **Error handling** - Use `BatchResult` for partial failures
- **Observability** - Enable tracing and metrics
- **CI/CD** - Set up GitHub Actions for automatic deployment

### Join the Community

- [GitHub](https://github.com/transire/transire) - Report issues, contribute
- [Discussions](https://github.com/transire/transire/discussions) - Ask questions
- [Discord](https://discord.gg/transire) - Chat with the community

## Upgrading to S3 Backend (Production)

The default local backend is perfect for development, but for team collaboration or production deployments, upgrade to S3 backend:

### Step 1: Update Configuration

Update `transire.yaml`:

```yaml
infra:
  backend:
    type: s3
    bucket: orders-api-tf-state  # Change to unique name
    dynamodb_table: tf-locks
    key_prefix: orders-api/
```

### Step 2: Initialize S3 Backend

Run the init command to create S3 bucket and DynamoDB table:

```bash
$ transire init --backend
✓ Creating S3 bucket: orders-api-tf-state
✓ Enabling versioning on bucket
✓ Creating DynamoDB table: tf-locks
✓ Backend initialized
```

### Step 3: Migrate State

Migrate your existing local state to S3:

```bash
cd infra
tofu init -migrate-state
```

Answer "yes" when prompted to copy existing state.

### Benefits of S3 Backend

- ✅ **Team collaboration** - Shared state across team members
- ✅ **State locking** - Prevents concurrent modifications with DynamoDB
- ✅ **State versioning** - Rollback capability via S3 versioning
- ✅ **Encryption** - State encrypted at rest in S3
- ✅ **Backup** - Automatic S3 durability and replication

## Troubleshooting

### Deployment Fails

**Error:** `Error: Failed to initialize backend`

**Solution:** For local backend, ensure you have write permissions in the infra/ directory. For S3 backend, ensure AWS credentials have S3/DynamoDB permissions.

---

**Error:** `Error: AccessDenied: User is not authorized`

**Solution:** Ensure AWS credentials have necessary permissions (Lambda, API Gateway, SQS, EventBridge, IAM, S3).

### Queue Not Processing

**Issue:** Orders created but never fulfilled

**Solution:** Check Lambda logs for the queue handler:

```bash
aws logs tail /aws/lambda/orders-api-dev-queue-fulfill-orders --follow
```

### Scheduled Job Not Running

**Issue:** Daily report not generating

**Solution:**
1. Check EventBridge rule is enabled:
   ```bash
   aws events describe-rule --name orders-api-dev-daily-report
   ```
2. Wait until scheduled time or manually trigger via AWS Console

## See Also

- [Installation](installation.md) - Install Transire CLI
- [Project Setup](project-setup.md) - Detailed project setup guide
- [HTTP Handlers](../sdk/http.md) - HTTP handler reference
- [Queue Handlers](../sdk/queue.md) - Queue processing guide
- [Scheduled Jobs](../sdk/schedule.md) - Scheduling reference
