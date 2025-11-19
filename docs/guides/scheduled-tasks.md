---
title: "Scheduled Tasks"
description: "Run periodic tasks and cron jobs with schedule handlers"
keywords:
  - scheduled tasks
  - cron
  - periodic tasks
  - eventbridge
  - timers
category: guides
difficulty: intermediate
estimated_time: 15 minutes
prerequisites:
  - "Understanding of cron syntax"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Running periodic tasks"
    - "Scheduling maintenance jobs"
    - "Understanding cron patterns"
  common_questions:
    - "How do I schedule tasks?"
    - "What cron expressions are supported?"
    - "How do I test scheduled tasks?"
---

# Scheduled Tasks Guide

Learn how to implement and deploy scheduled tasks (cron jobs) with Transire.

!!! tip "TL;DR"
    Implement `SchedulerHandler` interface, define cron expression, register with `app.RegisterScheduleHandler()`. Transire creates EventBridge rules automatically. Test locally with `transire run`.

---

## Overview

Scheduled tasks run at specific times or intervals, like cron jobs. Perfect for:

- **Maintenance tasks** – Clean up old data, vacuum databases
- **Reports** – Generate daily/weekly reports
- **Data synchronization** – Sync external APIs
- **Monitoring** – Health checks, alert aggregation
- **Batch processing** – Nightly data processing

Transire uses AWS EventBridge (formerly CloudWatch Events) for scheduling in production, with a local simulator for development.

---

## Quick Start

### 1. Implement SchedulerHandler

```go
// handlers.go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "github.com/transire/transire/pkg/transire"
)

type DailyCleanupHandler struct{}

// Name returns the unique schedule name
func (h *DailyCleanupHandler) Name() string {
    return "daily-cleanup"
}

// Schedule returns Unix cron expression
func (h *DailyCleanupHandler) Schedule() string {
    return "0 2 * * *"  // Daily at 2 AM UTC
}

// Config returns schedule configuration
func (h *DailyCleanupHandler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        Timezone:       "UTC",
        Enabled:        true,
        TimeoutSeconds: 300,  // 5 minutes
        RetryAttempts:  3,
        RetryDelay:     30 * time.Second,
    }
}

// HandleSchedule is called when schedule triggers
func (h *DailyCleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Printf("Starting cleanup at %v", event.ScheduledTime)

    // Your cleanup logic here
    if err := cleanupOldFiles(ctx); err != nil {
        return fmt.Errorf("cleanup failed: %w", err)
    }

    log.Println("Cleanup completed successfully")
    return nil
}

func cleanupOldFiles(ctx context.Context) error {
    // Implementation
    return nil
}
```

Source: Example adapted from [`examples/simple-api/handlers.go:96-135`](https://github.com/transire/transire/blob/main/examples/simple-api/handlers.go)

### 2. Register Handler

```go
// main.go
package main

import (
    "context"

    "github.com/transire/transire/pkg/transire"
)

func main() {
    app := transire.New()

    // Register HTTP handlers
    r := app.Router()
    r.Get("/health", healthHandler)

    // Register schedule handler
    app.RegisterScheduleHandler(&DailyCleanupHandler{})

    // Run app
    if err := app.Run(context.Background()); err != nil {
        panic(err)
    }
}
```

### 3. Test Locally

```bash
# Start app
transire run

# In another terminal, trigger manually
transire dev schedules execute daily-cleanup
```

Output:
```
Starting cleanup at 2024-01-18 14:30:00
Cleanup completed successfully
```

### 4. Deploy

```bash
transire build
transire deploy
```

EventBridge rule is created automatically. Schedule runs at configured time.

---

## Cron Expression Examples

### Common Patterns

| Expression | Description | Runs |
|------------|-------------|------|
| `"*/5 * * * *"` | Every 5 minutes | 288 times/day |
| `"0 * * * *"` | Every hour | 24 times/day |
| `"0 */6 * * *"` | Every 6 hours | 4 times/day |
| `"0 2 * * *"` | Daily at 2 AM | Once/day |
| `"0 9 * * MON-FRI"` | Weekdays at 9 AM | Once/weekday |
| `"0 0 1 * *"` | First of month | Once/month |
| `"0 0 * * SUN"` | Every Sunday midnight | Once/week |

### Syntax Reference

```
 ┌────────── minute (0-59)
 │ ┌──────── hour (0-23)
 │ │ ┌────── day of month (1-31)
 │ │ │ ┌──── month (1-12 or JAN-DEC)
 │ │ │ │ ┌── day of week (0-6 or SUN-SAT)
 * * * * *
```

**Special characters:**
- `*` – Any value
- `,` – List (`1,15` = 1st and 15th)
- `-` – Range (`MON-FRI`)
- `/` – Step (`*/15` = every 15 units)

Test expressions at [crontab.guru](https://crontab.guru/)

---

## Complete Example: Database Maintenance

```go
package main

import (
    "context"
    "database/sql"
    "fmt"
    "log"
    "time"

    _ "github.com/lib/pq"
    "github.com/transire/transire/pkg/transire"
)

type DatabaseMaintenanceHandler struct {
    db *sql.DB
}

func NewDatabaseMaintenanceHandler(db *sql.DB) *DatabaseMaintenanceHandler {
    return &DatabaseMaintenanceHandler{db: db}
}

func (h *DatabaseMaintenanceHandler) Name() string {
    return "database-maintenance"
}

func (h *DatabaseMaintenanceHandler) Schedule() string {
    return "0 3 * * SUN"  // Every Sunday at 3 AM
}

func (h *DatabaseMaintenanceHandler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        Timezone:       "UTC",
        Enabled:        true,
        TimeoutSeconds: 900,  // 15 minutes for DB operations
        RetryAttempts:  2,    // Limited retries for DB ops
        RetryDelay:     60 * time.Second,
    }
}

func (h *DatabaseMaintenanceHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Printf("Starting database maintenance at %v", event.ScheduledTime)

    start := time.Now()
    defer func() {
        log.Printf("Database maintenance completed in %v", time.Since(start))
    }()

    // Run VACUUM on all tables
    if err := h.vacuumTables(ctx); err != nil {
        return fmt.Errorf("vacuum failed: %w", err)
    }

    // Update statistics
    if err := h.analyzeData(ctx); err != nil {
        return fmt.Errorf("analyze failed: %w", err)
    }

    // Clean up old data
    if err := h.archiveOldRecords(ctx); err != nil {
        return fmt.Errorf("archive failed: %w", err)
    }

    return nil
}

func (h *DatabaseMaintenanceHandler) vacuumTables(ctx context.Context) error {
    log.Println("Running VACUUM...")

    tables := []string{"users", "orders", "logs"}
    for _, table := range tables {
        _, err := h.db.ExecContext(ctx, fmt.Sprintf("VACUUM ANALYZE %s", table))
        if err != nil {
            return fmt.Errorf("vacuum %s: %w", table, err)
        }
        log.Printf("  ✓ Vacuumed %s", table)
    }

    return nil
}

func (h *DatabaseMaintenanceHandler) analyzeData(ctx context.Context) error {
    log.Println("Analyzing statistics...")

    _, err := h.db.ExecContext(ctx, "ANALYZE")
    if err != nil {
        return err
    }

    log.Println("  ✓ Statistics updated")
    return nil
}

func (h *DatabaseMaintenanceHandler) archiveOldRecords(ctx context.Context) error {
    log.Println("Archiving old records...")

    // Archive logs older than 90 days
    cutoff := time.Now().AddDate(0, 0, -90)
    result, err := h.db.ExecContext(ctx,
        "DELETE FROM logs WHERE created_at < $1",
        cutoff,
    )
    if err != nil {
        return err
    }

    rows, _ := result.RowsAffected()
    log.Printf("  ✓ Archived %d old logs", rows)

    return nil
}
```

---

## Best Practices

### 1. Make Handlers Idempotent

Schedule handlers may run multiple times (retries, manual triggers). Design them to be safe when run multiple times.

**✅ Good (Idempotent):**

```go
func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    // Deletes files older than 7 days - safe to run multiple times
    deleted := deleteFilesOlderThan(ctx, 7*24*time.Hour)
    log.Printf("Deleted %d files", deleted)
    return nil
}
```

**❌ Bad (Not Idempotent):**

```go
func (h *ReportHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    // Sends email every time - duplicates on retry!
    sendEmail("Daily Report")  // ❌ Will send duplicate emails
    return nil
}
```

**✅ Better (Idempotent with Check):**

```go
func (h *ReportHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    today := time.Now().Format("2006-01-02")

    // Check if already sent today
    if reportSentToday(ctx, today) {
        log.Println("Report already sent today")
        return nil
    }

    // Send and record
    if err := sendEmail("Daily Report"); err != nil {
        return err
    }

    recordReportSent(ctx, today)
    return nil
}
```

### 2. Use Structured Logging

Include schedule metadata:

```go
func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Printf("[%s] Started at %v (scheduled for %v)",
        event.Name,
        time.Now(),
        event.ScheduledTime,
    )

    // ... task logic ...

    log.Printf("[%s] Completed", event.Name)
    return nil
}
```

### 3. Monitor Execution Time

Track duration for performance monitoring:

```go
func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    start := time.Now()
    defer func() {
        duration := time.Since(start)
        log.Printf("Cleanup took %v", duration)

        // Alert if slow
        if duration > 5*time.Minute {
            alertSlowTask("cleanup", duration)
        }
    }()

    // ... task logic ...
    return nil
}
```

### 4. Handle Partial Failures

Continue processing even if one step fails:

```go
func (h *MaintenanceHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    var errs []error

    // Step 1: Cleanup temp files (continue if fails)
    if err := cleanupTempFiles(ctx); err != nil {
        errs = append(errs, fmt.Errorf("temp files: %w", err))
        log.Printf("ERROR: %v", err)
    }

    // Step 2: Cleanup sessions (continue if fails)
    if err := cleanupSessions(ctx); err != nil {
        errs = append(errs, fmt.Errorf("sessions: %w", err))
        log.Printf("ERROR: %v", err)
    }

    // Step 3: Cleanup logs (continue if fails)
    if err := cleanupLogs(ctx); err != nil {
        errs = append(errs, fmt.Errorf("logs: %w", err))
        log.Printf("ERROR: %v", err)
    }

    // Return combined errors if any
    if len(errs) > 0 {
        return fmt.Errorf("maintenance completed with %d errors: %v", len(errs), errs)
    }

    return nil
}
```

### 5. Use Context for Timeouts

Respect Lambda timeout by using context:

```go
func (h *DataSyncHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    // Process items with context timeout
    for _, item := range items {
        select {
        case <-ctx.Done():
            return ctx.Err()  // Timeout or cancellation
        default:
            if err := processItem(ctx, item); err != nil {
                log.Printf("Failed to process item: %v", err)
            }
        }
    }

    return nil
}
```

---

## Testing

### Unit Testing

```go
// handlers_test.go
package main

import (
    "context"
    "testing"
    "time"

    "github.com/transire/transire/pkg/transire"
)

func TestCleanupHandler(t *testing.T) {
    handler := &CleanupHandler{}

    event := transire.ScheduleEvent{
        Name:          "daily-cleanup",
        ScheduledTime: time.Now(),
    }

    err := handler.HandleSchedule(context.Background(), event)
    if err != nil {
        t.Fatalf("HandleSchedule failed: %v", err)
    }
}

func TestCleanupHandlerSchedule(t *testing.T) {
    handler := &CleanupHandler{}

    // Verify cron expression
    expected := "0 2 * * *"
    if handler.Schedule() != expected {
        t.Errorf("Expected schedule %q, got %q", expected, handler.Schedule())
    }
}
```

### Local Testing

Test manually with the CLI:

```bash
# Start app
transire run

# Trigger schedule
transire dev schedules execute daily-cleanup
```

### Integration Testing

Test with actual schedule timing (use shorter intervals):

```go
// For testing only
func (h *TestHandler) Schedule() string {
    if os.Getenv("ENV") == "test" {
        return "*/1 * * * *"  // Every minute for testing
    }
    return "0 2 * * *"  // Daily in production
}
```

---

## Configuration

### Per-Schedule Overrides

Override settings in `transire.yaml`:

```yaml
schedules:
  daily-cleanup:
    timezone: "America/New_York"  # Override timezone
    enabled: true

  weekly-report:
    timezone: "UTC"
    enabled: false  # Temporarily disabled

  hourly-sync:
    timezone: "Europe/London"
    enabled: true
```

See: [Schedule Configuration](../configuration/schedules.md)

---

## Monitoring

### CloudWatch Logs

View execution logs:

```bash
aws logs tail /aws/lambda/my-api-dev-MainFunction-ABC123 --follow
```

Filter by schedule name:

```bash
aws logs tail /aws/lambda/my-api-dev-MainFunction-ABC123 \
  --follow \
  --filter-pattern "daily-cleanup"
```

### CloudWatch Metrics

Monitor schedule health:

- **Invocations** – Number of times triggered
- **Errors** – Failed executions
- **Duration** – Execution time
- **Throttles** – Rate-limited invocations

### CloudWatch Alarms

Alert on failures:

```yaml
# In CDK extension or CloudFormation
ScheduleErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 1
    ComparisonOperator: GreaterThanThreshold
    # Alert if any errors in 5 minutes
```

---

## Common Patterns

### Pattern 1: Data Cleanup

```go
type CleanupHandler struct{}

func (h *CleanupHandler) Schedule() string {
    return "0 2 * * *"  // Daily at 2 AM
}

func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    cutoff := time.Now().AddDate(0, 0, -30)  // 30 days ago

    deleted, err := db.DeleteOldRecords(ctx, cutoff)
    if err != nil {
        return err
    }

    log.Printf("Deleted %d old records", deleted)
    return nil
}
```

### Pattern 2: Report Generation

```go
type ReportHandler struct{}

func (h *ReportHandler) Schedule() string {
    return "0 9 * * MON"  // Every Monday at 9 AM
}

func (h *ReportHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    // Generate report for last week
    report, err := generateWeeklyReport(ctx)
    if err != nil {
        return err
    }

    // Send to stakeholders
    return emailReport(report, []string{"team@example.com"})
}
```

### Pattern 3: External API Sync

```go
type SyncHandler struct{}

func (h *SyncHandler) Schedule() string {
    return "*/15 * * * *"  // Every 15 minutes
}

func (h *SyncHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    // Fetch latest data from external API
    data, err := fetchExternalData(ctx)
    if err != nil {
        return err
    }

    // Update local database
    return updateLocalData(ctx, data)
}
```

---

## Troubleshooting

### Schedule not triggering

See: [Schedule Configuration - Troubleshooting](../configuration/schedules.md#troubleshooting)

### Handler timing out

Increase timeout:
```yaml
lambda:
  timeout_seconds: 900  # 15 minutes max
```

### Memory issues

Increase memory:
```yaml
lambda:
  memory_mb: 512  # More memory = more CPU
```

---

## Next Steps

- [Schedule Handlers](../core-concepts/schedule-handlers.md) – Core concepts
- [Schedule Configuration](../configuration/schedules.md) – Configuration reference
- [Queue Processing](queue-processing.md) – Compare with queue handlers

---

## See Also

- [Local Development](local-development.md) – Test schedules locally
- [Testing Guide](testing.md) – Unit test schedule handlers
- [EventBridge Documentation](https://docs.aws.amazon.com/eventbridge/)
