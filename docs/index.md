# Transire

## Cloud-Agnostic Go Framework for Building Production APIs

Write standard Go applications with Chi routing that run seamlessly across local development and cloud platforms. Zero boilerplate, no framework lock-in, just Go.

[Get Started in 5 Minutes](getting-started/quickstart.md){ .md-button .md-button--primary } [View on GitHub](https://github.com/transire/transire){ .md-button } [See Examples](examples/simple-api.md){ .md-button }

---

## Why Transire for Go Developers?

### Use What You Already Know

- ✅ **Chi router** – standard `chi.Router` and `http.Handler`
- ✅ **Standard library patterns** – `context.Context`, familiar Go idioms
- ✅ **No proprietary abstractions** – Just pure Go code

### Local Dev That Actually Works

- ✅ **Hot reload** with file watching (via fsnotify)
- ✅ **Simulated queues and schedules** for testing
- ✅ **Instant feedback loop** – see changes immediately

### Deploy to AWS Lambda (More Clouds Coming)

- ✅ **Same code runs locally and on Lambda** – no changes needed
- ✅ **Auto-generated CDK infrastructure** – zero config to deploy
- ✅ **Zero config to deploy** – just `transire deploy`

### Production Features

- ✅ **Queue handlers** (SQS integration)
- ✅ **Scheduled tasks** (EventBridge integration)
- ✅ **Multi-function architecture** for resource optimization
- ✅ **VPC support** for private network access

---

## Quick Example

Here's a complete Transire application (from `examples/simple-api/main.go`):

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

    // Standard Chi routes
    r.Get("/", homeHandler)
    r.Get("/health", healthHandler)

    r.Route("/api/v1", func(r chi.Router) {
        r.Post("/users", createUserHandler)
        r.Get("/users/{id}", getUserHandler)
    })

    // Add background handlers
    app.RegisterQueueHandler(&EmailQueueHandler{})
    app.RegisterScheduleHandler(&DailyCleanupHandler{})

    // Run the app (works locally AND on Lambda)
    app.Run(context.Background())
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

**What's happening here:**

- `transire.New()` creates the app
- `app.Router()` returns a standard Chi router – use it exactly like you normally would
- HTTP routes use standard `http.HandlerFunc` – no special interfaces
- `app.Run()` auto-detects runtime (local vs Lambda) and handles everything
- Background handlers (queues, schedules) are registered with simple interfaces

---

## How It Works

Transire provides a thin abstraction layer that:

1. **Locally**: Runs a full HTTP server with hot reload and simulated cloud services
2. **In AWS Lambda**: Adapts Lambda events (API Gateway, SQS, EventBridge) to your handlers
3. **Zero code changes**: Same `app.Run()` call works everywhere

The framework uses proven Go libraries:

- [Chi](https://github.com/go-chi/chi) for HTTP routing
- [Cobra](https://github.com/spf13/cobra) for CLI
- [AWS CDK](https://aws.amazon.com/cdk/) for infrastructure

**Philosophy:** Stand on the shoulders of giants. We use proven tools instead of reinventing the wheel.

---

## Next Steps

<div class="grid cards" markdown>

-   :material-clock-fast:{ .lg .middle } __Get Started in 5 Minutes__

    ---

    Install Transire, create your first app, and run it locally with hot reload.

    [:octicons-arrow-right-24: Quickstart](getting-started/quickstart.md)

-   :material-lightbulb:{ .lg .middle } __Understand Core Concepts__

    ---

    Learn how Transire's App, Runtime, and Handler abstractions work.

    [:octicons-arrow-right-24: Core Concepts](core-concepts/application-runtime.md)

-   :material-book-open-variant:{ .lg .middle } __Browse Guides__

    ---

    Deep-dive tutorials on local development, testing, deployment, and more.

    [:octicons-arrow-right-24: Guides](guides/local-development.md)

-   :material-code-braces:{ .lg .middle } __Explore Examples__

    ---

    Complete example applications you can run and learn from.

    [:octicons-arrow-right-24: Examples](examples/simple-api.md)

</div>

---

## Requirements

- **Go:** 1.21 or higher
- **Node.js:** 18+ (for CDK deployment)
- **AWS CLI:** Configured with credentials (for deployment)

---

## Community & Support

- **GitHub:** [transire/transire](https://github.com/transire/transire)
- **Issues:** [Report bugs or request features](https://github.com/transire/transire/issues)
- **Discussions:** [Ask questions and share ideas](https://github.com/transire/transire/discussions)

---

## License

Transire is open source under the [MIT License](https://github.com/transire/transire/blob/main/LICENSE).

---

**Ready to build?** Start with the [5-minute quickstart →](getting-started/quickstart.md)
