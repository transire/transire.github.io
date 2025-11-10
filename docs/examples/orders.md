---
title: "Complete Orders API Example"
category: examples
subcategory: null
complexity: intermediate
duration: 45 minutes
prerequisites:
  - Completed Quick Start
  - Go 1.22+
  - AWS account configured
mcp_use: template
mcp_operations:
  - scaffold_project
  - generate_example
  - deploy_example
features_covered:
  - HTTP CRUD endpoints
  - Queue handlers
  - Scheduled jobs
  - Dependency injection
  - Error handling
  - Testing
  - Deployment
code_blocks: true
last_updated: 2025-10-30
---

# Complete Orders API Example

## Overview

This example demonstrates a production-ready Orders API built with Transire. It showcases:

- **HTTP handlers:** CRUD operations for orders
- **Queue handlers:** Asynchronous order processing
- **Scheduled jobs:** Daily order reports
- **Dependency injection:** Service layer with shared dependencies
- **Error handling:** Graceful error responses and batch processing
- **Testing:** Unit and integration tests
- **Deployment:** Multi-environment AWS deployment

By the end of this guide, you'll have a fully functional API that:
- Creates and manages orders via REST endpoints
- Processes orders asynchronously via queues
- Generates daily reports via scheduled jobs
- Can be deployed to AWS with a single command

## Features Covered

### HTTP Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/orders` | List all orders |
| GET | `/orders/{id}` | Get order by ID |
| POST | `/orders` | Create new order |
| PUT | `/orders/{id}` | Update order |
| DELETE | `/orders/{id}` | Delete order |
| GET | `/health` | Health check |

### Queue Handlers

- **ProcessedOrder:** Async order fulfillment and notifications
- **OrderEmail:** Email notifications to customers

### Scheduled Jobs

- **Daily Report:** Generate and email daily order summaries at 9 AM

## Project Structure

```
orders-api/
├── main.go                 # Main application with all registrations
├── transire.yaml           # Configuration
├── go.mod                  # Go module dependencies
├── go.sum
├── models/
│   └── order.go           # Order data model
├── services/
│   ├── order_service.go   # Business logic
│   └── email_service.go   # Email sending
└── handlers/
    ├── http_handlers.go   # HTTP endpoint handlers
    ├── queue_handlers.go  # Queue message handlers
    └── schedule_handlers.go # Scheduled job handlers
```

## Complete Code Walkthrough

### Step 1: Project Setup

Create a new project:

```bash
mkdir orders-api
cd orders-api
go mod init github.com/yourname/orders-api
```

Install dependencies:

```bash
go get github.com/transire/sdk-go
go get github.com/transire/sdk-go/response
```

### Step 2: Data Models

Create `models/order.go`:

```go
package models

import "time"

// Order represents a customer order
type Order struct {
    ID          string    `json:"id"`
    CustomerID  string    `json:"customer_id"`
    Items       []Item    `json:"items"`
    TotalAmount float64   `json:"total_amount"`
    Status      string    `json:"status"`
    CreatedAt   time.Time `json:"created_at"`
    UpdatedAt   time.Time `json:"updated_at"`
}

// Item represents a product in an order
type Item struct {
    SKU      string  `json:"sku"`
    Name     string  `json:"name"`
    Quantity int     `json:"quantity"`
    Price    float64 `json:"price"`
}

// OrderStatus constants
const (
    StatusPending    = "pending"
    StatusProcessing = "processing"
    StatusCompleted  = "completed"
    StatusCancelled  = "cancelled"
)

// CreateOrderRequest is the request payload for creating orders
type CreateOrderRequest struct {
    CustomerID string  `json:"customer_id"`
    Items      []Item  `json:"items"`
}

// UpdateOrderRequest is the request payload for updating orders
type UpdateOrderRequest struct {
    Status string `json:"status"`
    Items  []Item `json:"items,omitempty"`
}

// ProcessedOrder is the queue message for async processing
type ProcessedOrder struct {
    OrderID    string    `json:"order_id"`
    CustomerID string    `json:"customer_id"`
    Amount     float64   `json:"amount"`
    ProcessAt  time.Time `json:"process_at"`
}

// OrderEmail is the queue message for email notifications
type OrderEmail struct {
    OrderID       string `json:"order_id"`
    CustomerEmail string `json:"customer_email"`
    Subject       string `json:"subject"`
    Body          string `json:"body"`
}
```

### Step 3: Service Layer

Create `services/order_service.go`:

```go
package services

import (
    "context"
    "fmt"
    "sync"
    "time"

    "github.com/google/uuid"
    "github.com/yourname/orders-api/models"
)

// OrderService handles business logic for orders
type OrderService struct {
    mu     sync.RWMutex
    orders map[string]*models.Order
}

// NewOrderService creates a new order service
func NewOrderService() *OrderService {
    return &OrderService{
        orders: make(map[string]*models.Order),
    }
}

// ListOrders returns all orders
func (s *OrderService) ListOrders(ctx context.Context) ([]*models.Order, error) {
    s.mu.RLock()
    defer s.mu.RUnlock()

    orders := make([]*models.Order, 0, len(s.orders))
    for _, order := range s.orders {
        orders = append(orders, order)
    }
    return orders, nil
}

// GetOrder retrieves an order by ID
func (s *OrderService) GetOrder(ctx context.Context, id string) (*models.Order, error) {
    s.mu.RLock()
    defer s.mu.RUnlock()

    order, exists := s.orders[id]
    if !exists {
        return nil, fmt.Errorf("order not found: %s", id)
    }
    return order, nil
}

// CreateOrder creates a new order
func (s *OrderService) CreateOrder(ctx context.Context, req models.CreateOrderRequest) (*models.Order, error) {
    // Validate request
    if req.CustomerID == "" {
        return nil, fmt.Errorf("customer_id is required")
    }
    if len(req.Items) == 0 {
        return nil, fmt.Errorf("at least one item is required")
    }

    // Calculate total amount
    var total float64
    for _, item := range req.Items {
        if item.Quantity <= 0 {
            return nil, fmt.Errorf("item quantity must be positive")
        }
        if item.Price < 0 {
            return nil, fmt.Errorf("item price cannot be negative")
        }
        total += float64(item.Quantity) * item.Price
    }

    // Create order
    now := time.Now()
    order := &models.Order{
        ID:          uuid.New().String(),
        CustomerID:  req.CustomerID,
        Items:       req.Items,
        TotalAmount: total,
        Status:      models.StatusPending,
        CreatedAt:   now,
        UpdatedAt:   now,
    }

    s.mu.Lock()
    s.orders[order.ID] = order
    s.mu.Unlock()

    return order, nil
}

// UpdateOrder updates an existing order
func (s *OrderService) UpdateOrder(ctx context.Context, id string, req models.UpdateOrderRequest) (*models.Order, error) {
    s.mu.Lock()
    defer s.mu.Unlock()

    order, exists := s.orders[id]
    if !exists {
        return nil, fmt.Errorf("order not found: %s", id)
    }

    // Update status if provided
    if req.Status != "" {
        // Validate status
        validStatus := map[string]bool{
            models.StatusPending:    true,
            models.StatusProcessing: true,
            models.StatusCompleted:  true,
            models.StatusCancelled:  true,
        }
        if !validStatus[req.Status] {
            return nil, fmt.Errorf("invalid status: %s", req.Status)
        }
        order.Status = req.Status
    }

    // Update items if provided
    if len(req.Items) > 0 {
        var total float64
        for _, item := range req.Items {
            total += float64(item.Quantity) * item.Price
        }
        order.Items = req.Items
        order.TotalAmount = total
    }

    order.UpdatedAt = time.Now()
    return order, nil
}

// DeleteOrder deletes an order
func (s *OrderService) DeleteOrder(ctx context.Context, id string) error {
    s.mu.Lock()
    defer s.mu.Unlock()

    if _, exists := s.orders[id]; !exists {
        return fmt.Errorf("order not found: %s", id)
    }

    delete(s.orders, id)
    return nil
}

// ProcessOrder processes an order (called by queue handler)
func (s *OrderService) ProcessOrder(ctx context.Context, orderID string) error {
    s.mu.Lock()
    defer s.mu.Unlock()

    order, exists := s.orders[orderID]
    if !exists {
        return fmt.Errorf("order not found: %s", orderID)
    }

    // Simulate processing
    order.Status = models.StatusProcessing
    order.UpdatedAt = time.Now()

    // In real app: charge payment, reserve inventory, etc.
    // For demo, just mark as completed
    order.Status = models.StatusCompleted
    order.UpdatedAt = time.Now()

    return nil
}

// GetOrdersForReport returns orders for daily reporting
func (s *OrderService) GetOrdersForReport(ctx context.Context, since time.Time) ([]*models.Order, error) {
    s.mu.RLock()
    defer s.mu.RUnlock()

    orders := make([]*models.Order, 0)
    for _, order := range s.orders {
        if order.CreatedAt.After(since) {
            orders = append(orders, order)
        }
    }
    return orders, nil
}
```

Create `services/email_service.go`:

```go
package services

import (
    "context"
    "fmt"
    "log"
)

// EmailService handles email sending
type EmailService struct {
    fromAddress string
}

// NewEmailService creates a new email service
func NewEmailService(fromAddress string) *EmailService {
    return &EmailService{
        fromAddress: fromAddress,
    }
}

// SendOrderConfirmation sends order confirmation email
func (s *EmailService) SendOrderConfirmation(ctx context.Context, customerEmail, orderID string, amount float64) error {
    // In production, use AWS SES, SendGrid, etc.
    log.Printf("Sending order confirmation email to %s for order %s (amount: $%.2f)",
        customerEmail, orderID, amount)
    return nil
}

// SendDailyReport sends daily report email
func (s *EmailService) SendDailyReport(ctx context.Context, toEmail, report string) error {
    // In production, use actual email service
    log.Printf("Sending daily report email to %s:\n%s", toEmail, report)
    return nil
}
```

### Step 4: HTTP Handlers

Create `handlers/http_handlers.go`:

```go
package handlers

import (
    "encoding/json"
    "net/http"

    "github.com/transire/sdk-go"
    "github.com/transire/sdk-go/response"
    "github.com/yourname/orders-api/models"
    "github.com/yourname/orders-api/services"
)

// ListOrders handles GET /orders
func ListOrders(w http.ResponseWriter, r *http.Request) {
    svc := transire.MustGet[*services.OrderService](r.Context())

    orders, err := svc.ListOrders(r.Context())
    if err != nil {
        response.InternalServerError(w, "Failed to list orders")
        return
    }

    response.OK(w, orders)
}

// GetOrder handles GET /orders/{id}
func GetOrder(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")
    svc := transire.MustGet[*services.OrderService](r.Context())

    order, err := svc.GetOrder(r.Context(), id)
    if err != nil {
        response.NotFound(w, "Order not found")
        return
    }

    response.OK(w, order)
}

// CreateOrder handles POST /orders
func CreateOrder(w http.ResponseWriter, r *http.Request) {
    var req models.CreateOrderRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        response.BadRequest(w, "Invalid request body")
        return
    }

    svc := transire.MustGet[*services.OrderService](r.Context())
    order, err := svc.CreateOrder(r.Context(), req)
    if err != nil {
        response.BadRequest(w, err.Error())
        return
    }

    // Enqueue for async processing
    app := transire.MustGetApp(r.Context())
    processedOrder := models.ProcessedOrder{
        OrderID:    order.ID,
        CustomerID: order.CustomerID,
        Amount:     order.TotalAmount,
        ProcessAt:  order.CreatedAt,
    }
    if err := app.Enqueue(r.Context(), "ProcessedOrder", processedOrder); err != nil {
        // Log error but don't fail request (order was created)
        log.Printf("Failed to enqueue order for processing: %v", err)
    }

    response.Created(w, order)
}

// UpdateOrder handles PUT /orders/{id}
func UpdateOrder(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")

    var req models.UpdateOrderRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        response.BadRequest(w, "Invalid request body")
        return
    }

    svc := transire.MustGet[*services.OrderService](r.Context())
    order, err := svc.UpdateOrder(r.Context(), id, req)
    if err != nil {
        if err.Error() == "order not found" {
            response.NotFound(w, "Order not found")
            return
        }
        response.BadRequest(w, err.Error())
        return
    }

    response.OK(w, order)
}

// DeleteOrder handles DELETE /orders/{id}
func DeleteOrder(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")

    svc := transire.MustGet[*services.OrderService](r.Context())
    if err := svc.DeleteOrder(r.Context(), id); err != nil {
        response.NotFound(w, "Order not found")
        return
    }

    w.WriteHeader(http.StatusNoContent)
}

// HealthCheck handles GET /health
func HealthCheck(w http.ResponseWriter, r *http.Request) {
    response.OK(w, map[string]string{
        "status": "healthy",
    })
}
```

### Step 5: Queue Handlers

Create `handlers/queue_handlers.go`:

```go
package handlers

import (
    "context"
    "log"

    "github.com/transire/sdk-go"
    "github.com/yourname/orders-api/models"
    "github.com/yourname/orders-api/services"
)

// ProcessOrderBatch handles ProcessedOrder queue messages
func ProcessOrderBatch(ctx context.Context, msgs []models.ProcessedOrder) error {
    svc := transire.MustGet[*services.OrderService](ctx)
    emailSvc := transire.MustGet[*services.EmailService](ctx)

    // Use BatchResult for per-message failure tracking
    br := transire.NewBatchResult(len(msgs))

    for i, msg := range msgs {
        // Check for context cancellation
        if err := ctx.Err(); err != nil {
            br.Fail(i, err)
            continue
        }

        // Process order
        if err := svc.ProcessOrder(ctx, msg.OrderID); err != nil {
            log.Printf("Failed to process order %s: %v", msg.OrderID, err)
            br.Fail(i, err)
            continue
        }

        // Send confirmation email
        customerEmail := msg.CustomerID + "@example.com" // In production, look up actual email
        if err := emailSvc.SendOrderConfirmation(ctx, customerEmail, msg.OrderID, msg.Amount); err != nil {
            log.Printf("Failed to send confirmation email for order %s: %v", msg.OrderID, err)
            // Don't fail the batch for email errors (order was processed successfully)
        }
    }

    // Return partial batch response (failed messages will be retried)
    return br.ToCloudPartialBatchResponse()
}

// SendEmailBatch handles OrderEmail queue messages
func SendEmailBatch(ctx context.Context, msgs []models.OrderEmail) error {
    emailSvc := transire.MustGet[*services.EmailService](ctx)
    br := transire.NewBatchResult(len(msgs))

    for i, msg := range msgs {
        if err := ctx.Err(); err != nil {
            br.Fail(i, err)
            continue
        }

        // Send email (implementation depends on email service)
        log.Printf("Sending email to %s: %s", msg.CustomerEmail, msg.Subject)
        // In production: emailSvc.Send(ctx, msg.CustomerEmail, msg.Subject, msg.Body)
    }

    return br.ToCloudPartialBatchResponse()
}
```

### Step 6: Scheduled Handlers

Create `handlers/schedule_handlers.go`:

```go
package handlers

import (
    "context"
    "fmt"
    "log"
    "time"

    "github.com/transire/sdk-go"
    "github.com/yourname/orders-api/services"
)

// GenerateDailyReport runs daily at 9 AM to generate order reports
func GenerateDailyReport(ctx context.Context) error {
    log.Println("Starting daily order report generation...")

    svc := transire.MustGet[*services.OrderService](ctx)
    emailSvc := transire.MustGet[*services.EmailService](ctx)

    // Get orders from the last 24 hours
    since := time.Now().Add(-24 * time.Hour)
    orders, err := svc.GetOrdersForReport(ctx, since)
    if err != nil {
        return fmt.Errorf("failed to fetch orders for report: %w", err)
    }

    // Generate report
    var totalAmount float64
    statusCounts := make(map[string]int)

    for _, order := range orders {
        totalAmount += order.TotalAmount
        statusCounts[order.Status]++
    }

    report := fmt.Sprintf(`
Daily Order Report - %s
======================

Total Orders: %d
Total Revenue: $%.2f

Orders by Status:
- Pending: %d
- Processing: %d
- Completed: %d
- Cancelled: %d
`,
        time.Now().Format("2006-01-02"),
        len(orders),
        totalAmount,
        statusCounts["pending"],
        statusCounts["processing"],
        statusCounts["completed"],
        statusCounts["cancelled"],
    )

    // Send report email (to admin)
    adminEmail := "admin@example.com" // In production, get from config
    if err := emailSvc.SendDailyReport(ctx, adminEmail, report); err != nil {
        return fmt.Errorf("failed to send daily report: %w", err)
    }

    log.Printf("Daily report sent successfully (%d orders, $%.2f total)", len(orders), totalAmount)
    return nil
}
```

### Step 7: Main Application

Create `main.go`:

```go
package main

import (
    "log"
    "os"

    "github.com/transire/sdk-go"
    "github.com/yourname/orders-api/handlers"
    "github.com/yourname/orders-api/services"
)

func main() {
    // Register singleton services (created once per process/cold start)
    transire.Provide(func() (*services.OrderService, error) {
        log.Println("Initializing OrderService...")
        return services.NewOrderService(), nil
    })

    transire.Provide(func() (*services.EmailService, error) {
        log.Println("Initializing EmailService...")
        fromAddress := os.Getenv("FROM_EMAIL_ADDRESS")
        if fromAddress == "" {
            fromAddress = "noreply@example.com"
        }
        return services.NewEmailService(fromAddress), nil
    })

    // Create application
    app := transire.New()

    // Register HTTP handlers
    app.GET("/health", handlers.HealthCheck)
    app.GET("/orders", handlers.ListOrders)
    app.GET("/orders/{id}", handlers.GetOrder)
    app.POST("/orders", handlers.CreateOrder)
    app.PUT("/orders/{id}", handlers.UpdateOrder)
    app.DELETE("/orders/{id}", handlers.DeleteOrder)

    // Register queue handlers
    if err := app.RegisterQueue("ProcessedOrder", handlers.ProcessOrderBatch); err != nil {
        log.Fatalf("Failed to register ProcessedOrder queue: %v", err)
    }

    if err := app.RegisterQueue("OrderEmail", handlers.SendEmailBatch); err != nil {
        log.Fatalf("Failed to register OrderEmail queue: %v", err)
    }

    // Register scheduled jobs (uses timezone from transire.yaml)
    if err := app.RegisterScheduled("@daily 09:00", handlers.GenerateDailyReport); err != nil {
        log.Fatalf("Failed to register daily report schedule: %v", err)
    }

    // Run application
    log.Println("Starting Orders API...")
    if err := app.Run(); err != nil {
        log.Fatalf("Application failed: %v", err)
    }
}
```

### Step 8: Configuration

Create `transire.yaml`:

```yaml
version: 1
service: orders
runtime: go
cloud: aws
ci: github
iac: opentofu
timezone: America/New_York

deploy:
  arch: arm64
  memory_mb: 256
  timeout_s: 30

http:
  simulate_apigw_limits: true
  cors:
    enabled: true
    allow_origins: ["*"]  # Use specific origins in production
    allow_methods: ["GET", "POST", "PUT", "DELETE"]
    allow_headers: ["Content-Type", "Authorization"]

queues:
  max_batch_size: 10
  batch_window_s: 5
  visibility_timeout_s: 35
  max_receive_count: 3
  error_mode: partial

observability:
  logging:
    level: info
    format: json
  tracing:
    enabled: false
    provider: aws-xray

infra:
  backend:
    type: s3
    bucket: my-transire-state
    dynamodb_table: transire-locks
    key_prefix: orders/
  vpc:
    enabled: false
  tags:
    env: dev
    service: orders

env:
  - name: dev
    workspace: dev
    variables:
      FROM_EMAIL_ADDRESS: noreply@example.com
      LOG_LEVEL: debug

  - name: prod
    workspace: prod
    variables:
      FROM_EMAIL_ADDRESS: noreply@mycompany.com
      LOG_LEVEL: info
```

## Running Locally

### Generate Manifest

```bash
transire gen
```

This creates `transire_manifest.json` with all your routes, queues, and schedules.

### Start Local Server

```bash
transire run
```

Output:
```
Initializing OrderService...
Initializing EmailService...
Starting Orders API...
HTTP server listening on :8080
Queue workers: ProcessedOrder (1 worker), OrderEmail (1 worker)
Scheduled jobs: GenerateDailyReport (@daily 09:00 America/New_York)
```

### Test Endpoints

**Health check:**
```bash
curl http://localhost:8080/health
```

**Create order:**
```bash
curl -X POST http://localhost:8080/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_123",
    "items": [
      {
        "sku": "WIDGET-001",
        "name": "Premium Widget",
        "quantity": 2,
        "price": 29.99
      },
      {
        "sku": "GADGET-002",
        "name": "Deluxe Gadget",
        "quantity": 1,
        "price": 49.99
      }
    ]
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": "cust_123",
  "items": [
    {
      "sku": "WIDGET-001",
      "name": "Premium Widget",
      "quantity": 2,
      "price": 29.99
    },
    {
      "sku": "GADGET-002",
      "name": "Deluxe Gadget",
      "quantity": 1,
      "price": 49.99
    }
  ],
  "total_amount": 109.97,
  "status": "pending",
  "created_at": "2025-10-30T10:30:00Z",
  "updated_at": "2025-10-30T10:30:00Z"
}
```

**List orders:**
```bash
curl http://localhost:8080/orders
```

**Get order:**
```bash
curl http://localhost:8080/orders/550e8400-e29b-41d4-a716-446655440000
```

**Update order:**
```bash
curl -X PUT http://localhost:8080/orders/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

**Delete order:**
```bash
curl -X DELETE http://localhost:8080/orders/550e8400-e29b-41d4-a716-446655440000
```

## Testing

Create `handlers/http_handlers_test.go`:

```go
package handlers_test

import (
    "net/http"
    "testing"

    "github.com/transire/sdk-go/testkit"
    "github.com/yourname/orders-api/models"
)

func TestOrdersCRUD(t *testing.T) {
    // Start test app
    app := testkit.App().Start(t)
    defer app.Stop()

    // Create order
    createReq := models.CreateOrderRequest{
        CustomerID: "cust_test",
        Items: []models.Item{
            {SKU: "TEST-001", Name: "Test Item", Quantity: 1, Price: 10.00},
        },
    }

    createResp := app.POST("/orders", createReq)
    testkit.EqualStatus(t, createResp, http.StatusCreated)

    var order models.Order
    testkit.DecodeJSON(t, createResp, &order)
    testkit.NotEmpty(t, order.ID)
    testkit.Equal(t, order.CustomerID, "cust_test")
    testkit.Equal(t, order.TotalAmount, 10.00)

    // Get order
    getResp := app.GET("/orders/" + order.ID)
    testkit.EqualStatus(t, getResp, http.StatusOK)

    // List orders
    listResp := app.GET("/orders")
    testkit.EqualStatus(t, listResp, http.StatusOK)

    var orders []models.Order
    testkit.DecodeJSON(t, listResp, &orders)
    testkit.True(t, len(orders) > 0)

    // Update order
    updateReq := models.UpdateOrderRequest{
        Status: models.StatusCompleted,
    }
    updateResp := app.PUT("/orders/"+order.ID, updateReq)
    testkit.EqualStatus(t, updateResp, http.StatusOK)

    // Delete order
    deleteResp := app.DELETE("/orders/" + order.ID)
    testkit.EqualStatus(t, deleteResp, http.StatusNoContent)

    // Verify deleted
    notFoundResp := app.GET("/orders/" + order.ID)
    testkit.EqualStatus(t, notFoundResp, http.StatusNotFound)
}

func TestQueueProcessing(t *testing.T) {
    app := testkit.App().Start(t)
    defer app.Stop()

    // Enqueue message
    msg := models.ProcessedOrder{
        OrderID:    "test-order-123",
        CustomerID: "cust_test",
        Amount:     99.99,
    }

    app.Enqueue("ProcessedOrder", msg)

    // Drain queue (waits for processing)
    app.DrainQueue(t, "ProcessedOrder")

    // Verify processing completed (check order status changed)
    // In real test, would verify side effects
}
```

Run tests:

```bash
go test ./...
```

## Deploying to AWS

### Prerequisites

1. **AWS CLI configured:**
```bash
aws configure
aws sts get-caller-identity
```

2. **Initialize backend:**
```bash
transire init --backend
```

This creates:
- S3 bucket for Terraform state
- DynamoDB table for state locking

### Deploy to Development

```bash
# Generate manifest
transire gen

# Deploy to dev environment
transire deploy
```

Output:
```
Building application...
Generating infrastructure...
Deploying to AWS (workspace: dev)...

Created resources:
  - Lambda: orders-dev-http
  - Lambda: orders-dev-queue-ProcessedOrder
  - Lambda: orders-dev-queue-OrderEmail
  - Lambda: orders-dev-scheduled-daily
  - API Gateway: orders-dev
  - SQS Queue: orders-dev-queue-ProcessedOrder
  - SQS Queue: orders-dev-queue-OrderEmail
  - EventBridge Rule: orders-dev-scheduled-daily

API Gateway URL: https://abc123.execute-api.us-east-1.amazonaws.com

Deployment complete!
```

### Test Deployed API

```bash
# Save API URL
export API_URL="https://abc123.execute-api.us-east-1.amazonaws.com"

# Health check
curl $API_URL/health

# Create order
curl -X POST $API_URL/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_prod",
    "items": [
      {"sku": "PROD-001", "name": "Product", "quantity": 1, "price": 99.99}
    ]
  }'
```

### Deploy to Production

Update workspace in deployment command:

```bash
transire deploy --workspace prod
```

Or use CI/CD (GitHub Actions):

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.22'

      - name: Install Transire CLI
        run: |
          # Install transire CLI
          go install github.com/transire/cli/transire@latest

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1

      - name: Deploy
        run: |
          transire gen
          transire deploy --workspace prod
```

## Next Steps

### Add Authentication

Add custom middleware for JWT authentication:

```go
func authMiddleware() transire.Middleware {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            token := r.Header.Get("Authorization")
            if token == "" {
                response.Unauthorized(w, "Missing authorization header")
                return
            }
            // Verify JWT token
            // Add user to context
            next.ServeHTTP(w, r)
        })
    }
}

// In main():
app.Use(authMiddleware())
```

### Add Database

Use a real database instead of in-memory storage:

```go
import "github.com/jackc/pgx/v5/pgxpool"

transire.Provide(func() (*pgxpool.Pool, error) {
    dbURL := os.Getenv("DATABASE_URL")
    return pgxpool.New(context.Background(), dbURL)
})

// Update OrderService to use database
func (s *OrderService) CreateOrder(ctx context.Context, req models.CreateOrderRequest) (*models.Order, error) {
    // INSERT INTO orders ...
}
```

### Add Observability

Enable tracing and metrics:

```yaml
# transire.yaml
observability:
  logging:
    level: info
    format: json
  tracing:
    enabled: true
    provider: aws-xray
```

### Add Caching

Add Redis for caching:

```go
transire.Provide(func() (*redis.Client, error) {
    return redis.NewClient(&redis.Options{
        Addr: os.Getenv("REDIS_URL"),
    }), nil
})
```

## See Also

- [HTTP Handlers](/sdk/http.md) - HTTP handler reference
- [Queue Handlers](/sdk/queue.md) - Queue handler reference
- [Scheduled Jobs](/sdk/schedule.md) - Scheduled job reference
- [Dependency Injection](/sdk/di.md) - DI patterns
- [Testing Guide](/guides/testing.md) - Testing strategies
- [Deployment Guide](/guides/deployment.md) - Deployment best practices
