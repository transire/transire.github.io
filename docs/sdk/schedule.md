---
title: "Scheduled Jobs"
category: sdk
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - Go 1.22+
  - Understanding of cron expressions
mcp_use: reference
mcp_operations:
  - add_scheduled_job
  - extract_schedule_patterns
features_covered:
  - Scheduled job registration
  - Cron expressions
  - Rate-based schedules
  - Timezone handling
  - Idempotency
code_blocks: true
last_updated: 2025-10-30
---

# Scheduled Jobs

## Overview

Scheduled jobs enable time-based execution of tasks in Transire. Perfect for:

- **Periodic tasks** - Daily reports, weekly cleanups, hourly syncs
- **Maintenance** - Database backups, cache warming, log rotation
- **Batch processing** - Process accumulated data at specific times
- **Monitoring** - Health checks, metric collection, status updates

**Key features:**
- Simple, expressive schedule syntax
- Timezone support
- Idempotent by design
- No overlapping executions (local mode)
- Automatic error recovery

## Handler Signature

Scheduled jobs have a simple signature:

```go
func(ctx context.Context) error
```

- No input parameters (idempotent by design)
- Return error if job fails (logged, doesn't block next execution)
- Always respect `ctx.Done()` for cancellation

## Registering Scheduled Jobs

Register scheduled jobs using `app.RegisterScheduled`:

```go
package main

import (
    "context"
    "log"
    "github.com/transire/sdk-go"
)

func main() {
    app := transire.New()

    // Daily at 9:00 AM (service timezone)
    err := app.RegisterScheduled("@daily 09:00", sendDailyReport)
    if err != nil {
        log.Fatal("Failed to register schedule:", err)
    }

    // Every hour
    err = app.RegisterScheduled("@hourly", cleanupExpiredSessions)
    if err != nil {
        log.Fatal("Failed to register schedule:", err)
    }

    // Custom cron expression
    err = app.RegisterScheduled("cron(0 */6 * * ? *)", syncData)
    if err != nil {
        log.Fatal("Failed to register schedule:", err)
    }

    app.Run()
}

func sendDailyReport(ctx context.Context) error {
    log.Println("Generating daily report...")

    report, err := generateReport(ctx)
    if err != nil {
        return err
    }

    if err := emailReport(ctx, report); err != nil {
        return err
    }

    log.Println("Daily report sent successfully")
    return nil
}
```

## Schedule Syntax

Transire supports multiple schedule formats:

### Shorthand: Rate-Based

Rate-based schedules fire every N time units (timezone-agnostic):

```go
// Every hour
app.RegisterScheduled("@hourly", handler)

// Every day (every 24 hours)
app.RegisterScheduled("@daily", handler)
```

**Equivalent to:**
- `@hourly` → `rate(1 hour)`
- `@daily` → `rate(1 day)`

### Shorthand: Daily at Specific Time

Fire at a specific wall-clock time daily:

```go
// 9:00 AM in service timezone
app.RegisterScheduled("@daily 09:00", handler)

// 2:30 PM in service timezone
app.RegisterScheduled("@daily 14:30", handler)

// 9:00 AM in specific timezone
app.RegisterScheduled("@daily 09:00 America/New_York", handler)

// Midnight UTC
app.RegisterScheduled("@daily 00:00 UTC", handler)
```

**Format:** `@daily HH:MM [TIMEZONE]`

### Cron Expressions

Full control with cron expressions:

```go
// Every 6 hours
app.RegisterScheduled("cron(0 */6 * * ? *)", handler)

// Weekdays at 10 AM
app.RegisterScheduled("cron(0 10 ? * MON-FRI *)", handler)

// First day of month at noon
app.RegisterScheduled("cron(0 12 1 * ? *)", handler)
```

**Cron format:** `cron(minute hour day month weekday year)`

| Field | Values | Wildcards |
|-------|--------|-----------|
| Minute | 0-59 | `, - * /` |
| Hour | 0-23 | `, - * /` |
| Day | 1-31 | `, - * ? /` |
| Month | 1-12 or JAN-DEC | `, - * /` |
| Weekday | 1-7 or SUN-SAT | `, - * ? /` |
| Year | 1970-2199 | `, - * /` |

**Special characters:**
- `*` - All values
- `?` - No specific value (use in day or weekday)
- `-` - Range (e.g., `MON-FRI`)
- `,` - List (e.g., `MON,WED,FRI`)
- `/` - Increments (e.g., `*/15` = every 15 minutes)

## Timezone Handling

Transire provides flexible timezone control:

### Service-Level Timezone

Set default timezone for all cron-based schedules in `transire.yaml`:

```yaml
service: orders
timezone: America/New_York  # Applied to all cron schedules
```

```go
// Uses service timezone (America/New_York)
app.RegisterScheduled("@daily 09:00", handler)
```

### Per-Schedule Timezone Override

Override timezone for individual schedules:

```go
// 9 AM Eastern
app.RegisterScheduled("@daily 09:00 America/New_York", handler)

// Midnight UTC
app.RegisterScheduled("@daily 00:00 UTC", handler)

// 8 PM Tokyo
app.RegisterScheduled("@daily 20:00 Asia/Tokyo", handler)
```

### Rate-Based (Timezone-Agnostic)

Rate-based schedules ignore timezones:

```go
// Fires every hour, regardless of timezone
app.RegisterScheduled("@hourly", handler)

// Fires every 24 hours (not tied to calendar day)
app.RegisterScheduled("@daily", handler)
```

## Complete Example

Here's a complete example of a scheduled reporting system:

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"
    "github.com/transire/sdk-go"
)

type Report struct {
    Date         time.Time
    TotalOrders  int
    TotalRevenue float64
    NewUsers     int
}

func main() {
    app := transire.New()

    // Daily report at 9 AM
    app.RegisterScheduled("@daily 09:00", sendDailyReport)

    // Weekly summary on Monday at 8 AM
    app.RegisterScheduled("cron(0 8 ? * MON *)", sendWeeklyReport)

    // Hourly data sync
    app.RegisterScheduled("@hourly", syncAnalytics)

    // Cleanup expired data every 6 hours
    app.RegisterScheduled("cron(0 */6 * * ? *)", cleanupExpiredData)

    app.Run()
}

// Daily report at 9 AM
func sendDailyReport(ctx context.Context) error {
    log.Println("Starting daily report generation")

    // Check for cancellation
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
    }

    // Generate report for yesterday
    yesterday := time.Now().AddDate(0, 0, -1)
    report, err := generateDailyReport(ctx, yesterday)
    if err != nil {
        log.Printf("ERROR: Failed to generate report: %v", err)
        return err
    }

    // Send to recipients
    recipients := []string{"team@example.com", "management@example.com"}
    for _, email := range recipients {
        if err := sendReportEmail(ctx, email, report); err != nil {
            log.Printf("ERROR: Failed to send report to %s: %v", email, err)
            return err
        }
    }

    log.Printf("Daily report sent successfully: %d orders, $%.2f revenue",
        report.TotalOrders, report.TotalRevenue)
    return nil
}

// Weekly summary on Monday mornings
func sendWeeklyReport(ctx context.Context) error {
    log.Println("Starting weekly report generation")

    // Get last 7 days of data
    endDate := time.Now()
    startDate := endDate.AddDate(0, 0, -7)

    orders, err := db.GetOrdersInRange(ctx, startDate, endDate)
    if err != nil {
        return fmt.Errorf("failed to fetch orders: %w", err)
    }

    users, err := db.GetNewUsersInRange(ctx, startDate, endDate)
    if err != nil {
        return fmt.Errorf("failed to fetch users: %w", err)
    }

    // Calculate metrics
    var totalRevenue float64
    for _, order := range orders {
        totalRevenue += order.Total
    }

    report := Report{
        Date:         endDate,
        TotalOrders:  len(orders),
        TotalRevenue: totalRevenue,
        NewUsers:     len(users),
    }

    // Send to stakeholders
    if err := sendWeeklySummary(ctx, report); err != nil {
        return err
    }

    log.Println("Weekly report sent successfully")
    return nil
}

// Hourly analytics sync
func syncAnalytics(ctx context.Context) error {
    log.Println("Starting analytics sync")

    // Sync with analytics service
    metrics, err := collectMetrics(ctx)
    if err != nil {
        return fmt.Errorf("failed to collect metrics: %w", err)
    }

    if err := analyticsService.Push(ctx, metrics); err != nil {
        return fmt.Errorf("failed to push metrics: %w", err)
    }

    log.Printf("Analytics synced: %d metrics", len(metrics))
    return nil
}

// Cleanup expired data every 6 hours
func cleanupExpiredData(ctx context.Context) error {
    log.Println("Starting cleanup job")

    cutoff := time.Now().AddDate(0, 0, -30)  // 30 days ago

    // Cleanup expired sessions
    sessionsDeleted, err := db.DeleteExpiredSessions(ctx, cutoff)
    if err != nil {
        return fmt.Errorf("failed to cleanup sessions: %w", err)
    }

    // Cleanup old logs
    logsDeleted, err := db.DeleteOldLogs(ctx, cutoff)
    if err != nil {
        return fmt.Errorf("failed to cleanup logs: %w", err)
    }

    log.Printf("Cleanup complete: %d sessions, %d logs deleted",
        sessionsDeleted, logsDeleted)
    return nil
}

// Helper functions

func generateDailyReport(ctx context.Context, date time.Time) (*Report, error) {
    startOfDay := time.Date(date.Year(), date.Month(), date.Day(), 0, 0, 0, 0, date.Location())
    endOfDay := startOfDay.AddDate(0, 0, 1)

    orders, err := db.GetOrdersInRange(ctx, startOfDay, endOfDay)
    if err != nil {
        return nil, err
    }

    users, err := db.GetNewUsersInRange(ctx, startOfDay, endOfDay)
    if err != nil {
        return nil, err
    }

    var totalRevenue float64
    for _, order := range orders {
        totalRevenue += order.Total
    }

    return &Report{
        Date:         date,
        TotalOrders:  len(orders),
        TotalRevenue: totalRevenue,
        NewUsers:     len(users),
    }, nil
}

func sendReportEmail(ctx context.Context, to string, report *Report) error {
    subject := fmt.Sprintf("Daily Report - %s", report.Date.Format("2006-01-02"))
    body := fmt.Sprintf(`
Daily Report for %s

Orders: %d
Revenue: $%.2f
New Users: %d
    `, report.Date.Format("January 2, 2006"), report.TotalOrders, report.TotalRevenue, report.NewUsers)

    return emailService.Send(ctx, to, subject, body)
}
```

## Idempotency

Scheduled jobs must be idempotent (safe to run multiple times):

```go
func processDaily(ctx context.Context) error {
    today := time.Now().Format("2006-01-02")

    // Check if already processed today
    processed, err := db.IsDateProcessed(ctx, today)
    if err != nil {
        return err
    }

    if processed {
        log.Printf("Date %s already processed, skipping", today)
        return nil
    }

    // Process data
    if err := process(ctx); err != nil {
        return err
    }

    // Mark as processed
    if err := db.MarkDateProcessed(ctx, today); err != nil {
        log.Printf("Warning: Failed to mark date processed: %v", err)
    }

    return nil
}
```

## Context Cancellation

Always respect `ctx.Done()` for graceful shutdown:

```go
func longRunningJob(ctx context.Context) error {
    items, err := db.GetItemsToProcess(ctx)
    if err != nil {
        return err
    }

    for i, item := range items {
        // Check for cancellation periodically
        select {
        case <-ctx.Done():
            log.Printf("Job cancelled after processing %d/%d items", i, len(items))
            return ctx.Err()
        default:
        }

        if err := processItem(ctx, item); err != nil {
            log.Printf("ERROR: Failed to process item %s: %v", item.ID, err)
            // Decide: continue or return error?
        }
    }

    return nil
}
```

## Error Handling

Errors don't block future executions:

```go
func scheduledTask(ctx context.Context) error {
    // If this fails, error is logged and next execution still runs
    if err := doSomething(ctx); err != nil {
        log.Printf("ERROR: Task failed: %v", err)
        return err
    }

    return nil
}
```

**Best practice:** Always log detailed errors for debugging:

```go
func scheduledTask(ctx context.Context) error {
    start := time.Now()
    log.Printf("Starting scheduled task at %s", start.Format(time.RFC3339))

    if err := doSomething(ctx); err != nil {
        duration := time.Since(start)
        log.Printf("ERROR: Task failed after %s: %v", duration, err)
        return err
    }

    duration := time.Since(start)
    log.Printf("Task completed successfully in %s", duration)
    return nil
}
```

## Local vs Cloud

Scheduled job behavior differs between local development and cloud deployment:

### Local Development

When running `transire run`, schedules are managed by an in-process scheduler:

- **Fixed-rate execution** - Fires at configured intervals
- **Non-overlapping** - Next run waits for current execution to finish
- **Immediate feedback** - See execution logs in real-time

```bash
# Start local development server with scheduler
transire run
```

### Cloud Deployment

When deployed, schedules use your cloud provider's native scheduler service:

- **Distributed scheduling** - No single point of failure
- **Concurrent executions** - May fire multiple instances simultaneously
- **Reliable triggers** - Guaranteed execution at scheduled times

**Design consideration:** Always design scheduled jobs to handle concurrent executions safely. Use idempotency checks to prevent duplicate processing.

## Testing

Test scheduled jobs directly:

```go
package main

import (
    "context"
    "testing"
)

func TestSendDailyReport(t *testing.T) {
    ctx := context.Background()

    err := sendDailyReport(ctx)
    if err != nil {
        t.Fatalf("sendDailyReport failed: %v", err)
    }

    // Verify report was sent
    // ... check database, mock calls, etc.
}

func TestCleanupExpiredData(t *testing.T) {
    ctx := context.Background()

    // Setup test data
    setupExpiredData(t)

    err := cleanupExpiredData(ctx)
    if err != nil {
        t.Fatalf("cleanupExpiredData failed: %v", err)
    }

    // Verify cleanup
    count := db.CountExpiredData(ctx)
    if count != 0 {
        t.Errorf("Expected 0 expired items, got %d", count)
    }
}
```

### Integration Testing

Use testkit to trigger schedules:

```go
package main

import (
    "testing"
    "github.com/transire/sdk-go/testkit"
)

func TestScheduledJobIntegration(t *testing.T) {
    app := testkit.App()
    app.RegisterScheduled("@daily 09:00", sendDailyReport)

    server := app.Start(t)
    defer server.Stop()

    // Manually trigger scheduled job
    err := server.TriggerSchedule(t, "@daily 09:00")
    if err != nil {
        t.Fatalf("Failed to trigger schedule: %v", err)
    }

    // Verify results
    // ...
}
```

## Best Practices

### Keep Jobs Short

Respect timeout limits:

```go
// ❌ BAD: May timeout
func badJob(ctx context.Context) error {
    // Processing millions of records
    items, _ := db.GetAllItems(ctx)
    for _, item := range items {
        process(item)  // Could take hours
    }
    return nil
}

// ✅ GOOD: Process in chunks
func goodJob(ctx context.Context) error {
    // Process 1000 items per execution
    items, _ := db.GetPendingItems(ctx, 1000)
    for _, item := range items {
        process(item)
        db.MarkProcessed(ctx, item)
    }
    return nil
}
```

### Monitoring

Log start, progress, and completion:

```go
func scheduledTask(ctx context.Context) error {
    start := time.Now()
    log.Printf("Task started at %s", start.Format(time.RFC3339))

    // Process...

    duration := time.Since(start)
    log.Printf("Task completed in %s", duration)
    return nil
}
```

### Use Metrics

Track job execution metrics:

```go
func scheduledTask(ctx context.Context) error {
    start := time.Now()
    defer func() {
        duration := time.Since(start)
        metrics.RecordScheduledJobDuration("task_name", duration)
    }()

    // Process...
    count, err := doWork(ctx)

    metrics.RecordScheduledJobCount("task_name", count)
    return err
}
```

### Graceful Degradation

Handle partial failures gracefully:

```go
func multiStepJob(ctx context.Context) error {
    // Step 1: Critical
    if err := criticalStep(ctx); err != nil {
        return err  // Fail job
    }

    // Step 2: Best-effort
    if err := optionalStep(ctx); err != nil {
        log.Printf("Warning: Optional step failed: %v", err)
        // Don't fail job
    }

    return nil
}
```

## Common Patterns

### Daily Report at Specific Time

```go
app.RegisterScheduled("@daily 09:00", sendDailyReport)
```

### Hourly Sync

```go
app.RegisterScheduled("@hourly", syncData)
```

### Weekday Business Hours

```go
// Monday-Friday at 8 AM, 12 PM, 5 PM
app.RegisterScheduled("cron(0 8,12,17 ? * MON-FRI *)", businessHoursTask)
```

### First of Month

```go
// First day of month at noon
app.RegisterScheduled("cron(0 12 1 * ? *)", monthlyReport)
```

### Every 15 Minutes

```go
app.RegisterScheduled("cron(*/15 * * * ? *)", frequentCheck)
```

## See Also

- [HTTP Handlers](/docs/sdk/http.md) - Triggering schedules from HTTP
- [Queue Handlers](/docs/sdk/queue.md) - Async message processing
- [Dependency Injection](/docs/sdk/di.md) - Injecting services into scheduled jobs
- [Testing](/docs/sdk/testkit.md) - Testing scheduled jobs
- [Configuration Reference](/docs/reference/config-schema.md) - Schedule configuration options
