# Message Types

Queue message and schedule event types.

!!! tip "TL;DR"
    `Message` interface provides access to queue message data. `ScheduleEvent` struct contains scheduled task information. Both are passed to handler methods.

---

## Message

```go
type Message interface {
    ID() string
    Body() []byte
    Attributes() map[string]string
    DeliveryCount() int
    EnqueuedAt() time.Time
}
```

Interface representing a queue message. Implemented by the runtime to abstract cloud-specific message formats.

**Source:** [`pkg/transire/interfaces.go:59-65`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go#L59-L65)

---

### ID

```go
ID() string
```

Returns unique identifier for this message.

**Returns:** `string` – Message ID

**Usage:**
- Track failed messages for retry
- Log message processing
- Implement idempotency

**Example:**
```go
func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        log.Printf("Processing message %s", msg.ID())

        if err := h.process(ctx, msg); err != nil {
            failedIDs = append(failedIDs, msg.ID())
        }
    }

    return failedIDs, nil
}
```

---

### Body

```go
Body() []byte
```

Returns the message body as raw bytes.

**Returns:** `[]byte` – Message content

**Usage:**
- Unmarshal JSON payloads
- Process binary data
- Read text content

**Example:**
```go
func (h *EmailHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        // Parse JSON body
        var emailReq EmailRequest
        if err := json.Unmarshal(msg.Body(), &emailReq); err != nil {
            log.Printf("Invalid JSON in message %s: %v", msg.ID(), err)
            continue  // Skip malformed messages
        }

        // Process email
        if err := h.sendEmail(emailReq); err != nil {
            failedIDs = append(failedIDs, msg.ID())
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

**String bodies:**
```go
textBody := string(msg.Body())
log.Printf("Received: %s", textBody)
```

---

### Attributes

```go
Attributes() map[string]string
```

Returns message attributes (metadata).

**Returns:** `map[string]string` – Key-value attributes

**Usage:**
- Access custom metadata
- Read system attributes
- Implement priority queues
- Track message origin

**Example:**
```go
func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    for _, msg := range messages {
        attrs := msg.Attributes()

        // Check priority
        priority := attrs["priority"]
        if priority == "high" {
            // Process with higher urgency
        }

        // Check message source
        source := attrs["source"]
        log.Printf("Message from %s", source)

        // Custom attributes
        userID := attrs["user_id"]
        correlationID := attrs["correlation_id"]
    }

    return nil, nil
}
```

**AWS SQS Attributes:**
- `ApproximateReceiveCount` – Number of times received
- `SentTimestamp` – When message was sent
- `ApproximateFirstReceiveTimestamp` – First receive time
- Custom attributes you set when sending

---

### DeliveryCount

```go
DeliveryCount() int
```

Returns number of times this message has been delivered (including current delivery).

**Returns:** `int` – Delivery count (1 for first delivery)

**Usage:**
- Implement custom retry logic
- Detect problematic messages
- Trigger special handling for repeated failures

**Example:**
```go
func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        count := msg.DeliveryCount()

        if count > 3 {
            // Message has been retried too many times
            log.Printf("Message %s failed %d times, sending to DLQ", msg.ID(), count)
            h.sendToDLQ(msg)
            continue  // Don't retry again
        }

        if count > 1 {
            // This is a retry - use longer timeout
            ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
            defer cancel()
        }

        if err := h.process(ctx, msg); err != nil {
            failedIDs = append(failedIDs, msg.ID())
        }
    }

    return failedIDs, nil
}
```

---

### EnqueuedAt

```go
EnqueuedAt() time.Time
```

Returns when the message was first added to the queue.

**Returns:** `time.Time` – Enqueue timestamp

**Usage:**
- Detect stale messages
- Calculate processing latency
- Implement TTL logic
- Monitor queue age

**Example:**
```go
func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    for _, msg := range messages {
        age := time.Since(msg.EnqueuedAt())

        if age > 24*time.Hour {
            // Message is too old
            log.Printf("Discarding stale message %s (age: %s)", msg.ID(), age)
            continue
        }

        // Calculate processing latency
        start := time.Now()
        err := h.process(ctx, msg)
        processingTime := time.Since(start)

        log.Printf("Message %s: queued=%s, processing=%s",
            msg.ID(), age, processingTime)

        if err != nil {
            return []string{msg.ID()}, nil
        }
    }

    return nil, nil
}
```

---

## ScheduleEvent

```go
type ScheduleEvent struct {
    ScheduledTime time.Time
    Name          string
    Payload       []byte
    EventID       string
}
```

Struct containing information about a scheduled event.

**Source:** [`pkg/transire/interfaces.go:68-73`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go#L68-L73)

---

### ScheduledTime

```go
ScheduledTime time.Time
```

The time this event was scheduled to execute.

**Usage:**
- Determine if execution is delayed
- Calculate schedule drift
- Log execution times

**Example:**
```go
func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    now := time.Now()
    delay := now.Sub(event.ScheduledTime)

    if delay > 1*time.Minute {
        log.Printf("Warning: Schedule delayed by %s", delay)
    }

    log.Printf("Executing cleanup scheduled for %s", event.ScheduledTime.Format(time.RFC3339))

    // Perform cleanup
    return h.cleanup(ctx)
}
```

---

### Name

```go
Name string
```

The name of the scheduled task (matches `SchedulerHandler.Name()`).

**Usage:**
- Identify which schedule triggered
- Log execution
- Conditional logic based on schedule

**Example:**
```go
func (h *MultiScheduleHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Printf("Executing schedule: %s", event.Name)

    switch event.Name {
    case "hourly-sync":
        return h.hourlySync(ctx)
    case "daily-report":
        return h.dailyReport(ctx)
    case "weekly-cleanup":
        return h.weeklyCleanup(ctx)
    default:
        return fmt.Errorf("unknown schedule: %s", event.Name)
    }
}
```

---

### Payload

```go
Payload []byte
```

Optional payload data for the scheduled event.

**Usage:**
- Pass configuration to scheduled tasks
- Provide context-specific data
- Parameterize schedules

**Example:**
```go
func (h *ReportHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    // Parse payload if present
    if len(event.Payload) > 0 {
        var config ReportConfig
        if err := json.Unmarshal(event.Payload, &config); err != nil {
            log.Printf("Failed to parse payload: %v", err)
            return err
        }

        return h.generateReport(ctx, config)
    }

    // Use default config
    return h.generateReport(ctx, DefaultReportConfig)
}

type ReportConfig struct {
    Format    string   `json:"format"`     // pdf, csv, json
    Recipients []string `json:"recipients"`
    Period    string   `json:"period"`     // daily, weekly, monthly
}
```

**Note:** In AWS EventBridge, payload is set via the event pattern or input transformer.

---

### EventID

```go
EventID string
```

Unique identifier for this event execution.

**Usage:**
- Implement idempotency
- Track execution history
- Deduplicate events

**Example:**
```go
func (h *Handler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    // Check if already processed
    processed, err := h.cache.Get(ctx, fmt.Sprintf("schedule:processed:%s", event.EventID)).Result()
    if err == nil && processed == "true" {
        log.Printf("Event %s already processed, skipping", event.EventID)
        return nil
    }

    // Execute task
    if err := h.executeTask(ctx); err != nil {
        return err
    }

    // Mark as processed (24h TTL)
    h.cache.Set(ctx, fmt.Sprintf("schedule:processed:%s", event.EventID), "true", 24*time.Hour)

    return nil
}
```

---

## Usage Examples

### Processing JSON Messages

```go
type OrderMessage struct {
    OrderID   string  `json:"order_id"`
    Total     float64 `json:"total"`
    UserID    string  `json:"user_id"`
    Timestamp string  `json:"timestamp"`
}

func (h *OrderHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        var order OrderMessage
        if err := json.Unmarshal(msg.Body(), &order); err != nil {
            log.Printf("Invalid JSON in message %s: %v", msg.ID(), err)
            continue
        }

        if err := h.processOrder(ctx, order); err != nil {
            failedIDs = append(failedIDs, msg.ID())
        }
    }

    return failedIDs, nil
}
```

---

### Implementing Priority Processing

```go
type PriorityMessage struct {
    transire.Message
    Priority int
}

func (h *Handler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    // Extract priority and sort
    priorityMessages := make([]PriorityMessage, 0, len(messages))
    for _, msg := range messages {
        priority := 0
        if p := msg.Attributes()["priority"]; p != "" {
            priority, _ = strconv.Atoi(p)
        }
        priorityMessages = append(priorityMessages, PriorityMessage{
            Message:  msg,
            Priority: priority,
        })
    }

    // Sort by priority (high to low)
    sort.Slice(priorityMessages, func(i, j int) bool {
        return priorityMessages[i].Priority > priorityMessages[j].Priority
    })

    // Process in priority order
    var failedIDs []string
    for _, pm := range priorityMessages {
        if err := h.process(ctx, pm.Message); err != nil {
            failedIDs = append(failedIDs, pm.Message.ID())
        }
    }

    return failedIDs, nil
}
```

---

### Scheduled Task with Payload

```go
func (h *BackupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Printf("Starting backup (event %s, scheduled %s)",
        event.EventID, event.ScheduledTime.Format(time.RFC3339))

    // Parse payload for backup configuration
    var config BackupConfig
    if len(event.Payload) > 0 {
        if err := json.Unmarshal(event.Payload, &config); err != nil {
            return fmt.Errorf("invalid payload: %w", err)
        }
    } else {
        config = DefaultBackupConfig
    }

    // Perform backup
    if err := h.performBackup(ctx, config); err != nil {
        return fmt.Errorf("backup failed: %w", err)
    }

    log.Printf("Backup completed successfully")
    return nil
}

type BackupConfig struct {
    IncludeTables []string `json:"include_tables"`
    Destination   string   `json:"destination"`
    Compress      bool     `json:"compress"`
}
```

---

## Next Steps

- **[Handler Interfaces](handlers.md)** – QueueHandler and SchedulerHandler
- **[Configuration](config.md)** – Config types
- **[Queue Processing Guide](../guides/queue-processing.md)** – Advanced patterns
- **[Examples](../examples/)** – Complete examples
