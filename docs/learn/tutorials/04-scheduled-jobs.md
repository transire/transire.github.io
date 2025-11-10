---
title: "Tutorial: Scheduled Jobs"
description: Add cron-based scheduled tasks for periodic work in 15 minutes
category: learn
subcategory: tutorial
complexity: beginner
duration: 15 minutes
prerequisites:
  - Completed Queue Processing tutorial
  - Understanding of cron expressions
  - Go 1.22+
mcp_use: template
mcp_operations:
  - add_scheduled_job
  - configure_schedule
  - test_schedule
features_covered:
  - Scheduled handlers
  - Cron expressions
  - Timezone handling
  - Idempotent jobs
  - Local vs cloud schedules
code_blocks: true
last_updated: 2025-11-10
---

# Tutorial: Scheduled Jobs

> **Quick Summary:** Add periodic tasks that run automatically on a schedule

## What You'll Build

Add scheduled jobs to your orders API:

```
Daily at 9 AM → Generate sales report
Every hour    → Cleanup old pending orders
Every 5 min   → Sync inventory (local dev only)
```

**Time:** 15 minutes • **Difficulty:** Beginner

---

## Why Use Scheduled Jobs?

Scheduled jobs are perfect for:

- **Reports** - Daily/weekly/monthly reports
- **Cleanup** - Remove old data
- **Synchronization** - Sync with external systems
- **Reminders** - Send notifications
- **Health checks** - System monitoring
- **Data processing** - Batch operations

**When to use:**
- Predictable, recurring tasks
- Time-based triggers
- Independent of user actions

---

## Step 1: Register a Scheduled Job

Add to your `main()` function:

```go
func main() {
    app := transire.New()

    // HTTP routes (existing)
    app.GET("/orders", listOrders)
    app.POST("/orders", createOrder)

    // Queue handlers (existing)
    app.RegisterQueue("fulfill-orders", fulfillOrders)

    // Scheduled jobs (NEW)
    err = app.RegisterScheduled("@daily 09:00", generateDailyReport)
    if err != nil {
        log.Fatal("Failed to register schedule:", err)
    }

    app.Run()
}
```

**Key points:**
- `"@daily 09:00"` is the schedule expression (shorthand)
- `generateDailyReport` is the handler function
- Handler signature: `func(ctx context.Context) error`

---

## Step 2: Implement the Handler

```go
import (
    "context"
    "fmt"
    "log"
    "time"
)

// generateDailyReport runs every day at 9 AM
func generateDailyReport(ctx context.Context) error {
    log.Println("Generating daily sales report...")

    // Get yesterday's date range
    now := time.Now()
    startOfYesterday := time.Date(now.Year(), now.Month(), now.Day()-1, 0, 0, 0, 0, now.Location())
    endOfYesterday := startOfYesterday.Add(24 * time.Hour)

    // Calculate metrics
    var totalSales float64
    var orderCount int
    var fulfilledCount int

    for _, order := range orders {
        // Only count orders from yesterday
        if order.CreatedAt.After(startOfYesterday) && order.CreatedAt.Before(endOfYesterday) {
            orderCount++
            totalSales += order.Price * float64(order.Quantity)

            if order.Status == "fulfilled" {
                fulfilledCount++
            }
        }
    }

    // Generate report
    report := fmt.Sprintf(`
Daily Sales Report - %s
=====================================
Total Orders:     %d
Fulfilled Orders: %d
Total Sales:      $%.2f
Fulfillment Rate: %.1f%%
`,
        startOfYesterday.Format("2006-01-02"),
        orderCount,
        fulfilledCount,
        totalSales,
        float64(fulfilledCount)/float64(orderCount)*100,
    )

    log.Println(report)

    // In production, this would:
    // - Save report to S3
    // - Send email to admins
    // - Update analytics dashboard
    // - Post to Slack channel

    return nil
}
```

**Handler best practices:**
- ✅ Idempotent (safe to run multiple times)
- ✅ Check `ctx.Done()` for cancellation
- ✅ Log start and completion
- ✅ Handle errors gracefully
- ✅ No side effects on failure

---

## Step 3: Test Locally

Start the server:

```bash
$ go run main.go
✓ Starting HTTP server on :8080
✓ Queue emulator: 1 queue
✓ Scheduler: 1 job (daily-report, next run: tomorrow at 09:00)
→ Ready
```

Notice: "Scheduler" confirms the job is registered.

### Trigger Manually (Local Testing)

For local testing, trigger immediately:

```go
// Add a test endpoint (development only)
app.GET("/admin/trigger-report", func(w http.ResponseWriter, r *http.Request) {
    if err := generateDailyReport(r.Context()); err != nil {
        response.InternalServerError(w, "Report generation failed")
        return
    }
    response.OK(w, map[string]string{"status": "Report generated"})
})
```

Test it:

```bash
$ curl http://localhost:8080/admin/trigger-report
{"status": "Report generated"}
```

Check server logs for the report output.

---

## Step 4: Schedule Expressions

Transire supports multiple schedule formats:

### Shorthand (Recommended)

```go
// Rate-based (timezone-agnostic)
app.RegisterScheduled("@hourly", handler)    // Every hour
app.RegisterScheduled("@daily", handler)     // Every 24 hours

// Time-based (uses service timezone)
app.RegisterScheduled("@daily 09:00", handler)               // 9 AM daily
app.RegisterScheduled("@daily 14:30", handler)               // 2:30 PM daily
app.RegisterScheduled("@daily 09:00 America/New_York", handler) // Explicit timezone
```

### Cron Expressions

```go
// Standard cron format
app.RegisterScheduled("cron(0 9 * * ? *)", handler)    // 9 AM daily
app.RegisterScheduled("cron(*/15 * * * ? *)", handler) // Every 15 minutes
app.RegisterScheduled("cron(0 0 * * 1 *)", handler)    // Monday at midnight
```

**Cron format:** `minute hour day month day-of-week year`

| Field | Values | Special |
|-------|--------|---------|
| minute | 0-59 | `*/15` = every 15 min |
| hour | 0-23 | `*/2` = every 2 hours |
| day | 1-31 | `?` = any |
| month | 1-12 or JAN-DEC | `*` = all |
| day-of-week | 0-6 or SUN-SAT | `1-5` = weekdays |
| year | 1970-2199 | `*` = all |

### Rate Expressions

```go
// Rate syntax (cloud provider specific)
app.RegisterScheduled("rate(1 hour)", handler)    // Every hour
app.RegisterScheduled("rate(30 minutes)", handler) // Every 30 min
app.RegisterScheduled("rate(7 days)", handler)    // Every week
```

---

## Step 5: Multiple Scheduled Jobs

Add more scheduled jobs:

```go
func main() {
    app := transire.New()

    // Daily report at 9 AM
    app.RegisterScheduled("@daily 09:00", generateDailyReport)

    // Cleanup old orders every hour
    app.RegisterScheduled("@hourly", cleanupOldOrders)

    // Weekly report on Mondays
    app.RegisterScheduled("cron(0 10 * * 1 *)", generateWeeklyReport)

    app.Run()
}

// cleanupOldOrders removes orders older than 30 days
func cleanupOldOrders(ctx context.Context) error {
    log.Println("Cleaning up old orders...")

    cutoff := time.Now().Add(-30 * 24 * time.Hour)
    deleted := 0

    for id, order := range orders {
        if order.CreatedAt.Before(cutoff) {
            delete(orders, id)
            deleted++
        }
    }

    log.Printf("Deleted %d old orders", deleted)
    return nil
}

// generateWeeklyReport runs every Monday at 10 AM
func generateWeeklyReport(ctx context.Context) error {
    log.Println("Generating weekly report...")
    // ... implementation ...
    return nil
}
```

---

## Step 6: Configure Timezone

Set service timezone in `transire.yaml`:

```yaml
version: 1
service: orders-api
timezone: America/New_York  # All cron schedules use this timezone

# Or use UTC (default)
# timezone: UTC
```

**Important:** Rate-based schedules (`@hourly`, `rate(1 hour)`) are timezone-agnostic. Only time-based schedules (`@daily 09:00`, cron) use the timezone.

---

## Understanding Schedules: Local vs Cloud

### Local Mode

```bash
$ transire run
✓ Scheduler: 1 job (daily-report, next run: tomorrow at 09:00)
```

**How it works:**
- Fixed-rate Go timer
- Non-overlapping execution
- Immediate feedback in logs

**Good for:**
- Development
- Testing schedule logic
- Quick iteration

### Cloud Mode

```bash
$ transire deploy
```

**How it works:**
- AWS EventBridge rule created
- Lambda invoked on schedule
- Serverless execution

**Good for:**
- Production reliability
- Distributed systems
- Cost-effective scaling

---

## Idempotent Job Design

Scheduled jobs must be **idempotent** (safe to run multiple times):

### ❌ Bad: Not Idempotent

```go
func processOrders(ctx context.Context) error {
    // Problem: Runs on ALL orders every time
    for _, order := range orders {
        process(order)  // Processes same order multiple times!
    }
    return nil
}
```

### ✅ Good: Idempotent

```go
func processOrders(ctx context.Context) error {
    // Only process orders not yet processed
    for _, order := range orders {
        if order.Status == "pending" {
            process(order)
            order.Status = "processed"
        }
    }
    return nil
}
```

**Key principle:** Check state before modifying.

---

## Common Patterns

### Pattern 1: Check Context

```go
func longRunningJob(ctx context.Context) error {
    for i := 0; i < 1000; i++ {
        // Check if cancelled
        if ctx.Err() != nil {
            log.Printf("Job cancelled after %d iterations", i)
            return ctx.Err()
        }

        // Do work
        processItem(i)
    }
    return nil
}
```

### Pattern 2: Error Handling

```go
func generateReport(ctx context.Context) error {
    // Retry on failure
    maxRetries := 3
    for i := 0; i < maxRetries; i++ {
        if err := tryGenerateReport(ctx); err == nil {
            return nil
        }
        log.Printf("Attempt %d failed, retrying...", i+1)
        time.Sleep(time.Second * time.Duration(i+1))
    }
    return fmt.Errorf("failed after %d retries", maxRetries)
}
```

### Pattern 3: Logging

```go
func dailyTask(ctx context.Context) error {
    start := time.Now()
    log.Println("Daily task started")

    defer func() {
        log.Printf("Daily task completed in %v", time.Since(start))
    }()

    // Do work...
    return nil
}
```

### Pattern 4: External API Calls

```go
func syncInventory(ctx context.Context) error {
    // Add timeout for external calls
    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()

    resp, err := externalAPI.GetInventory(ctx)
    if err != nil {
        log.Printf("Failed to sync inventory: %v", err)
        return err
    }

    // Update local data
    updateInventory(resp)
    return nil
}
```

---

## Configuration

Configure schedule behavior in `transire.yaml`:

```yaml
version: 1
service: orders-api
timezone: America/New_York

schedules:
  enabled: true
  concurrent_executions: false  # Prevent overlapping runs

observability:
  logging:
    level: info
    format: json

# Local development: faster schedules for testing
local:
  schedules:
    scale_factor: 0.1  # 10x faster (1 hour → 6 minutes)
```

---

## Troubleshooting

### Job Not Running

**Issue:** Scheduled job never executes.

**Check:**

1. **Is schedule registered?**
   ```go
   app.RegisterScheduled("@daily 09:00", handler)
   ```

2. **Is schedule expression valid?**
   ```bash
   # Test with crontab validator
   # https://crontab.guru/
   ```

3. **Local mode:** Check logs for "next run"
   ```
   ✓ Scheduler: 1 job (daily-report, next run: tomorrow at 09:00)
   ```

4. **Cloud mode:** Check EventBridge rule
   ```bash
   aws events describe-rule --name orders-api-dev-daily-report
   ```

### Wrong Timezone

**Issue:** Job runs at wrong time.

**Solution:**

1. **Check timezone configuration:**
   ```yaml
   timezone: America/New_York  # Must match your location
   ```

2. **Use explicit timezone in schedule:**
   ```go
   app.RegisterScheduled("@daily 09:00 America/New_York", handler)
   ```

3. **Verify in cloud:**
   ```bash
   aws events describe-rule --name app-schedule | jq '.ScheduleExpression'
   ```

### Overlapping Executions

**Issue:** Job starts before previous run finishes.

**Solutions:**

1. **Increase timeout:**
   ```yaml
   deploy:
     timeout_s: 60  # Increase from 30s
   ```

2. **Add execution lock:**
   ```go
   var mu sync.Mutex

   func job(ctx context.Context) error {
       if !mu.TryLock() {
           log.Println("Previous execution still running, skipping")
           return nil
       }
       defer mu.Unlock()

       // Do work...
       return nil
   }
   ```

3. **Configure non-concurrent:**
   ```yaml
   schedules:
     concurrent_executions: false
   ```

---

## Testing Scheduled Jobs

### Unit Test

```go
func TestGenerateDailyReport(t *testing.T) {
    // Setup test data
    orders = map[string]*Order{
        "1": {ID: "1", Price: 100, Status: "fulfilled"},
        "2": {ID: "2", Price: 200, Status: "pending"},
    }

    // Run job
    ctx := context.Background()
    err := generateDailyReport(ctx)

    // Assert
    if err != nil {
        t.Fatalf("Expected no error, got: %v", err)
    }
}
```

### Integration Test

```go
import "github.com/transire/transire-sdk-go/testkit"

func TestScheduledJob(t *testing.T) {
    tk := testkit.New(t)

    // Register app
    tk.Schedule("daily-report", "@daily 09:00", generateDailyReport)

    // Trigger manually
    err := tk.TriggerSchedule("daily-report")
    if err != nil {
        t.Fatalf("Schedule trigger failed: %v", err)
    }

    // Verify side effects
    // (check logs, database, etc.)
}
```

---

## Complete Code

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "github.com/transire/transire-sdk-go"
)

func main() {
    app := transire.New()

    // HTTP routes
    app.GET("/orders", listOrders)
    app.POST("/orders", createOrder)

    // Queue handlers
    app.RegisterQueue("fulfill-orders", fulfillOrders)

    // Scheduled jobs
    app.RegisterScheduled("@daily 09:00", generateDailyReport)
    app.RegisterScheduled("@hourly", cleanupOldOrders)
    app.RegisterScheduled("cron(0 10 * * 1 *)", generateWeeklyReport)

    app.Run()
}

func generateDailyReport(ctx context.Context) error {
    start := time.Now()
    log.Println("Generating daily sales report...")

    defer func() {
        log.Printf("Report generation completed in %v", time.Since(start))
    }()

    // Check cancellation
    if ctx.Err() != nil {
        return ctx.Err()
    }

    now := time.Now()
    startOfYesterday := time.Date(now.Year(), now.Month(), now.Day()-1, 0, 0, 0, 0, now.Location())
    endOfYesterday := startOfYesterday.Add(24 * time.Hour)

    var totalSales float64
    var orderCount int
    var fulfilledCount int

    for _, order := range orders {
        if order.CreatedAt.After(startOfYesterday) && order.CreatedAt.Before(endOfYesterday) {
            orderCount++
            totalSales += order.Price * float64(order.Quantity)
            if order.Status == "fulfilled" {
                fulfilledCount++
            }
        }
    }

    report := fmt.Sprintf(`
Daily Sales Report - %s
=====================================
Total Orders:     %d
Fulfilled Orders: %d
Total Sales:      $%.2f
Fulfillment Rate: %.1f%%
`,
        startOfYesterday.Format("2006-01-02"),
        orderCount,
        fulfilledCount,
        totalSales,
        float64(fulfilledCount)/float64(orderCount)*100,
    )

    log.Println(report)
    return nil
}

func cleanupOldOrders(ctx context.Context) error {
    log.Println("Cleaning up old orders...")

    cutoff := time.Now().Add(-30 * 24 * time.Hour)
    deleted := 0

    for id, order := range orders {
        if order.CreatedAt.Before(cutoff) {
            delete(orders, id)
            deleted++
        }
    }

    log.Printf("Deleted %d old orders", deleted)
    return nil
}

func generateWeeklyReport(ctx context.Context) error {
    log.Println("Generating weekly report...")
    // Implementation...
    return nil
}
```

---

## What You Learned

Congratulations! You've implemented scheduled jobs. You now know:

- ✅ How to register scheduled handlers
- ✅ Cron expressions and shorthand syntax
- ✅ Timezone handling
- ✅ Idempotent job design
- ✅ Local vs cloud scheduling
- ✅ Testing scheduled jobs
- ✅ Troubleshooting schedules
- ✅ Common patterns

---

## Next Steps

### Add Dependency Injection

Continue to [DI Tutorial →](05-dependency-injection.md) to learn how to manage service dependencies.

### Deploy to Cloud

See [First Deployment Guide →](../../guides/deployment/first-deployment/) to deploy your complete application.

### Advanced Patterns

- **Distributed Locking** - Prevent concurrent execution across instances
- **Job Queues** - Enqueue work from scheduled jobs
- **Monitoring** - Track execution time and failures
- **Dynamic Schedules** - Update schedules without redeployment

---

## See Also

- [Schedule API Reference](../../reference/sdk/schedule-api/) - Complete schedule documentation
- [AWS EventBridge](../../plugins/cloud/aws/schedules/) - How schedules work in AWS
- [Idempotency Guide](../../guides/idempotency/) - Safe retries
- [Troubleshooting Schedules](../../guides/troubleshooting/) - Common issues
- [Testing Guide](../../guides/testing/) - Test your jobs
