---
title: Transire - Cloud-Native Go Framework
description: Build cloud-native apps with Go. Same code, anywhere. No serverless complexity.
hide:
  - navigation
  - toc
---

<style>
.hero-section {
  text-align: center;
  padding: 3rem 1rem;
  background: linear-gradient(135deg, rgba(76, 81, 191, 0.05), rgba(6, 182, 212, 0.05));
  border-radius: 12px;
  margin-bottom: 3rem;
}
.hero-section h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
}
.hero-section .tagline {
  font-size: 1.5rem;
  color: var(--md-primary-fg-color);
  font-weight: 600;
  margin-bottom: 1rem;
}
.hero-section .description {
  font-size: 1.125rem;
  max-width: 800px;
  margin: 0 auto 2rem;
  line-height: 1.6;
}
.hero-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 2rem;
}
@media screen and (max-width: 768px) {
  .hero-section h1 {
    font-size: 2rem;
  }
  .hero-section .tagline {
    font-size: 1.25rem;
  }
  .hero-section .description {
    font-size: 1rem;
  }
}
</style>

<div class="hero-section" markdown>

# Transire

<p class="tagline">Build cloud-native apps with Go. Same code, anywhere.</p>

<p class="description">
Transire is a cloud-native development framework that lets you write your application once and run it anywhere—locally or in the cloud. No serverless complexity. No infrastructure boilerplate. Just code.
</p>

<div class="hero-buttons">
<a href="getting-started/quickstart/" class="md-button md-button--primary">
  Get Started <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="width:1em;height:1em;display:inline-block;vertical-align:middle;"><path d="M4,11V13H16L10.5,18.5L11.92,19.92L19.84,12L11.92,4.08L10.5,5.5L16,11H4Z" fill="currentColor"/></svg>
</a>
<a href="https://github.com/transire/transire" class="md-button">
  View on GitHub <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="width:1em;height:1em;display:inline-block;vertical-align:middle;"><path d="M12,2A10,10 0 0,0 2,12C2,16.42 4.87,20.17 8.84,21.5C9.34,21.58 9.5,21.27 9.5,21C9.5,20.77 9.5,20.14 9.5,19.31C6.73,19.91 6.14,17.97 6.14,17.97C5.68,16.81 5.03,16.5 5.03,16.5C4.12,15.88 5.1,15.9 5.1,15.9C6.1,15.97 6.63,16.93 6.63,16.93C7.5,18.45 8.97,18 9.54,17.76C9.63,17.11 9.89,16.67 10.17,16.42C7.95,16.17 5.62,15.31 5.62,11.5C5.62,10.39 6,9.5 6.65,8.79C6.55,8.54 6.2,7.5 6.75,6.15C6.75,6.15 7.59,5.88 9.5,7.17C10.29,6.95 11.15,6.84 12,6.84C12.85,6.84 13.71,6.95 14.5,7.17C16.41,5.88 17.25,6.15 17.25,6.15C17.8,7.5 17.45,8.54 17.35,8.79C18,9.5 18.38,10.39 18.38,11.5C18.38,15.32 16.04,16.16 13.81,16.41C14.17,16.72 14.5,17.33 14.5,18.26C14.5,19.6 14.5,20.68 14.5,21C14.5,21.27 14.66,21.59 15.17,21.5C19.14,20.16 22,16.42 22,12A10,10 0 0,0 12,2Z" fill="currentColor"/></svg>
</a>
</div>

</div>

```go
package main

import (
    "context"
    "github.com/transire/sdk-go"
)

func main() {
    app := transire.New()

    // HTTP endpoint
    app.GET("/orders/{id}", getOrder)

    // Queue handler - type-safe batch processing
    app.RegisterQueue("process-orders", processOrders)

    // Scheduled job - runs daily at 9 AM
    app.Schedule("daily-report", "@daily 09:00", generateReport)

    app.Run()
}
```

!!! success "One Command Deployment"
    ```bash
    $ transire deploy
    ✓ Deployed to AWS
    → API URL: https://api.example.com
    ```

---

## Choose Your Journey

<div class="grid cards" markdown>

-   :rocket:{ .lg .middle } **I'm new here**

    ---

    Get started in 5 minutes

    Build and deploy your first Transire app with a guided quick start.

    _Perfect for: First-time users • Time: 5-15 min_

    [:octicons-arrow-right-24: Get Started](learn/tutorials/01-hello-world/)

-   :books:{ .lg .middle } **I want to learn deeply**

    ---

    Follow structured learning paths

    Master Transire through progressive tutorials from beginner to advanced.

    _Perfect for: Developers building expertise • Time: 2-8 hours_

    [:octicons-arrow-right-24: Start Learning](learn/curriculum/beginner-path/)

-   :mag:{ .lg .middle } **I need specific info**

    ---

    Jump to API reference

    Quick lookup for specific APIs, CLI commands, or configuration options.

    _Perfect for: Experienced users • Time: Instant_

    [:octicons-arrow-right-24: API Reference](reference/sdk/overview/)

-   :wrench:{ .lg .middle } **I have a problem**

    ---

    Troubleshoot your issue

    Diagnostic decision trees and solutions for common problems.

    _Perfect for: Debugging • Time: 5-20 min_

    [:octicons-arrow-right-24: Get Help](guides/troubleshooting/)

</div>

---

## Why Developers Love Transire

<div class="grid cards" markdown>

-   :material-code-braces:{ .lg .middle } **Zero Boilerplate**

    ---

    Write business logic, not infrastructure code. Focus on what matters.

    ```go
    // That's it. Really.
    app.GET("/orders", listOrders)
    ```

-   :material-cloud-sync:{ .lg .middle } **Same Code, Anywhere**

    ---

    Develop locally, deploy to cloud. Zero code changes.

    ```bash
    transire run      # Local
    transire deploy   # Cloud
    ```

-   :material-shield-check:{ .lg .middle } **Type-Safe Queues**

    ---

    Strongly-typed message queues with automatic serialization.

    ```go
    app.RegisterQueue("orders", func(ctx context.Context, orders []Order) error {
        // Type-safe batch processing
        return nil
    })
    ```

-   :material-rocket-launch-outline:{ .lg .middle } **Production Ready**

    ---

    Built-in observability, error handling, graceful shutdown, and least-privilege IAM.

    ```go
    // All included out of the box
    ✓ Structured logging
    ✓ Distributed tracing
    ✓ Dead-letter queues
    ✓ Partial batch failures
    ```

</div>

---

## Quick Links by Role

=== "First Time User"

    **Your journey:** Learn → Build → Deploy

    1. [What is Transire?](intro/what-is-transire.md) · 10 min
    2. [Hello World Tutorial](learn/tutorials/01-hello-world/) · 5 min
    3. [Quick Start Guide](getting-started/quickstart.md) · 15 min

    **Next:** [Start Learning →](learn/curriculum/beginner-path/)

=== "Building an App"

    **Your toolkit:** Tutorials → Guides → Examples

    - [REST API Tutorial](learn/tutorials/02-rest-api/) · 15 min
    - [Queue Processing Tutorial](learn/tutorials/03-queue-processing/) · 20 min
    - [Complete Examples](examples/) · Ready to use

    **Next:** [View All Tutorials →](learn/tutorials/)

=== "Deploying to Production"

    **Your checklist:** Setup → Deploy → Monitor

    1. [Production Checklist](guides/deployment/production-checklist/)
    2. [CI/CD Setup](guides/deployment/ci-cd-setup/)
    3. [Troubleshooting Guide](guides/troubleshooting/)

    **Next:** [Deployment Guide →](guides/deployment/first-deployment/)

=== "Looking Up Syntax"

    **Quick reference:** API → CLI → Config

    - [SDK API Reference](reference/sdk/overview/)
    - [CLI Commands](reference/cli/overview/)
    - [Config Schema](reference/config/schema/)
    - [Error Codes](reference/error-codes/)

    **Next:** [All References →](reference/)

---

## Popular Topics

| Topic | Description | Time |
|-------|-------------|------|
| [Quick Start](getting-started/quickstart.md) | Build and deploy your first app | 15 min |
| [HTTP Handlers](reference/sdk/http-api/) | RESTful APIs with routing | 20 min |
| [Queue Processing](reference/sdk/queue-api/) | Async message handling | 25 min |
| [Dependency Injection](reference/sdk/di-api/) | Service management | 20 min |
| [Testing](guides/development/testing-strategies/) | Test your application | 30 min |
| [AWS Deployment](plugins/cloud/aws/) | Deploy to AWS Lambda | 15 min |

---

## Features at a Glance

| Feature | Local Dev | Cloud Deployment |
|---------|-----------|------------------|
| **HTTP Handlers** | Chi HTTP server on `:8080` | API Gateway v2 → Lambda |
| **Queue Handlers** | In-memory queue emulator | SQS → Lambda (batch) |
| **Scheduled Jobs** | Fixed-rate scheduler | EventBridge → Lambda |
| **Hot Reload** | `--watch` flag | N/A |
| **Database** | Your choice (Postgres, MySQL, etc.) | RDS, DynamoDB, etc. |
| **Observability** | Structured logs to stdout | CloudWatch Logs + X-Ray |

---

## Philosophy

Transire is built on five core principles:

1. **Developer Experience First** - Minimal API surface, intuitive patterns, fast feedback loops
2. **Zero Magic** - No runtime reflection, explicit registration, clear behavior
3. **Build-Time Analysis** - Static analysis using Go AST for manifest generation
4. **Production Ready** - Observability, error handling, and graceful shutdown built-in
5. **Cloud-Agnostic** - Write once, deploy anywhere with pluggable providers

---

## Community

<div class="grid cards" markdown>

-   :fontawesome-brands-github:{ .lg } **GitHub**

    ---

    Source code, issues, and contributions

    [:octicons-arrow-right-24: transire/transire](https://github.com/transire/transire)

-   :material-forum:{ .lg } **Discussions**

    ---

    Ask questions, share projects

    [:octicons-arrow-right-24: GitHub Discussions](https://github.com/transire/transire/discussions)

-   :material-frequently-asked-questions:{ .lg } **FAQ**

    ---

    Common questions and answers

    [:octicons-arrow-right-24: Read FAQ](community/faq/)

-   :material-hand-heart:{ .lg } **Contributing**

    ---

    Help improve Transire

    [:octicons-arrow-right-24: Contributing Guide](community/contributing/)

</div>

---

## Ready to Start?

<div class="grid" markdown>

<div markdown>

**New to Transire?**

Start with the 5-minute hello world tutorial:

[Hello World Tutorial →](learn/tutorials/01-hello-world/){ .md-button .md-button--primary }

</div>

<div markdown>

**Ready to build?**

Jump into the comprehensive quick start:

[Quick Start Guide →](getting-started/quickstart/){ .md-button }

</div>

</div>

---

<p style="text-align: center; color: var(--md-default-fg-color--light); margin-top: 3rem;">
Built with ❤️ for developers who want to focus on code, not infrastructure.
</p>
