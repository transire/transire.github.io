---
title: Schedule API Reference
description: Complete reference for Transire scheduled jobs, cron expressions, and periodic tasks
category: reference
subcategory: sdk
complexity: beginner
mcp_use: reference
features_covered:
  - Scheduled jobs
  - Cron expressions
  - Rate expressions
  - Shorthand syntax
  - Timezone handling
  - Job configuration
code_blocks: true
last_updated: 2025-11-10
---

# Schedule API Reference

> **Complete reference** for scheduled jobs and periodic tasks with Transire

## Table of Contents

- [Schedule Registration](#schedule-registration)
- [Handler Signatures](#handler-signatures)
- [Schedule Expressions](#schedule-expressions)
- [Timezone Handling](#timezone-handling)
- [Configuration](#configuration)
- [Idempotent Design](#idempotent-design)
- [Local vs Cloud](#local-vs-cloud)
- [Testing](#testing)
- [Monitoring](#monitoring)

---

## Schedule Registration

### Basic Registration

Register a scheduled job:

```go
app.Schedule(key string, schedule string, handler ScheduleHandler)
```

**Parameters:**
- `key` - Unique schedule identifier
- `schedule` - Schedule expression (cron, rate, or shorthand)
- `handler` - Function to execute on schedule

**Example:**

```go
func main() {
    app := transire.New()

    // Daily at 9 AM
    app.Schedule("daily-report", "@daily 09:00", generateDailyReport)

    app.Run()
}

func generateDailyReport(ctx context.Context) error {
    log.Println("Generating daily report...")
    // Generate report...
    return nil
}
```

### Multiple Schedules

```go
func main() {
    app := transire.New()

    // Daily report at 9 AM
    app.Schedule("daily-report", "@daily 09:00", generateDailyReport)

    // Hourly cleanup
    app.Schedule("hourly-cleanup", "@hourly", cleanupOldData)

    // Weekly report on Mondays at 10 AM
    app.Schedule("weekly-report", "cron(0 10 * * 1 *)", generateWeeklyReport)

    // Every 5 minutes (local dev only)
    app.Schedule("sync-inventory", "rate(5 minutes)", syncInventory)

    app.Run()
}
```

---

## Handler Signatures

### Basic Handler

No dependencies:

```go
func(ctx context.Context) error
```

**Example:**

```go
func generateDailyReport(ctx context.Context) error {
    log.Println("Generating report...")

    // Check context cancellation
    if ctx.Err() != nil {
        return ctx.Err()
    }

    // Generate report
    report := createReport()

    // Save or send report
    saveReport(report)

    return nil
}
```

### Handler with Dependencies

Inject services:

```go
func(ctx context.Context, deps ...interface{}) error
```

**Example:**

```go
func generateDailyReport(ctx context.Context, db *Database, logger *Logger) error {
    logger.Info("Generating daily report...")

    // Query database
    data, err := db.GetDailyMetrics(ctx)
    if err != nil {
        logger.Error("Failed to fetch metrics", err)
        return err
    }

    // Generate report
    report := createReport(data)

    // Send report
    emailService.Send(report)

    logger.Info("Daily report sent")
    return nil
}
```

---

## Schedule Expressions

Transire supports three expression formats:

### 1. Shorthand (Recommended)

Simple, readable syntax for common schedules.

#### Rate-Based (Timezone-Agnostic)

```go
// Every hour
app.Schedule("hourly-job", "@hourly", handler)

// Every 24 hours
app.Schedule("daily-job", "@daily", handler)

// Every week (168 hours)
app.Schedule("weekly-job", "@weekly", handler)
```

**Rate schedules:**
- Start when deployed
- Run at fixed intervals
- Timezone-independent

#### Time-Based (Uses Service Timezone)

```go
// Daily at 9:00 AM
app.Schedule("morning-report", "@daily 09:00", handler)

// Daily at 2:30 PM
app.Schedule("afternoon-task", "@daily 14:30", handler)

// Daily at 9 AM EST (explicit timezone)
app.Schedule("report", "@daily 09:00 America/New_York", handler)
```

**Time schedules:**
- Use service timezone (from `transire.yaml`)
- Can override with explicit timezone
- More predictable for business logic

### 2. Cron Expressions

Standard cron format with 6 fields:

```
cron(minute hour day month day-of-week year)
```

**Field values:**

| Field | Values | Special |
|-------|--------|---------|
| minute | 0-59 | `*` = every minute<br/>`*/15` = every 15 minutes |
| hour | 0-23 | `*` = every hour<br/>`*/2` = every 2 hours |
| day | 1-31 | `?` = any day<br/>`L` = last day of month |
| month | 1-12 or JAN-DEC | `*` = every month |
| day-of-week | 0-6 or SUN-SAT | `?` = any day<br/>`1-5` = weekdays |
| year | 1970-2199 | `*` = every year |

**Examples:**

```go
// Every day at 9 AM
app.Schedule("daily", "cron(0 9 * * ? *)", handler)

// Every 15 minutes
app.Schedule("frequent", "cron(*/15 * * * ? *)", handler)

// Weekdays at 5 PM
app.Schedule("weekday-task", "cron(0 17 ? * 1-5 *)", handler)

// First day of month at midnight
app.Schedule("monthly", "cron(0 0 1 * ? *)", handler)

// Every Monday at 10 AM
app.Schedule("weekly", "cron(0 10 ? * 1 *)", handler)

// Last day of month at 11:59 PM
app.Schedule("month-end", "cron(59 23 L * ? *)", handler)
```

**Cron tips:**
- Use `?` in day or day-of-week (not both)
- `*` means "every"
- `*/n` means "every n"
- `L` means "last"

### 3. Rate Expressions

AWS EventBridge rate syntax:

```
rate(value unit)
```

**Units:** `minute`, `minutes`, `hour`, `hours`, `day`, `days`

**Examples:**

```go
// Every hour
app.Schedule("hourly", "rate(1 hour)", handler)

// Every 30 minutes
app.Schedule("half-hourly", "rate(30 minutes)", handler)

// Every 12 hours
app.Schedule("twice-daily", "rate(12 hours)", handler)

// Every 7 days
app.Schedule("weekly", "rate(7 days)", handler)
```

---

## Schedule Expression Comparison

| Expression | When to Use | Timezone | Example |
|------------|-------------|----------|---------|
| **@hourly** | Fixed intervals | Agnostic | Every hour from deploy time |
| **@daily HH:MM** | Specific time daily | Service TZ | 9 AM every day |
| **cron(...)** | Complex schedules | Service TZ | Weekdays, month-end, etc. |
| **rate(...)** | Fixed intervals | Agnostic | Every 30 minutes |

---

## Timezone Handling

### Service Timezone

Set default timezone in `transire.yaml`:

```yaml
version: 1
service: orders-api
timezone: America/New_York  # All time-based schedules use this

# Or use UTC (default)
# timezone: UTC
```

**Applies to:**
- `@daily HH:MM` schedules
- Cron expressions

**Does NOT apply to:**
- `@hourly`, `@daily`, `@weekly` (rate-based)
- `rate(...)` expressions

### Explicit Timezone

Override per-schedule:

```go
// 9 AM Eastern Time
app.Schedule("report", "@daily 09:00 America/New_York", handler)

// 6 PM Pacific Time
app.Schedule("west-coast", "@daily 18:00 America/Los_Angeles", handler)

// 2 PM UTC
app.Schedule("global", "@daily 14:00 UTC", handler)
```

### Valid Timezones

Use IANA timezone database names:

```
America/New_York    (EST/EDT)
America/Chicago     (CST/CDT)
America/Denver      (MST/MDT)
America/Los_Angeles (PST/PDT)
Europe/London       (GMT/BST)
Europe/Paris        (CET/CEST)
Asia/Tokyo          (JST)
UTC                 (UTC)
```

**Full list:** [IANA Time Zone Database](https://www.iana.org/time-zones)

---

## Configuration

### Global Schedule Configuration

Configure in `transire.yaml`:

```yaml
schedules:
  enabled: true                    # Enable schedules (default)
  concurrent_executions: false     # Prevent overlapping runs
  max_instances: 1                 # Max concurrent executions

# Local development overrides
local:
  schedules:
    scale_factor: 0.1              # 10x faster (1 hour → 6 minutes)
```

### Per-Schedule Configuration

Override per schedule:

```yaml
schedules:
  # Global defaults
  concurrent_executions: false

  # Per-schedule overrides
  daily-report:
    timeout_s: 300                 # 5 minutes for long-running job
    concurrent_executions: true    # Allow multiple instances

  quick-task:
    timeout_s: 10                  # Fast task
```

---

## Idempotent Design

Scheduled jobs **must** be idempotent (safe to run multiple times).

### Why Idempotency Matters

Schedules can trigger multiple times due to:
- Retries on failure
- Overlapping executions
- Clock drift
- Manual invocations

### ❌ Not Idempotent

```go
func processOrders(ctx context.Context, db *Database) error {
    // Problem: Processes ALL orders every time
    orders, _ := db.GetAllOrders(ctx)

    for _, order := range orders {
        // Processes same order multiple times!
        db.UpdateOrder(ctx, order.ID, "processed")
        sendEmail(order)
    }

    return nil
}
```

**Issues:**
- Orders processed repeatedly
- Multiple emails sent
- Database pollution

### ✅ Idempotent

```go
func processOrders(ctx context.Context, db *Database) error {
    // Only process orders not yet processed
    orders, _ := db.GetOrdersByStatus(ctx, "pending")

    for _, order := range orders {
        // Check if already processed
        if order.Status == "pending" {
            db.UpdateOrder(ctx, order.ID, "processed")
            sendEmail(order)
        }
    }

    return nil
}
```

**Benefits:**
- Only unprocessed orders handled
- Safe to retry
- No duplicate work

### Idempotency Patterns

#### Pattern 1: Check State Before Modifying

```go
func dailyTask(ctx context.Context, db *Database) error {
    // Check if already ran today
    lastRun, _ := db.GetLastRun(ctx, "daily-task")
    if lastRun.Day() == time.Now().Day() {
        log.Println("Already ran today, skipping")
        return nil
    }

    // Do work
    performTask()

    // Record execution
    db.SetLastRun(ctx, "daily-task", time.Now())

    return nil
}
```

#### Pattern 2: Use Unique Identifiers

```go
func processRecords(ctx context.Context, db *Database) error {
    records, _ := db.GetUnprocessedRecords(ctx)

    for _, record := range records {
        // Use record ID for idempotency
        if db.IsProcessed(ctx, record.ID) {
            log.Printf("Record %s already processed", record.ID)
            continue
        }

        // Process
        processRecord(record)

        // Mark as processed
        db.MarkProcessed(ctx, record.ID)
    }

    return nil
}
```

#### Pattern 3: Time Window

```go
func generateReport(ctx context.Context, db *Database) error {
    now := time.Now()

    // Only process yesterday's data
    startOfYesterday := time.Date(now.Year(), now.Month(), now.Day()-1, 0, 0, 0, 0, now.Location())
    endOfYesterday := startOfYesterday.Add(24 * time.Hour)

    // Query specific time window
    data, _ := db.GetMetrics(ctx, startOfYesterday, endOfYesterday)

    // Generate report
    report := createReport(data)

    // Save with date in filename (idempotent)
    filename := fmt.Sprintf("report-%s.pdf", startOfYesterday.Format("2006-01-02"))
    saveReport(filename, report)

    return nil
}
```

---

## Local vs Cloud

### Local Mode

```bash
$ transire run

✓ HTTP server on :8080
✓ Scheduler: 1 job (daily-report, next run: tomorrow at 09:00)
→ Ready
```

**How it works:**
- Fixed-rate Go timer
- Non-overlapping execution
- Immediate feedback in logs
- Fast iteration

**Good for:**
- Development
- Testing schedule logic
- Debugging handlers

**Scale factor:**
```yaml
local:
  schedules:
    scale_factor: 0.1  # 10x faster
    # 1 hour → 6 minutes
    # @daily → every 2.4 hours
```

### Cloud Mode

```bash
$ transire deploy

✓ Lambda: orders-api-dev-schedule
✓ EventBridge rule: daily-report (cron(0 9 * * ? *))
✓ EventBridge target: Lambda
```

**How it works:**
- AWS EventBridge rule
- Lambda invoked on schedule
- Serverless execution
- Automatic retries

**Good for:**
- Production reliability
- Distributed systems
- Cost-effective scaling

---

## Testing

### Unit Testing Handlers

```go
func TestGenerateDailyReport(t *testing.T) {
    ctx := context.Background()

    // Mock database
    mockDB := &MockDatabase{
        metrics: []Metric{
            {Orders: 100, Revenue: 10000},
        },
    }

    // Call handler
    err := generateDailyReport(ctx, mockDB)

    // Assert
    if err != nil {
        t.Fatalf("Expected no error, got: %v", err)
    }

    // Verify side effects
    if !mockDB.ReportGenerated {
        t.Error("Expected report to be generated")
    }
}
```

### Integration Testing with Testkit

```go
import "github.com/transire/transire-sdk-go/testkit"

func TestScheduledJob(t *testing.T) {
    tk := testkit.New(t)

    // Setup database
    db := setupTestDB(t)
    defer db.Close()

    transire.Provide(func() *Database { return db })

    // Register schedule
    tk.Schedule("daily-report", "@daily 09:00", generateDailyReport)

    // Trigger manually
    err := tk.TriggerSchedule("daily-report")
    if err != nil {
        t.Fatalf("Schedule trigger failed: %v", err)
    }

    // Verify result
    report, _ := db.GetLatestReport(context.Background())
    if report == nil {
        t.Error("Expected report to be generated")
    }
}
```

### Testing Idempotency

```go
func TestIdempotentExecution(t *testing.T) {
    ctx := context.Background()
    mockDB := &MockDatabase{}

    // Run twice
    generateDailyReport(ctx, mockDB)
    generateDailyReport(ctx, mockDB)

    // Should only execute once
    if mockDB.ExecutionCount != 1 {
        t.Errorf("Expected 1 execution, got %d", mockDB.ExecutionCount)
    }
}
```

---

## Common Patterns

### Pattern: Check Context Cancellation

```go
func longRunningJob(ctx context.Context, db *Database) error {
    items, _ := db.GetAllItems(ctx)

    for i, item := range items {
        // Check if cancelled
        if ctx.Err() != nil {
            log.Printf("Job cancelled after %d items", i)
            return ctx.Err()
        }

        // Process item
        processItem(item)
    }

    return nil
}
```

### Pattern: Retry with Backoff

```go
func dailyTask(ctx context.Context) error {
    maxRetries := 3

    for i := 0; i < maxRetries; i++ {
        if err := attemptTask(ctx); err == nil {
            return nil
        }

        log.Printf("Attempt %d failed, retrying...", i+1)
        time.Sleep(time.Second * time.Duration(i+1))
    }

    return fmt.Errorf("failed after %d retries", maxRetries)
}
```

### Pattern: Logging Start/End

```go
func dailyTask(ctx context.Context, logger *Logger) error {
    start := time.Now()
    logger.Info("Daily task started")

    defer func() {
        logger.Info(fmt.Sprintf("Daily task completed in %v", time.Since(start)))
    }()

    // Do work...
    performTask()

    return nil
}
```

### Pattern: External API Calls

```go
func syncInventory(ctx context.Context, apiClient *APIClient) error {
    // Add timeout for external calls
    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()

    // Fetch from external API
    inventory, err := apiClient.GetInventory(ctx)
    if err != nil {
        log.Printf("Failed to fetch inventory: %v", err)
        return err
    }

    // Update local data
    updateInventory(inventory)

    return nil
}
```

### Pattern: Batch Operations

```go
func cleanupOldRecords(ctx context.Context, db *Database) error {
    cutoff := time.Now().Add(-90 * 24 * time.Hour)

    // Delete in batches
    batchSize := 1000
    deleted := 0

    for {
        // Delete batch
        count, err := db.DeleteOldRecords(ctx, cutoff, batchSize)
        if err != nil {
            return err
        }

        deleted += count

        // No more records
        if count < batchSize {
            break
        }

        // Prevent timeout
        if ctx.Err() != nil {
            log.Printf("Deleted %d records before timeout", deleted)
            return ctx.Err()
        }
    }

    log.Printf("Deleted %d old records", deleted)
    return nil
}
```

---

## Monitoring

### CloudWatch Metrics (AWS)

Key metrics for scheduled jobs:

- **Invocations** - Number of executions
- **Errors** - Failed executions
- **Duration** - Execution time
- **Throttles** - Rate-limited executions

### View Logs

```bash
# Tail schedule logs
$ transire logs --handler schedule

# Filter by schedule key
$ transire logs --handler schedule --filter daily-report

# Recent executions
$ transire logs --handler schedule --since 24h
```

### Custom Metrics

```go
import "github.com/prometheus/client_golang/prometheus"

var (
    jobDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "scheduled_job_duration_seconds",
            Help:    "Scheduled job duration",
            Buckets: prometheus.ExponentialBuckets(0.1, 2, 10),
        },
        []string{"job_key"},
    )

    jobSuccess = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "scheduled_job_success_total",
            Help: "Successful job executions",
        },
        []string{"job_key"},
    )

    jobFailures = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "scheduled_job_failures_total",
            Help: "Failed job executions",
        },
        []string{"job_key"},
    )
)

func init() {
    prometheus.MustRegister(jobDuration)
    prometheus.MustRegister(jobSuccess)
    prometheus.MustRegister(jobFailures)
}

func generateDailyReport(ctx context.Context, db *Database) error {
    start := time.Now()

    defer func() {
        jobDuration.WithLabelValues("daily-report").Observe(
            time.Since(start).Seconds(),
        )
    }()

    if err := doGenerateReport(ctx, db); err != nil {
        jobFailures.WithLabelValues("daily-report").Inc()
        return err
    }

    jobSuccess.WithLabelValues("daily-report").Inc()
    return nil
}
```

---

## Troubleshooting

### Schedule Not Running

**Issue:** Job never executes

**Check:**

1. **Is schedule registered?**
   ```go
   app.Schedule("key", "schedule", handler)
   ```

2. **Is schedule expression valid?**
   - Test at [crontab.guru](https://crontab.guru/)
   - Verify timezone

3. **Local mode:** Check logs for "next run"
   ```
   ✓ Scheduler: 1 job (daily-report, next run: tomorrow at 09:00)
   ```

4. **Cloud mode:** Check EventBridge rule
   ```bash
   aws events describe-rule --name orders-api-dev-daily-report
   ```

### Wrong Timezone

**Issue:** Job runs at wrong time

**Solutions:**

1. **Set service timezone:**
   ```yaml
   timezone: America/New_York
   ```

2. **Use explicit timezone:**
   ```go
   app.Schedule("key", "@daily 09:00 America/New_York", handler)
   ```

3. **Verify in cloud:**
   ```bash
   aws events describe-rule --name app-schedule | jq '.ScheduleExpression'
   ```

### Overlapping Executions

**Issue:** Job starts before previous run finishes

**Solutions:**

1. **Prevent concurrent:**
   ```yaml
   schedules:
     concurrent_executions: false
   ```

2. **Increase timeout:**
   ```yaml
   deploy:
     timeout_s: 300  # 5 minutes
   ```

3. **Add execution lock:**
   ```go
   var mu sync.Mutex

   func job(ctx context.Context) error {
       if !mu.TryLock() {
           log.Println("Previous execution still running")
           return nil
       }
       defer mu.Unlock()

       // Do work...
       return nil
   }
   ```

---

## Schedule Expression Examples

### Common Schedules

```go
// Every minute
"cron(* * * * ? *)"

// Every 5 minutes
"cron(*/5 * * * ? *)"

// Every hour
"@hourly"
"rate(1 hour)"
"cron(0 * * * ? *)"

// Every day at midnight
"@daily 00:00"
"cron(0 0 * * ? *)"

// Every day at 9 AM
"@daily 09:00"
"cron(0 9 * * ? *)"

// Weekdays at 5 PM
"cron(0 17 ? * 1-5 *)"

// First day of month at 8 AM
"cron(0 8 1 * ? *)"

// Last day of month at 11:59 PM
"cron(59 23 L * ? *)"

// Every Monday at 10 AM
"cron(0 10 ? * 1 *)"

// Every week (7 days)
"@weekly"
"rate(7 days)"

// Every 30 minutes
"rate(30 minutes)"
```

---

## See Also

- [Schedule Tutorial](../../learn/tutorials/04-scheduled-jobs/) - Build scheduled jobs
- [Cron Expression Guide](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html) - AWS docs
- [Timezone Database](https://www.iana.org/time-zones) - Valid timezones
- [Testing Guide](../../guides/testing/) - Test scheduled jobs
- [AWS EventBridge](../../plugins/cloud/aws/schedules/) - How schedules work in AWS

