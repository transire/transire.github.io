---
title: "Local vs Cloud Development"
category: guides
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - Understanding of Transire basics
  - Experience with local development
  - Familiarity with serverless concepts
mcp_use: reference
mcp_operations:
  - compare_environments
  - identify_differences
features_covered:
  - Local development workflow
  - Cloud deployment differences
  - Parity and limitations
  - Testing strategies
  - Common gotchas
code_blocks: true
last_updated: 2025-10-30
---

# Local vs Cloud Development

## Overview

Transire is designed to run the **same code** in both local development and cloud production environments. However, the underlying runtime differs: local uses emulators while cloud uses actual serverless infrastructure. Understanding these differences helps you develop confidently and avoid surprises.

**Philosophy:** Local mode is optimized for rapid development and testing, not for production-like load testing. The cloud is the source of truth for performance and scalability.

## Key Differences

### Runtime Comparison

| Aspect | Local Development | Cloud Production |
|--------|------------------|------------------|
| **HTTP Server** | Chi router (single process) | Lambda + API Gateway v2 |
| **Queue Processing** | In-memory queue, N workers | SQS + Lambda event source |
| **Scheduled Jobs** | Fixed-rate timer | EventBridge rules |
| **Concurrency** | Configurable workers (default 1) | Auto-scaling to thousands |
| **State** | In-memory (lost on restart) | Persistent (SQS, EventBridge) |
| **Timeouts** | Graceful cancellation via `ctx.Done()` | Hard-kill by platform |
| **Cold Starts** | None | Yes (optimized for ARM64) |
| **Cost** | Free (local compute) | Pay per invocation |
| **Networking** | localhost | VPC, security groups (optional) |

## HTTP Handler Parity

### What's The Same

**Handler signature:**
```go
func handler(w http.ResponseWriter, r *http.Request)
```

**Routing:**
```go
app.GET("/orders/{id}", getOrder)
app.POST("/orders", createOrder)
```

**URL parameters:**
```go
id := transire.URLParam(r, "id")
```

**Request/response helpers:**
```go
response.OK(w, data)
response.NotFound(w, "order not found")
```

**Middleware execution:**
```go
app.Use(authMiddleware)  // Runs in both environments
```

### What's Different

**Local:** Single Chi HTTP server handling all routes
```
Request → Chi Router → Handler → Response
```

**Cloud:** Lambda receives API Gateway events
```
Request → API Gateway → Lambda → Chi Router → Handler → Response
```

**Size limits (local):**
- Default: 6MB request/response limit (configurable)
- Can disable for local testing: `http.simulate_apigw_limits: false`

**Size limits (cloud):**
- API Gateway: 10MB request, 6MB response (hard limit)
- Lambda: 6MB sync response (hard limit)

**Connection handling:**
- **Local:** Persistent HTTP connections (keep-alive)
- **Cloud:** Stateless, no connection reuse between invocations

**Testing approach:**

```go
// Local development
func main() {
    app := transire.New()
    app.GET("/orders/{id}", getOrder)
    app.Run()  // Blocks, starts server
}

// Test locally
$ transire run
$ curl http://localhost:8080/orders/123

// Deploy to cloud (same code)
$ transire deploy
$ curl https://api-id.execute-api.us-east-1.amazonaws.com/orders/123
```

## Queue Handler Parity

### What's The Same

**Handler signature:**
```go
func processOrders(ctx context.Context, msgs []Order) error
```

**Batch processing:**
```go
br := transire.NewBatchResult(len(msgs))
for i, msg := range msgs {
    if err := process(msg); err != nil {
        br.Fail(i, err)
    }
}
return br.ToCloudPartialBatchResponse()
```

**Message type validation:**
- Both validate `__type` field
- Mismatched types logged and rejected

### What's Different

**Local emulator:**
```
Enqueue → In-memory queue → Worker goroutine → Handler
```

- Configurable workers per queue (default 1)
- Messages lost on restart
- Retries simulated (optional)
- No DLQ (failures logged)

**Cloud (SQS + Lambda):**
```
Enqueue → SQS → Event source mapping → Lambda → Handler
```

- Auto-scaling concurrency
- Persistent messages
- Automatic retries (max 3 by default)
- DLQ for failed messages

**Concurrency:**

Local configuration:
```yaml
queues:
  workers_per_queue: 2  # Parallel workers
```

Cloud configuration:
```yaml
queues:
  max_concurrency: 10  # Lambda concurrent executions
```

**Visibility timeout:**

Local behavior:
- Messages removed from queue immediately after handler starts
- Simulated visibility timeout (optional)

Cloud behavior:
- Messages hidden during processing
- Reappear if handler times out
- Visibility timeout: 30s (default)

**Testing approach:**

```go
// Local testing
app := testkit.App().Start(t)
app.Enqueue("ProcessedOrder", order)
app.DrainQueue(t, "ProcessedOrder")  // Waits for processing

// Cloud testing
$ transire deploy
$ aws sqs send-message --queue-url https://sqs.../ --message-body '{...}'
$ aws logs tail /aws/lambda/myapp-prod-queue-ProcessedOrder
```

## Scheduled Job Parity

### What's The Same

**Handler signature:**
```go
func dailyReport(ctx context.Context) error
```

**Schedule syntax:**
```go
app.RegisterScheduled("@daily 09:00", dailyReport)
app.RegisterScheduled("@hourly", hourlyCleanup)
```

### What's Different

**Local scheduler:**
- Fixed-rate timer
- Non-overlapping executions (skips if previous run still active)
- Starts immediately on `transire run`
- Stops gracefully on shutdown

**Cloud (EventBridge):**
- EventBridge rules with Lambda targets
- May fire concurrent executions if handler is slow
- Starts at scheduled time (not immediately)
- Lambda execution isolated per trigger

**Overlap handling:**

Local behavior:
```
09:00:00 - Job starts
09:00:05 - Still running
09:01:00 - Skipped (previous run not complete)
09:02:00 - Skipped
09:03:00 - Previous run finishes
09:04:00 - Job starts (next scheduled time)
```

Cloud behavior:
```
09:00:00 - Lambda invoked
09:00:05 - Still running
09:01:00 - Lambda invoked again (concurrent)
```

**Design for idempotency:**

```go
func dailyReport(ctx context.Context) error {
    // Check if report already generated today
    today := time.Now().Format("2006-01-02")
    exists, err := reportExists(ctx, today)
    if err != nil {
        return err
    }
    if exists {
        log.Printf("Report for %s already exists, skipping", today)
        return nil
    }

    // Generate report
    return generateReport(ctx, today)
}
```

## Dependency Injection Parity

### What's The Same

**Singleton providers:**
```go
transire.Provide(func() (*Database, error) {
    return connectDB(os.Getenv("DB_URL"))
})
```

**Request-scoped providers:**
```go
transire.ProvideRequest(func(ctx context.Context, r *http.Request) (*RequestID, error) {
    return &RequestID{ID: transire.Header(r, "X-Request-Id")}, nil
})
```

**Access patterns:**
```go
db := transire.MustGet[*Database](ctx)
```

### What's Different

**Local lifecycle:**
- Singletons created once per process
- Live until `transire run` stops
- Shared across all requests/handlers

**Cloud lifecycle:**
- Singletons created once per Lambda cold start
- Live until Lambda container recycles (minutes to hours)
- NOT shared across Lambda instances

**Cold starts:**

Local (no cold starts):
```
$ transire run
Creating singletons...  (once)
✓ Server started
```

Cloud (cold starts):
```
First request → Cold start → Create singletons → Handler
Subsequent requests → Warm start → Reuse singletons → Handler
After ~10 min idle → Container recycles → Next request is cold start
```

**Connection pooling:**

Local example:
```go
// Single DB connection pool shared by all requests
transire.Provide(func() (*Database, error) {
    return sql.Open("postgres", os.Getenv("DB_URL"))
})
```

Cloud example:
```go
// Connection pool per Lambda instance
// Reused across warm invocations
transire.Provide(func() (*Database, error) {
    db, err := sql.Open("postgres", os.Getenv("DB_URL"))
    if err != nil {
        return nil, err
    }
    db.SetMaxOpenConns(2)  // Limit connections per Lambda
    return db, nil
})
```

## Error Handling Parity

### What's The Same

**HTTP errors:**
```go
return transire.ErrNotFound("order not found")  // → 404
return transire.ErrInternal("database error")   // → 500
```

**Queue batch failures:**
```go
br := transire.NewBatchResult(len(msgs))
br.Fail(0, errors.New("invalid order"))
return br.ToCloudPartialBatchResponse()
```

**Panic recovery:**
- Both environments recover panics
- Stack traces logged
- HTTP returns 500, queue message retried

### What's Different

**Timeout handling:**

Local behavior:
```go
ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
defer cancel()

select {
case <-ctx.Done():
    return ctx.Err()  // Graceful cancellation
case result := <-doWork():
    return nil
}
```

Cloud behavior:
```go
// Lambda times out after configured limit
// Handler is killed mid-execution
// No cleanup code runs
```

**Best practice: Always respect `ctx.Done()`**

```go
func handler(ctx context.Context) error {
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()  // Exit cleanly
        default:
            // Do work
        }
    }
}
```

## Observability Differences

### Logging

**Local:**
```
2024-10-30T10:15:30Z INFO [http] GET /orders/123 status=200 duration=45ms
```

**Cloud (CloudWatch):**
```json
{
  "timestamp": "2024-10-30T10:15:30Z",
  "level": "INFO",
  "message": "GET /orders/123",
  "status": 200,
  "duration_ms": 45,
  "trace_id": "1-67234a3f-0123456789abcdef",
  "request_id": "abc123"
}
```

### Tracing

**Local (optional):**
```yaml
observability:
  tracing:
    enabled: true
    provider: otel
    endpoint: http://localhost:4318
```

**Cloud (AWS X-Ray):**
```yaml
observability:
  tracing:
    enabled: true
    provider: aws-xray
```

**Trace propagation:**
- 🔮 HTTP → Queue trace propagation is planned for v1.1 (not yet implemented)
- X-Ray integration will be automatic in cloud when implemented
- OTEL support will require manual setup locally when implemented
- For now, manually pass trace IDs via message payloads if needed

### Metrics

**Local:**
- No built-in metrics
- Can add Prometheus exporter manually

**Cloud (CloudWatch):**
- Automatic Lambda metrics (invocations, errors, duration)
- Custom metrics via CloudWatch SDK

## Testing Strategies

### Local-First Development

**Workflow:**
```bash
# 1. Develop locally
transire run

# 2. Test with curl/Postman
curl http://localhost:8080/orders

# 3. Run integration tests
go test ./...

# 4. Deploy to dev environment
transire deploy --env dev

# 5. Run smoke tests
./scripts/smoke-test.sh dev

# 6. Deploy to production
transire deploy --env prod
```

### When to Test Locally

✅ **Good for local testing:**
- HTTP handler logic
- Queue batch processing logic
- Business logic and validation
- Unit tests
- Integration tests with mocks
- Rapid iteration

❌ **NOT good for local testing:**
- Load testing (concurrency, throughput)
- Cold start performance
- Cloud-specific behavior (SQS retries, Lambda timeouts)
- Network latency
- VPC connectivity

### When to Test in Cloud

✅ **Deploy to dev/staging for:**
- Performance testing
- Load testing
- Cold start optimization
- Integration with cloud services (S3, DynamoDB)
- End-to-end testing
- Security testing (IAM policies, VPC)

## Common Gotchas

### 1. In-Memory State

**Problem:**
```go
var cache = make(map[string]string)  // Global state

func handler(w http.ResponseWriter, r *http.Request) {
    cache[key] = value  // Works locally, breaks in cloud
}
```

**Why:** Lambda instances are ephemeral. Cache lost between cold starts.

**Solution:** Use external state (Redis, DynamoDB)
```go
func handler(w http.ResponseWriter, r *http.Request) {
    redis.Set(ctx, key, value)  // Persistent across Lambda instances
}
```

### 2. Long-Running Operations

**Problem:**
```go
func handler(ctx context.Context) error {
    for i := 0; i < 1000000; i++ {
        process(item)  // Takes 5 minutes
    }
    return nil
}
```

**Why:** Lambda has max timeout (15 min). Local can run indefinitely.

**Solution:** Break into smaller chunks or use queues
```go
func handler(ctx context.Context) error {
    for i := 0; i < 100; i++ {  // Process 100 at a time
        if ctx.Err() != nil {
            return ctx.Err()  // Respect cancellation
        }
        process(item)
    }
    return nil
}
```

### 3. Database Connection Exhaustion

**Problem:**
```go
transire.Provide(func() (*Database, error) {
    db, _ := sql.Open("postgres", url)
    db.SetMaxOpenConns(100)  // Too many for Lambda
    return db, nil
})
```

**Why:** Each Lambda instance creates a connection pool. 100 instances = 10,000 connections.

**Solution:** Limit connections per Lambda
```go
transire.Provide(func() (*Database, error) {
    db, _ := sql.Open("postgres", url)
    db.SetMaxOpenConns(2)  // 2-5 per Lambda instance
    return db, nil
})
```

### 4. File System Assumptions

**Problem:**
```go
func handler(ctx context.Context) error {
    os.WriteFile("/tmp/report.pdf", data, 0644)  // Works
    return nil
}

// Later invocation
func handler2(ctx context.Context) error {
    data, err := os.ReadFile("/tmp/report.pdf")  // May fail!
    return err
}
```

**Why:** Lambda `/tmp` is per-instance, not shared. File may not exist in warm container.

**Solution:** Use S3 for persistent file storage
```go
func handler(ctx context.Context) error {
    s3.PutObject(ctx, "bucket", "report.pdf", data)
    return nil
}
```

### 5. Timezone Assumptions

**Problem:**
```go
now := time.Now()  // Uses system timezone
```

**Why:** Local system timezone may differ from Lambda (UTC).

**Solution:** Always use explicit timezone
```go
loc, _ := time.LoadLocation("America/New_York")
now := time.Now().In(loc)
```

Or configure in `transire.yaml`:
```yaml
timezone: America/New_York  # Applied to scheduled jobs
```

## Simulating Cloud Behavior Locally

### Size Limits

Enable API Gateway size limits locally:
```yaml
http:
  simulate_apigw_limits: true  # Enforce 6MB limit
```

### Timeouts

Simulate Lambda timeouts locally:
```yaml
deploy:
  timeout_s: 30  # Same as cloud

# Handler respects context timeout
func handler(ctx context.Context) error {
    // ctx has 30s deadline
}
```

### Queue Retries

Enable retry simulation locally:
```yaml
queues:
  simulate_retries: true
  max_receive_count: 3
```

Failed messages are retried up to 3 times before being logged as failures.

## Best Practices

1. **Test locally first** - Fast iteration, instant feedback
2. **Deploy to dev early** - Catch cloud-specific issues
3. **Use testkit** - Integration tests work both locally and in cloud
4. **Respect context cancellation** - Always check `ctx.Done()`
5. **Avoid global state** - Use external storage (Redis, DynamoDB)
6. **Limit DB connections** - 2-5 per Lambda instance
7. **Use external storage** - S3, not `/tmp`, for persistence
8. **Log structured JSON** - Consistent format for CloudWatch
9. **Enable tracing** - Debug issues across local and cloud
10. **Monitor cold starts** - Optimize Lambda init code

## Development Checklist

### Before Deploying

- [ ] Handlers tested locally (`transire run`)
- [ ] Integration tests pass (`go test ./...`)
- [ ] No global mutable state
- [ ] Context cancellation respected
- [ ] Database connection limits set
- [ ] Timeouts configured appropriately
- [ ] Structured logging enabled

### After Deploying

- [ ] Smoke tests pass
- [ ] CloudWatch logs show no errors
- [ ] Cold start time acceptable (< 5s)
- [ ] No connection pool exhaustion
- [ ] Traces show healthy behavior
- [ ] Performance meets requirements

## See Also

- [Testing Guide](/guides/testing.md) - Local and integration testing
- [Deployment Guide](/guides/deployment.md) - Deploying to cloud
- [Environments Guide](/guides/environments.md) - Multi-environment setup
- [Performance Guide](/guides/performance.md) - Optimization strategies
- [Testkit Reference](/sdk/testkit.md) - Testing utilities
