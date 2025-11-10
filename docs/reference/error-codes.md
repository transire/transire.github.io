---
title: "Error Code Reference"
category: reference
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - Basic Transire usage
mcp_use: reference
mcp_operations:
  - lookup_error
  - troubleshoot
  - suggest_fix
features_covered:
  - Error codes
  - Troubleshooting
  - Common issues
code_blocks: true
last_updated: 2025-10-30
---

# Error Code Reference

## Overview

Transire uses structured error codes to help diagnose and fix issues quickly. Each error code follows the format `EXXXX` where the first digit indicates the category:

- **E1XXX:** Manifest generation errors
- **E2XXX:** Handler signature errors
- **E3XXX:** Dependency injection errors
- **E4XXX:** Runtime errors
- **E5XXX:** Deployment errors
- **E9XXX:** General/internal errors

## Error Code Format

```
Error [E1003]: duplicate route 'POST /orders'
First defined at: main.go:45
Duplicate at: main.go:52

How to fix:
- Remove the duplicate registration
- Use a different HTTP method or path
- Check for copy-paste errors in route registration
```

Each error includes:
- **Code:** Unique identifier (e.g., `E1003`)
- **Message:** Human-readable description
- **Context:** File/line information where applicable
- **Fix suggestions:** How to resolve the issue

## Manifest Generation Errors (E1XXX)

Errors during `transire gen` (static analysis and manifest generation).

### E1001: Handler Not Found

**Description:** Referenced handler function doesn't exist or isn't accessible.

**Common Causes:**
- Handler function doesn't exist in package main
- Handler is defined in a different package
- Typo in handler name
- Handler is a method or closure (not supported in MVP)

**Example:**
```
Error [E1001]: handler 'getOrder' not found in package main
Registration: app.GET("/orders/{id}", getOrder)
File: main.go:42
```

**How to Fix:**

```go
// ❌ BAD: Handler doesn't exist
func main() {
    app := transire.New()
    app.GET("/orders/{id}", getOrder)  // getOrder not defined
}

// ✅ GOOD: Handler is a top-level function
func main() {
    app := transire.New()
    app.GET("/orders/{id}", getOrder)
}

func getOrder(w http.ResponseWriter, r *http.Request) {
    // Handler implementation
}
```

**See Also:** [HTTP Handlers](/sdk/http.md)

---

### E1002: Invalid Handler Signature

**Description:** Handler function signature doesn't match the expected pattern for its type.

**Common Causes:**
- Wrong parameters or return types
- Missing context parameter (queue/scheduled handlers)
- Wrong HTTP handler signature (should be standard Go)

**Example:**
```
Error [E1002]: handler 'createOrder' has invalid signature
Expected: func(w http.ResponseWriter, r *http.Request)
Found: func(w http.ResponseWriter, r *http.Request, ctx context.Context)
File: main.go:52
```

**How to Fix:**

```go
// ❌ BAD: HTTP handler with extra context parameter
func createOrder(w http.ResponseWriter, r *http.Request, ctx context.Context) {
    // Wrong signature
}

// ✅ GOOD: Standard Go HTTP handler
func createOrder(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()  // Get context from request
    // Handler implementation
}

// ❌ BAD: Queue handler without context
func processOrders(msgs []ProcessedOrder) error {
    // Missing context
}

// ✅ GOOD: Queue handler with context and slice
func processOrders(ctx context.Context, msgs []ProcessedOrder) error {
    // Handler implementation
}

// ❌ BAD: Scheduled handler without return value
func dailyReport(ctx context.Context) {
    // Missing error return
}

// ✅ GOOD: Scheduled handler with context and error
func dailyReport(ctx context.Context) error {
    // Handler implementation
    return nil
}
```

**Expected Signatures:**
- **HTTP:** `func(w http.ResponseWriter, r *http.Request)`
- **Queue:** `func(ctx context.Context, msgs []T) error`
- **Scheduled:** `func(ctx context.Context) error`

**See Also:**
- [HTTP Handlers](/sdk/http.md)
- [Queue Handlers](/sdk/queue.md)
- [Scheduled Jobs](/sdk/schedule.md)

---

### E1003: Duplicate Route

**Description:** Same HTTP method + path combination registered multiple times.

**Common Causes:**
- Accidental duplicate registration
- Copy-paste errors
- Conflicting route definitions

**Example:**
```
Error [E1003]: duplicate route 'POST /orders'
First defined at: main.go:45
Duplicate at: main.go:52
```

**How to Fix:**

```go
// ❌ BAD: Duplicate route
func main() {
    app := transire.New()
    app.POST("/orders", createOrder)
    app.POST("/orders", createOrderV2)  // Duplicate!
}

// ✅ GOOD: Unique routes
func main() {
    app := transire.New()
    app.POST("/orders", createOrder)
    app.POST("/v2/orders", createOrderV2)  // Different path
    // OR
    app.PUT("/orders", updateOrder)  // Different method
}
```

**Note:** Routes with different path parameters are considered different:
```go
// ✅ OK: Different routes (different parameters)
app.GET("/orders/{id}", getOrder)
app.GET("/users/{id}", getUser)
```

**See Also:** [HTTP Handlers](/sdk/http.md)

---

### E1004: Duplicate Queue Key

**Description:** Same queue key registered multiple times.

**Common Causes:**
- Duplicate `RegisterQueue` calls
- Copy-paste errors
- Reusing queue key names

**Example:**
```
Error [E1004]: duplicate queue key 'ProcessedOrder'
First defined at: main.go:38
Duplicate at: main.go:42
```

**How to Fix:**

```go
// ❌ BAD: Duplicate queue key
func main() {
    app := transire.New()
    app.RegisterQueue("ProcessedOrder", processOrderV1)
    app.RegisterQueue("ProcessedOrder", processOrderV2)  // Duplicate!
}

// ✅ GOOD: Unique queue keys
func main() {
    app := transire.New()
    app.RegisterQueue("ProcessedOrder", processOrders)
    app.RegisterQueue("EmailNotification", sendEmails)  // Different key
}
```

**See Also:** [Queue Handlers](/sdk/queue.md)

---

### E1005: Unable to Infer Message Type

**Description:** Cannot extract message type `T` from queue handler's `[]T` parameter.

**Common Causes:**
- Using `interface{}` as message type
- Using type parameters/generics
- Complex type that can't be resolved
- Message type not in accessible scope

**Example:**
```
Error [E1005]: unable to infer message type for queue 'ProcessedOrder'
Handler: processedOrderBatch
Signature: func(ctx context.Context, msgs []interface{}) error
File: main.go:55
```

**How to Fix:**

```go
// ❌ BAD: Using interface{} (type not concrete)
func processOrderBatch(ctx context.Context, msgs []interface{}) error {
    // Can't infer type
}

// ❌ BAD: Using generics (not supported in MVP)
func processBatch[T any](ctx context.Context, msgs []T) error {
    // Type parameter not supported
}

// ✅ GOOD: Concrete type
type ProcessedOrder struct {
    OrderID string `json:"order_id"`
    Status  string `json:"status"`
}

func processOrderBatch(ctx context.Context, msgs []ProcessedOrder) error {
    // Type is clearly ProcessedOrder
    for _, msg := range msgs {
        // Process each message
    }
    return nil
}

// ✅ GOOD: Imported type
import "github.com/acme/orders/types"

func processOrderBatch(ctx context.Context, msgs []types.ProcessedOrder) error {
    // Type is types.ProcessedOrder
    return nil
}
```

**Requirements:**
- Message type must be a concrete struct or type alias
- Type must be defined in an accessible package
- No interfaces, type parameters, or complex generic types

**See Also:** [Queue Handlers](/sdk/queue.md)

---

### E1006: Duplicate Path Parameter

**Description:** URL path contains the same parameter name multiple times.

**Common Causes:**
- Reusing parameter names in nested routes
- Copy-paste errors in path definitions
- Misunderstanding of path parameter scope

**Example:**
```
Error [E1006]: path '/orders/{id}/items/{id}' contains duplicate parameter 'id'
Each path parameter must have a unique name within the path
File: main.go:45
```

**How to Fix:**

```go
// ❌ BAD: Duplicate parameter name
app.GET("/orders/{id}/items/{id}", getOrderItem)

// ✅ GOOD: Unique parameter names
app.GET("/orders/{orderId}/items/{itemId}", getOrderItem)

func getOrderItem(w http.ResponseWriter, r *http.Request) {
    orderId := transire.URLParam(r, "orderId")
    itemId := transire.URLParam(r, "itemId")
    // ...
}
```

**See Also:** [HTTP Handlers](/sdk/http.md)

---

### E1007: Invalid Greedy Parameter Position

**Description:** Greedy path parameter (`{name+}`) is not the last segment in the path.

**Common Causes:**
- Greedy parameter followed by other segments
- Misunderstanding of greedy parameter behavior
- Invalid path pattern

**Example:**
```
Error [E1007]: greedy parameter '{path+}' must be the last segment
Found: /files/{path+}/info
File: main.go:50
```

**How to Fix:**

```go
// ❌ BAD: Greedy parameter not at end
app.GET("/files/{path+}/info", getFileInfo)

// ✅ GOOD: Greedy parameter at end
app.GET("/files/{path+}", serveFile)

func serveFile(w http.ResponseWriter, r *http.Request) {
    path := transire.URLParam(r, "path")  // Matches entire rest of path
    // path could be "docs/readme.txt" or "images/logo.png"
}

// ✅ GOOD: Non-greedy parameters can be anywhere
app.GET("/orders/{id}/items/{itemId}", getOrderItem)
```

**Greedy Parameter Behavior:**
- `{path+}` matches all remaining segments including slashes
- Must be the final segment in the route
- Use for catch-all routes or file serving

**See Also:** [HTTP Handlers](/sdk/http.md)

---

## Handler Signature Errors (E2XXX)

Errors related to handler function signatures (detected at runtime or during validation).

### E2001: Missing Context Parameter

**Description:** Handler is missing required `context.Context` parameter.

**Applies to:** Queue handlers, Scheduled handlers

**Example:**
```
Error [E2001]: queue handler 'processOrders' missing context parameter
Expected: func(ctx context.Context, msgs []T) error
Found: func(msgs []ProcessedOrder) error
```

**How to Fix:**

```go
// ❌ BAD: Missing context
func processOrders(msgs []ProcessedOrder) error {
    // No way to handle cancellation or timeouts
}

// ✅ GOOD: Include context
func processOrders(ctx context.Context, msgs []ProcessedOrder) error {
    for _, msg := range msgs {
        // Check for cancellation
        if err := ctx.Err(); err != nil {
            return err
        }
        // Process message
    }
    return nil
}
```

---

### E2002: Invalid Return Type

**Description:** Handler returns wrong type or wrong number of values.

**Example:**
```
Error [E2002]: handler 'processOrders' has invalid return type
Expected: error
Found: (int, error)
```

**How to Fix:**

```go
// ❌ BAD: Multiple return values
func processOrders(ctx context.Context, msgs []ProcessedOrder) (int, error) {
    return len(msgs), nil
}

// ✅ GOOD: Single error return
func processOrders(ctx context.Context, msgs []ProcessedOrder) error {
    // Handler implementation
    return nil
}
```

---

## Dependency Injection Errors (E3XXX)

Errors related to the dependency injection system.

### E3001: Provider Not Found

**Description:** Attempted to get a dependency that hasn't been provided.

**Example:**
```
Error [E3001]: no provider registered for type *OrderService
Use transire.Provide() to register a provider for this type
```

**How to Fix:**

```go
// ❌ BAD: Getting dependency without provider
func main() {
    app := transire.New()
    app.GET("/orders/{id}", getOrder)
    app.Run()
}

func getOrder(w http.ResponseWriter, r *http.Request) {
    // This will fail - no provider registered
    svc, err := transire.Get[*OrderService](r.Context())
}

// ✅ GOOD: Register provider first
func main() {
    // Register provider
    transire.Provide(func() (*OrderService, error) {
        return &OrderService{
            DB: connectDB(),
        }, nil
    })

    app := transire.New()
    app.GET("/orders/{id}", getOrder)
    app.Run()
}

func getOrder(w http.ResponseWriter, r *http.Request) {
    svc, err := transire.Get[*OrderService](r.Context())
    if err != nil {
        // Handle error
    }
    // Use service
}
```

**See Also:** [Dependency Injection](/sdk/di.md)

---

### E3002: Provider Initialization Failed

**Description:** Provider function returned an error during initialization.

**Example:**
```
Error [E3002]: failed to initialize *OrderService
Cause: failed to connect to database: connection refused
```

**How to Fix:**

```go
// ❌ BAD: Provider fails without useful error
transire.Provide(func() (*OrderService, error) {
    db, err := connectDB()
    if err != nil {
        return nil, err  // Generic error
    }
    return &OrderService{DB: db}, nil
})

// ✅ GOOD: Provider with clear error messages
transire.Provide(func() (*OrderService, error) {
    dbURL := os.Getenv("DB_URL")
    if dbURL == "" {
        return nil, fmt.Errorf("DB_URL environment variable not set")
    }

    db, err := connectDB(dbURL)
    if err != nil {
        return nil, fmt.Errorf("failed to connect to database at %s: %w", dbURL, err)
    }

    return &OrderService{DB: db}, nil
})
```

**Common Causes:**
- Database connection failures
- Missing environment variables
- Invalid configuration
- Network issues

**Debugging:**
- Check environment variables are set
- Test external service connectivity
- Review error messages for specific failures
- Use structured logging in providers

---

### E3003: Circular Dependency

**Description:** Providers have a circular dependency chain.

**Example:**
```
Error [E3003]: circular dependency detected
Chain: *OrderService → *PaymentService → *OrderService
```

**How to Fix:**

```go
// ❌ BAD: Circular dependency
transire.Provide(func(ps *PaymentService) (*OrderService, error) {
    return &OrderService{Payments: ps}, nil
})

transire.Provide(func(os *OrderService) (*PaymentService, error) {
    return &PaymentService{Orders: os}, nil  // Circular!
})

// ✅ GOOD: Break circular dependency with interface
type PaymentProcessor interface {
    ProcessPayment(orderID string, amount float64) error
}

transire.Provide(func() (*OrderService, error) {
    return &OrderService{}, nil
})

transire.Provide(func(os *OrderService) (*PaymentService, error) {
    return &PaymentService{Orders: os}, nil
})
```

**See Also:** [DI Patterns](/guides/di-patterns.md)

---

## Runtime Errors (E4XXX)

Errors that occur during application runtime (local or cloud).

### E4001: Invalid Configuration

**Description:** Configuration file has invalid values or structure.

**Example:**
```
Error [E4001]: invalid configuration
Field: deploy.timeout_s
Value: -5
Expected: value between 1 and 900
```

**How to Fix:**

Check `transire.yaml` for invalid values:

```yaml
# ❌ BAD: Invalid timeout
deploy:
  timeout_s: -5

# ✅ GOOD: Valid timeout
deploy:
  timeout_s: 30
```

**See Also:** [Config Schema](/reference/config-schema.md)

---

### E4002: Handler Panic

**Description:** Handler panicked during execution (caught and logged).

**Example:**
```
Error [E4002]: handler panic recovered
Handler: getOrder
Route: GET /orders/{id}
Panic: runtime error: invalid memory address or nil pointer dereference
Stack trace:
  main.getOrder (main.go:85)
  ...
```

**How to Fix:**

```go
// ❌ BAD: Unchecked nil dereference
func getOrder(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")
    order := orders[id]
    response.OK(w, order.Details)  // Panics if order is nil!
}

// ✅ GOOD: Check for nil
func getOrder(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")
    order, exists := orders[id]
    if !exists {
        response.NotFound(w, "Order not found")
        return
    }
    response.OK(w, order.Details)
}
```

**Common Causes:**
- Nil pointer dereferences
- Index out of bounds
- Type assertions that fail
- Division by zero

**Prevention:**
- Check for nil before dereferencing
- Validate input data
- Use defensive programming
- Add comprehensive error handling

---

### E4003: Context Cancelled

**Description:** Operation cancelled due to context cancellation (timeout or shutdown).

**Example:**
```
Error [E4003]: context cancelled
Handler: processOrders
Queue: ProcessedOrder
Cause: context deadline exceeded
```

**How to Fix:**

```go
// ❌ BAD: Ignoring context cancellation
func processOrders(ctx context.Context, msgs []ProcessedOrder) error {
    for _, msg := range msgs {
        // Long-running operation without checking context
        processOrder(msg)
    }
    return nil
}

// ✅ GOOD: Check context in loops
func processOrders(ctx context.Context, msgs []ProcessedOrder) error {
    for _, msg := range msgs {
        // Check if context is cancelled
        if err := ctx.Err(); err != nil {
            return fmt.Errorf("processing cancelled: %w", err)
        }

        // Pass context to sub-operations
        if err := processOrder(ctx, msg); err != nil {
            return err
        }
    }
    return nil
}
```

**Best Practices:**
- Always pass and check `ctx.Err()` in loops
- Pass context to database queries and HTTP requests
- Set appropriate timeouts in config
- Handle graceful shutdown properly

---

### E4004: Message Type Mismatch

**Description:** Enqueued message type doesn't match queue handler's expected type.

**Example:**
```
Error [E4004]: message type mismatch
Queue: ProcessedOrder
Expected: github.com/acme/orders.ProcessedOrder
Found: github.com/acme/orders.OrderRequest
Message moved to DLQ
```

**How to Fix:**

```go
// ❌ BAD: Enqueueing wrong type
type OrderRequest struct {
    SKU string
    Qty int
}

type ProcessedOrder struct {
    OrderID string
}

func createOrder(w http.ResponseWriter, r *http.Request) {
    var req OrderRequest
    json.NewDecoder(r.Body).Decode(&req)

    // Wrong type! Handler expects ProcessedOrder
    app.Enqueue(r.Context(), "ProcessedOrder", req)
}

// ✅ GOOD: Enqueue correct type
func createOrder(w http.ResponseWriter, r *http.Request) {
    var req OrderRequest
    json.NewDecoder(r.Body).Decode(&req)

    // Create order and enqueue correct type
    orderID := createOrderInDB(req)
    app.Enqueue(r.Context(), "ProcessedOrder", ProcessedOrder{
        OrderID: orderID,
    })
}
```

**Note:** Type validation is automatic. Mismatched messages are moved to DLQ for inspection.

**See Also:** [Queue Handlers](/sdk/queue.md)

---

## Deployment Errors (E5XXX)

Errors during deployment to cloud provider.

### E5001: Backend Not Initialized

**Description:** OpenTofu backend (S3 bucket, DynamoDB table) doesn't exist.

**Example:**
```
Error [E5001]: backend not initialized
Backend bucket 'my-tf-state' does not exist
Run 'transire init --backend' to create backend resources
```

**How to Fix:**

```bash
# Initialize backend resources
transire init --backend

# Then deploy
transire deploy
```

**See Also:** [Backend Setup](/iac/backend.md)

---

### E5002: Authentication Failed

**Description:** Cloud provider authentication failed.

**Example:**
```
Error [E5002]: AWS authentication failed
Unable to locate credentials
Check: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables
Or: ~/.aws/credentials file
Or: IAM role (if running in AWS)
```

**How to Fix:**

```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1

# Verify authentication
aws sts get-caller-identity
```

**See Also:** [Deployment Guide](/guides/deployment.md)

---

### E5003: Insufficient Permissions

**Description:** AWS credentials lack required permissions.

**Example:**
```
Error [E5003]: insufficient permissions
Action: lambda:CreateFunction
Resource: arn:aws:lambda:us-east-1:123456789012:function:orders-dev-http
Required IAM permissions: lambda:CreateFunction, iam:PassRole
```

**How to Fix:**

Ensure your IAM user/role has deployment permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*",
        "apigateway:*",
        "sqs:*",
        "events:*",
        "iam:*",
        "s3:*",
        "dynamodb:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

**Note:** This is a broad policy for development. Use least-privilege in production.

**See Also:** [AWS Deployment](/cloud/aws/deployment.md)

---

### E5004: Resource Conflict

**Description:** Resource already exists with conflicting configuration.

**Example:**
```
Error [E5004]: resource conflict
Resource: Lambda function 'orders-dev-http'
Conflict: Function already exists and is not managed by this Terraform state
Solution: Import existing resource or delete manually
```

**How to Fix:**

```bash
# Option 1: Import existing resource
cd infra
tofu import aws_lambda_function.http orders-dev-http

# Option 2: Delete and recreate
aws lambda delete-function --function-name orders-dev-http
transire deploy
```

---

### E5005: Deployment Timeout

**Description:** Deployment took too long and timed out.

**Example:**
```
Error [E5005]: deployment timeout
Operation: Creating Lambda function 'orders-dev-http'
Timeout: 10 minutes
Possible causes: Large deployment package, VPC cold start, AWS API throttling
```

**How to Fix:**

- Check deployment package size (should be < 50 MB compressed)
- Disable VPC if not needed (faster cold starts)
- Retry deployment (may be transient AWS issue)
- Check AWS service health dashboard

---

## General Errors (E9XXX)

General and internal errors.

### E9001: Internal Error

**Description:** Unexpected internal error (bug in Transire).

**Example:**
```
Error [E9001]: internal error
Please report this issue at: https://github.com/transire/transire/issues
Include: error message, transire version, and minimal reproduction
```

**How to Fix:**

This indicates a bug in Transire. Please:

1. Check if you're using the latest version: `transire version`
2. Search existing issues: https://github.com/transire/transire/issues
3. File a bug report with:
   - Error message and stack trace
   - Transire and Go versions
   - Minimal code to reproduce
   - Operating system

---

## Troubleshooting Guide

### Quick Diagnosis

**Manifest generation fails:**
1. Run `transire gen --verbose` for detailed output
2. Check error code (E1XXX)
3. Review handler signatures and registrations
4. Ensure all registrations are in `func main()`

**Runtime errors:**
1. Check error code (E4XXX)
2. Review logs for stack traces
3. Verify configuration values
4. Test locally before deploying

**Deployment fails:**
1. Check error code (E5XXX)
2. Verify AWS credentials: `aws sts get-caller-identity`
3. Ensure backend is initialized: `transire init --backend`
4. Check IAM permissions

### Getting Help

**Documentation:**
- [Guides](/docs/guides/) - Topic-specific guides
- [SDK Reference](/docs/sdk/) - API documentation
- [Examples](/docs/examples/) - Complete working examples

**Community:**
- GitHub Issues: https://github.com/transire/transire/issues
- Discussions: https://github.com/transire/transire/discussions

**Debugging Tips:**
- Use `--verbose` flag for detailed output
- Check `transire.yaml` for configuration errors
- Review generated manifest: `cat transire_manifest.json | jq`
- Test handlers locally before deploying
- Enable debug logging: `LOG_LEVEL=debug`

## See Also

- [Config Schema](/reference/config-schema.md) - Configuration reference
- [Manifest Schema](/reference/manifest-schema.md) - Manifest format
- [Troubleshooting Guide](/guides/troubleshooting.md) - Common issues and solutions
- [Testing Guide](/guides/testing.md) - Testing strategies
