---
title: HTTP API Reference
description: Complete reference for Transire HTTP handlers, routing, and request/response types
category: reference
subcategory: sdk
complexity: beginner
mcp_use: reference
features_covered:
  - HTTP routing
  - Request handling
  - Response helpers
  - Path parameters
  - Query parameters
  - Middleware
code_blocks: true
last_updated: 2025-11-10
---

# HTTP API Reference

> **Complete reference** for building HTTP APIs with Transire

## Table of Contents

- [Handler Registration](#handler-registration)
- [Handler Signatures](#handler-signatures)
- [Request Types](#request-types)
- [Response Helpers](#response-helpers)
- [Path Parameters](#path-parameters)
- [Query Parameters](#query-parameters)
- [Headers](#headers)
- [Middleware](#middleware)
- [Error Handling](#error-handling)
- [Testing](#testing)

---

## Handler Registration

### GET

Register a GET handler:

```go
app.GET(path string, handler HandlerFunc)
```

**Example:**

```go
app.GET("/orders", listOrders)
app.GET("/orders/{id}", getOrder)
```

### POST

Register a POST handler:

```go
app.POST(path string, handler HandlerFunc)
```

**Example:**

```go
app.POST("/orders", createOrder)
```

### PUT

Register a PUT handler:

```go
app.PUT(path string, handler HandlerFunc)
```

**Example:**

```go
app.PUT("/orders/{id}", updateOrder)
```

### PATCH

Register a PATCH handler:

```go
app.PATCH(path string, handler HandlerFunc)
```

**Example:**

```go
app.PATCH("/orders/{id}", partialUpdateOrder)
```

### DELETE

Register a DELETE handler:

```go
app.DELETE(path string, handler HandlerFunc)
```

**Example:**

```go
app.DELETE("/orders/{id}", deleteOrder)
```

### OPTIONS

Register an OPTIONS handler:

```go
app.OPTIONS(path string, handler HandlerFunc)
```

**Example:**

```go
app.OPTIONS("/orders", corsPreflightHandler)
```

### HEAD

Register a HEAD handler:

```go
app.HEAD(path string, handler HandlerFunc)
```

**Example:**

```go
app.HEAD("/orders/{id}", checkOrderExists)
```

---

## Handler Signatures

Transire supports multiple handler signatures:

### Standard Handler

```go
func(w http.ResponseWriter, r *http.Request)
```

**Example:**

```go
func listOrders(w http.ResponseWriter, r *http.Request) {
    response.OK(w, orders)
}
```

### Handler with Dependencies

```go
func(w http.ResponseWriter, r *http.Request, deps ...interface{})
```

**Example:**

```go
func listOrders(w http.ResponseWriter, r *http.Request, db *Database, logger *Logger) {
    logger.Info("Listing orders")
    orders, _ := db.GetOrders(r.Context())
    response.OK(w, orders)
}
```

### Typed Input Handler

```go
func(w http.ResponseWriter, r *http.Request, input T, deps ...interface{})
```

**Example:**

```go
type CreateOrderRequest struct {
    Product  string  `json:"product" validate:"required"`
    Quantity int     `json:"quantity" validate:"min=1"`
    Price    float64 `json:"price" validate:"min=0"`
}

func createOrder(w http.ResponseWriter, r *http.Request, req CreateOrderRequest, db *Database) {
    // Request is automatically parsed and validated
    order := &Order{
        Product:  req.Product,
        Quantity: req.Quantity,
        Price:    req.Price,
    }
    db.CreateOrder(r.Context(), order)
    response.Created(w, order)
}
```

---

## Request Types

### HTTPRequest

Access request data:

```go
type http.Request struct {
    Method     string
    URL        *url.URL
    Header     http.Header
    Body       io.ReadCloser
    Host       string
    RemoteAddr string
    Context    context.Context
}
```

**Example:**

```go
func handler(w http.ResponseWriter, r *http.Request) {
    // Method
    method := r.Method  // "GET", "POST", etc.

    // URL path
    path := r.URL.Path  // "/orders/123"

    // Headers
    contentType := r.Header.Get("Content-Type")
    auth := r.Header.Get("Authorization")

    // Body
    var req CreateOrderRequest
    json.NewDecoder(r.Body).Decode(&req)

    // Remote address
    ip := r.RemoteAddr

    // Context
    ctx := r.Context()
}
```

### Reading JSON Body

```go
import "encoding/json"

func createOrder(w http.ResponseWriter, r *http.Request) {
    var req CreateOrderRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        response.BadRequest(w, "Invalid JSON: "+err.Error())
        return
    }

    // Use req...
}
```

### Reading Form Data

```go
func createOrder(w http.ResponseWriter, r *http.Request) {
    if err := r.ParseForm(); err != nil {
        response.BadRequest(w, "Invalid form data")
        return
    }

    product := r.FormValue("product")
    quantity, _ := strconv.Atoi(r.FormValue("quantity"))

    // Use values...
}
```

### Reading Multipart Form

```go
func uploadFile(w http.ResponseWriter, r *http.Request) {
    // Parse multipart form (max 10MB)
    if err := r.ParseMultipartForm(10 << 20); err != nil {
        response.BadRequest(w, "Invalid form")
        return
    }

    // Get file
    file, header, err := r.FormFile("file")
    if err != nil {
        response.BadRequest(w, "File required")
        return
    }
    defer file.Close()

    // Read file
    data, _ := io.ReadAll(file)

    // Get form fields
    description := r.FormValue("description")
}
```

---

## Response Helpers

### Success Responses

#### OK (200)

```go
response.OK(w http.ResponseWriter, data interface{})
```

**Example:**

```go
response.OK(w, map[string]string{"status": "healthy"})
```

#### Created (201)

```go
response.Created(w http.ResponseWriter, data interface{})
```

**Example:**

```go
order := &Order{ID: "123", Product: "Widget"}
w.Header().Set("Location", "/orders/123")
response.Created(w, order)
```

#### Accepted (202)

```go
response.Accepted(w http.ResponseWriter, data interface{})
```

**Example:**

```go
response.Accepted(w, map[string]string{"message": "Processing"})
```

#### NoContent (204)

```go
response.NoContent(w http.ResponseWriter)
```

**Example:**

```go
func deleteOrder(w http.ResponseWriter, r *http.Request, db *Database) {
    id := transire.URLParam(r, "id")
    db.DeleteOrder(r.Context(), id)
    response.NoContent(w)
}
```

### Client Error Responses

#### BadRequest (400)

```go
response.BadRequest(w http.ResponseWriter, message string)
```

**Example:**

```go
if req.Quantity <= 0 {
    response.BadRequest(w, "Quantity must be positive")
    return
}
```

#### Unauthorized (401)

```go
response.Unauthorized(w http.ResponseWriter, message string)
```

**Example:**

```go
if !validateToken(token) {
    response.Unauthorized(w, "Invalid or expired token")
    return
}
```

#### Forbidden (403)

```go
response.Forbidden(w http.ResponseWriter, message string)
```

**Example:**

```go
if user.Role != "admin" {
    response.Forbidden(w, "Admin access required")
    return
}
```

#### NotFound (404)

```go
response.NotFound(w http.ResponseWriter, message string)
```

**Example:**

```go
if err == sql.ErrNoRows {
    response.NotFound(w, "Order not found")
    return
}
```

#### MethodNotAllowed (405)

```go
response.MethodNotAllowed(w http.ResponseWriter, message string)
```

#### Conflict (409)

```go
response.Conflict(w http.ResponseWriter, message string)
```

**Example:**

```go
if orderExists {
    response.Conflict(w, "Order already exists")
    return
}
```

#### UnprocessableEntity (422)

```go
response.UnprocessableEntity(w http.ResponseWriter, message string)
```

**Example:**

```go
if !validateEmail(email) {
    response.UnprocessableEntity(w, "Invalid email format")
    return
}
```

#### TooManyRequests (429)

```go
response.TooManyRequests(w http.ResponseWriter, message string)
```

**Example:**

```go
if !rateLimiter.Allow() {
    response.TooManyRequests(w, "Rate limit exceeded")
    return
}
```

### Server Error Responses

#### InternalServerError (500)

```go
response.InternalServerError(w http.ResponseWriter, message string)
```

**Example:**

```go
if err != nil {
    log.Printf("Database error: %v", err)
    response.InternalServerError(w, "Failed to fetch orders")
    return
}
```

#### ServiceUnavailable (503)

```go
response.ServiceUnavailable(w http.ResponseWriter, message string)
```

**Example:**

```go
if !dbHealthCheck() {
    response.ServiceUnavailable(w, "Database unavailable")
    return
}
```

### Custom Response

```go
response.JSON(w http.ResponseWriter, status int, data interface{})
```

**Example:**

```go
response.JSON(w, 418, map[string]string{"error": "I'm a teapot"})
```

### Text Response

```go
response.Text(w http.ResponseWriter, status int, text string)
```

**Example:**

```go
response.Text(w, 200, "OK")
```

### HTML Response

```go
response.HTML(w http.ResponseWriter, status int, html string)
```

**Example:**

```go
response.HTML(w, 200, "<h1>Hello, World!</h1>")
```

---

## Path Parameters

### Defining Path Parameters

Use `{name}` syntax:

```go
app.GET("/orders/{id}", getOrder)
app.GET("/users/{userID}/orders/{orderID}", getUserOrder)
```

### Extracting Path Parameters

```go
import "github.com/go-chi/chi/v5"

func getOrder(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")

    // Use id...
}

func getUserOrder(w http.ResponseWriter, r *http.Request) {
    userID := transire.URLParam(r, "userID")
    orderID := transire.URLParam(r, "orderID")

    // Use IDs...
}
```

### Wildcard Parameters

Capture remaining path:

```go
app.GET("/files/{path...}", serveFile)
```

**Example:**

```go
func serveFile(w http.ResponseWriter, r *http.Request) {
    path := transire.URLParam(r, "path")
    // path could be "folder/subfolder/file.txt"

    http.ServeFile(w, r, "/var/files/"+path)
}
```

---

## Query Parameters

### Reading Query Parameters

```go
func listOrders(w http.ResponseWriter, r *http.Request) {
    // Single value
    status := r.URL.Query().Get("status")  // "" if not present

    // With default
    page := r.URL.Query().Get("page")
    if page == "" {
        page = "1"
    }

    // Parse to int
    limit, err := strconv.Atoi(r.URL.Query().Get("limit"))
    if err != nil {
        limit = 10  // Default
    }

    // Multiple values
    tags := r.URL.Query()["tag"]  // []string{"tag1", "tag2"}
}
```

### Example: Pagination

```go
type PaginationParams struct {
    Page  int
    Limit int
}

func getPagination(r *http.Request) PaginationParams {
    page, _ := strconv.Atoi(r.URL.Query().Get("page"))
    if page < 1 {
        page = 1
    }

    limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
    if limit < 1 || limit > 100 {
        limit = 10
    }

    return PaginationParams{Page: page, Limit: limit}
}

func listOrders(w http.ResponseWriter, r *http.Request, db *Database) {
    params := getPagination(r)

    orders, _ := db.GetOrders(r.Context(), params.Page, params.Limit)
    response.OK(w, orders)
}
```

### Example: Filtering

```go
type FilterParams struct {
    Status    string
    MinPrice  float64
    MaxPrice  float64
    SortBy    string
    SortOrder string
}

func getFilters(r *http.Request) FilterParams {
    minPrice, _ := strconv.ParseFloat(r.URL.Query().Get("min_price"), 64)
    maxPrice, _ := strconv.ParseFloat(r.URL.Query().Get("max_price"), 64)

    sortBy := r.URL.Query().Get("sort_by")
    if sortBy == "" {
        sortBy = "created_at"
    }

    sortOrder := r.URL.Query().Get("sort_order")
    if sortOrder != "asc" && sortOrder != "desc" {
        sortOrder = "desc"
    }

    return FilterParams{
        Status:    r.URL.Query().Get("status"),
        MinPrice:  minPrice,
        MaxPrice:  maxPrice,
        SortBy:    sortBy,
        SortOrder: sortOrder,
    }
}
```

---

## Headers

### Reading Headers

```go
func handler(w http.ResponseWriter, r *http.Request) {
    // Standard headers
    contentType := r.Header.Get("Content-Type")
    accept := r.Header.Get("Accept")
    userAgent := r.Header.Get("User-Agent")

    // Authorization
    auth := r.Header.Get("Authorization")

    // Custom headers
    requestID := r.Header.Get("X-Request-ID")
    apiVersion := r.Header.Get("X-API-Version")

    // Check if header exists
    if r.Header.Get("X-Custom-Header") != "" {
        // Header is present
    }

    // Get all values (multi-value header)
    cookies := r.Header["Cookie"]  // []string
}
```

### Setting Response Headers

```go
func handler(w http.ResponseWriter, r *http.Request) {
    // Set header before WriteHeader or Write
    w.Header().Set("Content-Type", "application/json")
    w.Header().Set("X-Request-ID", requestID)
    w.Header().Set("Cache-Control", "no-cache")

    // Location header for 201 Created
    w.Header().Set("Location", "/orders/123")

    // Add header (doesn't replace existing)
    w.Header().Add("Set-Cookie", "session=abc123")

    // Delete header
    w.Header().Del("X-Debug-Info")
}
```

---

## Middleware

### Global Middleware

Apply to all routes:

```go
app.Use(middleware func(http.Handler) http.Handler)
```

**Example:**

```go
func LoggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        log.Printf("[%s] %s", r.Method, r.URL.Path)

        next.ServeHTTP(w, r)

        log.Printf("[%s] %s - %v", r.Method, r.URL.Path, time.Since(start))
    })
}

app.Use(LoggingMiddleware)
```

### Route-Specific Middleware

Apply to specific route:

```go
app.With(middleware).GET(path, handler)
```

**Example:**

```go
app.With(AuthMiddleware).GET("/admin/orders", listAllOrders)
```

### Grouped Middleware

Apply to group of routes:

```go
app.Group(func(r transire.Router) {
    r.Use(AuthMiddleware)
    r.Use(AdminMiddleware)

    r.GET("/admin/orders", listAllOrders)
    r.DELETE("/admin/orders/{id}", deleteOrder)
})
```

### Middleware Chain Order

```go
app.Use(Middleware1)  // Runs first
app.Use(Middleware2)  // Runs second
app.Use(Middleware3)  // Runs third

// Request flow:
// Request → Middleware1 → Middleware2 → Middleware3 → Handler → Middleware3 → Middleware2 → Middleware1 → Response
```

---

## Error Handling

### Standard Error Pattern

```go
func getOrder(w http.ResponseWriter, r *http.Request, db *Database) {
    id := transire.URLParam(r, "id")

    order, err := db.GetOrder(r.Context(), id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            response.NotFound(w, "Order not found")
            return
        }
        log.Printf("Database error: %v", err)
        response.InternalServerError(w, "Failed to fetch order")
        return
    }

    response.OK(w, order)
}
```

### Structured Error Response

```go
type ErrorResponse struct {
    Error struct {
        Code    string `json:"code"`
        Message string `json:"message"`
    } `json:"error"`
}

func respondError(w http.ResponseWriter, status int, code, message string) {
    resp := ErrorResponse{}
    resp.Error.Code = code
    resp.Error.Message = message

    response.JSON(w, status, resp)
}

// Usage
if !validateEmail(email) {
    respondError(w, 400, "INVALID_EMAIL", "Email format is invalid")
    return
}
```

### Panic Recovery

```go
func RecoveryMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                log.Printf("PANIC: %v\n%s", err, debug.Stack())
                response.InternalServerError(w, "Internal server error")
            }
        }()

        next.ServeHTTP(w, r)
    })
}

app.Use(RecoveryMiddleware)
```

---

## Testing

### Testing Handlers

```go
import (
    "net/http/httptest"
    "testing"
)

func TestListOrders(t *testing.T) {
    // Create test request
    req := httptest.NewRequest("GET", "/orders", nil)

    // Create response recorder
    rec := httptest.NewRecorder()

    // Mock dependencies
    mockDB := &MockDatabase{
        orders: []Order{
            {ID: "1", Product: "Widget"},
        },
    }

    // Call handler
    listOrders(rec, req, mockDB)

    // Assert response
    if rec.Code != http.StatusOK {
        t.Errorf("Expected 200, got %d", rec.Code)
    }

    // Assert body
    var orders []Order
    json.NewDecoder(rec.Body).Decode(&orders)

    if len(orders) != 1 {
        t.Errorf("Expected 1 order, got %d", len(orders))
    }
}
```

### Testing with Testkit

```go
import "github.com/transire/sdk-go/testkit"

func TestOrdersAPI(t *testing.T) {
    tk := testkit.New(t)

    // Register routes
    tk.GET("/orders", listOrders)
    tk.POST("/orders", createOrder)

    // Test GET
    resp := tk.Get("/orders")
    tk.AssertStatus(200)
    tk.AssertJSONArray()

    // Test POST
    resp = tk.Post("/orders", map[string]interface{}{
        "product":  "Widget",
        "quantity": 5,
        "price":    99.99,
    })
    tk.AssertStatus(201)
    tk.AssertHeader("Location", "/orders/")
}
```

---

## Common Patterns

### Pattern: Resource CRUD

```go
func main() {
    app := transire.New()

    // List all
    app.GET("/orders", listOrders)

    // Get one
    app.GET("/orders/{id}", getOrder)

    // Create
    app.POST("/orders", createOrder)

    // Update (full replacement)
    app.PUT("/orders/{id}", updateOrder)

    // Partial update
    app.PATCH("/orders/{id}", patchOrder)

    // Delete
    app.DELETE("/orders/{id}", deleteOrder)

    app.Run()
}
```

### Pattern: Nested Resources

```go
// User's orders
app.GET("/users/{userID}/orders", getUserOrders)
app.POST("/users/{userID}/orders", createUserOrder)

// Specific user's order
app.GET("/users/{userID}/orders/{orderID}", getUserOrder)
```

### Pattern: Health Check

```go
app.GET("/health", func(w http.ResponseWriter, r *http.Request) {
    response.OK(w, map[string]string{"status": "healthy"})
})

app.GET("/health/ready", func(w http.ResponseWriter, r *http.Request, db *Database) {
    if err := db.Ping(r.Context()); err != nil {
        response.ServiceUnavailable(w, "Database unavailable")
        return
    }
    response.OK(w, map[string]string{"status": "ready"})
})
```

### Pattern: Versioned API

```go
// v1
app.Group(func(r transire.Router) {
    r.GET("/v1/orders", listOrdersV1)
    r.POST("/v1/orders", createOrderV1)
})

// v2
app.Group(func(r transire.Router) {
    r.GET("/v2/orders", listOrdersV2)
    r.POST("/v2/orders", createOrderV2)
})
```

---

## Performance Tips

### 1. Reuse JSON Encoder

```go
var encoderPool = sync.Pool{
    New: func() interface{} {
        return json.NewEncoder(nil)
    },
}

func respondJSON(w http.ResponseWriter, data interface{}) {
    w.Header().Set("Content-Type", "application/json")

    enc := encoderPool.Get().(*json.Encoder)
    defer encoderPool.Put(enc)

    enc.Reset(w)
    enc.Encode(data)
}
```

### 2. Streaming Responses

```go
func streamOrders(w http.ResponseWriter, r *http.Request, db *Database) {
    w.Header().Set("Content-Type", "application/json")
    w.Header().Set("Transfer-Encoding", "chunked")

    enc := json.NewEncoder(w)

    rows, _ := db.QueryOrders(r.Context())
    defer rows.Close()

    w.Write([]byte("["))
    first := true

    for rows.Next() {
        var order Order
        rows.Scan(&order)

        if !first {
            w.Write([]byte(","))
        }
        first = false

        enc.Encode(order)
        w.(http.Flusher).Flush()
    }

    w.Write([]byte("]"))
}
```

### 3. Response Compression

```go
import "github.com/go-chi/chi/v5/middleware"

app.Use(middleware.Compress(5))  // Gzip compression
```

---

## See Also

- [HTTP Tutorial](../../learn/tutorials/02-rest-api/) - Build REST API
- [Middleware Reference](middleware-api/) - Middleware patterns
- [Response Helpers](response-helpers/) - All response methods
- [Testing Guide](../../guides/testing/) - Test HTTP handlers

