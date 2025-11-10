---
title: "SDK Overview"
category: sdk
subcategory: null
complexity: beginner
duration: null
prerequisites:
  - Go 1.22+
mcp_use: reference
features_covered:
  - SDK architecture
  - Handler types
  - Development workflow
code_blocks: false
last_updated: 2025-10-31
---

# SDK Overview

## Introduction

The Transire SDK for Go provides a developer-friendly API for building cloud-native applications that run seamlessly in both local development and cloud environments.

## Core Concepts

The SDK is built around three main handler types:

1. **HTTP Handlers** - Handle synchronous HTTP requests
2. **Queue Handlers** - Process asynchronous messages from queues
3. **Scheduled Handlers** - Execute code on fixed schedules

## Key Features

- **Zero boilerplate** - Minimal, intuitive API
- **Standard Go HTTP** - Uses `http.HandlerFunc` for HTTP handlers
- **Type-safe queues** - Generic types for queue message handling
- **Dependency injection** - Built-in DI system for managing dependencies
- **Middleware support** - Standard Go middleware patterns
- **Local development** - Run everything locally with emulated services
- **Testing utilities** - Comprehensive test kit for unit and integration tests

## Getting Started

To start using the SDK:

```go
package main

import "github.com/transire/sdk-go"

func main() {
    app := transire.New()

    // Register your handlers
    app.GET("/hello", helloHandler)
    app.RegisterQueue("orders", processOrder)
    app.RegisterScheduled("@daily", dailyJob)

    app.Run()
}
```

## Documentation Structure

- [HTTP Handlers](/docs/sdk/http.md) - Synchronous HTTP request handling
- [Queue Handlers](/docs/sdk/queue.md) - Asynchronous message processing
- [Scheduled Handlers](/docs/sdk/schedule.md) - Cron-based task execution
- [Dependency Injection](/docs/sdk/di.md) - Managing service dependencies
- [Middleware](/docs/sdk/middleware.md) - Request/response middleware
- [Error Handling](/docs/sdk/errors.md) - Error handling patterns
- [Testing](/docs/sdk/testkit.md) - Testing your application

## Next Steps

Start with the [Quickstart Guide](/docs/getting-started/quickstart.md) to build your first Transire application, or dive into specific handler types:

- Build a REST API with [HTTP Handlers](/docs/sdk/http.md)
- Process messages with [Queue Handlers](/docs/sdk/queue.md)
- Schedule tasks with [Scheduled Handlers](/docs/sdk/schedule.md)
