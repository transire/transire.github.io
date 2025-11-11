---
template_id: scaffold_project
template_version: 1.0
description: Scaffold a new Transire project with all necessary files
mcp_use: template
operations:
  - create_directory_structure
  - generate_main_go
  - generate_config
  - initialize_go_module
parameters:
  - name: project_name
    type: string
    required: true
    description: Name of the project (e.g., "orders-api")
  - name: module_path
    type: string
    required: true
    description: Go module path (e.g., "github.com/username/orders-api")
  - name: include_queue
    type: boolean
    default: false
    description: Include queue handler example
  - name: include_schedule
    type: boolean
    default: false
    description: Include scheduled job example
validation:
  - check: go_version >= 1.22
    error: "Go 1.22 or later required"
  - check: directory_not_exists
    error: "Directory already exists"
---

# Template: Scaffold Transire Project

This template creates a complete Transire project structure.

## Generated Structure

```
${PROJECT_NAME}/
├── main.go
├── go.mod
├── transire.yaml
├── .gitignore
└── README.md
```

## Step 1: Create Directory

```bash
mkdir ${PROJECT_NAME}
cd ${PROJECT_NAME}
```

## Step 2: Initialize Go Module

```bash
go mod init ${MODULE_PATH}
```

## Step 3: Create main.go

```go
package main

import (
    "context"
    "net/http"

    "github.com/transire/sdk-go"
    "github.com/transire/sdk-go/response"
)

func main() {
    app := transire.New()

    // HTTP handlers
    app.GET("/health", healthCheck)
    app.GET("/orders", listOrders)
    app.GET("/orders/{id}", getOrder)
    app.POST("/orders", createOrder)

{{#if include_queue}}
    // Queue handler
    app.RegisterQueue("process-orders", processOrders)
{{/if}}

{{#if include_schedule}}
    // Scheduled job
    app.Schedule("daily-report", "@daily 09:00", generateReport)
{{/if}}

    app.Run()
}

// Health check endpoint
func healthCheck(w http.ResponseWriter, r *http.Request) {
    response.OK(w, map[string]string{"status": "healthy"})
}

// List all orders
func listOrders(w http.ResponseWriter, r *http.Request) {
    // TODO: Fetch from database
    orders := []Order{}
    response.OK(w, orders)
}

// Get single order
func getOrder(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")

    // TODO: Fetch from database
    order := &Order{ID: id}

    response.OK(w, order)
}

// Create new order
func createOrder(w http.ResponseWriter, r *http.Request) {
    var req CreateOrderRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        response.BadRequest(w, "Invalid request body")
        return
    }

    // TODO: Validate and save to database
    order := &Order{
        ID:      generateID(),
        Product: req.Product,
        Status:  "pending",
    }

{{#if include_queue}}
    // Enqueue for async processing
    if err := app.Enqueue(r.Context(), "process-orders", order); err != nil {
        log.Printf("Failed to enqueue: %v", err)
    }
{{/if}}

    response.Created(w, order)
}

{{#if include_queue}}
// Process orders asynchronously
func processOrders(ctx context.Context, orders []Order) error {
    log.Printf("Processing %d orders", len(orders))

    for _, order := range orders {
        // TODO: Implement order processing
        log.Printf("Processing order %s", order.ID)
    }

    return nil
}
{{/if}}

{{#if include_schedule}}
// Generate daily report
func generateReport(ctx context.Context) error {
    log.Println("Generating daily report")

    // TODO: Implement report generation

    return nil
}
{{/if}}

// Order model
type Order struct {
    ID      string `json:"id"`
    Product string `json:"product"`
    Status  string `json:"status"`
}

// CreateOrderRequest payload
type CreateOrderRequest struct {
    Product string `json:"product" validate:"required"`
}

func generateID() string {
    return fmt.Sprintf("ORD-%d", time.Now().UnixNano())
}
```

## Step 4: Create transire.yaml

```yaml
version: 1
service: ${PROJECT_NAME}
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
    type: local

env:
  - name: dev
    workspace: dev
```

## Step 5: Create .gitignore

```
# Binaries
${PROJECT_NAME}
*.exe
*.exe~
*.dll
*.so
*.dylib

# Test binaries
*.test

# Output of the go coverage tool
*.out

# Dependency directories
vendor/

# Go workspace file
go.work

# Transire
infra/
transire_manifest.json
build/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```

## Step 6: Create README.md

```markdown
# ${PROJECT_NAME}

A Transire cloud-native application.

## Prerequisites

- Go 1.22+
- AWS CLI configured
- Transire CLI

## Development

\`\`\`bash
# Run locally
go run main.go

# Or with hot reload
transire run --watch
\`\`\`

## Deployment

\`\`\`bash
# Generate manifest
transire gen

# Deploy to AWS
transire deploy --environment=dev
\`\`\`

## API Endpoints

- `GET /health` - Health check
- `GET /orders` - List orders
- `GET /orders/{id}` - Get order
- `POST /orders` - Create order

{{#if include_queue}}
## Queue Handlers

- `process-orders` - Process order batches
{{/if}}

{{#if include_schedule}}
## Scheduled Jobs

- `daily-report` - Generate daily report (runs at 9 AM)
{{/if}}
```

## Step 7: Install Dependencies

```bash
go get github.com/transire/sdk-go@latest
go mod tidy
```

## Step 8: Verify Setup

```bash
# Run the app
go run main.go

# Should see:
✓ Starting HTTP server on :8080
→ Ready: http://localhost:8080
```

## Next Steps

1. **Test locally:**

    ```bash
    curl http://localhost:8080/health
    ```

2. **Generate manifest:**

    ```bash
    transire gen
    ```

3. **Deploy to AWS:**

    ```bash
    transire deploy --environment=dev
    ```

## Success Criteria

- [ ] Project structure created
- [ ] Go module initialized
- [ ] Dependencies installed
- [ ] App runs locally
- [ ] Health check responds
- [ ] Ready for development

## Troubleshooting

**Go version too old:**

```bash
# Install Go 1.22+
# Download from: https://golang.org/dl/
```

**Port 8080 in use:**

```bash
# Change port in transire.yaml:
http:
  port: 8081
```

**Import errors:**

```bash
go mod download
go mod tidy
```

## See Also

- [Hello World Tutorial](../learn/tutorials/01-hello-world/)
- [Quick Start Guide](../getting-started/quickstart/)
- [Project Setup Guide](../getting-started/project-setup/)
