# Handler Interfaces

Queue and schedule handler interfaces for background processing.

!!! tip "TL;DR"
    Implement `QueueHandler` for message processing or `SchedulerHandler` for cron jobs. Both interfaces require configuration methods and a processing method.

---

## QueueHandler

```go
type QueueHandler interface {
    HandleMessages(ctx context.Context, messages []Message) ([]string, error)
    QueueName() string
    Config() QueueConfig
}
```

Interface for processing messages from queues (SQS in AWS).

**Source:** [`pkg/transire/interfaces.go:30-41`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go#L30-L41)

---

### HandleMessages

```go
HandleMessages(ctx context.Context, messages []Message) ([]string, error)
```

Processes a batch of messages from the queue.

**Parameters:**
- `ctx` – Request context with timeout and cancellation
- `messages` – Slice of messages to process

**Returns:**
- `[]string` – IDs of messages that failed and should be retried
- `error` – Critical error that affects the entire batch

**Behavior:**
- Process each message independently
- Return IDs of failed messages for retry
- Continue processing even if individual messages fail
- Transire handles retry logic based on returned IDs

**Example:**
```go
func (h *EmailHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        var email EmailRequest
        if err := json.Unmarshal(msg.Body(), &email); err != nil {
            log.Printf("Invalid message format: %v", err)
            continue  // Skip malformed messages
        }

        if err := h.sendEmail(ctx, email); err != nil {
            log.Printf("Failed to send email: %v", err)
            failedIDs = append(failedIDs, msg.ID())
            continue
        }

        log.Printf("Sent email to %s", email.To)
    }

    return failedIDs, nil
}
```

**Best Practices:**
- Process messages in parallel when order doesn't matter
- Use context deadline for timeouts
- Log failures with message IDs
- Distinguish transient vs permanent errors
- Only return IDs for retryable failures

---

### QueueName

```go
QueueName() string
```

Returns the logical queue name for this handler.

**Returns:** `string` – Queue name (e.g., "email-queue")

**Behavior:**
- **Local runtime:** Test with `transire dev queues send {queue-name} '{message}'`
- **AWS runtime:** SQS queue created with this name
- Must be unique across all queue handlers

**Example:**
```go
func (h *EmailHandler) QueueName() string {
    return "email-queue"
}
```

---

### Config

```go
Config() QueueConfig
```

Returns configuration for queue behavior.

**Returns:** `QueueConfig` – Queue configuration

**Example:**
```go
func (h *EmailHandler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        VisibilityTimeoutSeconds: 30,   // Message invisible for 30s after delivery
        MaxReceiveCount:          3,     // 3 retries before DLQ
        BatchSize:                10,    // Process up to 10 messages at once
        WaitTimeSeconds:          5,     // Long polling wait time
        FIFO:                     false, // Standard queue
    }
}
```

**See:** [QueueConfig reference](config.md#queueconfig)

---

### Complete Example

```go
// From examples/simple-api/handlers.go
type EmailQueueHandler struct {
    emailService *EmailService
}

func (h *EmailQueueHandler) QueueName() string {
    return "email-queue"
}

func (h *EmailQueueHandler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        VisibilityTimeoutSeconds: 30,
        MaxReceiveCount:          3,
        BatchSize:                10,
        WaitTimeSeconds:          5,
    }
}

func (h *EmailQueueHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    log.Printf("Processing %d email messages", len(messages))

    var failedIDs []string

    for _, msg := range messages {
        var emailReq EmailRequest
        if err := json.Unmarshal(msg.Body(), &emailReq); err != nil {
            log.Printf("Failed to parse email request: %v", err)
            continue
        }

        if err := h.emailService.Send(ctx, emailReq); err != nil {
            log.Printf("Failed to send email: %v", err)
            failedIDs = append(failedIDs, msg.ID())
        } else {
            log.Printf("Successfully sent email to %s", emailReq.To)
        }
    }

    return failedIDs, nil
}

type EmailRequest struct {
    To      string `json:"to"`
    Subject string `json:"subject"`
    Body    string `json:"body"`
}
```

---

## SchedulerHandler

```go
type SchedulerHandler interface {
    HandleSchedule(ctx context.Context, event ScheduleEvent) error
    Schedule() string
    Name() string
    Config() ScheduleConfig
}
```

Interface for handling scheduled/cron events.

**Source:** [`pkg/transire/interfaces.go:43-56`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go#L43-L56)

---

### HandleSchedule

```go
HandleSchedule(ctx context.Context, event ScheduleEvent) error
```

Executes the scheduled task.

**Parameters:**
- `ctx` – Request context with timeout
- `event` – Schedule event information

**Returns:** `error` – Error if execution fails (triggers retry if configured)

**Example:**
```go
func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Printf("Starting cleanup at %v", event.ScheduledTime)

    // Cleanup old files
    if err := h.cleanupFiles(ctx); err != nil {
        return fmt.Errorf("failed to cleanup files: %w", err)
    }

    // Cleanup expired sessions
    if err := h.cleanupSessions(ctx); err != nil {
        return fmt.Errorf("failed to cleanup sessions: %w", err)
    }

    log.Println("Cleanup completed successfully")
    return nil
}
```

**Best Practices:**
- Use context deadline for timeouts
- Break work into smaller chunks
- Log progress for debugging
- Return errors for retry (if configured)
- Consider idempotency (task may run multiple times)

---

### Schedule

```go
Schedule() string
```

Returns the cron expression or interval for this task.

**Returns:** `string` – Cron expression

**Format:** Standard Unix cron format
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

**Examples:**
```go
func (h *CleanupHandler) Schedule() string {
    return "0 2 * * *"  // Daily at 2 AM
}

func (h *HourlyHandler) Schedule() string {
    return "0 * * * *"  // Every hour
}

func (h *WeeklyHandler) Schedule() string {
    return "0 9 * * 1"  // Mondays at 9 AM
}

func (h *MonthlyHandler) Schedule() string {
    return "0 0 1 * *"  // First day of month at midnight
}
```

---

### Name

```go
Name() string
```

Returns unique identifier for this scheduled task.

**Returns:** `string` – Schedule name (e.g., "daily-cleanup")

**Behavior:**
- **Local runtime:** Trigger with `transire dev schedules execute {schedule-name}`
- **AWS runtime:** EventBridge rule created with this name
- Must be unique across all schedule handlers

**Example:**
```go
func (h *CleanupHandler) Name() string {
    return "daily-cleanup"
}
```

---

### Config

```go
Config() ScheduleConfig
```

Returns configuration for schedule behavior.

**Returns:** `ScheduleConfig` – Schedule configuration

**Example:**
```go
func (h *CleanupHandler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        Timezone:       "UTC",           // Timezone for cron expression
        Enabled:        true,            // Enable this schedule
        TimeoutSeconds: 300,             // 5 minute timeout
        RetryAttempts:  3,               // Retry up to 3 times on failure
        RetryDelay:     30 * time.Second, // Wait 30s between retries
    }
}
```

**See:** [ScheduleConfig reference](config.md#scheduleconfig)

---

### Complete Example

```go
// From examples/simple-api/handlers.go
type CleanupHandler struct {
    db *sql.DB
}

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
        TimeoutSeconds: 300,
        RetryAttempts:  3,
        RetryDelay:     30 * time.Second,
    }
}

func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Printf("Starting daily cleanup at %v", event.ScheduledTime)

    // Cleanup temporary files
    if err := h.cleanupTempFiles(ctx); err != nil {
        return fmt.Errorf("failed to cleanup temp files: %w", err)
    }

    // Cleanup expired sessions
    if err := h.cleanupExpiredSessions(ctx); err != nil {
        return fmt.Errorf("failed to cleanup expired sessions: %w", err)
    }

    // Cleanup old logs
    if err := h.cleanupOldLogs(ctx); err != nil {
        return fmt.Errorf("failed to cleanup old logs: %w", err)
    }

    log.Println("Daily cleanup completed successfully")
    return nil
}
```

---

## Next Steps

- **[Message Types](messages.md)** – Message and ScheduleEvent types
- **[Configuration](config.md)** – QueueConfig and ScheduleConfig
- **[Queue Processing Guide](../guides/queue-processing.md)** – Advanced patterns
- **[Examples](../examples/)** – Complete examples
