# Configuration Types

Go configuration structs for handlers and applications.

!!! tip "TL;DR"
    `QueueConfig` and `ScheduleConfig` configure handler behavior. `Config` is the main application configuration loaded from `transire.yaml`.

---

## QueueConfig

```go
type QueueConfig struct {
    VisibilityTimeoutSeconds int  `yaml:"visibility_timeout_seconds"`
    MaxReceiveCount          int  `yaml:"max_receive_count"`
    BatchSize                int  `yaml:"batch_size"`
    WaitTimeSeconds          int  `yaml:"wait_time_seconds"`
    FIFO                     bool `yaml:"fifo"`
}
```

Configuration for queue handler behavior.

**Source:** [`pkg/transire/interfaces.go:76-82`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go#L76-L82)

---

### VisibilityTimeoutSeconds

```go
VisibilityTimeoutSeconds int
```

How long (in seconds) messages are invisible after being delivered to a consumer.

**Behavior:**
- After a message is received, it becomes invisible to other consumers
- If not deleted within this time, it becomes visible again for retry
- Should be longer than your Lambda timeout

**Typical values:**
- **Fast processing:** 30-60 seconds
- **Slow processing:** 300-900 seconds
- **Rule of thumb:** 2-3x your expected processing time

**Example:**
```go
func (h *Handler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        VisibilityTimeoutSeconds: 60,  // Messages invisible for 1 minute
    }
}
```

**AWS Mapping:** Sets SQS queue `VisibilityTimeout` attribute

---

### MaxReceiveCount

```go
MaxReceiveCount int
```

Maximum number of times a message can be delivered before moving to Dead Letter Queue (DLQ).

**Behavior:**
- After this many delivery attempts, message goes to DLQ
- Prevents infinite retry loops for permanently failing messages
- DLQ is automatically created by Transire

**Typical values:**
- **Strict:** 1-3 retries
- **Moderate:** 3-5 retries
- **Lenient:** 5-10 retries

**Example:**
```go
func (h *Handler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        MaxReceiveCount: 3,  // Try up to 3 times, then DLQ
    }
}
```

**AWS Mapping:** Sets SQS queue redrive policy with `maxReceiveCount`

---

### BatchSize

```go
BatchSize int
```

Maximum number of messages to process in a single batch.

**Behavior:**
- Lambda is invoked with up to this many messages
- Smaller batches = more frequent invocations = higher cost
- Larger batches = better throughput = lower cost per message

**Typical values:**
- **Low latency:** 1-5 messages
- **Balanced:** 10 messages (recommended)
- **High throughput:** 10 (SQS max per batch)

**Example:**
```go
func (h *Handler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        BatchSize: 10,  // Process up to 10 messages at once
    }
}
```

**AWS Mapping:** Sets Lambda event source mapping `BatchSize`

---

### WaitTimeSeconds

```go
WaitTimeSeconds int
```

Long polling wait time in seconds. How long to wait for messages before returning empty.

**Behavior:**
- **0 seconds:** Short polling (instant return, more API calls)
- **1-20 seconds:** Long polling (wait for messages, fewer API calls)
- Long polling reduces costs and improves efficiency

**Typical values:**
- **Short polling:** 0 (not recommended)
- **Long polling:** 5-20 seconds (recommended)

**Example:**
```go
func (h *Handler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        WaitTimeSeconds: 5,  // Wait up to 5 seconds for messages
    }
}
```

**AWS Mapping:** Sets SQS queue `ReceiveMessageWaitTimeSeconds`

---

### FIFO

```go
FIFO bool
```

Whether this is a FIFO (First-In-First-Out) queue.

**Behavior:**
- **false:** Standard queue (at-least-once delivery, best-effort ordering)
- **true:** FIFO queue (exactly-once delivery, strict ordering)

**FIFO constraints:**
- Require `.fifo` suffix in queue name
- Limited to 300 TPS (3000 with batching)
- Require message group IDs
- Higher latency than standard queues

**Example:**
```go
// Standard queue
func (h *StandardHandler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        FIFO: false,
    }
}

// FIFO queue
func (h *FIFOHandler) QueueName() string {
    return "order-processing.fifo"  // Must end with .fifo
}

func (h *FIFOHandler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        FIFO: true,
    }
}
```

**AWS Mapping:** Creates FIFO SQS queue if true, standard queue if false

---

### Complete Example

```go
type EmailHandler struct{}

func (h *EmailHandler) QueueName() string {
    return "email-queue"
}

func (h *EmailHandler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        VisibilityTimeoutSeconds: 30,   // 30s processing window
        MaxReceiveCount:          3,     // 3 retries before DLQ
        BatchSize:                10,    // Process 10 at once
        WaitTimeSeconds:          5,     // Long polling for efficiency
        FIFO:                     false, // Standard queue
    }
}
```

---

## ScheduleConfig

```go
type ScheduleConfig struct {
    Timezone       string        `yaml:"timezone"`
    Enabled        bool          `yaml:"enabled"`
    TimeoutSeconds int           `yaml:"timeout_seconds"`
    RetryAttempts  int           `yaml:"retry_attempts"`
    RetryDelay     time.Duration `yaml:"retry_delay"`
}
```

Configuration for scheduled task behavior.

**Source:** [`pkg/transire/interfaces.go:84-90`](https://github.com/transire/transire/blob/main/pkg/transire/interfaces.go#L84-L90)

---

### Timezone

```go
Timezone string
```

Timezone for interpreting the cron expression.

**Format:** IANA timezone name (e.g., "America/New_York", "Europe/London")

**Example:**
```go
func (h *Handler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        Timezone: "America/Los_Angeles",  // Pacific Time
    }
}

// Schedule: "0 9 * * *" = 9 AM Pacific Time
```

**Common timezones:**
- `UTC` – Coordinated Universal Time (recommended for consistency)
- `America/New_York` – Eastern Time
- `America/Chicago` – Central Time
- `America/Los_Angeles` – Pacific Time
- `Europe/London` – UK Time
- `Asia/Tokyo` – Japan Time

**AWS Mapping:** Sets EventBridge rule timezone

---

### Enabled

```go
Enabled bool
```

Whether this scheduled task is enabled.

**Behavior:**
- **true:** Schedule is active, will execute
- **false:** Schedule is disabled, will not execute

**Usage:**
- Disable schedules during maintenance
- Conditionally enable per environment
- Temporarily pause scheduled tasks

**Example:**
```go
func (h *Handler) Config() transire.ScheduleConfig {
    env := os.Getenv("ENV")

    return transire.ScheduleConfig{
        Enabled: env == "production",  // Only run in production
    }
}
```

**AWS Mapping:** Sets EventBridge rule state (ENABLED/DISABLED)

---

### TimeoutSeconds

```go
TimeoutSeconds int
```

Maximum execution time in seconds before timeout.

**Behavior:**
- Lambda function timeout for this schedule
- Should accommodate worst-case execution time
- If exceeded, function is terminated

**Typical values:**
- **Quick tasks:** 30-60 seconds
- **Normal tasks:** 300 seconds (5 minutes)
- **Long tasks:** 900 seconds (15 minutes, Lambda max)

**Example:**
```go
func (h *CleanupHandler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        TimeoutSeconds: 300,  // 5 minute timeout
    }
}
```

**AWS Mapping:** Sets Lambda function timeout for scheduler invocations

---

### RetryAttempts

```go
RetryAttempts int
```

Number of retry attempts if execution fails.

**Behavior:**
- If `HandleSchedule()` returns error, task is retried
- After this many failures, task is abandoned
- Retries happen with delay specified in `RetryDelay`

**Typical values:**
- **No retries:** 0
- **Moderate:** 2-3 retries
- **Persistent:** 5+ retries

**Example:**
```go
func (h *Handler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        RetryAttempts: 3,  // Retry up to 3 times on failure
    }
}
```

**AWS Mapping:** Sets EventBridge retry policy

---

### RetryDelay

```go
RetryDelay time.Duration
```

Delay between retry attempts.

**Behavior:**
- Wait this long before retrying after failure
- Gives time for transient issues to resolve
- Applied between each retry attempt

**Typical values:**
- **Fast retry:** 10-30 seconds
- **Moderate:** 30-60 seconds
- **Slow retry:** 60+ seconds

**Example:**
```go
func (h *Handler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        RetryAttempts: 3,
        RetryDelay:    30 * time.Second,  // Wait 30s between retries
    }
}
```

**AWS Mapping:** Sets EventBridge retry policy delay

---

### Complete Example

```go
type DailyReportHandler struct{}

func (h *DailyReportHandler) Name() string {
    return "daily-report"
}

func (h *DailyReportHandler) Schedule() string {
    return "0 9 * * *"  // Daily at 9 AM
}

func (h *DailyReportHandler) Config() transire.ScheduleConfig {
    return transire.ScheduleConfig{
        Timezone:       "America/New_York",  // Eastern Time
        Enabled:        true,                 // Active
        TimeoutSeconds: 600,                  // 10 minute timeout
        RetryAttempts:  3,                    // Retry 3 times on failure
        RetryDelay:     60 * time.Second,     // Wait 1 min between retries
    }
}
```

---

## Config

```go
type Config struct {
    Name     string
    Language string
    Cloud    string
    Runtime  string
    IaC      string
    CI       string

    Lambda      LambdaConfig
    Functions   map[string]FunctionConfig
    Environment map[string]string
    VPC         *VPCConfig

    ExistingResources ExistingResourcesConfig
    Queues            map[string]QueueConfig
    Schedules         map[string]ScheduleConfig

    CDKExtensions []ExtensionConfig
    Development   DevelopmentConfig
}
```

Main application configuration, typically loaded from `transire.yaml`.

**Source:** [`pkg/transire/config.go:12-31`](https://github.com/transire/transire/blob/main/pkg/transire/config.go#L12-L31)

---

### LoadConfig

```go
func LoadConfig(path string) (*Config, error)
```

Loads configuration from a YAML file.

**Parameters:**
- `path` – Path to config file (defaults to "transire.yaml")

**Returns:**
- `*Config` – Parsed configuration
- `error` – Parse error

**Example:**
```go
config, err := transire.LoadConfig("transire.yaml")
if err != nil {
    log.Fatalf("Failed to load config: %v", err)
}

app := transire.New(transire.WithConfig(config))
```

---

### LambdaConfig

```go
type LambdaConfig struct {
    Architecture   string
    TimeoutSeconds int
    MemoryMB       int
}
```

Default Lambda function configuration.

**Example:**
```yaml
# transire.yaml
lambda:
  architecture: arm64
  timeout_seconds: 30
  memory_mb: 512
```

**Fields:**
- `Architecture` – `arm64` or `x86_64`
- `TimeoutSeconds` – Function timeout (1-900)
- `MemoryMB` – Memory allocation (128-10240)

---

### DevelopmentConfig

```go
type DevelopmentConfig struct {
    HTTPPort        int
    QueuePort       int
    SchedulerPort   int
    AutoReload      bool
    LogLevel        string
    MockAWSServices bool
}
```

Local development configuration.

**Example:**
```yaml
# transire.yaml
development:
  http_port: 3000
  queue_port: 4000
  scheduler_port: 5000
  auto_reload: true
  log_level: debug
  mock_aws_services: true
```

**Fields:**
- `HTTPPort` – HTTP server port (default: 3000)
- `QueuePort` – Queue simulator port (default: 4000)
- `SchedulerPort` – Schedule simulator port (default: 5000)
- `AutoReload` – Enable hot reload (default: true)
- `LogLevel` – Log level: debug, info, warn, error
- `MockAWSServices` – Use LocalStack/mocks (default: false)

---

## See Also

- **[Configuration Reference](../configuration/transire-yaml.md)** – Complete YAML reference
- **[Handler Interfaces](handlers.md)** – QueueHandler and SchedulerHandler
- **[Examples](../examples/)** – Configuration examples
