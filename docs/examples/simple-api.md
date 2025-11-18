---
title: "Simple API Example"
description: "Complete example of a REST API with queues and schedules"
keywords:
  - example
  - simple api
  - rest
  - queues
  - schedules
  - tutorial
category: examples
difficulty: beginner
estimated_time: 20 minutes
prerequisites:
  - "Completed Quickstart"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Learning by example"
    - "Understanding complete app"
    - "REST API patterns"
  common_questions:
    - "How do I build a REST API?"
    - "Show me a complete example"
    - "How do handlers work together?"
---

# Simple API Example

A complete walkthrough of the `simple-api` example, demonstrating HTTP handlers, queue processing, and scheduled tasks.

!!! tip "TL;DR"
    The simple-api example shows a REST API with user CRUD operations, email queue processing, notification queue processing, and a daily cleanup scheduler. It demonstrates all core Transire features in one application.

---

## Overview

The **simple-api** example demonstrates:

- **HTTP Routes** – RESTful user management API
- **Queue Handlers** – Email and notification processing
- **Schedule Handlers** – Daily cleanup tasks
- **Chi Router** – Standard Go HTTP routing
- **Middleware** – Logging, recovery, request IDs
- **Local Testing** – Hot reload and simulators

**Location:** [`examples/simple-api/`](https://github.com/transire/transire/tree/main/examples/simple-api)

---

## Project Structure

```
simple-api/
├── main.go              # Application entry point with HTTP routes
├── handlers.go          # Queue and schedule handler implementations
├── e2e_test.go          # End-to-end tests
├── transire.yaml        # Configuration
└── go.mod               # Dependencies
```

---

## Application Code

### Main Entry Point

From [`examples/simple-api/main.go`](https://github.com/transire/transire/blob/main/examples/simple-api/main.go):

```go
package main

import (
    "context"
    "encoding/json"
    "net/http"

    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
    "github.com/transire/transire/pkg/transire"
)

func main() {
    // Create Transire app
    app := transire.New()

    // Get Chi router - use exactly like normal Chi
    r := app.Router()

    // Standard Chi middleware
    r.Use(middleware.Logger)
    r.Use(middleware.Recoverer)
    r.Use(middleware.RequestID)

    // Standard Chi routes
    r.Get("/", homeHandler)
    r.Get("/health", healthHandler)

    r.Route("/api/v1", func(r chi.Router) {
        r.Post("/users", createUserHandler)
        r.Get("/users/{id}", getUserHandler)
        r.Put("/users/{id}", updateUserHandler)
        r.Delete("/users/{id}", deleteUserHandler)
    })

    // Register queue and schedule handlers
    app.RegisterQueueHandler(&EmailQueueHandler{})
    app.RegisterQueueHandler(&NotificationQueueHandler{})
    app.RegisterScheduleHandler(&CleanupHandler{})

    // Run the app (works locally and in Lambda)
    if err := app.Run(context.Background()); err != nil {
        panic(err)
    }
}
```

**Key points:**
- `transire.New()` creates the app
- `app.Router()` returns standard Chi router
- Use Chi exactly as you normally would
- Register queue/schedule handlers before `Run()`
- Single `Run()` call works everywhere

---

### HTTP Handlers

**Home handler:**
```go
func homeHandler(w http.ResponseWriter, r *http.Request) {
    response := map[string]string{
        "message": "Welcome to Transire Simple API",
        "version": "2.0.0",
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}
```

**Health check:**
```go
func healthHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{
        "status":  "healthy",
        "service": "transire-simple-api",
    })
}
```

**User CRUD operations:**
```go
type User struct {
    ID    string `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}

func createUserHandler(w http.ResponseWriter, r *http.Request) {
    var user User
    if err := json.NewDecoder(r.Body).Decode(&user); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    user.ID = "generated-id"  // In production: generate UUID

    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(user)
}

func getUserHandler(w http.ResponseWriter, r *http.Request) {
    userID := chi.URLParam(r, "id")

    // In production: fetch from database
    user := User{
        ID:    userID,
        Name:  "John Doe",
        Email: "john@example.com",
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(user)
}
```

---

### Queue Handlers

From [`examples/simple-api/handlers.go`](https://github.com/transire/transire/blob/main/examples/simple-api/handlers.go):

**Email queue handler:**
```go
type EmailQueueHandler struct{}

func (h *EmailQueueHandler) QueueName() string {
    return "email-queue"
}

func (h *EmailQueueHandler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        VisibilityTimeoutSeconds: 30,
        MaxReceiveCount:          3,
        BatchSize:                10,
        WaitTimeSeconds:          5, // Long polling
    }
}

func (h *EmailQueueHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    log.Printf("Processing %d email messages", len(messages))

    var failedIDs []string

    for _, msg := range messages {
        var emailReq EmailRequest
        if err := json.Unmarshal(msg.Body(), &emailReq); err != nil {
            log.Printf("Failed to parse email request: %v", err)
            continue  // Skip malformed messages
        }

        if err := sendEmail(emailReq); err != nil {
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
    From    string `json:"from,omitempty"`
}
```

**Notification queue handler:**
```go
type NotificationQueueHandler struct{}

func (h *NotificationQueueHandler) QueueName() string {
    return "notification-queue"
}

func (h *NotificationQueueHandler) Config() transire.QueueConfig {
    return transire.QueueConfig{
        VisibilityTimeoutSeconds: 60,
        MaxReceiveCount:          5,
        BatchSize:                5,
    }
}

func (h *NotificationQueueHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    log.Printf("Processing %d notification messages", len(messages))

    var failedIDs []string

    for _, msg := range messages {
        var notificationReq NotificationRequest
        if err := json.Unmarshal(msg.Body(), &notificationReq); err != nil {
            log.Printf("Failed to parse notification: %v", err)
            continue
        }

        if err := sendNotification(notificationReq); err != nil {
            log.Printf("Failed to send notification: %v", err)
            failedIDs = append(failedIDs, msg.ID())
        } else {
            log.Printf("Successfully sent notification to %s", notificationReq.UserID)
        }
    }

    return failedIDs, nil
}

type NotificationRequest struct {
    UserID  string `json:"user_id"`
    Title   string `json:"title"`
    Message string `json:"message"`
    Type    string `json:"type"` // push, sms, slack
}
```

---

### Schedule Handler

**Daily cleanup scheduler:**
```go
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
        TimeoutSeconds: 300, // 5 minutes
        RetryAttempts:  3,
        RetryDelay:     30 * time.Second,
    }
}

func (h *CleanupHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Printf("Starting daily cleanup at %v", event.ScheduledTime)

    // Cleanup tasks
    if err := cleanupTempFiles(); err != nil {
        return fmt.Errorf("failed to cleanup temp files: %w", err)
    }

    if err := cleanupExpiredSessions(); err != nil {
        return fmt.Errorf("failed to cleanup expired sessions: %w", err)
    }

    if err := cleanupOldLogs(); err != nil {
        return fmt.Errorf("failed to cleanup old logs: %w", err)
    }

    log.Println("Daily cleanup completed successfully")
    return nil
}
```

---

## Running Locally

### Start the Application

```bash
cd examples/simple-api
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
[INFO] Ready! Watching for file changes...
```

---

### Test HTTP Endpoints

**Home endpoint:**
```bash
curl http://localhost:3000/
```

Response:
```json
{
  "message": "Welcome to Transire Simple API",
  "version": "2.0.0"
}
```

**Health check:**
```bash
curl http://localhost:3000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "transire-simple-api"
}
```

**Create user:**
```bash
curl -X POST http://localhost:3000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com"}'
```

Response:
```json
{
  "id": "generated-id",
  "name": "Alice",
  "email": "alice@example.com"
}
```

**Get user:**
```bash
curl http://localhost:3000/api/v1/users/123
```

---

### Test Queue Handlers

**Send email message:**
```bash
transire dev queues send email-queue '{
  "to": "user@example.com",
  "subject": "Welcome!",
  "body": "Welcome to Transire",
  "from": "no-reply@example.com"
}'
```

**Send notification message:**
```bash
transire dev queues send notification-queue '{
  "user_id": "user123",
  "title": "New Message",
  "message": "You have a new message",
  "type": "push"
}'
```

---

### Test Schedule Handler

**Trigger cleanup manually:**
```bash
transire dev schedules execute daily-cleanup
```

Output in console:
```
Starting daily cleanup at 2025-01-18 14:30:00
Cleaning up temporary files...
Cleaning up expired sessions...
Cleaning up old logs...
Daily cleanup completed successfully
```

---

## Deploying to AWS

### Build Artifacts

```bash
transire build
```

Output:
```
🔨 Building Transire application: simple-api
📦 Building artifacts for aws/lambda
🏗️  Generating infrastructure definitions
✅ Build completed successfully
```

### Deploy

```bash
transire deploy
```

**Deployed resources:**
- Lambda function with handler code
- API Gateway HTTP API
- 2 SQS queues (email-queue, notification-queue)
- 2 DLQs (one per queue)
- EventBridge rule for daily cleanup
- CloudWatch log groups
- IAM roles and policies

**Stack outputs:**
```
my-api-stack.ApiEndpoint = https://abc123.execute-api.us-east-1.amazonaws.com
```

---

## Testing in Production

**Test API Gateway:**
```bash
curl https://abc123.execute-api.us-east-1.amazonaws.com/health
```

**Send message to SQS:**
```bash
aws sqs send-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/email-queue \
  --message-body '{"to":"user@example.com","subject":"Test","body":"Hello"}'
```

**View logs:**
```bash
aws logs tail /aws/lambda/my-api-stack-MainFunction-ABC123 --follow
```

---

## Key Learnings

### 1. Standard Go Patterns

Transire uses familiar Go patterns:
- **Chi router** – No framework abstractions
- **`http.Handler`** – Standard interface
- **`context.Context`** – Request context
- **Interfaces** – Clean abstractions

### 2. Handler Registration

Three handler types:
- **HTTP** – Via Chi router
- **Queue** – Via `RegisterQueueHandler()`
- **Schedule** – Via `RegisterScheduleHandler()`

### 3. Local Development

Full local experience:
- **Hot reload** – Automatic rebuild on save
- **Queue simulator** – Test queue handlers locally
- **Schedule simulator** – Trigger schedules manually

### 4. Deployment

Single command deployment:
- **`transire build`** – Creates artifacts
- **`transire deploy`** – Deploys everything
- **Infrastructure as Code** – CDK generated automatically

---

## Next Steps

- **[Testing Guide](../guides/testing.md)** – Write tests for your handlers
- **[Queue Processing Patterns](../guides/queue-processing.md)** – Advanced queue patterns
- **[Multi-Function Architecture](../guides/multi-function-architecture.md)** – Split into multiple functions
- **[Custom CDK Extensions](../guides/custom-cdk.md)** – Add custom infrastructure

---

## See Also

- [Simple API Source Code](https://github.com/transire/transire/tree/main/examples/simple-api)
- [Todo App Example](todo-app.md)
- [API Reference](../api-reference/)
