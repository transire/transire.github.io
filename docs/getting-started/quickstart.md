# Quickstart

Get your first Transire API running locally in under 5 minutes.

!!! tip "TL;DR"
    Install Transire CLI → Create a project → Run locally with hot reload. That's it!

---

## Prerequisites

- **Go 1.21 or higher** – Verify with `go version`
- Basic familiarity with Go and `http.Handler`

---

## 1. Install the Transire CLI

```bash
go install github.com/transire/transire/cmd/transire@latest
```

Verify installation:

```bash
transire --version
```

You should see output like: `transire version v0.1.0`

---

## 2. Create a New Project

```bash
transire init my-api
cd my-api
```

This generates:

- **`main.go`** – Your application entry point
- **`transire.yaml`** – Configuration file
- **`go.mod`** – Go module with Transire dependency

!!! note "Development Note"
    If you're developing before the first Transire release is published to GitHub, you'll need to add a replace directive to your `go.mod`:
    ```go
    replace github.com/transire/transire => /path/to/local/transire
    ```
    This will not be needed once Transire v0.1.0 is released.

---

## 3. Explore the Generated Code

Open `main.go` to see your application:

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
    })

    // Register queue and schedule handlers
    app.RegisterQueueHandler(&EmailQueueHandler{})
    app.RegisterScheduleHandler(&CleanupHandler{})

    // Run the app (works locally and in Lambda)
    if err := app.Run(context.Background()); err != nil {
        panic(err)
    }
}

func homeHandler(w http.ResponseWriter, r *http.Request) {
    response := map[string]string{
        "message": "Welcome to Transire!",
        "version": "1.0.0",
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("OK"))
}
```

### What's happening here?

- **`transire.New()`** creates the app ([`pkg/transire/app.go:New`](https://github.com/transire/transire/blob/main/pkg/transire/app.go))
- **`app.Router()`** returns a standard Chi router ([`pkg/transire/app.go:Router`](https://github.com/transire/transire/blob/main/pkg/transire/app.go))
- **HTTP routes** use standard `http.HandlerFunc` – no special interfaces required
- **`app.Run(context.Background())`** auto-detects runtime (local vs Lambda) and handles everything ([`pkg/transire/app.go:Run`](https://github.com/transire/transire/blob/main/pkg/transire/app.go))

---

## 4. Run Locally with Hot Reload

```bash
transire run
```

Expected output:

```
[INFO] Transire starting in local mode
[INFO] Discovered handlers:
[INFO]   HTTP: 4 routes
[INFO]   Queues: 1 handler (email-queue)
[INFO]   Schedules: 1 handler (daily-cleanup)
[INFO] Starting HTTP server on :3000
[INFO] Starting queue simulator on :4000
[INFO] Ready! Watching for file changes...
```

Visit [http://localhost:3000](http://localhost:3000) – you'll see:

```json
{
  "message": "Welcome to Transire!",
  "version": "1.0.0"
}
```

### Try hot reload

1. Open `main.go`
2. Change the `message` field to something else
3. Save the file
4. Refresh your browser – the change appears instantly!

Hot reload is implemented via `internal/cli/runner/` using [`github.com/fsnotify/fsnotify`](https://github.com/fsnotify/fsnotify).

---

## 5. Test Queue and Schedule Handlers (Optional)

The generated project includes example queue and schedule handlers.

### Send a test message to a queue

```bash
transire dev queues send email-queue '{"to":"test@example.com","subject":"Hello","body":"World"}'
```

Your `EmailQueueHandler.HandleMessages()` method will be called.

### Trigger a scheduled task

```bash
transire dev schedules execute daily-cleanup
```

Your `CleanupHandler.HandleSchedule()` method will execute immediately.

Queue and schedule simulation: [`pkg/transire/local_runtime.go`](https://github.com/transire/transire/blob/main/pkg/transire/local_runtime.go)

---

## 6. What's Next?

Congratulations! You've created and run your first Transire application. Here's what to explore next:

### Deploy to AWS Lambda

Ready to deploy to production?

[:octicons-arrow-right-24: Deploying to AWS](../guides/deploying-to-aws.md)

### Understand How It Works

Learn about the App abstraction and runtime detection:

[:octicons-arrow-right-24: Application & Runtime](../core-concepts/application-runtime.md)

### Process Messages with Queues

Deep-dive into queue handler patterns:

[:octicons-arrow-right-24: Queue Handlers](../core-concepts/queue-handlers.md)

### Customize Configuration

Learn all the options in `transire.yaml`:

[:octicons-arrow-right-24: Configuration Reference](../configuration/transire-yaml.md)

---

## Troubleshooting

### Port already in use

**Error:**
```
Error: failed to start HTTP server: listen tcp :3000: bind: address already in use
```

**Solution:**
Change the port in `transire.yaml`:

```yaml
development:
  http_port: 8080  # Use a different port
  queue_port: 8081
```

### Build errors

If Transire shows build errors, fix them in your code and save – hot reload will retry automatically.

### "transire: command not found"

Ensure `$GOPATH/bin` is in your `$PATH`:

```bash
export PATH=$PATH:$(go env GOPATH)/bin
```

Add this to your `~/.bashrc` or `~/.zshrc` to make it permanent.

---

## Next Steps

<div class="grid cards" markdown>

-   :material-cloud-upload:{ .lg .middle } __Deploy to AWS__

    ---

    Get your app running on Lambda with API Gateway, SQS, and EventBridge.

    [:octicons-arrow-right-24: Deployment Guide](../guides/deploying-to-aws.md)

-   :material-cog:{ .lg .middle } __Configure Your App__

    ---

    Learn all the options available in `transire.yaml`.

    [:octicons-arrow-right-24: Configuration](../configuration/transire-yaml.md)

-   :material-test-tube:{ .lg .middle } __Test Your Application__

    ---

    Write unit, integration, and E2E tests for your Transire app.

    [:octicons-arrow-right-24: Testing Guide](../guides/testing.md)

-   :material-code-braces:{ .lg .middle } __Browse Examples__

    ---

    Explore complete example applications with real-world patterns.

    [:octicons-arrow-right-24: Examples](../examples/simple-api.md)

</div>
