---
title: "transire run"
category: cli
subcategory: null
complexity: beginner
duration: null
prerequisites:
  - Go 1.22+
  - Transire project set up
  - Manifest generated (transire gen)
mcp_use: reference
mcp_operations:
  - run_locally
  - test_handlers
features_covered:
  - Local development server
  - Hot reload
  - Queue emulation
  - Scheduler emulation
code_blocks: true
last_updated: 2025-10-30
---

# transire run

## Overview

`transire run` starts a local development server that emulates your cloud environment. It runs your HTTP handlers, queue processors, and scheduled jobs locally for fast iteration.

**Purpose:**
- Test your application before deploying to cloud
- Debug handlers with your favorite tools
- Verify routing, middleware, and business logic
- Develop without cloud credentials (optional cloud resources)

## Usage

### Basic

```bash
transire run
```

Starts the server on port 8080 (default).

### With Custom Port

```bash
transire run --port 3000
```

### With Hot Reload

```bash
transire run --watch
```

Automatically restarts server when Go files change.

### With Queue Workers

```bash
transire run --queue-workers=5
```

Run 5 workers per queue (default: 1).

## What It Does

When you run `transire run`, the CLI:

### 1. Loads Configuration

Reads `transire.yaml` and validates settings.

### 2. Generates Manifest (if needed)

If `transire_manifest.json` doesn't exist or is outdated, runs `transire gen` automatically.

### 3. Starts HTTP Server

Starts Chi HTTP server with all your routes:

```bash
Server listening on http://localhost:8080
Routes:
  GET    /orders
  GET    /orders/{id}
  POST   /orders
  PUT    /orders/{id}
  DELETE /orders/{id}
```

### 4. Starts Queue Emulators

For each registered queue, starts an in-memory queue with configurable workers:

```bash
Queue workers started:
  OrderCreated: 1 worker
  PaymentProcessed: 1 worker
```

### 5. Starts Scheduler

For each scheduled job, starts a timer:

```bash
Scheduled jobs:
  sendDailyReport: @daily 09:00 (America/New_York)
  syncData: @hourly
```

### 6. Graceful Shutdown

On SIGINT/SIGTERM (Ctrl+C), gracefully shuts down:

```bash
^C
Shutting down gracefully...
✓ HTTP server stopped
✓ Queue workers stopped
✓ Scheduled jobs cancelled
Shutdown complete
```

Default timeout: 30 seconds (configurable in `transire.yaml`).

## Local Environment

### HTTP Server

- **Port:** 8080 (default)
- **Router:** Chi (same as cloud adapter)
- **Middleware:** All middleware runs (logging, CORS, custom)
- **Size limits:** Enforces 6MB limit by default (matches API Gateway)

### Queue Emulator

- **Storage:** In-memory (not persistent)
- **Workers:** Configurable per queue (default: 1)
- **Batch processing:** Same as cloud (default: 10 messages, 5s window)
- **Retries:** Optional simulation (failures logged, no physical DLQ)
- **Visibility timeout:** Honored (default: 30s)

**Note:** Local queues don't persist across restarts. This is intentional for development.

### Scheduler

- **Type:** Fixed-rate (interval-based)
- **Overlap:** Non-overlapping (next run waits for current to finish)
- **Timezone:** Honors service timezone from `transire.yaml`
- **Immediate trigger:** Optional (useful for testing)

## Examples

### Start Server

```bash
$ transire run
✓ Configuration loaded
✓ Manifest loaded
Server listening on http://localhost:8080

Routes:
  GET    /orders
  POST   /orders

Queues:
  OrderCreated (1 worker)

Schedules:
  dailyReport: @daily 09:00

Press Ctrl+C to stop
```

### Test HTTP Endpoint

```bash
# In another terminal
$ curl http://localhost:8080/orders
{"orders": []}

$ curl -X POST http://localhost:8080/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": "123", "total": 99.99}'
{"id": "order-1", "user_id": "123", "total": 99.99, "status": "pending"}
```

### Enqueue Messages

Messages enqueued via `app.Enqueue()` are processed by local workers:

```go
// In your HTTP handler
func createOrder(w http.ResponseWriter, r *http.Request) {
    // ... create order

    // Enqueue for processing
    app.Enqueue(r.Context(), "OrderCreated", OrderCreated{
        OrderID: order.ID,
        UserID:  order.UserID,
    })

    response.Created(w, order)
}
```

Server logs show queue processing:

```bash
[INFO] Enqueued message to OrderCreated
[INFO] Worker processing batch: 1 messages
[INFO] Processing order order-1
[INFO] Order order-1 processed successfully
```

## Hot Reload (`--watch`)

Hot reload mode automatically restarts your server when Go files change:

```bash
$ transire run --watch
✓ Watching for changes: *.go
Server listening on http://localhost:8080
...

[File changed: handlers.go]
Restarting server...
✓ Manifest regenerated
✓ Server restarted
Server listening on http://localhost:8080
```

### How It Works

1. Watches all `*.go` files in current directory and subdirectories
2. On change, gracefully stops server
3. Runs `transire gen` to regenerate manifest
4. If gen fails, keeps old server running and logs error
5. Rebuilds binary and restarts server

### Limitations

- In-flight requests are cancelled (best-effort via `ctx.Done()`)
- Queue messages in-memory are lost (re-enqueue after restart)
- `transire.yaml` changes require manual restart (MVP constraint)

## Configuration

Configure local runtime behavior in `transire.yaml`:

```yaml
service: orders
runtime: go

# HTTP server config
http:
  simulate_apigw_limits: true  # Enforce 6MB limit locally
  cors:
    enabled: true
    allow_origins: ["http://localhost:3000"]

# Queue config
queues:
  max_batch_size: 10           # Max messages per batch
  batch_window_s: 5            # Max seconds to wait for batch
  visibility_timeout_s: 30     # Retry delay
  max_receive_count: 3         # Max retries before "DLQ" (logged)

# Deployment config (also used for local timeout)
deploy:
  timeout_s: 30                # Graceful shutdown timeout
```

## Debugging

### Enable Debug Logging

Set log level in `transire.yaml`:

```yaml
observability:
  logging:
    level: debug  # debug, info, warn, error
    format: text  # json or text (text is easier to read locally)
```

### Use Go Debugger

Run with `dlv`:

```bash
dlv debug . -- run
```

Or attach to running process:

```bash
transire run &
dlv attach $(pgrep transire)
```

### Check Handler Execution

Add logging to handlers:

```go
func getOrder(w http.ResponseWriter, r *http.Request) {
    log.Printf("GET /orders/{id} called with id=%s", transire.URLParam(r, "id"))
    // ... handler logic
}
```

### Inspect Queue Messages

Log messages before processing:

```go
func processOrder(ctx context.Context, msgs []OrderCreated) error {
    log.Printf("Processing batch of %d orders", len(msgs))
    for i, msg := range msgs {
        log.Printf("  [%d] Order %s", i, msg.OrderID)
    }
    // ... processing logic
}
```

## Command-Line Options

### `--port` (default: 8080)

```bash
transire run --port 3000
```

Change HTTP server port.

### `--watch` (default: false)

```bash
transire run --watch
```

Enable hot reload.

### `--queue-workers` (default: 1)

```bash
transire run --queue-workers=5
```

Number of concurrent workers per queue.

### `--log-level` (default: from config)

```bash
transire run --log-level=debug
```

Override log level from config.

### `--no-color` (default: false)

```bash
transire run --no-color
```

Disable colored output (useful for CI or logs).

## Local vs Cloud Parity

Transire's local emulator provides a **good-enough** approximation for development:

### Same Behavior

- ✅ HTTP routing (same Chi router)
- ✅ Handler signatures
- ✅ Middleware execution order
- ✅ Error handling
- ✅ Queue message format and type validation
- ✅ Scheduled job execution

### Different Behavior (by design)

- ❌ **Concurrency:** Local runs N workers; cloud scales to thousands
- ❌ **Persistence:** Local queues are in-memory; cloud queues persist
- ❌ **DLQ:** Local logs failures; cloud moves to physical DLQ
- ❌ **Timeouts:** Local uses graceful shutdown; cloud may hard-kill
- ❌ **Scheduler:** Local prevents overlap; cloud may fire concurrently
- ❌ **VPC/Networking:** No VPC simulation locally

**Use local for:** Rapid development, debugging, testing happy paths

**Use cloud for:** Load testing, production-like testing, final validation

## Common Workflows

### Development Loop

```bash
# 1. Start server with hot reload
transire run --watch

# 2. Edit code in your editor
vim handlers.go

# 3. Server restarts automatically
# (watch for errors in terminal)

# 4. Test changes
curl http://localhost:8080/orders
```

### Testing Before Deploy

```bash
# 1. Regenerate manifest
transire gen

# 2. Start server
transire run

# 3. Run integration tests
go test ./tests/integration/...

# 4. Deploy
transire deploy
```

### Debugging Issues

```bash
# 1. Enable debug logging
transire run --log-level=debug

# 2. Make failing request
curl http://localhost:8080/orders/bad-id

# 3. Check logs for details
# (stack traces, errors, timing)
```

## Troubleshooting

### "Port already in use"

**Problem:** Port 8080 is already taken

**Solution:** Use different port:

```bash
transire run --port 3000
```

Or find and kill process:

```bash
lsof -i :8080
kill <PID>
```

### "Manifest out of date"

**Problem:** Handlers changed but manifest not regenerated

**Solution:** Run gen before run:

```bash
transire gen && transire run
```

Or use `--watch` mode to auto-regenerate.

### "Handler not found"

**Problem:** Handler registered but not in manifest

**Solution:** Ensure registration is in `func main()`:

```go
func main() {
    app := transire.New()
    app.GET("/orders", listOrders)  // Must be here
    app.Run()
}
```

Then regenerate:

```bash
transire gen
```

### Queue messages not processing

**Problem:** No workers started for queue

**Solution:** Check that queue is registered:

```go
func main() {
    app := transire.New()
    app.RegisterQueue("OrderCreated", processOrder)  // Must register
    app.Run()
}
```

And workers are running:

```bash
transire run --queue-workers=1
```

### Scheduled job not firing

**Problem:** Schedule expression invalid or timezone wrong

**Solution:** Verify schedule in manifest:

```bash
cat transire_manifest.json | jq '.schedules'
```

Check logs for schedule errors:

```bash
transire run --log-level=debug
```

## See Also

- [transire gen](/docs/cli/gen.md) - Generate manifest
- [transire deploy](/docs/cli/deploy.md) - Deploy to cloud
- [Configuration](/docs/reference/config-schema.md) - transire.yaml schema
- [Testing](/docs/guides/testing.md) - Testing strategies
- [Local vs Cloud](/docs/guides/local-vs-cloud.md) - Parity details
