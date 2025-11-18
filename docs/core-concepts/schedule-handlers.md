---
title: "Schedule Handlers"
description: "Run scheduled tasks and cron jobs with Transire's SchedulerHandler interface"
keywords:
  - schedule handlers
  - cron jobs
  - scheduled tasks
  - periodic tasks
  - SchedulerHandler interface
  - eventbridge
  - timers
category: core-concepts
difficulty: intermediate
estimated_time: 10 minutes
prerequisites:
  - "Understanding of cron syntax"
  - "Basic scheduling concepts"
related_docs:
  - path: "/guides/scheduled-tasks/"
    relationship: "deep_dive"
  - path: "/configuration/schedules/"
    relationship: "related"
  - path: "/examples/simple-api/"
    relationship: "related"
mcp_metadata:
  primary_use_cases:
    - "Running periodic tasks"
    - "Scheduling cron jobs"
    - "Understanding schedule patterns"
  common_questions:
    - "How do I run scheduled tasks?"
    - "How do I use cron syntax?"
    - "How do I test schedules locally?"
    - "How do schedules work on AWS?"
---

# Schedule Handlers

Learn how to run scheduled tasks (cron jobs) with Transire's `SchedulerHandler` interface.

!!! tip "TL;DR"
    Implement `SchedulerHandler` interface to run tasks on a schedule. Locally, trigger via REST endpoint. On AWS, runs via EventBridge with cron expressions.

---

## Overview

Schedule handlers enable time-based task execution:

- **Development**: Trigger manually via REST endpoint (instant testing)
- **Production**: Runs automatically via AWS EventBridge (cron expressions)
- **Use cases**: Daily cleanup, hourly reports, weekly backups, periodic data sync

Source: [`pkg/transire/interfaces.go:45-49`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go)

---

## The `SchedulerHandler` Interface

```go
type SchedulerHandler interface {
    Name() string                  // Unique identifier for this schedule
    Schedule() string              // Cron expression
    Config() ScheduleConfig        // Schedule configuration
    HandleSchedule(ctx context.Context, event ScheduleEvent) error
}

type ScheduleEvent struct {
    ScheduledTime time.Time
    Name          string
    Payload       []byte
    EventID       string
}

type ScheduleConfig struct {
    Timezone       string        // Timezone for cron expression
    Enabled        bool          // Whether schedule is enabled
    TimeoutSeconds int           // Execution timeout
    RetryAttempts  int           // Number of retry attempts on failure
    RetryDelay     time.Duration // Delay between retries
}
```

---

## Basic Example

### Daily Cleanup Task

```go
package main

import (
    "context"
    "log"
    "time"

    "github.com/transire/transire/pkg/transire"
)

type DailyCleanupHandler struct{}

func (h *DailyCleanupHandler) Name() string {
    return "daily-cleanup"
}

func (h *DailyCleanupHandler) Schedule() string {
    return "cron(0 2 * * ? *)" // 2 AM UTC daily
}

func (h *DailyCleanupHandler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        Timezone:       "UTC",
        Enabled:        true,
        TimeoutSeconds: 300,
        RetryAttempts:  3,
        RetryDelay:     5 * time.Second,
    }
}

func (h *DailyCleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Printf("Running daily cleanup at %s", event.ScheduledTime)

    // Delete old records
    if err := cleanupOldRecords(ctx); err != nil {
        return err
    }

    // Archive completed jobs
    if err := archiveCompletedJobs(ctx); err != nil {
        return err
    }

    log.Println("Daily cleanup completed successfully")
    return nil
}

// Register handler
func main() {
    app := transire.New()
    app.RegisterScheduleHandler(&DailyCleanupHandler{})
    app.Run(context.Background())
}
```

---

## Cron Expression Syntax

Transire uses AWS EventBridge cron expression format:

```
cron(Minutes Hours Day-of-month Month Day-of-week Year)
```

### Fields

| Field         | Values           | Wildcards |
|---------------|------------------|-----------|
| Minutes       | 0-59             | , - * /   |
| Hours         | 0-23             | , - * /   |
| Day-of-month  | 1-31             | , - * ? / L W |
| Month         | 1-12 or JAN-DEC  | , - * /   |
| Day-of-week   | 1-7 or SUN-SAT   | , - * ? L # |
| Year          | 1970-2199        | , - * /   |

**Note:** Use `?` for either day-of-month or day-of-week (not both).

---

### Common Examples

```go
// Every day at 2 AM UTC
"cron(0 2 * * ? *)"

// Every hour at minute 0
"cron(0 * * * ? *)"

// Every 15 minutes
"cron(0/15 * * * ? *)"

// Every Monday at 9 AM UTC
"cron(0 9 ? * MON *)"

// First day of every month at midnight
"cron(0 0 1 * ? *)"

// Weekdays at 6 PM UTC
"cron(0 18 ? * MON-FRI *)"

// Every 30 minutes between 9 AM and 5 PM on weekdays
"cron(0/30 9-17 ? * MON-FRI *)"
```

See: [AWS EventBridge Schedule Expressions](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schedule-expressions.html)

---

## Registration

Register schedule handlers in `main()`:

```go
func main() {
    app := transire.New()

    // Register schedule handlers
    app.RegisterScheduleHandler(&DailyCleanupHandler{})
    app.RegisterScheduleHandler(&HourlyReportHandler{})
    app.RegisterScheduleHandler(&WeeklyBackupHandler{})

    app.Run(context.Background())
}
```

Source: [`pkg/transire/app.go:60-67`](https://github.com/transire/transire/blob/main/pkg/transire/app.go)

---

## Local Testing

### Trigger Manually via CLI

When running locally with `transire run`, trigger schedules via the CLI:

```bash
transire dev schedules execute daily-cleanup
```

**Response:**
```json
{
  "success": true,
  "message": "Schedule triggered successfully"
}
```

This calls `HandleSchedule()` immediately without waiting for the cron expression.

Source: [`pkg/transire/local_runtime.go:142-167`](https://github.com/transire/transire/blob/main/pkg/transire/local_runtime.go)

---

### Test in Unit Tests

```go
func TestDailyCleanupHandler(t *testing.T) {
    handler := &DailyCleanupHandler{}

    event := transire.ScheduleEvent{
        ScheduledTime: time.Now(),
        Name:          "daily-cleanup",
    }

    err := handler.HandleSchedule(context.Background(), event)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
}
```

---

## Error Handling

### Return Errors for Retries

If `HandleSchedule()` returns an error, EventBridge will retry based on the configured retry policy:

```go
func (h *DailyCleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    if err := performCleanup(ctx); err != nil {
        // Return error to trigger retry
        return fmt.Errorf("cleanup failed: %w", err)
    }
    return nil
}
```

**Default retry behavior:**
- **Retry count**: 2 retries (total 3 attempts)
- **Retry delay**: Exponential backoff

---

### Partial Failures

Log partial failures but return success:

```go
func (h *DailyCleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    errors := []error{}

    // Task 1
    if err := cleanupOldRecords(ctx); err != nil {
        log.Printf("Failed to cleanup records: %v", err)
        errors = append(errors, err)
    }

    // Task 2
    if err := archiveCompletedJobs(ctx); err != nil {
        log.Printf("Failed to archive jobs: %v", err)
        errors = append(errors, err)
    }

    // Return nil to avoid retry, but log errors
    if len(errors) > 0 {
        log.Printf("Completed with %d errors", len(errors))
    }

    return nil
}
```

---

## Context and Timeouts

### Use Context for Cancellation

```go
func (h *DailyCleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    // Use context for long-running operations
    select {
    case <-ctx.Done():
        return ctx.Err() // Timeout or cancellation
    default:
        // Continue processing
    }

    // Pass context to database calls
    if err := db.DeleteOldRecordsWithContext(ctx); err != nil {
        return err
    }

    return nil
}
```

---

### Set Lambda Timeout

Configure Lambda timeout in `transire.yaml`:

```yaml
lambda:
  timeout_seconds: 300  # 5 minutes for long-running tasks
```

**Important:** Schedule tasks must complete within Lambda timeout (max 900 seconds / 15 minutes).

---

## Advanced Examples

### Hourly Report Generation

```go
type HourlyReportHandler struct {
    emailService *EmailService
}

func (h *HourlyReportHandler) ScheduleName() string {
    return "hourly-report"
}

func (h *HourlyReportHandler) Schedule() string {
    return "cron(0 * * * ? *)" // Every hour
}

func (h *HourlyReportHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Printf("Generating hourly report for %s", event.ScheduledTime)

    // Generate report data
    report, err := generateHourlyReport(ctx, event.ScheduledTime)
    if err != nil {
        return fmt.Errorf("failed to generate report: %w", err)
    }

    // Send report via email
    if err := h.emailService.SendReport(ctx, report); err != nil {
        return fmt.Errorf("failed to send report: %w", err)
    }

    return nil
}
```

---

### Weekly Backup

```go
type WeeklyBackupHandler struct {
    s3Client *s3.Client
}

func (h *WeeklyBackupHandler) ScheduleName() string {
    return "weekly-backup"
}

func (h *WeeklyBackupHandler) Schedule() string {
    return "cron(0 0 ? * SUN *)" // Sunday midnight UTC
}

func (h *WeeklyBackupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Println("Starting weekly backup...")

    // Export database
    backupFile, err := exportDatabase(ctx)
    if err != nil {
        return fmt.Errorf("database export failed: %w", err)
    }

    // Upload to S3
    if err := h.uploadToS3(ctx, backupFile); err != nil {
        return fmt.Errorf("S3 upload failed: %w", err)
    }

    // Cleanup old backups
    if err := h.cleanupOldBackups(ctx); err != nil {
        log.Printf("Warning: cleanup failed: %v", err)
        // Don't return error - backup succeeded
    }

    log.Println("Weekly backup completed successfully")
    return nil
}
```

---

### Data Synchronization

```go
type DataSyncHandler struct {
    source      *SourceAPI
    destination *DestinationDB
}

func (h *DataSyncHandler) ScheduleName() string {
    return "data-sync"
}

func (h *DataSyncHandler) Schedule() string {
    return "cron(0/30 * * * ? *)" // Every 30 minutes
}

func (h *DataSyncHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    // Get last sync timestamp
    lastSync, err := h.destination.GetLastSyncTime(ctx)
    if err != nil {
        return err
    }

    // Fetch new data from source
    newData, err := h.source.FetchSince(ctx, lastSync)
    if err != nil {
        return fmt.Errorf("failed to fetch data: %w", err)
    }

    if len(newData) == 0 {
        log.Println("No new data to sync")
        return nil
    }

    // Sync to destination
    if err := h.destination.BulkInsert(ctx, newData); err != nil {
        return fmt.Errorf("failed to insert data: %w", err)
    }

    log.Printf("Synced %d records", len(newData))
    return nil
}
```

---

## Configuration

### Per-Schedule Configuration

Configure individual schedules in `transire.yaml`:

```yaml
schedules:
  daily-cleanup:
    timezone: "UTC"
    enabled: true

  hourly-report:
    timezone: "America/New_York"
    enabled: true

  weekly-backup:
    timezone: "UTC"
    enabled: false  # Temporarily disabled
```

Source: [`pkg/transire/config.go:87-93`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

---

### Disable Schedule Temporarily

Set `enabled: false` to disable without removing code:

```yaml
schedules:
  daily-cleanup:
    enabled: false
```

The handler remains in code but won't be deployed or triggered.

---

## Deployment

### Generated EventBridge Rule

`transire build` generates CloudFormation for EventBridge:

```typescript
// Generated CDK code
const dailyCleanupRule = new events.Rule(this, 'DailyCleanupRule', {
  schedule: events.Schedule.expression('cron(0 2 * * ? *)'),
  targets: [new targets.LambdaFunction(mainFunction)],
});
```

Source: [`internal/providers/aws/cdk_generator.go:142-158`](https://github.com/transire/transire/blob/main/internal/providers/aws/cdk_generator.go)

---

### Monitoring Executions

**View Lambda logs:**
```bash
aws logs tail /aws/lambda/my-api-stack-MainFunction-ABC123 --follow
```

**View EventBridge rule status:**
```bash
aws events describe-rule --name my-api-stack-DailyCleanupRule
```

**View failed executions:**
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=my-api-stack-MainFunction-ABC123 \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

---

## Best Practices

### 1. Use Idempotency

Schedules may execute multiple times. Make operations idempotent:

```go
func (h *DailyCleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    // Use scheduled time, not current time
    cutoffDate := event.ScheduledTime.AddDate(0, 0, -30)

    // Delete records older than cutoff (idempotent - can run multiple times)
    deleted, err := db.DeleteRecordsOlderThan(ctx, cutoffDate)
    if err != nil {
        return err
    }

    log.Printf("Deleted %d old records", deleted)
    return nil
}
```

---

### 2. Log Execution Start and End

```go
func (h *DailyCleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Printf("Starting daily cleanup for %s", event.ScheduledTime)
    start := time.Now()

    // Perform cleanup...
    err := performCleanup(ctx)

    duration := time.Since(start)
    if err != nil {
        log.Printf("Cleanup failed after %s: %v", duration, err)
        return err
    }

    log.Printf("Cleanup completed successfully in %s", duration)
    return nil
}
```

---

### 3. Set Appropriate Timeouts

Schedule handlers can run longer than HTTP handlers:

```yaml
lambda:
  timeout_seconds: 300  # 5 minutes for background tasks
```

**Maximum Lambda timeout:** 900 seconds (15 minutes)

---

### 4. Handle Timezone Carefully

EventBridge cron expressions use UTC by default. Be explicit:

```go
// Good: Comment clarifies timezone
func (h *DailyCleanupHandler) Schedule() string {
    return "cron(0 2 * * ? *)" // 2 AM UTC
}
```

---

### 5. Monitor Failures

Set up CloudWatch alarms for schedule failures:

```yaml
# In transire.yaml or CDK extensions
alarms:
  schedule_failures:
    metric: Errors
    threshold: 1
    evaluation_periods: 1
```

---

## Troubleshooting

### Schedule Not Triggering Locally

**Problem:** `transire dev schedules execute {name}` returns "schedule not found"

**Solutions:**
1. Verify handler is registered:
   ```go
   app.RegisterScheduleHandler(&DailyCleanupHandler{})
   ```

2. Check `ScheduleName()` matches URL:
   ```go
   func (h *DailyCleanupHandler) ScheduleName() string {
       return "daily-cleanup" // Must match /schedules/daily-cleanup
   }
   ```

3. Restart `transire run` to re-discover handlers

---

### Schedule Not Deploying to AWS

**Problem:** EventBridge rule not created

**Solutions:**
1. Verify schedule is enabled:
   ```yaml
   schedules:
     daily-cleanup:
       enabled: true
   ```

2. Check cron expression is valid

3. Run `transire build` and check generated CDK code in `infrastructure/`

---

### Lambda Timeout

**Problem:** Schedule execution times out

**Solutions:**
1. Increase Lambda timeout:
   ```yaml
   lambda:
     timeout_seconds: 600  # 10 minutes
   ```

2. Optimize handler code to complete faster

3. Break long tasks into smaller chunks processed by queues

---

## Next Steps

- [Queue Handlers](queue-handlers.md) – Process background tasks asynchronously
- [HTTP Handlers](http-handlers.md) – Build REST APIs
- [Local Development](../guides/local-development.md) – Test schedules locally
- [Deploying to AWS](../guides/deploying-to-aws.md) – Deploy schedules to production

---

## See Also

- [AWS EventBridge Schedule Expressions](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schedule-expressions.html)
- [Cron Expression Examples](https://crontab.guru/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
