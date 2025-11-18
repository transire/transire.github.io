---
title: "Local Development"
description: "Develop and test Transire applications locally with hot reload"
keywords:
  - local development
  - hot reload
  - testing
  - transire run
  - development workflow
category: guides
difficulty: beginner
estimated_time: 15 minutes
prerequisites:
  - "Completed Quickstart"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Setting up local development environment"
    - "Testing locally with hot reload"
    - "Debugging Transire applications"
  common_questions:
    - "How do I run my app locally?"
    - "How does hot reload work?"
    - "How do I test queues and schedules locally?"
---

# Local Development

Best practices for developing Transire applications locally with hot reload, simulators, and debugging.

!!! tip "TL;DR"
    `transire run` starts your app with hot reload, HTTP server on :3000, queue simulator on :4000, and schedule simulator on :5000. Edit code and save to automatically rebuild and restart.

---

## Development Workflow

### 1. Start Development Server

```bash
transire run
```

**Output:**
```
[INFO] Transire starting in local mode
[INFO] Discovered handlers:
[INFO]   HTTP: 5 routes
[INFO]   Queues: 2 handlers (email-queue, notification-queue)
[INFO]   Schedules: 1 handler (daily-cleanup)
[INFO] Starting HTTP server on :3000
[INFO] Starting queue simulator on :4000
[INFO] Starting scheduler simulator on :5000
[INFO] Ready! Watching for file changes...
```

Source: [`internal/cli/commands/run.go:8-41`](https://github.com/transire/transire/blob/main/internal/cli/commands/run.go)

---

### 2. Make Code Changes

Edit your Go files:

```go
// handlers.go
func healthHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    w.Write([]byte(`{"status":"healthy","version":"1.0.1"}`)) // Changed version
}
```

**Save the file** → Transire automatically rebuilds and restarts.

---

### 3. Test Changes

```bash
curl http://localhost:3000/health
# => {"status":"healthy","version":"1.0.1"}
```

---

## Hot Reload Deep Dive

### How It Works

Hot reload is implemented via file watching with [`github.com/fsnotify/fsnotify`](https://github.com/fsnotify/fsnotify):

1. **File watcher** monitors `*.go` and `*.yaml` files in your project
2. **Debouncing** batches rapid changes (~500ms window) to avoid excessive rebuilds
3. **On change:**
   - Kills running application process
   - Rebuilds Go binary (`go build`)
   - Restarts application with fresh code
4. **Error handling:** Build errors are displayed in console; next save triggers retry

Source: [`internal/cli/runner/`](https://github.com/transire/transire/blob/main/internal/cli/runner/)

---

### Watched Files

Hot reload triggers on changes to:

- **`*.go` files** – All Go source files in your project
- **`*.yaml` files** – Configuration changes (e.g., `transire.yaml`)

**Not watched:**
- Test files (`*_test.go`) – Only included if explicitly imported
- Vendor directory (`vendor/`)
- Hidden files/directories (`.git/`, `.idea/`)

---

### Disabling Hot Reload

Edit `transire.yaml`:

```yaml
development:
  auto_reload: false
```

Then restart `transire run`. Changes will require manual restart.

---

## Testing During Development

Transire provides multiple ways to test your application locally:

### HTTP API Testing

**URL:** `http://localhost:3000`

Test your Chi routes with standard HTTP clients:

```bash
# Health check
curl http://localhost:3000/health

# API endpoints
curl http://localhost:3000/api/v1/users

# POST requests
curl -X POST http://localhost:3000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'
```

---

### Queue Handler Testing

Use the `transire dev queues` commands to test your queue handlers:

**List registered queues:**
```bash
transire dev queues list
# => email-queue
# => notification-queue
```

**Send test message:**
```bash
transire dev queues send email-queue '{"to":"test@example.com","subject":"Test Email","body":"Hello!"}'
```

**What happens:**
1. Message is sent to your running application
2. Your `QueueHandler.HandleMessages()` is called with the message
3. Success/failure is displayed in the terminal

**Test with different messages:**
```bash
# Simple notification
transire dev queues send notification-queue '{"user_id":"123","type":"welcome"}'

# Complex message with nested data
transire dev queues send email-queue '{
  "to":"user@example.com",
  "subject":"Monthly Report",
  "body":"Here is your report...",
  "metadata":{"priority":"high","campaign":"monthly"}
}'
```

[:octicons-arrow-right-24: Learn more about `transire dev queues`](../cli-reference/transire-dev.md#queue-commands)

---

### Schedule Handler Testing

Use the `transire dev schedules` commands to test your schedule handlers:

**List registered schedules:**
```bash
transire dev schedules list
# => daily-cleanup (cron: 0 0 * * *)
# => hourly-report (cron: 0 * * * *)
```

**Execute schedule immediately:**
```bash
transire dev schedules execute daily-cleanup
```

**What happens:**
1. A `ScheduleEvent` is created with the current timestamp
2. Your `SchedulerHandler.HandleSchedule()` method is called
3. Success/failure is displayed in the terminal

**Useful for:**
- Testing cron logic without waiting for the schedule
- Debugging scheduled tasks
- Verifying schedule handler registration

[:octicons-arrow-right-24: Learn more about `transire dev schedules`](../cli-reference/transire-dev.md#schedule-commands)

Source: [`pkg/transire/local_runtime.go`](https://github.com/transire/transire/blob/main/pkg/transire/local_runtime.go)

---

## Debugging Techniques

### 1. Standard Go Debugger (Delve)

**Install Delve:**
```bash
go install github.com/go-delve/delve/cmd/dlv@latest
```

**Option A: Debug with Delve directly**

```bash
# Build without transire CLI
go build -o myapp

# Start with Delve
dlv exec ./myapp
```

**Set breakpoints:**
```
(dlv) break handlers.go:42
(dlv) continue
```

**Option B: Attach to running process**

```bash
# Terminal 1: Start app
transire run

# Terminal 2: Find PID and attach
ps aux | grep myapp
dlv attach <PID>
```

---

### 2. Print Debugging

Add strategic log statements:

```go
import "log"

func HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    log.Printf("Processing %d messages", len(messages))

    for _, msg := range messages {
        log.Printf("Message ID: %s, Body: %s", msg.ID(), string(msg.Body()))
        // Process message...
    }

    return nil, nil
}
```

**View logs:**
```bash
transire run
# Logs appear in console
```

---

### 3. VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Transire App",
      "type": "go",
      "request": "launch",
      "mode": "auto",
      "program": "${workspaceFolder}",
      "env": {
        "TRANSIRE_ENV": "local"
      },
      "args": []
    }
  ]
}
```

**Set breakpoints** in VS Code and press F5 to debug.

---

### 4. HTTP Request Debugging

Use verbose curl to see full request/response:

```bash
curl -v http://localhost:3000/api/v1/users
```

Or use tools like:
- **HTTPie:** `http :3000/api/v1/users`
- **Postman:** GUI for API testing
- **Insomnia:** Alternative to Postman

---

### 5. Queue Message Debugging

View message processing in real-time:

```bash
# Terminal 1: Start app with debug logging
# In transire.yaml:
# development:
#   log_level: debug

transire run

# Terminal 2: Send test message
transire dev queues send email-queue '{"to":"test@example.com","subject":"Debug Test"}'

# Terminal 1 shows detailed logs
```

---

## Configuration for Development

### Customize Ports

Edit `transire.yaml`:

```yaml
development:
  http_port: 8080        # Change HTTP port
  queue_port: 8081       # Change queue simulator port
  scheduler_port: 8082   # Change schedule simulator port
  auto_reload: true
  log_level: debug
```

Source: [`pkg/transire/config.go:74-82`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

---

### Environment Variables

Set environment variables for local development:

```bash
# .env file (not committed to git)
DATABASE_URL=postgres://localhost:5432/mydb
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
LOG_LEVEL=debug
```

**Load in terminal:**
```bash
source .env
transire run
```

**Access in code:**
```go
dbURL := os.Getenv("DATABASE_URL")
```

---

### Local AWS Services (LocalStack)

Run AWS services locally with LocalStack:

```bash
# Start LocalStack
docker run --rm -p 4566:4566 localstack/localstack

# Set endpoint in code
export AWS_ENDPOINT_URL=http://localhost:4566
```

Configure AWS SDK to use LocalStack:

```go
import (
    "github.com/aws/aws-sdk-go-v2/config"
    "github.com/aws/aws-sdk-go-v2/aws"
)

cfg, err := config.LoadDefaultConfig(context.Background(),
    config.WithEndpointResolver(aws.EndpointResolverFunc(
        func(service, region string) (aws.Endpoint, error) {
            return aws.Endpoint{
                URL: "http://localhost:4566",
            }, nil
        },
    )),
)
```

---

## Development Best Practices

### 1. Use Build Tags for Local-Only Code

Exclude code from Lambda builds:

```go
//go:build local

package main

import "log"

func init() {
    log.Println("This only runs locally, not in Lambda")
}
```

This code is **excluded** from `transire build` output.

Source: See "Build Process" in [`transire build` documentation](../cli-reference/transire-build.md)

---

### 2. Separate Development Configuration

Create `transire.dev.yaml`:

```yaml
name: my-api-dev
development:
  http_port: 3000
  log_level: debug
environment:
  DATABASE_URL: postgres://localhost:5432/mydb_dev
  LOG_LEVEL: debug
```

**Use in development:**
```bash
transire run -c transire.dev.yaml
```

---

### 3. Mock External Services

Create mock implementations for development:

```go
//go:build local

package services

type MockEmailService struct{}

func (m *MockEmailService) SendEmail(to, subject, body string) error {
    log.Printf("MOCK: Sending email to %s: %s", to, subject)
    return nil
}
```

```go
//go:build !local

package services

import "github.com/aws/aws-sdk-go-v2/service/ses"

type EmailService struct {
    client *ses.Client
}

func (e *EmailService) SendEmail(to, subject, body string) error {
    // Real SES implementation
}
```

---

### 4. Use Context Timeouts

Always set timeouts in development to catch slow operations:

```go
func myHandler(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
    defer cancel()

    // Use ctx for all operations
    result, err := fetchData(ctx)
    if err != nil {
        http.Error(w, "Request timeout", http.StatusGatewayTimeout)
        return
    }

    // Return result...
}
```

---

### 5. Log Request/Response in Development

Add middleware for request logging:

```go
func loggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        log.Printf("→ %s %s", r.Method, r.URL.Path)

        next.ServeHTTP(w, r)

        log.Printf("← %s %s (%s)", r.Method, r.URL.Path, time.Since(start))
    })
}

// In main.go
app := transire.New()
r := app.Router()
r.Use(loggingMiddleware)
```

---

## Common Development Issues

### Hot Reload Not Triggering

**Symptoms:** File changes don't trigger rebuild

**Solutions:**
1. Check `auto_reload` setting:
   ```yaml
   development:
     auto_reload: true
   ```

2. Ensure you're editing `*.go` or `*.yaml` files

3. Check file permissions (must be readable)

4. Try restarting `transire run`

---

### Port Already in Use

**Symptoms:**
```
Error: listen tcp :3000: bind: address already in use
```

**Solutions:**
1. Kill process using the port:
   ```bash
   lsof -ti:3000 | xargs kill -9
   ```

2. Change port in `transire.yaml`:
   ```yaml
   development:
     http_port: 3001
   ```

---

### Build Errors Not Showing

**Symptoms:** App doesn't start, no error message

**Solutions:**
1. Run build manually to see errors:
   ```bash
   go build
   ```

2. Check for syntax errors in Go files

3. Run `go mod tidy` to ensure dependencies are correct

---

### Queue/Schedule Handlers Not Found

**Symptoms:** `transire dev` commands return "queue not found" or "schedule not found"

**Solutions:**
1. List registered handlers to check names:
   ```bash
   transire dev queues list
   transire dev schedules list
   ```

2. Verify handler registration in `main.go`:
   ```go
   app.RegisterQueueHandler(&EmailQueueHandler{})
   app.RegisterScheduleHandler(&CleanupHandler{})
   ```

3. Check handler implements correct interface:
   ```go
   type EmailQueueHandler struct{}

   func (h *EmailQueueHandler) QueueName() string {
       return "email-queue"
   }

   func (h *EmailQueueHandler) HandleMessages(ctx context.Context, msgs []transire.Message) ([]string, error) {
       // Implementation
   }
   ```

4. Restart `transire run` to re-discover handlers

---

### Environment Variables Not Loading

**Symptoms:** `os.Getenv()` returns empty string

**Solutions:**
1. Export variables before running:
   ```bash
   export DATABASE_URL=postgres://localhost:5432/mydb
   transire run
   ```

2. Use a `.env` file and load it:
   ```bash
   source .env
   transire run
   ```

3. Or use a tool like `direnv`

---

## Integration with Other Tools

### Docker Compose for Dependencies

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

**Start dependencies:**
```bash
docker-compose up -d
export DATABASE_URL=postgres://user:password@localhost:5432/mydb
transire run
```

---

### Air for Advanced Hot Reload

For more control over hot reload, use [`air`](https://github.com/cosmtrek/air):

```bash
go install github.com/cosmtrek/air@latest
```

Create `.air.toml`:

```toml
[build]
  cmd = "go build -o ./tmp/main ."
  bin = "./tmp/main"
  include_ext = ["go", "yaml"]
  exclude_dir = ["tmp", "vendor"]
  delay = 1000
```

**Run with air:**
```bash
air
```

---

## Next Steps

- [transire run CLI Reference](../cli-reference/transire-run.md) – Detailed command reference
- [Testing Your Application](testing.md) – Write automated tests
- [Deploying to AWS](deploying-to-aws.md) – Deploy to production

---

## See Also

- [Delve Debugger Documentation](https://github.com/go-delve/delve)
- [VS Code Go Extension](https://code.visualstudio.com/docs/languages/go)
- [LocalStack Documentation](https://docs.localstack.cloud/)
- [Air Hot Reload](https://github.com/cosmtrek/air)
