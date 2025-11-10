---
title: "transire gen"
category: cli
subcategory: null
complexity: beginner
duration: null
prerequisites:
  - Go 1.22+
  - Transire project set up
mcp_use: reference
mcp_operations:
  - generate_manifest
  - validate_handlers
features_covered:
  - Manifest generation
  - AST analysis
  - Handler validation
  - Build-time discovery
code_blocks: true
last_updated: 2025-10-30
---

# transire gen

## Overview

`transire gen` analyzes your Go code and generates a manifest file (`transire_manifest.json`) containing all your routes, queues, schedules, and their configurations.

**Purpose:**
- Discover all registered handlers via static analysis (no runtime reflection)
- Validate handler signatures and detect errors early
- Generate manifest for infrastructure deployment
- Provide build-time feedback on configuration issues

## Usage

```bash
transire gen
```

Run from your project root (where `main.go` and `transire.yaml` are located).

## What It Does

`transire gen` performs several tasks:

### 1. Load Configuration

Reads `transire.yaml` and validates:
- Syntax (valid YAML)
- Required fields (service name, runtime, cloud provider)
- Semantic rules (timeout > 0, valid architecture, etc.)

### 2. AST Analysis

Scans your `package main` code using Go's AST (Abstract Syntax Tree) to find:
- HTTP route registrations (`app.GET`, `app.POST`, etc.)
- Queue handler registrations (`app.RegisterQueue`)
- Scheduled job registrations (`app.RegisterScheduled`)

### 3. Type Inference

For queue handlers, extracts the message type `T` from the signature `func(ctx context.Context, msgs []T) error`:
- Supports direct types, type aliases, and imported types
- Uses `go/types` for accurate type resolution

### 4. Handler Validation

Verifies each handler:
- Exists as a function in `package main`
- Has the correct signature for its handler type
- No duplicate routes or queue keys

### 5. Manifest Generation

Outputs `transire_manifest.json` with:
- All routes (paths, HTTP methods, handler names)
- All queues (keys, message types, batch configurations)
- All schedules (expressions, handler names)
- Infrastructure requirements (permissions, resources)

## Output

### Success

```bash
$ transire gen
✓ Configuration loaded
✓ Analyzing package main
✓ Found 5 HTTP routes
✓ Found 2 queue handlers
✓ Found 1 scheduled job
✓ Manifest generated: transire_manifest.json
```

### With Warnings

```bash
$ transire gen
✓ Configuration loaded
✓ Analyzing package main
⚠ Warning: Timeout 900s exceeds recommended max (300s)
✓ Found 3 HTTP routes
✓ Manifest generated: transire_manifest.json
```

### With Errors

```bash
$ transire gen
✗ Error: Handler 'getOrder' not found in package main
  Location: main.go:15:10

  app.GET("/orders/{id}", getOrder)
                          ^^^^^^^^

Fix: Ensure getOrder function is defined in main.go

Exit code: 1
```

## Generated Manifest

Example `transire_manifest.json`:

```json
{
  "version": "1.0",
  "service": "orders",
  "runtime": "go",
  "cloud": "aws",
  "routes": [
    {
      "method": "GET",
      "path": "/orders",
      "handler": "listOrders"
    },
    {
      "method": "GET",
      "path": "/orders/{id}",
      "handler": "getOrder"
    },
    {
      "method": "POST",
      "path": "/orders",
      "handler": "createOrder"
    }
  ],
  "queues": [
    {
      "key": "OrderCreated",
      "handler": "processOrderCreated",
      "message_type": "github.com/acme/orders.OrderCreated",
      "batch_size": 10,
      "visibility_timeout": 30,
      "max_retries": 3
    }
  ],
  "schedules": [
    {
      "expression": "@daily 09:00",
      "handler": "sendDailyReport",
      "timezone": "America/New_York"
    }
  ],
  "permissions": {
    "intents": ["sqs:send", "sqs:receive", "events:put"]
  }
}
```

## Constraints (MVP)

### Registration Location

All handler registrations must be in `func main()` of `package main`:

```go
// ✅ GOOD: Registration in main()
func main() {
    app := transire.New()
    app.GET("/orders", listOrders)
    app.Run()
}

// ❌ BAD: Registration outside main()
func init() {
    app := transire.New()
    app.GET("/orders", listOrders)  // NOT detected
}

// ❌ BAD: Registration in another function
func setupRoutes(app *transire.App) {
    app.GET("/orders", listOrders)  // NOT detected
}
```

### Direct Registration Only

Registrations must be direct function calls:

```go
// ✅ GOOD: Direct registration
app.GET("/orders", listOrders)

// ❌ BAD: Conditional registration
if debug {
    app.GET("/debug", debugHandler)  // NOT detected
}

// ❌ BAD: Loop registration
for _, route := range routes {
    app.GET(route.Path, route.Handler)  // NOT detected
}
```

### Handler Functions

Handlers must be functions in `package main`:

```go
// ✅ GOOD: Function in main package
func listOrders(w http.ResponseWriter, r *http.Request) {
    // ...
}

// ❌ BAD: Variable holding function
var listOrders = func(w http.ResponseWriter, r *http.Request) {
    // ... NOT detected as handler
}

// ❌ BAD: Method on struct
type API struct{}
func (a *API) ListOrders(w http.ResponseWriter, r *http.Request) {
    // ... NOT detected as handler
}
```

## Error Codes

`transire gen` uses specific error codes for different failure scenarios:

### E1001: Handler Not Found

```bash
Error E1001: Handler 'getOrder' is not a function in package main
```

**Fix:** Ensure the handler function is defined:

```go
func getOrder(w http.ResponseWriter, r *http.Request) {
    // Implementation
}
```

### E1002: Invalid Handler Signature

```bash
Error E1002: Handler 'createOrder' has invalid signature
Expected: func(http.ResponseWriter, *http.Request)
Got: func(*http.Request) error
```

**Fix:** Use the correct signature for your handler type:

```go
// HTTP handlers
func createOrder(w http.ResponseWriter, r *http.Request) {
    // Implementation
}

// Queue handlers
func processOrder(ctx context.Context, msgs []OrderCreated) error {
    // Implementation
}

// Scheduled handlers
func dailyReport(ctx context.Context) error {
    // Implementation
}
```

### E1003: Duplicate Route

```bash
Error E1003: Duplicate route: POST /orders
Defined at:
  - main.go:15
  - main.go:23
```

**Fix:** Remove duplicate registration:

```go
func main() {
    app := transire.New()
    app.POST("/orders", createOrder)
    // app.POST("/orders", anotherHandler)  // Remove duplicate
    app.Run()
}
```

### E1004: Duplicate Queue Key

```bash
Error E1004: Duplicate queue key: "OrderCreated"
Defined at:
  - main.go:18
  - main.go:27
```

**Fix:** Use unique queue keys:

```go
func main() {
    app := transire.New()
    app.RegisterQueue("OrderCreated", processOrderCreated)
    // app.RegisterQueue("OrderCreated", anotherHandler)  // Remove duplicate
    app.Run()
}
```

### E1005: Complex Type Not Supported

```bash
Error E1005: Cannot infer message type for queue handler 'processMessage'
Complex types (interfaces, type parameters) are not supported
```

**Fix:** Use concrete struct types for queue messages:

```go
// ✅ GOOD: Concrete struct type
type OrderCreated struct {
    OrderID string
    UserID  string
}

func processOrder(ctx context.Context, msgs []OrderCreated) error {
    // Implementation
}

// ❌ BAD: Interface type
func processMessage(ctx context.Context, msgs []interface{}) error {
    // NOT supported
}
```

### E1006: Syntax Error

```bash
Error E1006: Syntax error in main.go:42:15
  expected ')', found 'EOF'
```

**Fix:** Fix Go syntax errors before running `transire gen`.

### E1007: Invalid Schedule Expression

```bash
Error E1007: Invalid schedule expression: "@daily 25:00"
Hour must be 0-23
```

**Fix:** Use valid schedule expressions:

```go
// ✅ GOOD
app.RegisterScheduled("@daily 09:00", handler)

// ❌ BAD
app.RegisterScheduled("@daily 25:00", handler)  // Invalid hour
```

## Integration with Build Process

### go:generate

Add `go:generate` directive to automatically run `transire gen` during `go generate`:

```go
//go:generate transire gen

package main

func main() {
    // ...
}
```

Then run:

```bash
go generate ./...
```

### Pre-commit Hook

Ensure manifest is always up-to-date:

```bash
#!/bin/bash
# .git/hooks/pre-commit

transire gen
if [ $? -ne 0 ]; then
    echo "transire gen failed. Fix errors before committing."
    exit 1
fi

git add transire_manifest.json
```

### CI Pipeline

Validate manifest in CI:

```yaml
# .github/workflows/ci.yml
- name: Generate manifest
  run: transire gen

- name: Check for changes
  run: |
    if git diff --exit-code transire_manifest.json; then
      echo "Manifest is up-to-date"
    else
      echo "Manifest out of date. Run 'transire gen' and commit changes."
      exit 1
    fi
```

## Common Patterns

### After Adding New Handler

```bash
# 1. Add handler to main.go
vim main.go

# 2. Regenerate manifest
transire gen

# 3. Test locally
transire run
```

### Before Deploying

```bash
# Always regenerate manifest before deploy
transire gen && transire deploy
```

### When Changing Configuration

```bash
# Edit config
vim transire.yaml

# Regenerate manifest (picks up config changes)
transire gen

# Verify changes
git diff transire_manifest.json
```

## Troubleshooting

### "Handler not found" but it exists

**Problem:** Handler defined outside `main()` or in init()

**Solution:** Move handler registration to `func main()`:

```go
func main() {
    app := transire.New()
    app.GET("/orders", listOrders)  // Must be here
    app.Run()
}
```

### "Duplicate route" but I don't see it

**Problem:** Same path with same method registered twice

**Solution:** Search for all registrations:

```bash
grep -n 'app.GET("/orders' main.go
```

### "Cannot infer message type"

**Problem:** Queue handler uses interface{} or complex type

**Solution:** Use concrete struct types:

```go
type MyMessage struct {
    ID   string
    Data string
}

func handler(ctx context.Context, msgs []MyMessage) error {
    // ...
}
```

### "Syntax validation runs at..."

`transire gen` runs validation every time. If you see repeated warnings, fix them in `transire.yaml`.

## See Also

- [transire run](/docs/cli/run.md) - Running your app locally
- [transire deploy](/docs/cli/deploy.md) - Deploying to cloud
- [Configuration](/docs/reference/config-schema.md) - transire.yaml schema
- [Manifest](/docs/reference/manifest-schema.md) - Manifest format
- [Error Codes](/docs/reference/error-codes.md) - Complete error reference
