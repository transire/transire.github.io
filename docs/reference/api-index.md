---
title: "API Index"
description: "Complete reference of all Transire SDK functions and CLI commands"
category: reference
subcategory: null
complexity: beginner
duration: null
prerequisites: []
mcp_use: reference
api_surface: true
keywords:
  - API
  - SDK
  - CLI
  - reference
  - functions
  - commands
  - methods
code_blocks: false
last_updated: 2025-11-10
---

# API Index

Complete alphabetical reference of all Transire SDK functions, types, and CLI commands. This page is optimized for quick lookups and MCP (Model Context Protocol) indexing.

## SDK API Reference

### App Methods

| Function | Description | Link |
|----------|-------------|------|
| `transire.New()` | Creates a new Transire application instance | [SDK Overview](/sdk/overview.md) |
| `app.Config()` | Returns the application configuration | [SDK Overview](/sdk/overview.md) |
| `app.DELETE(pattern, handler)` | Registers a DELETE HTTP route | [HTTP Reference](/sdk/http.md) |
| `app.Enqueue(ctx, queueName, message)` | Enqueues a single message | [Queue Reference](/sdk/queue.md) |
| `app.EnqueueBatch(ctx, queueName, messages)` | Enqueues multiple messages efficiently | [Queue Reference](/sdk/queue.md) |
| `app.GET(pattern, handler)` | Registers a GET HTTP route | [HTTP Reference](/sdk/http.md) |
| `app.HEAD(pattern, handler)` | Registers a HEAD HTTP route | [HTTP Reference](/sdk/http.md) |
| `app.OPTIONS(pattern, handler)` | Registers an OPTIONS HTTP route | [HTTP Reference](/sdk/http.md) |
| `app.PATCH(pattern, handler)` | Registers a PATCH HTTP route | [HTTP Reference](/sdk/http.md) |
| `app.POST(pattern, handler)` | Registers a POST HTTP route | [HTTP Reference](/sdk/http.md) |
| `app.PUT(pattern, handler)` | Registers a PUT HTTP route | [HTTP Reference](/sdk/http.md) |
| `app.RegisterQueue(queueName, handler)` | Registers a queue message handler | [Queue Reference](/sdk/queue.md) |
| `app.RegisterScheduled(schedule, handler)` | Registers a scheduled job | [Schedule Reference](/sdk/schedule.md) |
| `app.Run()` | Starts the application (blocks) | [SDK Overview](/sdk/overview.md) |
| `app.SetConfig(config)` | Sets the application configuration | [SDK Overview](/sdk/overview.md) |
| `app.Use(middleware...)` | Adds global middleware | [Middleware Reference](/sdk/middleware.md) |

### Dependency Injection

| Function | Description | Link |
|----------|-------------|------|
| `GetDep[T](ctx)` | Retrieves a dependency with error handling | [DI Reference](/sdk/di.md) |
| `MustGetDep[T](ctx)` | Retrieves a dependency or panics if not found | [DI Reference](/sdk/di.md) |
| `Provide(provider)` | Registers a singleton dependency provider | [DI Reference](/sdk/di.md) |
| `ProvideRequest(provider)` | Registers a request-scoped dependency provider | [DI Reference](/sdk/di.md) |

### Response Helpers

| Function | Description | Link |
|----------|-------------|------|
| `response.Accepted(w, data)` | Returns 202 Accepted with JSON body | [HTTP API](/reference/sdk/http-api.md) |
| `response.BadRequest(w, message)` | Returns 400 Bad Request with error message | [HTTP API](/reference/sdk/http-api.md) |
| `response.Bytes(w, status, contentType, data)` | Returns raw bytes with custom content type | [HTTP API](/reference/sdk/http-api.md) |
| `response.Created(w, data)` | Returns 201 Created with JSON body | [HTTP API](/reference/sdk/http-api.md) |
| `response.Forbidden(w, message)` | Returns 403 Forbidden with error message | [HTTP API](/reference/sdk/http-api.md) |
| `response.HTML(w, status, html)` | Returns HTML response | [HTTP API](/reference/sdk/http-api.md) |
| `response.JSON(w, status, data)` | Returns JSON response with custom status code | [HTTP API](/reference/sdk/http-api.md) |
| `response.NoContent(w)` | Returns 204 No Content (empty body) | [HTTP API](/reference/sdk/http-api.md) |
| `response.NotFound(w, message)` | Returns 404 Not Found with error message | [HTTP API](/reference/sdk/http-api.md) |
| `response.OK(w, data)` | Returns 200 OK with JSON body | [HTTP API](/reference/sdk/http-api.md) |
| `response.Redirect(w, r, url, code)` | Returns HTTP redirect response | [HTTP API](/reference/sdk/http-api.md) |
| `response.Text(w, status, text)` | Returns plain text response | [HTTP API](/reference/sdk/http-api.md) |
| `response.Unauthorized(w, message)` | Returns 401 Unauthorized with error message | [HTTP API](/reference/sdk/http-api.md) |
| `response.WriteError(w, status, message)` | Returns error response with custom status | [HTTP API](/reference/sdk/http-api.md) |

### Request Helpers

| Function | Description | Link |
|----------|-------------|------|
| `FormValue(r, key)` | Gets form value from multipart or urlencoded form | [HTTP API](/reference/sdk/http-api.md) |
| `Header(r, key)` | Gets HTTP header value | [HTTP API](/reference/sdk/http-api.md) |
| `PostFormValue(r, key)` | Gets POST form value only | [HTTP API](/reference/sdk/http-api.md) |
| `QueryParam(r, key)` | Gets single query parameter value | [HTTP API](/reference/sdk/http-api.md) |
| `QueryParamInt(r, key, defaultVal)` | Gets query parameter as integer | [HTTP API](/reference/sdk/http-api.md) |
| `QueryParamInt64(r, key, defaultVal)` | Gets query parameter as int64 | [HTTP API](/reference/sdk/http-api.md) |
| `QueryParams(r, key)` | Gets all values for multi-value query parameter | [HTTP API](/reference/sdk/http-api.md) |
| `URLParam(r, key)` | Gets URL path parameter (e.g., `/orders/{id}`) | [HTTP API](/reference/sdk/http-api.md) |
| `URLParamInt(r, key)` | Gets URL path parameter as integer | [HTTP API](/reference/sdk/http-api.md) |
| `URLParamInt64(r, key)` | Gets URL path parameter as int64 | [HTTP API](/reference/sdk/http-api.md) |

### Error Handling

| Function/Type | Description | Link |
|---------------|-------------|------|
| `ErrBadRequest(message)` | Creates a 400 Bad Request error | [Error Handling](/sdk/errors.md) |
| `ErrForbidden(message)` | Creates a 403 Forbidden error | [Error Handling](/sdk/errors.md) |
| `ErrInternal(message)` | Creates a 500 Internal Server Error | [Error Handling](/sdk/errors.md) |
| `ErrNotFound(message)` | Creates a 404 Not Found error | [Error Handling](/sdk/errors.md) |
| `ErrUnauthorized(message)` | Creates a 401 Unauthorized error | [Error Handling](/sdk/errors.md) |
| `HTTPError` | Error type with HTTP status code | [Error Handling](/sdk/errors.md) |
| `NewBatchResult(size)` | Creates a new batch result for partial failures | [Queue API](/reference/sdk/queue-api.md) |
| `NewTransireError(message)` | Creates a framework error | [Error Handling](/sdk/errors.md) |
| `TransireError` | Framework-level error type | [Error Handling](/sdk/errors.md) |

### Handler Types

| Type | Description | Link |
|------|-------------|------|
| `QueueHandler[T any]` | Queue message handler type: `func(ctx context.Context, msgs []T) error` | [Queue API](/reference/sdk/queue-api.md) |
| `ScheduledHandler` | Scheduled job handler type: `func(ctx context.Context) error` | [Schedule API](/reference/sdk/schedule-api.md) |

### Testkit Utilities

| Function | Description | Link |
|----------|-------------|------|
| `testkit.AddQueryParam(req, key, value)` | Adds query parameter to test request | [Test Kit](/sdk/testkit.md) |
| `testkit.AssertResponse(t, w)` | Creates response assertion helper | [Test Kit](/sdk/testkit.md) |
| `testkit.NewJSONRequest(method, target, body)` | Creates HTTP request with JSON body | [Test Kit](/sdk/testkit.md) |
| `testkit.NewRecorder()` | Creates HTTP response recorder | [Test Kit](/sdk/testkit.md) |
| `testkit.NewRequest(method, target, body)` | Creates HTTP request for testing | [Test Kit](/sdk/testkit.md) |
| `testkit.SetQueryParam(req, key, value)` | Sets query parameter on test request | [Test Kit](/sdk/testkit.md) |
| `testkit.SetupTest(t)` | Performs common test setup | [Test Kit](/sdk/testkit.md) |
| `testkit.SetURLParam(req, key, value)` | Sets URL path parameter on test request | [Test Kit](/sdk/testkit.md) |

---

## CLI Command Reference

### Core Commands

| Command | Description | Link |
|---------|-------------|------|
| `transire deploy` | Deploys application to cloud via OpenTofu | [Deploy Command](/cli/deploy.md) |
| `transire gen` | Generates manifest from Go code using AST analysis | [Gen Command](/cli/gen.md) |
| `transire init --backend` | Bootstraps cloud backend for Tofu state | [Init Command](/cli/init.md) |
| `transire run` | Starts local development server | [Run Command](/cli/run.md) |
| `transire version` | Displays CLI version information | [CLI Overview](/cli/overview.md) |

### Command Options

#### `transire run` Options

| Option | Description | Link |
|--------|-------------|------|
| `--log-level` | Set log level (debug, info, warn, error) | [Run Command](/cli/run.md) |
| `--no-color` | Disable colored output | [Run Command](/cli/run.md) |
| `--port` | HTTP server port (default: 8080) | [Run Command](/cli/run.md) |
| `--queue-workers` | Number of workers per queue (default: 1) | [Run Command](/cli/run.md) |
| `--watch` | 🔮 Hot reload mode (Coming in v1.1) | [Run Command](/cli/run.md) |

#### `transire deploy` Options

| Option | Description | Link |
|--------|-------------|------|
| `--env` | Target environment (dev, staging, prod) | [Deploy Command](/cli/deploy.md) |
| `--workspace` | OpenTofu workspace name | [Deploy Command](/cli/deploy.md) |

#### `transire gen` Options

| Option | Description | Link |
|--------|-------------|------|
| `--output` | Output file path (default: transire_manifest.json) | [Gen Command](/cli/gen.md) |
| `--validate` | Validate generated manifest | [Gen Command](/cli/gen.md) |

---

## Configuration Schema

### Top-Level Keys

| Key | Description | Link |
|-----|-------------|------|
| `ci` | CI/CD provider configuration | [Config Schema](/reference/config-schema.md) |
| `cloud` | Cloud provider selection (aws, azure, gcp) | [Config Schema](/reference/config-schema.md) |
| `deploy` | Deployment configuration (memory, timeout, architecture) | [Config Schema](/reference/config-schema.md) |
| `env` | Environment-specific configurations | [Config Schema](/reference/config-schema.md) |
| `http` | HTTP server configuration | [Config Schema](/reference/config-schema.md) |
| `iac` | Infrastructure-as-Code provider (opentofu, terraform) | [Config Schema](/reference/config-schema.md) |
| `infra` | Infrastructure backend configuration | [Config Schema](/reference/config-schema.md) |
| `observability` | Logging, tracing, and metrics configuration | [Config Schema](/reference/config-schema.md) |
| `queues` | Queue processing configuration | [Config Schema](/reference/config-schema.md) |
| `runtime` | Programming language runtime (go) | [Config Schema](/reference/config-schema.md) |
| `service` | Service name | [Config Schema](/reference/config-schema.md) |
| `timezone` | Default timezone for scheduled jobs | [Config Schema](/reference/config-schema.md) |

---

## Schedule Expression Syntax

| Expression | Description | Link |
|------------|-------------|------|
| `@daily` | Runs once per day at midnight | [Schedule Reference](/sdk/schedule.md) |
| `@daily HH:MM` | Runs daily at specific time (e.g., `@daily 09:00`) | [Schedule Reference](/sdk/schedule.md) |
| `@hourly` | Runs once per hour at minute 0 | [Schedule Reference](/sdk/schedule.md) |
| `@weekly` | Runs once per week on Sunday at midnight | [Schedule Reference](/sdk/schedule.md) |
| `cron(...)` | AWS EventBridge cron expression | [Schedule Reference](/sdk/schedule.md) |
| `rate(N units)` | AWS EventBridge rate expression | [Schedule Reference](/sdk/schedule.md) |

---

## Middleware Types

| Pattern | Description | Link |
|---------|-------------|------|
| `func(http.Handler) http.Handler` | Standard Go middleware signature | [Middleware Reference](/sdk/middleware.md) |
| Global middleware | Applied to all routes via `app.Use()` | [Middleware Reference](/sdk/middleware.md) |
| Route-specific middleware | Applied to specific routes | [Middleware Reference](/sdk/middleware.md) |

---

## HTTP Handler Signatures

| Signature | Description | Link |
|-----------|-------------|------|
| `func(w http.ResponseWriter, r *http.Request)` | Standard Go HTTP handler | [HTTP Reference](/sdk/http.md) |

---

## Queue Handler Signatures

| Signature | Description | Link |
|-----------|-------------|------|
| `func(ctx context.Context, msgs []T) error` | Batch message handler | [Queue API](/reference/sdk/queue-api.md) |

---

## Scheduled Handler Signatures

| Signature | Description | Link |
|-----------|-------------|------|
| `func(ctx context.Context) error` | Scheduled job handler | [Schedule API](/reference/sdk/schedule-api.md) |

---

## Implementation Status

For feature maturity and roadmap information, see the [Implementation Status](/reference/implementation-status.md) page.

---

## See Also

- [SDK Overview](/sdk/overview.md) - Getting started with the SDK
- [CLI Overview](/cli/overview.md) - Command-line interface guide
- [Config Schema](/reference/config-schema.md) - Configuration file reference
- [Implementation Status](/reference/implementation-status.md) - Feature maturity tracking
- [Glossary](/reference/glossary.md) - Terminology reference
