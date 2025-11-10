---
title: "HTTP Handlers"
category: sdk
subcategory: null
complexity: beginner
duration: null
prerequisites:
  - Go 1.22+
  - Basic understanding of Go HTTP handlers
mcp_use: reference
mcp_operations:
  - add_http_handler
  - extract_http_patterns
features_covered:
  - HTTP handler registration
  - URL parameters
  - Request/response helpers
  - Standard Go HTTP patterns
code_blocks: true
last_updated: 2025-10-30
---

# HTTP Handlers

## Overview

Transire uses **standard Go HTTP handlers** (`http.HandlerFunc`) for HTTP routes. This means your handlers work with the entire Go ecosystem—middleware, testing tools, and any library that works with `net/http`.

The framework provides convenient helper functions for common operations while maintaining full compatibility with Go's standard library.

**Key benefits:**
- Zero learning curve if you know Go HTTP
- Works with all Go HTTP middleware
- Easy testing with standard tools
- Full access to stdlib when you need it

## Handler Signature

HTTP handlers in Transire use the standard Go signature:

```go
func(w http.ResponseWriter, r *http.Request)
```

This is the same signature as `http.HandlerFunc` from Go's standard library.

## Registering HTTP Handlers

Use the HTTP verb methods on your `transire.App` instance:

```go
package main

import (
    "net/http"
    "github.com/transire/sdk-go"
    "github.com/transire/sdk-go/response"
)

func main() {
    app := transire.New()

    // Register HTTP handlers
    app.GET("/users/{id}", getUser)
    app.POST("/users", createUser)
    app.PUT("/users/{id}", updateUser)
    app.PATCH("/users/{id}", patchUser)
    app.DELETE("/users/{id}", deleteUser)

    app.Run()
}
```

### Available Methods

- `app.GET(path string, handler http.HandlerFunc)` - Register GET handler
- `app.POST(path string, handler http.HandlerFunc)` - Register POST handler
- `app.PUT(path string, handler http.HandlerFunc)` - Register PUT handler
- `app.PATCH(path string, handler http.HandlerFunc)` - Register PATCH handler
- `app.DELETE(path string, handler http.HandlerFunc)` - Register DELETE handler
- `app.Route(path string, handler http.HandlerFunc)` - Register handler for all methods

## URL Parameters

Transire uses Chi router syntax for URL parameters:

```go
// Simple parameter
app.GET("/users/{id}", getUser)

// Multiple parameters
app.GET("/users/{userId}/orders/{orderId}", getUserOrder)

// Greedy parameter (captures rest of path)
app.GET("/files/{path+}", getFile)
```

Extract URL parameters using the `transire.URLParam` helper:

```go
func getUser(w http.ResponseWriter, r *http.Request) {
    userID := transire.URLParam(r, "id")

    // Fetch user from database
    user, err := db.GetUser(r.Context(), userID)
    if err != nil {
        response.InternalServerError(w, "Failed to fetch user")
        return
    }

    response.OK(w, user)
}
```

## Request Helpers

Transire provides helpers for common request operations:

```go
import "github.com/transire/sdk-go"

// URL parameters (from path)
id := transire.URLParam(r, "id")

// Query parameters (single value)
page := transire.QueryParam(r, "page")

// Query parameters (multi-value)
tags := transire.QueryParams(r, "tags")  // ?tags=go&tags=web

// Headers
authToken := transire.Header(r, "Authorization")

// Form values
email := transire.FormValue(r, "email")
```

### Reading Request Body

Use Go's standard library to read request bodies:

```go
func createUser(w http.ResponseWriter, r *http.Request) {
    var user User

    // Decode JSON body
    if err := json.NewDecoder(r.Body).Decode(&user); err != nil {
        response.BadRequest(w, "Invalid JSON")
        return
    }

    // Validate
    if user.Email == "" {
        response.BadRequest(w, "Email is required")
        return
    }

    // Create user
    createdUser, err := db.CreateUser(r.Context(), &user)
    if err != nil {
        response.InternalServerError(w, "Failed to create user")
        return
    }

    response.Created(w, createdUser)
}
```

## Response Helpers

The `response` package provides helpers for common response types:

```go
import "github.com/transire/sdk-go/response"
```

### Success Responses

```go
// 200 OK with JSON
response.OK(w, data)

// 201 Created with JSON
response.Created(w, createdData)

// Custom status with JSON
response.JSON(w, http.StatusAccepted, data)

// Plain text response
response.Text(w, http.StatusOK, "Success")
```

### Error Responses

```go
// 400 Bad Request
response.BadRequest(w, "Invalid input")

// 404 Not Found
response.NotFound(w, "User not found")

// 500 Internal Server Error
response.InternalServerError(w, "Database connection failed")
```

### Special Headers

```go
// Enable CORS
response.EnableCORS(w)

// Disable caching
response.NoCache(w)
```

## Complete Example

Here's a complete REST API for managing orders:

```go
package main

import (
    "encoding/json"
    "net/http"
    "github.com/transire/sdk-go"
    "github.com/transire/sdk-go/response"
)

type Order struct {
    ID     string  `json:"id"`
    UserID string  `json:"user_id"`
    Total  float64 `json:"total"`
    Status string  `json:"status"`
}

func main() {
    app := transire.New()

    // Register routes
    app.GET("/orders", listOrders)
    app.GET("/orders/{id}", getOrder)
    app.POST("/orders", createOrder)
    app.PUT("/orders/{id}", updateOrder)
    app.DELETE("/orders/{id}", deleteOrder)

    app.Run()
}

// List all orders (with optional filtering)
func listOrders(w http.ResponseWriter, r *http.Request) {
    // Optional query parameters
    userID := transire.QueryParam(r, "user_id")
    status := transire.QueryParam(r, "status")

    orders, err := db.ListOrders(r.Context(), userID, status)
    if err != nil {
        response.InternalServerError(w, "Failed to fetch orders")
        return
    }

    response.OK(w, orders)
}

// Get single order by ID
func getOrder(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")

    order, err := db.GetOrder(r.Context(), id)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            response.NotFound(w, "Order not found")
            return
        }
        response.InternalServerError(w, "Failed to fetch order")
        return
    }

    response.OK(w, order)
}

// Create new order
func createOrder(w http.ResponseWriter, r *http.Request) {
    var order Order

    if err := json.NewDecoder(r.Body).Decode(&order); err != nil {
        response.BadRequest(w, "Invalid JSON")
        return
    }

    // Validate required fields
    if order.UserID == "" {
        response.BadRequest(w, "user_id is required")
        return
    }

    if order.Total <= 0 {
        response.BadRequest(w, "total must be positive")
        return
    }

    // Create in database
    created, err := db.CreateOrder(r.Context(), &order)
    if err != nil {
        response.InternalServerError(w, "Failed to create order")
        return
    }

    response.Created(w, created)
}

// Update existing order
func updateOrder(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")

    var updates Order
    if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
        response.BadRequest(w, "Invalid JSON")
        return
    }

    updated, err := db.UpdateOrder(r.Context(), id, &updates)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            response.NotFound(w, "Order not found")
            return
        }
        response.InternalServerError(w, "Failed to update order")
        return
    }

    response.OK(w, updated)
}

// Delete order
func deleteOrder(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")

    err := db.DeleteOrder(r.Context(), id)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            response.NotFound(w, "Order not found")
            return
        }
        response.InternalServerError(w, "Failed to delete order")
        return
    }

    response.Text(w, http.StatusNoContent, "")
}
```

## Using Standard Library

You can always use Go's standard library directly:

```go
func customResponse(w http.ResponseWriter, r *http.Request) {
    // Set headers manually
    w.Header().Set("Content-Type", "application/json")
    w.Header().Set("X-Custom-Header", "value")

    // Write status code
    w.WriteHeader(http.StatusOK)

    // Write response body
    json.NewEncoder(w).Encode(map[string]string{
        "message": "Success",
    })
}
```

## Working with Middleware

Since Transire uses standard Go HTTP handlers, you can use any Go HTTP middleware:

```go
import (
    "github.com/go-chi/chi/v5/middleware"
    "net/http"
)

func main() {
    app := transire.New()

    // Add middleware to specific routes
    app.GET("/admin/users", middleware.BasicAuth("admin", map[string]string{
        "admin": "password",
    })(listUsers))

    app.Run()
}
```

For more advanced middleware patterns, see the [Middleware Guide](/docs/sdk/middleware.md).

## Local vs Cloud

HTTP handlers work identically in local and cloud environments:

- **Local:** Chi HTTP server routes requests to your handlers
- **Cloud:** API Gateway/ALB routes requests through a cloud adapter to your handlers

The handler code is identical in both environments.

## Error Handling

Always handle errors appropriately:

```go
func getUser(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")

    user, err := db.GetUser(r.Context(), id)
    if err != nil {
        // Distinguish between different error types
        switch {
        case errors.Is(err, ErrNotFound):
            response.NotFound(w, "User not found")
        case errors.Is(err, ErrUnauthorized):
            response.Text(w, http.StatusUnauthorized, "Unauthorized")
        default:
            // Log unexpected errors
            log.Printf("Error fetching user %s: %v", id, err)
            response.InternalServerError(w, "Internal server error")
        }
        return
    }

    response.OK(w, user)
}
```

## Context Usage

Always use `r.Context()` for cancellation and timeout handling:

```go
func longRunningOperation(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()

    // Pass context to database operations
    result, err := db.ComplexQuery(ctx, params)
    if err != nil {
        // Check if context was cancelled
        if ctx.Err() != nil {
            response.Text(w, http.StatusRequestTimeout, "Request timeout")
            return
        }
        response.InternalServerError(w, "Query failed")
        return
    }

    response.OK(w, result)
}
```

## Testing

Test HTTP handlers using Go's standard `httptest` package:

```go
package main

import (
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestGetUser(t *testing.T) {
    // Create test request
    req := httptest.NewRequest("GET", "/users/123", nil)
    w := httptest.NewRecorder()

    // Call handler
    getUser(w, req)

    // Assert response
    if w.Code != http.StatusOK {
        t.Errorf("Expected 200, got %d", w.Code)
    }
}
```

For more testing patterns, see the [Testing Guide](/docs/sdk/testkit.md).

## See Also

- [Queue Handlers](/docs/sdk/queue.md) - Async message processing
- [Middleware](/docs/sdk/middleware.md) - Request/response middleware patterns
- [Testing](/docs/sdk/testkit.md) - Testing HTTP handlers
- [Dependency Injection](/docs/sdk/di.md) - Injecting services into handlers
- [Error Handling](/docs/sdk/errors.md) - Error handling best practices
