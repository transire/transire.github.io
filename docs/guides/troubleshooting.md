---
title: "Troubleshooting Guide"
category: guides
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - Basic Transire knowledge
mcp_use: reference
features_covered:
  - Common issues
  - Debugging techniques
  - Error resolution
code_blocks: true
last_updated: 2025-10-31
---

# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when developing with Transire.

## Manifest Generation Issues

### Error: Handler function not found

**Problem:** `transire gen` reports that a handler function cannot be found.

**Possible causes:**
1. Handler function is not in `package main`
2. Function is unexported (lowercase name)
3. Function signature doesn't match expected pattern

**Solution:**

```go
// ✗ Wrong - unexported function
func getUser(w http.ResponseWriter, r *http.Request) { }

// ✓ Correct - exported function
func GetUser(w http.ResponseWriter, r *http.Request) { }
```

Ensure handler is registered correctly:

```go
app.GET("/users/{id}", GetUser)  // Handler must be exported
```

### Error: Invalid handler signature

**Problem:** Handler signature doesn't match expected pattern.

**Expected signatures:**

```go
// HTTP handlers
func(w http.ResponseWriter, r *http.Request)

// Queue handlers
func(ctx context.Context, msgs []MessageType) error

// Scheduled handlers
func(ctx context.Context) error
```

See [Error Codes](/reference/error-codes.md) for detailed signature requirements.

## Local Runtime Issues

### Server won't start

**Problem:** `transire run` fails to start.

**Check:**

1. **Port already in use:**
   ```bash
   # Find process using port 3000
   lsof -i :3000

   # Kill the process or use different port
   transire run --port 8080
   ```

2. **Manifest not generated:**
   ```bash
   transire gen  # Generate manifest first
   transire run
   ```

3. **Configuration errors:**
   ```bash
   # Check transire.yaml syntax
   cat transire.yaml
   ```

### Handlers not being called

**Problem:** Requests return 404 or routes don't work.

**Check:**

1. **Route registration:**
   ```go
   // Make sure routes are registered before app.Run()
   app.GET("/users", ListUsers)
   app.Run()
   ```

2. **URL parameters:**
   ```go
   // Chi syntax for URL parameters
   app.GET("/users/{id}", GetUser)  // Correct
   app.GET("/users/:id", GetUser)   // Wrong
   ```

3. **Manifest generation:**
   ```bash
   transire gen  # Regenerate manifest
   ```

### Queue messages not processing

**Problem:** Enqueued messages aren't being processed.

**Check:**

1. **Queue handler registered:**
   ```go
   app.RegisterQueue("orders", ProcessOrders)
   ```

2. **Queue name matches:**
   ```go
   // Names must match exactly
   app.RegisterQueue("orders", ProcessOrders)
   transire.Enqueue(ctx, app, "orders", order)
   ```

3. **Message type matches:**
   ```go
   // Handler signature must match enqueued type
   func ProcessOrders(ctx context.Context, msgs []Order) error

   // Enqueue must use same type
   transire.Enqueue(ctx, app, "orders", Order{...})
   ```

4. **Check logs:**
   ```bash
   transire run  # Watch for queue processing logs
   ```

## Dependency Injection Issues

### Panic: dependency not found

**Problem:** `transire.MustGet[T]()` panics.

**Cause:** Dependency not registered.

**Solution:**

```go
// Register dependency before using
app.Provide(func() *Database {
    return NewDatabase()
})

// Then use in handlers
func Handler(w http.ResponseWriter, r *http.Request) {
    db := transire.MustGet[*Database](r.Context())
    // ...
}
```

### Multiple providers for same type

**Problem:** Multiple calls to `app.Provide` for same type.

**Solution:** Only register each type once:

```go
// ✗ Wrong - duplicate registrations
app.Provide(func() *Database { return NewDatabase() })
app.Provide(func() *Database { return NewDatabase() })

// ✓ Correct - single registration
app.Provide(func() *Database { return NewDatabase() })
```

## Deployment Issues

### Backend not initialized

**Problem:** `transire deploy` fails with backend error.

**Solution:**

```bash
# Initialize backend first
transire init --backend

# Then deploy
transire deploy
```

### AWS credentials not found

**Problem:** Deployment fails with authentication error.

**Solution:**

1. Configure AWS credentials:
   ```bash
   aws configure
   ```

2. Or use environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your-key
   export AWS_SECRET_ACCESS_KEY=your-secret
   export AWS_REGION=us-east-1
   ```

3. Or use AWS profiles:
   ```bash
   AWS_PROFILE=myprofile transire deploy
   ```

### OpenTofu errors

**Problem:** OpenTofu apply fails.

**Check:**

1. **OpenTofu installed:**
   ```bash
   tofu --version
   ```

2. **State conflicts:**
   ```bash
   cd infra
   tofu state list
   ```

3. **Resource limits:**
   - Check AWS service quotas
   - Verify IAM permissions

### Deployment timeout

**Problem:** Lambda functions timeout in cloud.

**Solution:**

Increase timeout in `transire.yaml`:

```yaml
deploy:
  lambda:
    timeout: 30  # Increase from default
```

## Testing Issues

### Tests can't find dependencies

**Problem:** Tests fail to resolve DI dependencies.

**Solution:**

Register dependencies in test setup:

```go
func TestHandler(t *testing.T) {
    tk := testkit.New(t)

    // Register test dependencies
    tk.App.Provide(func() *Database {
        return NewMockDatabase()
    })

    // Test handler
    resp := tk.GET("/users")
    tk.AssertStatus(resp, 200)
}
```

### Test isolation issues

**Problem:** Tests interfere with each other.

**Solution:**

Use `testkit.New(t)` for each test to get isolated app instance:

```go
func TestA(t *testing.T) {
    tk := testkit.New(t)  // Isolated instance
    // ...
}

func TestB(t *testing.T) {
    tk := testkit.New(t)  // Separate instance
    // ...
}
```

## Performance Issues

### Slow local startup

**Problem:** `transire run` takes long to start.

**Possible causes:**
1. Large number of dependencies
2. Heavy initialization in `Provide` functions

**Solution:**

Use lazy initialization:

```go
// ✗ Slow - eager initialization
app.Provide(func() *Database {
    db := ConnectToDatabase()  // Happens at startup
    return db
})

// ✓ Fast - lazy initialization
app.Provide(func() *Database {
    return &Database{
        // Connect on first use
    }
})
```

### High memory usage locally

**Problem:** Local runtime uses too much memory.

**Solution:**

Adjust queue worker count in `transire.yaml`:

```yaml
runtime:
  queue:
    workers: 2  # Reduce from default
```

## Common Error Messages

### "E1001: Invalid HTTP handler signature"

Handler must be: `func(w http.ResponseWriter, r *http.Request)`

See [Error Codes Reference](/docs/reference/error-codes.md#e1001).

### "E2001: Invalid queue handler signature"

Handler must be: `func(ctx context.Context, msgs []T) error`

See [Error Codes Reference](/docs/reference/error-codes.md#e2001).

### "E3001: Invalid scheduled handler signature"

Handler must be: `func(ctx context.Context) error`

See [Error Codes Reference](/docs/reference/error-codes.md#e3001).

## Getting More Help

If these solutions don't resolve your issue:

1. Check [Error Codes Reference](/reference/error-codes.md)
2. Review [FAQ](/community/faq.md)
3. Search existing GitHub issues
4. Create a new issue with:
   - Error message
   - Minimal reproduction
   - Environment details (OS, Go version, etc.)

## Debug Mode

Enable verbose logging for more information:

```bash
# Local runtime
transire run --debug

# Deployment
transire deploy --debug
```

This will output detailed information about:
- Manifest parsing
- Handler registration
- Request routing
- Queue message processing
- Deployment steps
