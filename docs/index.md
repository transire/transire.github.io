---
title: Transire - Cloud-Native Go Framework
description: Build cloud-native apps with Go. Same code, anywhere. No serverless complexity.
hide:
  - navigation
  - toc
---

<style>
.journey-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}
.journey-card {
  background: var(--md-code-bg-color);
  border: 2px solid var(--md-default-fg-color--lightest);
  border-radius: 8px;
  padding: 1.5rem;
  transition: all 0.2s;
  cursor: pointer;
}
.journey-card:hover {
  border-color: var(--md-primary-fg-color);
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.journey-card h3 {
  margin-top: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.journey-card p {
  margin-bottom: 0.5rem;
}
.journey-meta {
  font-size: 0.85em;
  color: var(--md-default-fg-color--light);
}
</style>

# Transire

**Build cloud-native apps with Go. Same code, anywhere.**

Transire is a cloud-native development framework that lets you write your application once and run it anywhere—locally or in the cloud. No serverless complexity. No infrastructure boilerplate. Just code.

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

Deploy to AWS with one command:

```bash
$ transire deploy
✓ Deployed to AWS
→ API URL: https://api.example.com
```

---

## Choose Your Journey

<div class="journey-cards" markdown>

<a href="learn/tutorials/01-hello-world/" class="journey-card" markdown>

### 🚀 I'm new here

**Get started in 5 minutes**

Build and deploy your first Transire app with a guided quick start.

<span class="journey-meta">Perfect for: First-time users • Time: 5-15 min</span>

</a>

<a href="learn/curriculum/beginner-path/" class="journey-card" markdown>

### 📚 I want to learn deeply

**Follow structured learning paths**

Master Transire through progressive tutorials from beginner to advanced.

<span class="journey-meta">Perfect for: Developers building expertise • Time: 2-8 hours</span>

</a>

<a href="reference/sdk/overview/" class="journey-card" markdown>

### 🔍 I need specific info

**Jump to API reference**

Quick lookup for specific APIs, CLI commands, or configuration options.

<span class="journey-meta">Perfect for: Experienced users • Time: Instant</span>

</a>

<a href="guides/troubleshooting/" class="journey-card" markdown>

### 🔧 I have a problem

**Troubleshoot your issue**

Diagnostic decision trees and solutions for common problems.

<span class="journey-meta">Perfect for: Debugging • Time: 5-20 min</span>

</a>

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

-   :material-safety-check:{ .lg .middle } **Type-Safe Queues**

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

    1. [What is Transire?](learn/introduction/what-is-transire.md) · 10 min
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
