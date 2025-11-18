---
title: "Schedule Configuration"
description: "Configure scheduled task settings and cron expressions"
keywords:
  - schedule configuration
  - cron
  - eventbridge
  - timezone
  - enabled
category: configuration
difficulty: intermediate
estimated_time: 10 minutes
prerequisites:
  - "Understanding of cron syntax"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Configuring scheduled tasks"
    - "Setting timezones"
    - "Enabling/disabling schedules"
  common_questions:
    - "How do I configure schedules?"
    - "How do I set timezone?"
    - "How do I disable a schedule?"
---

# Schedule Configuration

Configure AWS EventBridge scheduled tasks for your Transire schedule handlers.

!!! tip "TL;DR"
    Schedule configuration comes from two sources: 1) `ScheduleConfig` struct in your `SchedulerHandler` implementation, 2) per-schedule overrides in `transire.yaml`. Use Unix cron syntax: `"0 2 * * *"` for daily at 2 AM UTC.

---

## Overview

Transire automatically creates EventBridge rules for each registered `SchedulerHandler`. Schedule behavior is configured in two places:

1. **Default configuration:** In your `SchedulerHandler.Config()` method (code)
2. **Per-schedule overrides:** In `transire.yaml` under `schedules:` key (config file)

Values in `transire.yaml` override values from code.

---

## ScheduleConfig Struct (Code)

Define default schedule configuration in your handler:

```go
func (h *CleanupHandler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        Timezone:       "UTC",
        Enabled:        true,
        TimeoutSeconds: 300,  // 5 minutes
        RetryAttempts:  3,
        RetryDelay:     30 * time.Second,
    }
}
```

Source: [`pkg/transire/interfaces.go`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go), example from [`examples/simple-api/handlers.go:103-111`](https://github.com/transire/transire/blob/main/examples/simple-api/handlers.go)

---

## Configuration Fields

### Timezone

```go
Timezone: "UTC"
```

**Type:** `string`
**Default:** `"UTC"`
**Allowed values:** Any IANA timezone (e.g., `"America/New_York"`, `"Europe/London"`, `"Asia/Tokyo"`)

**What it does:**
Determines which timezone the cron expression is evaluated in.

**Examples:**

| Timezone | Cron | Description |
|----------|------|-------------|
| `"UTC"` | `"0 2 * * *"` | 2 AM UTC every day |
| `"America/New_York"` | `"0 9 * * MON-FRI"` | 9 AM ET, weekdays only |
| `"Europe/London"` | `"30 6 * * *"` | 6:30 AM UK time |
| `"Asia/Tokyo"` | `"0 0 * * *"` | Midnight JST |

**Important:**
- UTC is recommended for consistency
- Timezones with DST (daylight saving time) will shift schedule times twice a year
- EventBridge handles DST transitions automatically

---

### Enabled

```go
Enabled: true
```

**Type:** `bool`
**Default:** `true`

**What it does:**
Controls whether the schedule is active.

**Use cases:**
- **Temporarily disable** a schedule without removing code
- **Environment-specific** schedules (run in prod but not dev)
- **Feature flags** for new scheduled tasks

**Example:**

```yaml
schedules:
  daily-cleanup:
    enabled: true   # Runs in production

  weekly-report:
    enabled: false  # Disabled temporarily
```

---

### Timeout Seconds

```go
TimeoutSeconds: 300  // 5 minutes
```

**Type:** `int`
**Default:** `300` (5 minutes)
**Range:** `1` to `900` (15 minutes)
**Unit:** Seconds

**What it does:**
Maximum execution time for the scheduled task. This should match or be less than the Lambda function timeout.

**Recommendations:**

| Task Type | Timeout | Example |
|-----------|---------|---------|
| Quick cleanup | 60s | Delete old logs |
| Database maintenance | 300s | Vacuum, analyze |
| Report generation | 600s | Generate daily reports |
| Data exports | 900s | Export to S3 |

**Important:**
- Set Lambda timeout ≥ schedule timeout
- EventBridge doesn't enforce timeout (Lambda does)
- Long-running tasks should checkpoint progress

---

### Retry Attempts

```go
RetryAttempts: 3
```

**Type:** `int`
**Default:** `3`
**Range:** `0` to `185` (EventBridge max)

**What it does:**
Number of times to retry a failed scheduled task.

**Recommendations:**

| Failure Type | Retry Attempts | Reason |
|--------------|----------------|--------|
| Transient (network) | 3-5 | Usually recovers quickly |
| Idempotent operations | 5-10 | Safe to retry multiple times |
| Non-idempotent | 0-1 | Risk of duplicate side effects |

**Example:** Idempotent cleanup task

```go
func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    // Idempotent: Can run multiple times safely
    filesDeleted, err := deleteOldFiles(ctx)
    if err != nil {
        return fmt.Errorf("cleanup failed: %w", err)  // Will retry
    }

    log.Printf("Deleted %d old files", filesDeleted)
    return nil  // Success, no retry needed
}
```

---

### Retry Delay

```go
RetryDelay: 30 * time.Second
```

**Type:** `time.Duration`
**Default:** `30 * time.Second`
**Range:** `0` to `24 hours`

**What it does:**
Delay between retry attempts.

**Recommendations:**

| Retry Strategy | Delay | Use Case |
|----------------|-------|----------|
| Fast retry | 10-30s | Quick recovery expected |
| Standard retry | 60-300s | Most scenarios |
| Backoff retry | Increasing | Rate-limited APIs |

**Exponential backoff (manual):**

```go
func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    var err error
    delay := 10 * time.Second

    for attempt := 0; attempt < 3; attempt++ {
        err = performCleanup(ctx)
        if err == nil {
            return nil  // Success
        }

        log.Printf("Attempt %d failed: %v. Retrying in %v", attempt+1, err, delay)
        time.Sleep(delay)
        delay *= 2  // Exponential backoff: 10s, 20s, 40s
    }

    return fmt.Errorf("cleanup failed after 3 attempts: %w", err)
}
```

---

## Cron Expression Syntax

### Unix Cron Format

Transire uses standard Unix cron syntax (5 fields):

```
 ┌───────────── minute (0-59)
 │ ┌───────────── hour (0-23)
 │ │ ┌───────────── day of month (1-31)
 │ │ │ ┌───────────── month (1-12 or JAN-DEC)
 │ │ │ │ ┌───────────── day of week (0-6 or SUN-SAT)
 │ │ │ │ │
 * * * * *
```

**Examples:**

| Cron Expression | Description |
|-----------------|-------------|
| `"0 2 * * *"` | Daily at 2:00 AM |
| `"*/15 * * * *"` | Every 15 minutes |
| `"0 */6 * * *"` | Every 6 hours |
| `"0 9 * * MON-FRI"` | Weekdays at 9:00 AM |
| `"30 14 1 * *"` | First day of month at 2:30 PM |
| `"0 0 * * SUN"` | Every Sunday at midnight |

**Special characters:**

- `*` – Any value
- `,` – List of values (`1,15` = 1st and 15th)
- `-` – Range (`MON-FRI`)
- `/` – Step values (`*/15` = every 15 units)

### EventBridge Cron Format

**Important:** Transire converts Unix cron to EventBridge cron format automatically.

EventBridge uses 6 fields (adds year):
```
minute hour day month day-of-week year
```

Example conversion:
- **Your code:** `"0 2 * * *"`
- **EventBridge:** `cron(0 2 * * ? *)`

The conversion is handled by Transire CDK generator.

Source: [`internal/providers/aws/cdk_generator.go`](https://github.com/transire/transire/blob/main/internal/providers/aws/cdk_generator.go) `convertCronToEventBridge()`

---

## Per-Schedule Overrides (YAML)

Override schedule settings in `transire.yaml` without changing code:

```yaml
schedules:
  daily-cleanup:
    timezone: "America/New_York"  # Override: Was "UTC" in code
    enabled: true

  weekly-report:
    timezone: "UTC"
    enabled: false  # Temporarily disabled

  hourly-sync:
    timezone: "UTC"
    enabled: true
```

Source: Example adapted from [`examples/simple-api/transire.yaml:40-43`](https://github.com/transire/transire/blob/main/examples/simple-api/transire.yaml)

---

## Complete Example

### In Code

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

type CleanupHandler struct{}

func (h *CleanupHandler) Name() string {
    return "daily-cleanup"
}

func (h *CleanupHandler) Schedule() string {
    return "0 2 * * *"  // Daily at 2 AM UTC
}

func (h *CleanupHandler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        Timezone:       "UTC",
        Enabled:        true,
        TimeoutSeconds: 300,  // 5 minutes
        RetryAttempts:  3,
        RetryDelay:     30 * time.Second,
    }
}

func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Printf("Starting daily cleanup at %v", event.ScheduledTime)

    // Cleanup old temporary files
    if err := cleanupTempFiles(ctx); err != nil {
        return fmt.Errorf("failed to cleanup temp files: %w", err)
    }

    // Cleanup expired sessions
    if err := cleanupExpiredSessions(ctx); err != nil {
        return fmt.Errorf("failed to cleanup expired sessions: %w", err)
    }

    log.Println("Daily cleanup completed successfully")
    return nil
}

func cleanupTempFiles(ctx context.Context) error {
    // Implementation
    return nil
}

func cleanupExpiredSessions(ctx context.Context) error {
    // Implementation
    return nil
}
```

Source: Example adapted from [`examples/simple-api/handlers.go:96-135`](https://github.com/transire/transire/blob/main/examples/simple-api/handlers.go)

### In Configuration

```yaml
# transire.yaml
name: my-api

# ... other configuration ...

schedules:
  daily-cleanup:
    timezone: "UTC"
    enabled: true
```

---

## Generated EventBridge Resources

When you run `transire build`, CDK generates:

```typescript
// infrastructure/lib/my-api-stack.ts (generated)

const dailyCleanupRule = new events.Rule(this, 'DailyCleanupRule', {
  ruleName: 'daily-cleanup',
  schedule: events.Schedule.expression('cron(0 2 * * ? *)'),
  enabled: true,
});

dailyCleanupRule.addTarget(
  new targets.LambdaFunction(mainFunctionAlias, {
    retryAttempts: 3,
    maxEventAge: cdk.Duration.hours(24),
  })
);
```

Source: CDK template from [`internal/providers/aws/cdk_generator.go:92-175`](https://github.com/transire/transire/blob/main/internal/providers/aws/cdk_generator.go)

---

## Local Testing

Test schedules locally with `transire run`:

```bash
# Start app
transire run

# In another terminal, trigger schedule manually
transire dev schedules execute daily-cleanup
```

Your `HandleSchedule` method executes immediately.

Source: Schedule simulator in [`pkg/transire/local_runtime.go`](https://github.com/transire/transire/blob/main/pkg/transire/local_runtime.go)

---

## Monitoring Schedules

### CloudWatch Metrics

Key metrics for EventBridge rules:

| Metric | Description | Alert On |
|--------|-------------|----------|
| `Invocations` | Number of times rule triggered | Low rate |
| `TriggeredRules` | Successful triggers | Unexpected drops |
| `FailedInvocations` | Failed triggers | Any failures |
| `ThrottledRules` | Rate-limited triggers | Throttling |

### CloudWatch Logs

View schedule execution logs:

```bash
aws logs tail /aws/lambda/my-api-stack-MainFunction-ABC123 --follow --filter-pattern "daily-cleanup"
```

Example log output:
```
2024-01-18T02:00:00.123Z INFO Starting daily cleanup at 2024-01-18 02:00:00
2024-01-18T02:00:05.456Z INFO Cleaning up temporary files...
2024-01-18T02:00:10.789Z INFO Daily cleanup completed successfully
```

---

## Common Configuration Patterns

### Frequent Monitoring Task

```go
// Every 5 minutes
func (h *HealthCheckHandler) Schedule() string {
    return "*/5 * * * *"
}

func (h *HealthCheckHandler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        Timezone:       "UTC",
        Enabled:        true,
        TimeoutSeconds: 60,  // Quick check
        RetryAttempts:  1,   // Runs again in 5 min anyway
    }
}
```

### Daily Maintenance Task

```go
// Every day at 2 AM UTC
func (h *MaintenanceHandler) Schedule() string {
    return "0 2 * * *"
}

func (h *MaintenanceHandler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        Timezone:       "UTC",
        Enabled:        true,
        TimeoutSeconds: 900,  // 15 minutes max
        RetryAttempts:  3,
        RetryDelay:     60 * time.Second,
    }
}
```

### Business Hours Report

```go
// Weekdays at 9 AM Eastern Time
func (h *ReportHandler) Schedule() string {
    return "0 9 * * MON-FRI"
}

func (h *ReportHandler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        Timezone:       "America/New_York",  // Handles DST
        Enabled:        true,
        TimeoutSeconds: 600,  // 10 minutes
        RetryAttempts:  2,
    }
}
```

---

## Troubleshooting

### Schedule not triggering

**Check 1:** Is the schedule enabled?
```yaml
schedules:
  my-schedule:
    enabled: true  # Must be true
```

**Check 2:** Is the cron expression correct?

Test at [crontab.guru](https://crontab.guru/)

**Check 3:** Check EventBridge console

```bash
aws events list-rules --name-prefix my-api
```

### Schedule running at wrong time

**Cause:** Timezone misconfiguration.

**Solution:**
Verify timezone in config:
```go
Timezone: "America/New_York"  // Not "EST" or "EDT"
```

Use IANA timezone names, not abbreviations.

### Handler timing out

**Cause:** Task takes longer than `TimeoutSeconds`.

**Solution:**
Increase timeout:
```yaml
schedules:
  long-task:
    timeout_seconds: 900  # Was 300
```

Also increase Lambda function timeout:
```yaml
lambda:
  timeout_seconds: 900
```

### Failed retries exhausted

**Cause:** Persistent error or insufficient retry attempts.

**Solution:**
1. Check CloudWatch Logs for error details
2. Increase retry attempts:
```go
RetryAttempts: 5  // Was 3
```

---

## Best Practices

### 1. Make Handlers Idempotent

Schedule handlers may run multiple times (retries, manual triggers):

```go
func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    // ✅ Idempotent: Safe to run multiple times
    deleted := deleteFilesOlderThan(time.Now().Add(-7 * 24 * time.Hour))
    log.Printf("Deleted %d files", deleted)
    return nil
}
```

### 2. Use Structured Logging

Include schedule metadata in logs:

```go
func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Printf("Schedule: %s, Triggered: %v", event.Name, event.ScheduledTime)
    // ... task logic ...
    return nil
}
```

### 3. Monitor Execution Time

Track how long tasks take:

```go
func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    start := time.Now()
    defer func() {
        log.Printf("Cleanup took %v", time.Since(start))
    }()

    // ... task logic ...
    return nil
}
```

### 4. Handle Partial Failures

Continue processing even if one step fails:

```go
func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    var errs []error

    if err := cleanupTempFiles(ctx); err != nil {
        errs = append(errs, fmt.Errorf("temp files: %w", err))
    }

    if err := cleanupSessions(ctx); err != nil {
        errs = append(errs, fmt.Errorf("sessions: %w", err))
    }

    if len(errs) > 0 {
        return fmt.Errorf("cleanup completed with errors: %v", errs)
    }

    return nil
}
```

---

## Next Steps

- [Schedule Handlers](../core-concepts/schedule-handlers.md) – Implement schedule handlers
- [Scheduled Tasks Guide](../guides/scheduled-tasks.md) – Best practices and patterns
- [transire.yaml Reference](transire-yaml.md) – Complete configuration reference

---

## See Also

- [Queue Configuration](queues.md) – Configure SQS queues
- [Lambda Configuration](lambda.md) – Function memory and timeout
- [Local Development](../guides/local-development.md) – Test schedules locally
