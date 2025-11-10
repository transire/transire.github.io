---
title: "Local Provider"
category: providers
complexity: beginner
duration: 5 minutes
mcp_use: reference
last_updated: 2025-11-10
---

# Local Provider

The local provider enables fast development without cloud dependencies. Run your entire Transire application on your local machine with in-process emulation of queues and schedules.

## Overview

The local provider is **built into Transire** - no installation required. It automatically activates when you run `transire run`.

**Key Features:**
- ✅ **No cloud account needed** - Develop offline
- ✅ **Fast feedback** - Instant restarts, no deployment delays
- ✅ **Zero cost** - No cloud charges during development
- ✅ **Full feature support** - HTTP, queues, schedules all work locally
- ✅ **Parity with cloud** - Same APIs, same behavior

## How It Works

```
┌─────────────────────────────────────────────┐
│  transire run                               │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  HTTP Server (Chi Router)            │  │
│  │  • Port 8080 (default)               │  │
│  │  • All your HTTP routes              │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  In-Memory Queue Manager             │  │
│  │  • Batch processing                  │  │
│  │  • Configurable workers              │  │
│  │  • Simulated retries                 │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Fixed-Rate Scheduler                │  │
│  │  • Non-overlapping execution         │  │
│  │  • Respects cron expressions         │  │
│  └──────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

All components run in a single Go process.

## Getting Started

No installation needed - just run your app:

```bash
# Start local development server
transire run

# Output:
# ✓ Generated manifest
# ✓ Compiled application
# ✓ Starting local server on :8080
# ✓ Registered 3 HTTP routes
# ✓ Registered 1 queue handler
# ✓ Registered 1 scheduled job
# → Server ready at http://localhost:8080
```

## HTTP Handlers

HTTP handlers work exactly like they will in the cloud:

```go
app.GET("/users/{id}", getUserHandler)
app.POST("/users", createUserHandler)
```

**Local behavior:**
- Chi router handles all routing
- Requests served on `http://localhost:8080`
- Standard Go middleware works
- Full HTTP request/response cycle

**Testing:**
```bash
curl http://localhost:8080/users/123
```

## Queue Handlers

Queues are emulated in-memory:

```go
app.RegisterQueue("orders", processOrders)
```

**Local behavior:**
- Messages stored in memory
- Processed by background workers
- Batching works as configured
- Retry logic simulated

**How enqueuing works:**
```go
// Enqueue from HTTP handler
app.Enqueue(ctx, "orders", order)

// Message immediately available to worker
// Processed in background
```

**Configuration:**
```yaml
queues:
  max_batch_size: 10
  visibility_timeout_s: 30
  max_receive_count: 3
```

**Worker concurrency:**
- Default: 1 worker per queue
- All workers run in same process
- Messages processed sequentially per queue

## Scheduled Jobs

Schedules are managed by a fixed-rate scheduler:

```go
app.RegisterScheduled("@daily 09:00", generateReport)
app.RegisterScheduled("@hourly", cleanupTask)
```

**Local behavior:**
- Jobs fire at configured times
- Non-overlapping execution (next waits for current)
- Uses local system time
- Respects timezone in schedule expression

**Testing schedules:**
Scheduled jobs won't fire during short test runs. To test:

1. Use very short intervals during development:
   ```go
   // Development only
   app.RegisterScheduled("rate(1 minute)", testJob)
   ```

2. Or test handlers directly:
   ```go
   func TestGenerateReport(t *testing.T) {
       err := generateReport(context.Background())
       assert.NoError(t, err)
   }
   ```

## Configuration

Configure local behavior in `transire.yaml`:

```yaml
service: myapp
runtime: go

# Local development settings
local:
  port: 8080                    # HTTP server port
  queue_workers: 1              # Workers per queue
  enable_scheduler: true        # Run scheduled jobs
  log_level: info               # Log verbosity

# These apply locally too
queues:
  max_batch_size: 10
  visibility_timeout_s: 30

http:
  max_request_size_mb: 10
  timeout_s: 30
```

## Known Differences from Cloud

The local provider is designed for **development convenience**, not **production parity**. Some differences:

### Persistence
- **Local:** Messages lost on restart (in-memory)
- **Cloud:** Messages persisted in queue service
- **Impact:** Don't rely on queue persistence locally

### Concurrency
- **Local:** Single process, limited parallelism
- **Cloud:** Massive horizontal scaling
- **Impact:** Load testing should happen in cloud

### Dead Letter Queue
- **Local:** Failed messages logged, not persisted
- **Cloud:** DLQ is real, messages can be inspected
- **Impact:** Monitor logs locally, use cloud DLQ for debugging production issues

### Scheduler Precision
- **Local:** Fixed-rate, may drift slightly
- **Cloud:** Distributed, highly reliable
- **Impact:** Use cloud for critical time-sensitive jobs

### Network Isolation
- **Local:** All handlers in same process
- **Cloud:** Each handler in separate function
- **Impact:** Local state sharing won't work in cloud

## Performance Considerations

### Memory Usage
- Queues stored in memory
- Large backlogs can consume RAM
- Limit batch sizes during local dev

### CPU Usage
- Single process handles everything
- Heavy queue processing can slow HTTP responses
- Consider reducing queue workers for better HTTP responsiveness:
  ```yaml
  local:
    queue_workers: 1  # Reduce to 1 if HTTP feels slow
  ```

### File System
- No automatic cleanup of temp files
- Application restarts don't clean state
- Manually clean up if needed

## Hot Reload

Enable hot reload to automatically restart on code changes:

```bash
transire run --watch
```

**How it works:**
1. Watches `*.go` files for changes
2. Recompiles on save
3. Gracefully stops old process
4. Starts new process
5. Preserves HTTP server port

**Note:** In-flight requests and queue messages may be lost during reload.

## Debugging

### View Logs
All logs go to stdout:

```bash
transire run

# Output:
[INFO] HTTP GET /users/123 200 45ms
[INFO] Queue: processing 5 messages from orders
[ERROR] Failed to process message: invalid order ID
```

### Debug Mode
Enable verbose logging:

```yaml
local:
  log_level: debug
```

Or via flag:
```bash
transire run --log-level=debug
```

### Inspect Queue State
No built-in queue inspector (messages in memory only). Use logging:

```go
func processOrders(ctx context.Context, msgs []Order) error {
    log.Printf("Processing batch of %d orders", len(msgs))
    // Your logic
}
```

## Testing

The local provider makes testing straightforward:

```go
func TestCreateUser(t *testing.T) {
    app := transire.New()
    app.POST("/users", createUser)

    // Test HTTP handler
    req := httptest.NewRequest("POST", "/users", body)
    w := httptest.NewRecorder()
    app.ServeHTTP(w, req)

    assert.Equal(t, 201, w.Code)
}
```

See [Testing Guide](/docs/sdk/testkit.md) for more patterns.

## Troubleshooting

### Port Already in Use
```
Error: listen tcp :8080: bind: address already in use
```

**Solution:** Change port in config or stop conflicting process
```yaml
local:
  port: 3000
```

### Queue Messages Not Processing
```
Messages enqueued but handler never called
```

**Check:**
1. Is queue handler registered?
   ```go
   app.RegisterQueue("orders", processOrders)
   ```
2. Are workers enabled?
   ```yaml
   local:
     queue_workers: 1  # Must be > 0
   ```

### Scheduled Job Not Firing
```
Scheduled job registered but never executes
```

**Check:**
1. Is scheduler enabled?
   ```yaml
   local:
     enable_scheduler: true
   ```
2. Is interval long enough for test duration?
   Use short intervals for testing:
   ```go
   app.RegisterScheduled("rate(1 minute)", handler)
   ```

## Best Practices

### Do's ✅
- Use local provider for rapid development
- Test HTTP handlers thoroughly locally
- Use short schedules for testing
- Monitor logs for errors
- Keep queue backlogs small

### Don'ts ❌
- Don't rely on message persistence
- Don't run load tests locally
- Don't share state between handlers
- Don't test DLQ behavior locally
- Don't use local provider for production

## Migration to Cloud

When ready to deploy, your code works unchanged:

```bash
# 1. Install cloud provider
go get github.com/transire/cloud-aws@latest

# 2. Add import
import _ "github.com/transire/cloud-aws"

# 3. Deploy
transire deploy --environment=dev
```

No code changes needed!

## See Also

- [AWS Provider](/docs/providers/aws/overview.md) - Deploy to AWS
- [Deployment Guide](/docs/deployment/overview.md) - Deployment workflow
- [Testing Guide](/docs/sdk/testkit.md) - Testing patterns
- [Configuration Reference](/docs/reference/config-schema.md) - Full config
