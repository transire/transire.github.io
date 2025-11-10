# Implementation Status

This page provides a clear overview of what's implemented, what's in progress, and what's planned for Transire.

!!! info "Legend"
    - ✅ **Stable** - Fully implemented, tested, and production-ready
    - 🚧 **Beta** - Implemented but may have rough edges or limited testing
    - 🔮 **Roadmap** - Planned for future release
    - ❌ **Not Planned** - Not currently on the roadmap

---

## SDK API (transire-sdk-go)

### Core Application

| Feature | Status | Notes |
|---------|--------|-------|
| `transire.New()` | ✅ Stable | Create new application |
| App-based HTTP registration | ✅ Stable | GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD |
| Standard Go HTTP handlers | ✅ Stable | `func(w http.ResponseWriter, r *http.Request)` |
| Queue registration | ✅ Stable | `app.RegisterQueue(name, handler)` |
| Schedule registration | ✅ Stable | `app.RegisterScheduled(schedule, handler)` |
| Message enqueueing | ✅ Stable | `app.Enqueue()` and `app.EnqueueBatch()` |
| App execution | ✅ Stable | `app.Run()` |

### Response Helpers

| Feature | Status | Notes |
|---------|--------|-------|
| `response.OK()` | ✅ Stable | 200 OK with JSON |
| `response.Created()` | ✅ Stable | 201 Created with JSON |
| `response.Accepted()` | ✅ Stable | 202 Accepted with JSON |
| `response.NoContent()` | ✅ Stable | 204 No Content |
| `response.BadRequest()` | ✅ Stable | 400 Bad Request error |
| `response.Unauthorized()` | ✅ Stable | 401 Unauthorized error |
| `response.Forbidden()` | ✅ Stable | 403 Forbidden error |
| `response.NotFound()` | ✅ Stable | 404 Not Found error |
| `response.JSON()` | ✅ Stable | Generic JSON response |
| `response.Text()` | ✅ Stable | Plain text response |
| `response.HTML()` | ✅ Stable | HTML response |
| `response.Bytes()` | ✅ Stable | Raw bytes response |
| `response.Redirect()` | ✅ Stable | HTTP redirect |

### Dependency Injection

| Feature | Status | Notes |
|---------|--------|-------|
| `Provide()` singleton | ✅ Stable | Register singleton providers |
| `ProvideRequest()` request-scoped | ✅ Stable | Register request-scoped providers |
| `GetDep[T]()` | ✅ Stable | Retrieve dependency with error |
| `MustGetDep[T]()` | ✅ Stable | Retrieve dependency or panic |
| Provider function signatures | ✅ Stable | Multiple signature support |
| Dependency auto-wiring | 🚧 Beta | Basic implementation functional |
| Circular dependency detection | 🔮 Roadmap | Planned for v1.1 |

### Request Helpers

| Feature | Status | Notes |
|---------|--------|-------|
| `URLParam()` | ✅ Stable | Extract URL path parameter |
| `URLParamInt()` | ✅ Stable | Extract URL parameter as int |
| `URLParamInt64()` | ✅ Stable | Extract URL parameter as int64 |
| `QueryParam()` | ✅ Stable | Get single query parameter |
| `QueryParams()` | ✅ Stable | Get multi-value query parameter |
| `QueryParamInt()` | ✅ Stable | Get query parameter as int |
| `QueryParamInt64()` | ✅ Stable | Get query parameter as int64 |
| `Header()` | ✅ Stable | Get header value |
| `FormValue()` | ✅ Stable | Get form value |
| `PostFormValue()` | ✅ Stable | Get POST form value |

### Middleware

| Feature | Status | Notes |
|---------|--------|-------|
| Standard Go middleware | ✅ Stable | `func(http.Handler) http.Handler` |
| Global middleware | ✅ Stable | Apply to all routes |
| Grouped middleware | ✅ Stable | Apply to route groups |
| Built-in CORS | 🚧 Beta | Basic CORS support |
| Built-in auth middleware | 🔮 Roadmap | Planned for v1.1 |
| Built-in rate limiting | 🔮 Roadmap | Planned for v1.2 |

### Queue Processing

| Feature | Status | Notes |
|---------|--------|-------|
| Type-safe queue handlers | ✅ Stable | `QueueHandler[T]` |
| Batch processing | ✅ Stable | Handlers receive `[]T` |
| Message enqueueing | ✅ Stable | Single and batch |
| Automatic `__type` injection | 🚧 Beta | Type safety enforcement in progress |
| Partial batch failures | 🚧 Beta | `BatchResult` pattern |
| Dead-letter queues | ✅ Stable | Automatic DLQ creation |

### Scheduled Jobs

| Feature | Status | Notes |
|---------|--------|-------|
| Cron-like scheduling | ✅ Stable | EventBridge syntax |
| ScheduledHandler type | ✅ Stable | `func(ctx context.Context) error` |
| Fixed-rate local emulation | ✅ Stable | Non-overlapping executions |
| Timezone support | ✅ Stable | Configured in `transire.yaml` |

### Error Handling

| Feature | Status | Notes |
|---------|--------|-------|
| `TransireError` type | ✅ Stable | Framework errors |
| `HTTPError` type | ✅ Stable | HTTP-specific errors |
| Error helpers | ✅ Stable | Various constructors |
| Automatic panic recovery | ✅ Stable | HTTP handlers |
| Stack trace preservation | ✅ Stable | Error context |

### Testing (testkit)

| Feature | Status | Notes |
|---------|--------|-------|
| `testkit` package | 🚧 Beta | Basic testing utilities |
| HTTP test assertions | 🔮 Roadmap | Planned for v1.1 |
| Queue test helpers | 🔮 Roadmap | Queue draining, etc. |
| Schedule test triggers | 🔮 Roadmap | Manual trigger support |
| `InitializeForTesting()` | ✅ Stable | Test mode initialization |

### Observability

| Feature | Status | Notes |
|---------|--------|-------|
| Structured logging | ✅ Stable | JSON to stdout |
| Log levels | ✅ Stable | Configurable |
| OTEL trace support | 🔮 Roadmap | Planned for v1.2 |
| Trace propagation | 🔮 Roadmap | HTTP → Queue propagation |
| Metrics | ❌ Not Planned | Use CloudWatch/provider metrics |

---

## CLI (transire-cli)

### Commands

| Command | Status | Notes |
|---------|--------|-------|
| `transire gen` | ✅ Stable | Manifest generation via AST |
| `transire run` | ✅ Stable | Local development server |
| `transire run --watch` | 🔮 Roadmap | Hot reload planned for v1.1 |
| `transire deploy` | ✅ Stable | Cloud deployment |
| `transire init` | ✅ Stable | Backend initialization |
| `transire version` | ✅ Stable | Version information |
| `transire destroy` | ❌ Not Planned | Use IaC tool directly (e.g., `tofu destroy`) |
| `transire logs` | 🔮 Roadmap | Tail cloud logs |
| `transire status` | 🔮 Roadmap | Deployment status |

### Local Runtime

| Feature | Status | Notes |
|---------|--------|-------|
| Chi HTTP server | ✅ Stable | Port 8080 default |
| In-memory queue emulator | ✅ Stable | Configurable workers |
| Fixed-rate scheduler | ✅ Stable | Non-overlapping |
| Graceful shutdown | ✅ Stable | 30s timeout |
| Hot reload | 🔮 Roadmap | `--watch` flag planned |
| Multi-worker concurrency | 🚧 Beta | Basic support |

### Manifest Generation

| Feature | Status | Notes |
|---------|--------|-------|
| AST-based analysis | ✅ Stable | Go AST parsing |
| HTTP route extraction | ✅ Stable | All HTTP methods |
| Queue handler detection | ✅ Stable | Type inference |
| Schedule detection | ✅ Stable | Cron expression parsing |
| Handler signature validation | ✅ Stable | Error codes E1001-E1007 |
| Manifest validation | ✅ Stable | Duplicate detection, etc. |

---

## Cloud Providers

### AWS (transire-cloud-aws)

| Feature | Status | Notes |
|---------|--------|-------|
| Lambda packaging | ✅ Stable | ARM64 and x86_64 |
| API Gateway v2 integration | ✅ Stable | HTTP API |
| SQS queue integration | ✅ Stable | Standard queues |
| SQS DLQ | ✅ Stable | Automatic creation |
| EventBridge scheduling | ✅ Stable | Cron and rate expressions |
| IAM least-privilege roles | ✅ Stable | Auto-generated policies |
| Lambda layers | 🔮 Roadmap | Planned for v1.2 |
| VPC integration | 🔮 Roadmap | Planned for v1.2 |
| Lambda@Edge | ❌ Not Planned | Use CloudFront directly |

### Azure (transire-cloud-azure)

| Feature | Status | Notes |
|---------|--------|-------|
| Azure Functions | 🔮 Roadmap | Planned for v1.3 |
| API Management | 🔮 Roadmap | HTTP integration |
| Service Bus | 🔮 Roadmap | Queue integration |
| Timer triggers | 🔮 Roadmap | Schedule integration |

### GCP (transire-cloud-gcp)

| Feature | Status | Notes |
|---------|--------|-------|
| Cloud Functions | 🔮 Roadmap | Planned for v1.4 |
| API Gateway | 🔮 Roadmap | HTTP integration |
| Cloud Tasks | 🔮 Roadmap | Queue integration |
| Cloud Scheduler | 🔮 Roadmap | Schedule integration |

---

## IaC (transire-iac-opentofu)

### Infrastructure as Code

| Feature | Status | Notes |
|---------|--------|-------|
| OpenTofu generation | ✅ Stable | Terraform-compatible |
| Local backend | ✅ Stable | Default for development |
| S3 backend (AWS) | ✅ Stable | With DynamoDB locking |
| Azure backend | 🔮 Roadmap | Planned for v1.3 |
| GCP backend | 🔮 Roadmap | Planned for v1.4 |
| Workspace support | ✅ Stable | Environment isolation |
| State migration | ✅ Stable | Local ↔ Remote |

---

## CI/CD (transire-ci-github)

### GitHub Actions Integration

| Feature | Status | Notes |
|---------|--------|-------|
| Workflow generation | ✅ Stable | `.github/workflows/` |
| Multi-environment support | ✅ Stable | Dev, staging, prod |
| Guard blocks | ✅ Stable | Manual approval for prod |
| E2E testing | ✅ Stable | Automated test runs |
| GitLab CI | 🔮 Roadmap | Planned for v1.3 |
| Circle CI | 🔮 Roadmap | Planned for v1.3 |
| Jenkins | ❌ Not Planned | Use generic CI patterns |

---

## Configuration

### transire.yaml Schema

| Section | Status | Notes |
|---------|--------|-------|
| `service` | ✅ Stable | Service name |
| `runtime` | ✅ Stable | Runtime language |
| `cloud` | ✅ Stable | Cloud provider selection |
| `iac` | ✅ Stable | IaC tool selection |
| `ci` | ✅ Stable | CI provider selection |
| `timezone` | ✅ Stable | Schedule timezone |
| `deploy.*` | ✅ Stable | Deployment configuration |
| `http.*` | ✅ Stable | HTTP configuration |
| `queues.*` | ✅ Stable | Queue configuration |
| `observability.*` | ✅ Stable | Logging configuration |
| `infra.backend.*` | ✅ Stable | Backend configuration |
| `env[]` | ✅ Stable | Environment definitions |

---

## Version History

### Current Version: v1.0.0 (Stable)

**Released**: TBD

**Features**:
- Core SDK with HTTP, Queue, and Schedule handlers
- Standard Go HTTP compatibility
- Dependency injection (basic)
- Local development runtime
- AWS provider (Lambda, API Gateway, SQS, EventBridge)
- OpenTofu IaC generation
- GitHub Actions CI/CD
- Manifest generation via AST analysis

### Upcoming: v1.1.0 (Q1 2026)

**Planned**:
- Hot reload (`transire run --watch`)
- Enhanced testkit with HTTP assertions
- Complete DI auto-wiring
- Circular dependency detection
- Built-in auth middleware
- Queue type safety enforcement (`__type` validation)

### Future: v1.2.0 (Q2 2026)

**Planned**:
- OTEL trace support
- Trace propagation (HTTP → Queue)
- Lambda layers support (AWS)
- VPC integration (AWS)
- Built-in rate limiting middleware
- Enhanced error reporting

---

## How to Use This Page

**For Users**: Check if a feature you need is ✅ Stable before relying on it in production.

**For Contributors**: See 🔮 Roadmap items for opportunities to contribute.

**For Documentation Writers**: Only document ✅ Stable features as "implemented". Mark 🚧 Beta features clearly, and list 🔮 Roadmap items in separate "Coming Soon" sections.

---

## Reporting Issues

If you find a feature marked as ✅ Stable that doesn't work as documented:

1. Check the [GitHub Issues](https://github.com/transire/transire/issues)
2. File a new issue with:
   - Feature name
   - Expected behavior
   - Actual behavior
   - Steps to reproduce

---

**Last Updated**: November 10, 2025
