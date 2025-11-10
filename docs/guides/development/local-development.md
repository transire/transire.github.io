---
title: Local Development Guide
description: Best practices and workflows for developing Transire applications locally
category: guide
subcategory: development
complexity: beginner
duration: 20 minutes
mcp_use: guide
mcp_operations:
  - setup_local_environment
  - configure_hot_reload
  - debug_application
  - manage_configuration
features_covered:
  - Local development server
  - Hot reload
  - Environment configuration
  - Debugging techniques
  - Development workflow
code_blocks: true
last_updated: 2025-11-10
---

# Local Development Guide

> **Master local development** with Transire's development server and hot reload

## Overview

Transire's local development mode provides a fast, productive environment that closely mimics cloud behavior while keeping you in a tight feedback loop.

**What you get locally:**
- HTTP server with same routing as cloud
- In-memory queue emulator with batch processing
- Fixed-rate scheduler for testing cron jobs
- Hot reload for instant feedback
- Environment variable management
- Structured logging

**Time to read:** 20 minutes

---

## Quick Start

```bash
# Start development server
$ transire run

✓ Starting HTTP server on :8080
✓ Queue emulator: 2 queues, 1 worker each
✓ Scheduler: 1 job (daily-report, next run: tomorrow at 09:00)
→ Ready: http://localhost:8080

Watching for changes... (Ctrl+C to stop)
```

**Your app is now running locally!**

Test it:
```bash
$ curl http://localhost:8080/health
{"status":"healthy"}
```

---

## Development Server

### Basic Usage

Start the server:

```bash
# Default port 8080
transire run

# Custom port
transire run --port 3000

# With environment file
transire run --env-file .env.local

# Hot reload enabled
transire run --watch  # Coming in v1.1
```

### What's Running?

The local server includes:

#### 1. HTTP Server
- Chi router with all registered routes
- Same middleware as cloud
- Same error handling
- Same request/response types

```bash
$ transire run

✓ Starting HTTP server on :8080
  Routes:
    GET    /
    GET    /health
    GET    /orders
    POST   /orders
    GET    /orders/{id}
    PUT    /orders/{id}
    DELETE /orders/{id}
```

#### 2. Queue Emulator
- In-memory message queue
- Configurable workers per queue
- Batch processing simulation
- Retry behavior
- DLQ simulation

```bash
✓ Queue emulator: 2 queues, 1 worker each
  Queues:
    - fulfill-orders (1 worker)
    - send-emails (1 worker)
```

#### 3. Scheduler
- Fixed-rate execution (non-overlapping)
- Shows next run time
- Logs execution results

```bash
✓ Scheduler: 1 job
  Jobs:
    - daily-report (next run: tomorrow at 09:00)
```

---

## Hot Reload

### Enable Watch Mode

```bash
$ transire run --watch  # Coming in v1.1

✓ Starting HTTP server on :8080
✓ Watching: *.go

# Edit main.go
→ Change detected: main.go
→ Rebuilding...
✓ Restarted in 1.2s
```

### What Triggers Reload?

- `.go` file changes
- `transire.yaml` changes
- `.env` file changes (if using `--env-file`)

### What Doesn't Trigger Reload?

- Generated files (`transire_manifest.json`)
- Vendor directory
- Test files (`*_test.go`)
- Temporary files

### Best Practices

**DO:**
```bash
# ✅ Use watch mode during active development
transire run --watch  # Coming in v1.1

# ✅ Keep terminal visible to see reload feedback
# ✅ Wait for "Restarted in X.Xs" before testing
# ✅ Use structured logging to see what's happening
```

**DON'T:**
```bash
# ❌ Don't save files repeatedly while typing
# ❌ Don't run multiple `transire run` instances
# ❌ Don't ignore compile errors in the terminal
```

---

## Environment Configuration

### Environment Files

Create environment-specific files:

```bash
# Project structure
my-app/
├── .env                  # Default (checked into git - no secrets!)
├── .env.local            # Local overrides (gitignored)
├── .env.development      # Development
├── .env.staging          # Staging
├── .env.production       # Production (never commit!)
└── main.go
```

**.env (safe to commit):**
```bash
# Default configuration
LOG_LEVEL=info
PORT=8080
ENVIRONMENT=development
```

**.env.local (gitignored):**
```bash
# Local overrides with secrets
DATABASE_URL=postgresql://localhost:5432/orders_dev
STRIPE_API_KEY=sk_test_xxx
LOG_LEVEL=debug
```

### Load Environment Files

```bash
# Default: loads .env
transire run

# Load specific file
transire run --env-file .env.local

# Load multiple (later files override)
transire run --env-file .env --env-file .env.local
```

### Access in Code

```go
package main

import (
    "os"
    "log"
)

func main() {
    // Read environment variables
    dbURL := os.Getenv("DATABASE_URL")
    if dbURL == "" {
        log.Fatal("DATABASE_URL not set")
    }

    logLevel := os.Getenv("LOG_LEVEL")
    if logLevel == "" {
        logLevel = "info" // Default
    }

    // Use in configuration
    cfg := &Config{
        DatabaseURL: dbURL,
        LogLevel:    logLevel,
    }
}
```

### Configuration Best Practices

**DO:**
- Use `.env.local` for secrets (add to `.gitignore`)
- Provide defaults in code for optional values
- Document required variables in README
- Validate configuration at startup

**DON'T:**
- Commit secrets to git (use `.env.local`)
- Hardcode configuration values
- Mix environment-specific logic in code
- Ignore missing required variables

---

## Debugging

### Enable Debug Logging

```bash
# Set log level
LOG_LEVEL=debug transire run

# Or in .env.local
echo "LOG_LEVEL=debug" >> .env.local
transire run --env-file .env.local
```

**Output:**
```
2025-11-10 15:23:45 [DEBUG] HTTP: GET /orders
2025-11-10 15:23:45 [DEBUG] Query: SELECT * FROM orders
2025-11-10 15:23:45 [DEBUG] Rows: 10
2025-11-10 15:23:45 [DEBUG] Response: 200 OK
```

### Structured Logging

Use structured logging for better debugging:

```go
import "log/slog"

func listOrders(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()

    slog.InfoContext(ctx, "Listing orders",
        "user_id", getUserID(ctx),
        "limit", 10,
    )

    orders, err := db.GetOrders(ctx)
    if err != nil {
        slog.ErrorContext(ctx, "Failed to list orders",
            "error", err,
            "user_id", getUserID(ctx),
        )
        response.InternalServerError(w, "Failed to fetch orders")
        return
    }

    slog.DebugContext(ctx, "Orders retrieved",
        "count", len(orders),
    )

    response.OK(w, orders)
}
```

**Benefits:**
- Searchable logs (`grep user_id=123`)
- JSON output in production
- Request tracing
- Error context

### Debugging HTTP Requests

#### Use `curl` with verbose output:

```bash
# Verbose request
$ curl -v http://localhost:8080/orders

> GET /orders HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.88.1
> Accept: */*
>
< HTTP/1.1 200 OK
< Content-Type: application/json
< Date: Sun, 10 Nov 2025 15:23:45 GMT
< Content-Length: 234
<
[{"id":"1","product":"Widget","quantity":5}]
```

#### Test with different methods:

```bash
# GET
curl http://localhost:8080/orders

# POST with JSON
curl -X POST http://localhost:8080/orders \
  -H "Content-Type: application/json" \
  -d '{"product":"Widget","quantity":5}'

# PUT
curl -X PUT http://localhost:8080/orders/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"fulfilled"}'

# DELETE
curl -X DELETE http://localhost:8080/orders/1
```

#### Test authentication:

```bash
# With Bearer token
curl http://localhost:8080/orders \
  -H "Authorization: Bearer eyJhbGc..."

# With API key
curl http://localhost:8080/orders \
  -H "X-API-Key: abc123"
```

### Debugging Queue Processing

#### Enqueue test messages:

```go
// Add test endpoint
app.POST("/test/enqueue-order", func(w http.ResponseWriter, r *http.Request) {
    order := Order{
        ID:      "test-123",
        Product: "Test Widget",
        Status:  "pending",
    }

    if err := app.Enqueue(r.Context(), "fulfill-orders", order); err != nil {
        response.InternalServerError(w, "Failed to enqueue")
        return
    }

    response.OK(w, map[string]string{"status": "enqueued"})
})
```

```bash
# Trigger test message
curl -X POST http://localhost:8080/test/enqueue-order
```

**Watch logs:**
```
→ Enqueued: fulfill-orders
→ Processing batch of 1 messages
[INFO] Fulfilling order test-123
→ Batch complete: 1 succeeded, 0 failed
```

#### Test queue failures:

```go
// Add test endpoint for failure
app.POST("/test/enqueue-failing", func(w http.ResponseWriter, r *http.Request) {
    order := Order{
        ID:      "fail-me",  // Special ID that triggers error
        Product: "Widget",
    }

    app.Enqueue(r.Context(), "fulfill-orders", order)
    response.OK(w, map[string]string{"status": "enqueued"})
})
```

**Watch retry behavior:**
```
→ Processing batch of 1 messages
[ERROR] Order fulfillment failed: fail-me
→ Batch complete: 0 succeeded, 1 failed
→ Retry 1/3 in 5s
→ Processing batch of 1 messages
[ERROR] Order fulfillment failed: fail-me
→ Retry 2/3 in 10s
```

### Debugging Scheduled Jobs

#### Trigger manually:

```go
// Add test endpoint
app.POST("/test/trigger-daily-report", func(w http.ResponseWriter, r *http.Request) {
    // Call schedule handler directly
    if err := generateDailyReport(r.Context()); err != nil {
        response.InternalServerError(w, "Report generation failed")
        return
    }
    response.OK(w, map[string]string{"status": "complete"})
})
```

```bash
# Trigger job
curl -X POST http://localhost:8080/test/trigger-daily-report
```

#### Speed up schedules for testing:

```yaml
# transire.yaml
local:
  schedules:
    scale_factor: 0.01  # 100x faster (1 hour → 36 seconds)
```

Now `@daily` runs every 14.4 minutes instead of 24 hours!

### Using Delve Debugger

Install Delve:
```bash
go install github.com/go-delve/delve/cmd/dlv@latest
```

Debug with breakpoints:
```bash
# Start with debugger
dlv debug ./cmd/myapp --headless --listen=:2345 --api-version=2

# In VS Code, attach to :2345
```

**VS Code `launch.json`:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Attach to Transire",
      "type": "go",
      "request": "attach",
      "mode": "remote",
      "remotePath": "${workspaceFolder}",
      "port": 2345,
      "host": "127.0.0.1"
    }
  ]
}
```

---

## Development Workflow

### Recommended Workflow

```bash
# Terminal 1: Run app with hot reload
transire run --watch  # Coming in v1.1 --env-file .env.local

# Terminal 2: Watch tests
go test ./... -watch

# Terminal 3: Make requests
curl http://localhost:8080/orders

# IDE: Edit code, save, see instant reload
```

### Typical Development Session

**1. Start server:**
```bash
$ transire run --watch  # Coming in v1.1

✓ Ready: http://localhost:8080
Watching for changes...
```

**2. Make changes:**
```go
// main.go
app.GET("/orders/{id}", getOrder)
```

**3. Save file:**
```
→ Change detected: main.go
→ Rebuilding...
✓ Restarted in 1.2s
```

**4. Test immediately:**
```bash
$ curl http://localhost:8080/orders/123
{"id":"123","product":"Widget"}
```

**5. Iterate quickly:**
- Edit code
- Save
- Test
- Repeat

### Pre-Commit Workflow

Before committing, run:

```bash
# 1. Format code
go fmt ./...

# 2. Run linter
golangci-lint run ./...

# 3. Run tests
go test ./...

# 4. Generate manifest
transire gen

# 5. Validate config
transire validate
```

**Automate with Git hook:**

Create `.git/hooks/pre-commit`:
```bash
#!/bin/sh
set -e

echo "Running pre-commit checks..."

# Format
go fmt ./...

# Lint
golangci-lint run ./...

# Test
go test ./...

# Generate manifest
transire gen

echo "✓ Pre-commit checks passed"
```

```bash
chmod +x .git/hooks/pre-commit
```

---

## Local vs Cloud Differences

### What's the Same ✅

- HTTP routing and middleware
- Request/response handling
- Queue message types and batching
- Schedule expressions
- Dependency injection
- Error handling
- Handler signatures

### What's Different ⚠️

| Feature | Local | Cloud |
|---------|-------|-------|
| **HTTP** | Single Chi server | API Gateway + Lambda |
| **Queues** | In-memory | SQS + Lambda |
| **Schedules** | Fixed-rate Go timer | EventBridge + Lambda |
| **Concurrency** | Single process | Auto-scaling functions |
| **Cold starts** | None | First request ~100-500ms |
| **Timeout** | No limit | Configurable (max 15min) |
| **Memory** | System memory | Configurable (128MB-10GB) |
| **State** | In-memory (lost on restart) | Stateless (use DB/cache) |

### Testing Cloud Behavior Locally

#### Simulate Lambda timeout:

```yaml
# transire.yaml
local:
  http:
    timeout_s: 30  # Enforce 30s timeout locally
```

#### Simulate cold starts:

```go
var coldStartDelay = 500 * time.Millisecond

func init() {
    if os.Getenv("SIMULATE_COLD_START") == "true" {
        time.Sleep(coldStartDelay)
    }
}
```

#### Simulate memory limits:

```yaml
# transire.yaml
local:
  simulate_limits:
    memory_mb: 256  # Enforce memory limit locally
```

---

## Configuration Management

### Project Configuration

**transire.yaml:**
```yaml
version: 1
service: orders-api
runtime: go
cloud: aws

# Local development
local:
  port: 8080
  hot_reload: true
  log_level: debug

# HTTP configuration
http:
  cors:
    enabled: true
    allow_origins: ["http://localhost:3000"]

# Queue configuration
queues:
  workers: 1              # Workers per queue
  max_batch_size: 10
  batch_window_s: 5

# Schedule configuration
schedules:
  enabled: true
  scale_factor: 1.0       # Normal speed

# Observability
observability:
  logging:
    level: info
    format: json
```

### Environment-Specific Config

**Development:**
```yaml
# transire.yaml
local:
  log_level: debug
  schedules:
    scale_factor: 0.1     # 10x faster for testing
```

**Staging:**
```yaml
environments:
  staging:
    deploy:
      region: us-east-1
      memory_mb: 512
    observability:
      logging:
        level: info
```

**Production:**
```yaml
environments:
  prod:
    deploy:
      region: us-east-1
      memory_mb: 1024
      timeout_s: 60
    observability:
      logging:
        level: warn
      alarms:
        enabled: true
```

---

## Development Tools

### Recommended VS Code Extensions

```json
// .vscode/extensions.json
{
  "recommendations": [
    "golang.go",
    "humao.rest-client",
    "redhat.vscode-yaml",
    "esbenp.prettier-vscode"
  ]
}
```

### VS Code Settings

```json
// .vscode/settings.json
{
  "go.useLanguageServer": true,
  "go.lintOnSave": "workspace",
  "go.formatTool": "gofmt",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### HTTP Client Files

Create `.http` files for testing:

**requests.http:**
```http
### Health check
GET http://localhost:8080/health

### List orders
GET http://localhost:8080/orders

### Create order
POST http://localhost:8080/orders
Content-Type: application/json

{
  "product": "Widget",
  "quantity": 5,
  "price": 99.99
}

### Get order
GET http://localhost:8080/orders/1

### Update order
PUT http://localhost:8080/orders/1
Content-Type: application/json

{
  "status": "fulfilled"
}

### Delete order
DELETE http://localhost:8080/orders/1
```

Use with REST Client extension or `curl`:
```bash
# Convert to curl
cat requests.http | grep -A3 "POST" | curl -X POST ...
```

---

## Testing During Development

### Quick Test Loop

```bash
# Terminal 1: Run app
transire run --watch  # Coming in v1.1

# Terminal 2: Run tests on save
go test ./... -watch

# Terminal 3: Manual testing
curl http://localhost:8080/health
```

### Test with testkit

```go
import "github.com/transire/transire-sdk-go/testkit"

func TestCreateOrder(t *testing.T) {
    tk := testkit.New(t)

    // Register routes
    tk.GET("/orders", listOrders)
    tk.POST("/orders", createOrder)

    // Make request
    resp := tk.POST("/orders").
        JSON(map[string]interface{}{
            "product":  "Widget",
            "quantity": 5,
        }).
        Send()

    // Assert response
    resp.ExpectStatus(201)
    resp.ExpectJSON(map[string]interface{}{
        "product": "Widget",
    })
}
```

---

## Troubleshooting

### Server Won't Start

**Error:** `address already in use`

**Solution:**
```bash
# Find process using port 8080
lsof -i :8080

# Kill process
kill -9 <PID>

# Or use different port
transire run --port 3000
```

---

**Error:** `config file not found`

**Solution:**
```bash
# Verify transire.yaml exists
ls transire.yaml

# Or specify path
transire run --config path/to/transire.yaml
```

---

### Hot Reload Not Working

**Issue:** Changes not triggering reload

**Check:**
1. Watch mode enabled: `transire run --watch  # Coming in v1.1`
2. Saving files (not just editing)
3. Editing `.go` files (not generated files)
4. No compile errors in terminal

**Solution:**
```bash
# Restart with verbose logging
transire run --watch  # Coming in v1.1 --verbose
```

---

### Environment Variables Not Loading

**Issue:** Variables from `.env.local` not available

**Check:**
1. File exists: `ls .env.local`
2. Loading file: `transire run --env-file .env.local`
3. No syntax errors in file
4. Variables have no spaces: `KEY=value` not `KEY = value`

**Debug:**
```go
func main() {
    // Print all env vars
    for _, env := range os.Environ() {
        fmt.Println(env)
    }
}
```

---

### Queue Messages Not Processing

**Issue:** Messages enqueued but handler not called

**Check:**
1. Queue registered: `app.RegisterQueue("key", handler)`
2. Worker running: Check startup logs for "Queue emulator"
3. Message type matches handler signature
4. No errors in handler (check logs)

**Debug:**
```go
app.RegisterQueue("fulfill-orders", func(ctx context.Context, orders []Order) error {
    log.Printf("Received %d orders", len(orders))
    for _, order := range orders {
        log.Printf("Order: %+v", order)
    }
    return nil
})
```

---

## Performance Tips

### Fast Startup

```bash
# Skip manifest generation if unchanged
transire run --skip-gen

# Use cached build
go build -o ./bin/app
./bin/app
```

### Optimize Hot Reload

```yaml
# transire.yaml
local:
  hot_reload:
    debounce_ms: 500      # Wait 500ms for multiple changes
    ignore_patterns:
      - ".*_test.go"
      - ".*/testdata/.*"
```

### Database Connection Pooling

```go
// Reuse DB connection across requests
var db *sql.DB

func init() {
    var err error
    db, err = sql.Open("postgres", os.Getenv("DATABASE_URL"))
    if err != nil {
        log.Fatal(err)
    }

    // Configure pool
    db.SetMaxOpenConns(10)
    db.SetMaxIdleConns(5)
    db.SetConnMaxLifetime(5 * time.Minute)
}
```

---

## See Also

- [Hot Reload Guide](hot-reload/) - Advanced watch mode usage
- [Debugging Guide](debugging/) - Deep debugging techniques
- [Testing Guide](../testing/) - Comprehensive testing strategies
- [CLI Commands Reference](../../reference/cli/commands/) - All CLI commands
- [Configuration Reference](../../reference/config/reference/) - Complete config options

