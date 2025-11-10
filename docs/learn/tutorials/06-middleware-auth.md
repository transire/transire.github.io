---
title: "Tutorial: Middleware & Authentication"
description: Add authentication, logging, and cross-cutting concerns with middleware in 30 minutes
category: learn
subcategory: tutorial
complexity: beginner
duration: 30 minutes
prerequisites:
  - Completed Dependency Injection tutorial
  - Understanding of HTTP middleware concept
  - Go 1.22+
mcp_use: template
mcp_operations:
  - add_middleware
  - add_authentication
  - configure_cors
features_covered:
  - Middleware
  - Authentication
  - Authorization
  - CORS
  - Request logging
  - Middleware chaining
code_blocks: true
last_updated: 2025-11-10
---

# Tutorial: Middleware & Authentication

> **Quick Summary:** Add authentication, logging, and CORS with composable middleware

## What You'll Build

Add cross-cutting concerns to your orders API:

```
Request
  ↓
CORS Middleware
  ↓
Logging Middleware
  ↓
Authentication Middleware
  ↓
Handler
  ↓
Response
```

**Time:** 30 minutes • **Difficulty:** Beginner

---

## Why Use Middleware?

Middleware solves common concerns:

- **Authentication** - Verify user identity
- **Authorization** - Check permissions
- **Logging** - Track requests/responses
- **CORS** - Enable cross-origin requests
- **Rate limiting** - Prevent abuse
- **Request ID** - Trace requests
- **Error handling** - Consistent error responses

**When to use:**
- Authentication required for routes
- Logging all requests
- CORS headers needed
- Shared logic across handlers

---

## Understanding Middleware

Middleware wraps handlers to add behavior:

```go
type Middleware func(http.Handler) http.Handler

// Middleware execution flow
func middleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Before handler
        log.Println("Before")

        // Call next handler
        next.ServeHTTP(w, r)

        // After handler
        log.Println("After")
    })
}
```

**Middleware chains** execute in order:

```
Request → Middleware 1 → Middleware 2 → Handler → Middleware 2 → Middleware 1 → Response
```

---

## Step 1: Create Logging Middleware

Add request/response logging:

```go
package main

import (
    "log"
    "net/http"
    "time"
)

// LoggingMiddleware logs all HTTP requests
func LoggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()

        // Log incoming request
        log.Printf("[%s] %s %s", r.Method, r.URL.Path, r.RemoteAddr)

        // Wrap response writer to capture status code
        wrapped := &responseWriter{
            ResponseWriter: w,
            statusCode:     200, // Default
        }

        // Call next handler
        next.ServeHTTP(wrapped, r)

        // Log response
        duration := time.Since(start)
        log.Printf("[%s] %s %s - %d (%v)",
            r.Method,
            r.URL.Path,
            r.RemoteAddr,
            wrapped.statusCode,
            duration,
        )
    })
}

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
    http.ResponseWriter
    statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
    rw.statusCode = code
    rw.ResponseWriter.WriteHeader(code)
}
```

---

## Step 2: Create CORS Middleware

Enable cross-origin requests:

```go
// CORSMiddleware adds CORS headers
func CORSMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Set CORS headers
        w.Header().Set("Access-Control-Allow-Origin", "*")
        w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
        w.Header().Set("Access-Control-Max-Age", "86400") // 24 hours

        // Handle preflight requests
        if r.Method == "OPTIONS" {
            w.WriteHeader(http.StatusNoContent)
            return
        }

        // Call next handler
        next.ServeHTTP(w, r)
    })
}
```

**Production CORS config:**

```go
type CORSConfig struct {
    AllowedOrigins []string
    AllowedMethods []string
    AllowedHeaders []string
    MaxAge         int
}

func CORSMiddleware(config CORSConfig) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            origin := r.Header.Get("Origin")

            // Check if origin is allowed
            allowed := false
            for _, allowedOrigin := range config.AllowedOrigins {
                if allowedOrigin == "*" || allowedOrigin == origin {
                    allowed = true
                    break
                }
            }

            if allowed {
                w.Header().Set("Access-Control-Allow-Origin", origin)
                w.Header().Set("Access-Control-Allow-Methods",
                    strings.Join(config.AllowedMethods, ", "))
                w.Header().Set("Access-Control-Allow-Headers",
                    strings.Join(config.AllowedHeaders, ", "))
                w.Header().Set("Access-Control-Max-Age",
                    strconv.Itoa(config.MaxAge))
            }

            if r.Method == "OPTIONS" {
                w.WriteHeader(http.StatusNoContent)
                return
            }

            next.ServeHTTP(w, r)
        })
    }
}
```

---

## Step 3: Register Global Middleware

Add middleware to all routes:

```go
import "github.com/transire/transire-sdk-go"

func main() {
    app := transire.New()

    // Register services
    transire.Provide(func() *Database { return NewDatabase() })
    transire.Provide(func() *Logger { return NewLogger() })

    // Global middleware (applied to ALL routes)
    app.Use(CORSMiddleware)
    app.Use(LoggingMiddleware)

    // Routes
    app.GET("/orders", listOrders)
    app.POST("/orders", createOrder)
    app.GET("/orders/{id}", getOrder)

    app.Run()
}
```

**Execution order:**
```
CORS → Logging → Handler
```

---

## Step 4: Create Authentication Middleware

Verify JWT tokens:

```go
import (
    "context"
    "net/http"
    "strings"

    "github.com/transire/transire-sdk-go/response"
)

// AuthMiddleware validates JWT tokens
func AuthMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Extract token from Authorization header
        authHeader := r.Header.Get("Authorization")
        if authHeader == "" {
            response.Unauthorized(w, "Missing authorization header")
            return
        }

        // Expect: "Bearer <token>"
        parts := strings.Split(authHeader, " ")
        if len(parts) != 2 || parts[0] != "Bearer" {
            response.Unauthorized(w, "Invalid authorization header format")
            return
        }

        token := parts[1]

        // Validate token
        claims, err := validateJWT(token)
        if err != nil {
            response.Unauthorized(w, "Invalid or expired token")
            return
        }

        // Add user info to context
        ctx := context.WithValue(r.Context(), "user_id", claims.UserID)
        ctx = context.WithValue(ctx, "user_email", claims.Email)
        ctx = context.WithValue(ctx, "user_role", claims.Role)

        // Call next handler with enriched context
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// JWT claims structure
type JWTClaims struct {
    UserID string `json:"user_id"`
    Email  string `json:"email"`
    Role   string `json:"role"`
}

// validateJWT validates and parses JWT token
func validateJWT(tokenString string) (*JWTClaims, error) {
    // In production, use a proper JWT library like github.com/golang-jwt/jwt

    // For demo purposes, simple validation
    if tokenString == "" {
        return nil, fmt.Errorf("empty token")
    }

    // Parse token (simplified - use proper JWT lib in production)
    claims := &JWTClaims{
        UserID: "user-123",
        Email:  "user@example.com",
        Role:   "user",
    }

    return claims, nil
}
```

---

## Step 5: Protect Routes with Middleware

Apply middleware to specific routes:

```go
func main() {
    app := transire.New()

    // Global middleware (all routes)
    app.Use(CORSMiddleware)
    app.Use(LoggingMiddleware)

    // Public routes (no auth)
    app.GET("/health", healthCheck)
    app.POST("/auth/login", login)

    // Protected routes (with auth)
    app.Group(func(r transire.Router) {
        // Apply auth middleware to this group
        r.Use(AuthMiddleware)

        r.GET("/orders", listOrders)
        r.POST("/orders", createOrder)
        r.GET("/orders/{id}", getOrder)
        r.PUT("/orders/{id}", updateOrder)
        r.DELETE("/orders/{id}", deleteOrder)
    })

    app.Run()
}
```

**Middleware order:**

```
Public:    CORS → Logging → Handler
Protected: CORS → Logging → Auth → Handler
```

---

## Step 6: Access User Context in Handlers

Use authenticated user data:

```go
func listOrders(w http.ResponseWriter, r *http.Request, db *Database) {
    // Get user ID from context
    userID, ok := r.Context().Value("user_id").(string)
    if !ok {
        response.InternalServerError(w, "User context missing")
        return
    }

    // Get user role
    role, _ := r.Context().Value("user_role").(string)

    // Query based on role
    var orders []Order
    var err error

    if role == "admin" {
        // Admins see all orders
        orders, err = db.GetAllOrders(r.Context())
    } else {
        // Users see only their orders
        orders, err = db.GetOrdersByUser(r.Context(), userID)
    }

    if err != nil {
        response.InternalServerError(w, "Failed to fetch orders")
        return
    }

    response.OK(w, orders)
}

func createOrder(w http.ResponseWriter, r *http.Request, db *Database) {
    // Get user ID from context
    userID, ok := r.Context().Value("user_id").(string)
    if !ok {
        response.InternalServerError(w, "User context missing")
        return
    }

    var req CreateOrderRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        response.BadRequest(w, "Invalid JSON")
        return
    }

    // Create order for authenticated user
    order := &Order{
        ID:       generateID(),
        UserID:   userID, // From auth context
        Product:  req.Product,
        Quantity: req.Quantity,
        Price:    req.Price,
        Status:   "pending",
    }

    if err := db.CreateOrder(r.Context(), order); err != nil {
        response.InternalServerError(w, "Failed to create order")
        return
    }

    response.Created(w, order)
}
```

---

## Step 7: Authorization Middleware

Check permissions:

```go
// RequireRole middleware checks if user has required role
func RequireRole(role string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            userRole, ok := r.Context().Value("user_role").(string)
            if !ok {
                response.Forbidden(w, "Role information missing")
                return
            }

            if userRole != role {
                response.Forbidden(w, fmt.Sprintf("Requires %s role", role))
                return
            }

            next.ServeHTTP(w, r)
        })
    }
}

// Usage
func main() {
    app := transire.New()

    app.Use(CORSMiddleware)
    app.Use(LoggingMiddleware)

    // Public routes
    app.POST("/auth/login", login)

    // User routes (authenticated)
    app.Group(func(r transire.Router) {
        r.Use(AuthMiddleware)
        r.GET("/orders", listOrders)
        r.POST("/orders", createOrder)
    })

    // Admin routes (authenticated + admin role)
    app.Group(func(r transire.Router) {
        r.Use(AuthMiddleware)
        r.Use(RequireRole("admin"))

        r.GET("/admin/orders", listAllOrders)
        r.DELETE("/admin/orders/{id}", adminDeleteOrder)
        r.GET("/admin/users", listUsers)
    })

    app.Run()
}
```

---

## Step 8: Request ID Middleware

Track requests across services:

```go
import "github.com/google/uuid"

// RequestIDMiddleware adds unique ID to each request
func RequestIDMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Check if request already has ID (from upstream)
        requestID := r.Header.Get("X-Request-ID")
        if requestID == "" {
            // Generate new ID
            requestID = uuid.New().String()
        }

        // Add to context
        ctx := context.WithValue(r.Context(), "request_id", requestID)

        // Add to response headers
        w.Header().Set("X-Request-ID", requestID)

        // Call next handler
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// Use in logging
func LoggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()

        // Get request ID from context
        requestID, _ := r.Context().Value("request_id").(string)

        log.Printf("[%s] [%s] %s %s", requestID, r.Method, r.URL.Path, r.RemoteAddr)

        wrapped := &responseWriter{ResponseWriter: w, statusCode: 200}
        next.ServeHTTP(wrapped, r)

        duration := time.Since(start)
        log.Printf("[%s] [%s] %s - %d (%v)",
            requestID, r.Method, r.URL.Path, wrapped.statusCode, duration)
    })
}
```

---

## Middleware Best Practices

### Pattern 1: Configurable Middleware

```go
type RateLimitConfig struct {
    RequestsPerMinute int
    BurstSize         int
}

func RateLimitMiddleware(config RateLimitConfig) func(http.Handler) http.Handler {
    // Create rate limiter
    limiter := rate.NewLimiter(
        rate.Limit(config.RequestsPerMinute),
        config.BurstSize,
    )

    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            if !limiter.Allow() {
                response.TooManyRequests(w, "Rate limit exceeded")
                return
            }
            next.ServeHTTP(w, r)
        })
    }
}

// Usage
app.Use(RateLimitMiddleware(RateLimitConfig{
    RequestsPerMinute: 60,
    BurstSize:         10,
}))
```

### Pattern 2: Conditional Middleware

```go
// OnlyInProduction applies middleware only in production
func OnlyInProduction(middleware func(http.Handler) http.Handler) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        if os.Getenv("ENVIRONMENT") == "production" {
            return middleware(next)
        }
        return next
    }
}

// Usage
app.Use(OnlyInProduction(RateLimitMiddleware(config)))
```

### Pattern 3: Recovery Middleware

```go
// RecoveryMiddleware recovers from panics
func RecoveryMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                // Log panic with stack trace
                log.Printf("PANIC: %v\n%s", err, debug.Stack())

                // Return 500 error
                response.InternalServerError(w, "Internal server error")
            }
        }()

        next.ServeHTTP(w, r)
    })
}
```

### Pattern 4: Timeout Middleware

```go
// TimeoutMiddleware adds request timeout
func TimeoutMiddleware(timeout time.Duration) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            ctx, cancel := context.WithTimeout(r.Context(), timeout)
            defer cancel()

            // Channel to signal handler completion
            done := make(chan struct{})

            go func() {
                next.ServeHTTP(w, r.WithContext(ctx))
                close(done)
            }()

            select {
            case <-done:
                // Handler completed
                return
            case <-ctx.Done():
                // Timeout reached
                response.RequestTimeout(w, "Request timeout")
                return
            }
        })
    }
}
```

---

## Testing Middleware

### Unit Test

```go
func TestAuthMiddleware(t *testing.T) {
    // Create test handler
    handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        userID := r.Context().Value("user_id").(string)
        w.Write([]byte(userID))
    })

    // Wrap with middleware
    wrapped := AuthMiddleware(handler)

    // Test without token
    req := httptest.NewRequest("GET", "/orders", nil)
    rec := httptest.NewRecorder()
    wrapped.ServeHTTP(rec, req)

    if rec.Code != http.StatusUnauthorized {
        t.Errorf("Expected 401, got %d", rec.Code)
    }

    // Test with valid token
    req = httptest.NewRequest("GET", "/orders", nil)
    req.Header.Set("Authorization", "Bearer valid-token")
    rec = httptest.NewRecorder()
    wrapped.ServeHTTP(rec, req)

    if rec.Code != http.StatusOK {
        t.Errorf("Expected 200, got %d", rec.Code)
    }

    if body := rec.Body.String(); body != "user-123" {
        t.Errorf("Expected user-123, got %s", body)
    }
}
```

### Integration Test

```go
import "github.com/transire/transire-sdk-go/testkit"

func TestProtectedRoute(t *testing.T) {
    tk := testkit.New(t)

    // Setup app with middleware
    tk.Use(AuthMiddleware)
    tk.GET("/orders", listOrders)

    // Test without auth
    resp := tk.Get("/orders")
    tk.AssertStatus(401)

    // Test with auth
    resp = tk.Get("/orders", testkit.WithHeader("Authorization", "Bearer valid-token"))
    tk.AssertStatus(200)
}
```

---

## Common Patterns

### Pattern 1: Middleware Chain Order

```go
func main() {
    app := transire.New()

    // Order matters!
    app.Use(RecoveryMiddleware)    // 1. Catch panics first
    app.Use(RequestIDMiddleware)   // 2. Generate request ID
    app.Use(LoggingMiddleware)     // 3. Log with request ID
    app.Use(CORSMiddleware)        // 4. Set CORS headers
    app.Use(AuthMiddleware)        // 5. Authenticate last

    app.GET("/orders", listOrders)
    app.Run()
}
```

### Pattern 2: Composite Middleware

```go
// StandardMiddleware combines common middleware
func StandardMiddleware() []func(http.Handler) http.Handler {
    return []func(http.Handler) http.Handler{
        RecoveryMiddleware,
        RequestIDMiddleware,
        LoggingMiddleware,
        CORSMiddleware,
    }
}

func main() {
    app := transire.New()

    for _, mw := range StandardMiddleware() {
        app.Use(mw)
    }

    app.Run()
}
```

### Pattern 3: Per-Route Middleware

```go
func main() {
    app := transire.New()

    // Public route - no middleware
    app.GET("/health", healthCheck)

    // Rate-limited public route
    app.With(RateLimitMiddleware(config)).GET("/auth/login", login)

    // Authenticated routes
    app.Group(func(r transire.Router) {
        r.Use(AuthMiddleware)
        r.GET("/orders", listOrders)

        // Admin-only nested group
        r.Group(func(admin transire.Router) {
            admin.Use(RequireRole("admin"))
            admin.DELETE("/orders/{id}", deleteOrder)
        })
    })

    app.Run()
}
```

---

## Complete Code

```go
package main

import (
    "context"
    "fmt"
    "log"
    "net/http"
    "runtime/debug"
    "strings"
    "time"

    "github.com/transire/transire-sdk-go"
    "github.com/transire/transire-sdk-go/response"
)

func main() {
    app := transire.New()

    // Register services
    transire.Provide(func() *Database { return NewDatabase() })

    // Global middleware
    app.Use(RecoveryMiddleware)
    app.Use(RequestIDMiddleware)
    app.Use(LoggingMiddleware)
    app.Use(CORSMiddleware)

    // Public routes
    app.GET("/health", healthCheck)
    app.POST("/auth/login", login)

    // Protected routes
    app.Group(func(r transire.Router) {
        r.Use(AuthMiddleware)

        r.GET("/orders", listOrders)
        r.POST("/orders", createOrder)
        r.GET("/orders/{id}", getOrder)
    })

    // Admin routes
    app.Group(func(r transire.Router) {
        r.Use(AuthMiddleware)
        r.Use(RequireRole("admin"))

        r.GET("/admin/orders", listAllOrders)
        r.DELETE("/admin/orders/{id}", adminDeleteOrder)
    })

    app.Run()
}

// Middleware implementations
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

func RequestIDMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        requestID := r.Header.Get("X-Request-ID")
        if requestID == "" {
            requestID = fmt.Sprintf("req-%d", time.Now().UnixNano())
        }
        ctx := context.WithValue(r.Context(), "request_id", requestID)
        w.Header().Set("X-Request-ID", requestID)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

func LoggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        requestID, _ := r.Context().Value("request_id").(string)

        log.Printf("[%s] [%s] %s %s", requestID, r.Method, r.URL.Path, r.RemoteAddr)

        wrapped := &responseWriter{ResponseWriter: w, statusCode: 200}
        next.ServeHTTP(wrapped, r)

        duration := time.Since(start)
        log.Printf("[%s] [%s] %s - %d (%v)",
            requestID, r.Method, r.URL.Path, wrapped.statusCode, duration)
    })
}

type responseWriter struct {
    http.ResponseWriter
    statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
    rw.statusCode = code
    rw.ResponseWriter.WriteHeader(code)
}

func CORSMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Access-Control-Allow-Origin", "*")
        w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

        if r.Method == "OPTIONS" {
            w.WriteHeader(http.StatusNoContent)
            return
        }

        next.ServeHTTP(w, r)
    })
}

func AuthMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        authHeader := r.Header.Get("Authorization")
        if authHeader == "" {
            response.Unauthorized(w, "Missing authorization header")
            return
        }

        parts := strings.Split(authHeader, " ")
        if len(parts) != 2 || parts[0] != "Bearer" {
            response.Unauthorized(w, "Invalid authorization format")
            return
        }

        token := parts[1]
        claims, err := validateJWT(token)
        if err != nil {
            response.Unauthorized(w, "Invalid token")
            return
        }

        ctx := context.WithValue(r.Context(), "user_id", claims.UserID)
        ctx = context.WithValue(ctx, "user_email", claims.Email)
        ctx = context.WithValue(ctx, "user_role", claims.Role)

        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

func RequireRole(role string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            userRole, ok := r.Context().Value("user_role").(string)
            if !ok || userRole != role {
                response.Forbidden(w, fmt.Sprintf("Requires %s role", role))
                return
            }
            next.ServeHTTP(w, r)
        })
    }
}

type JWTClaims struct {
    UserID string
    Email  string
    Role   string
}

func validateJWT(token string) (*JWTClaims, error) {
    // Simplified - use proper JWT library in production
    if token == "" {
        return nil, fmt.Errorf("empty token")
    }
    return &JWTClaims{
        UserID: "user-123",
        Email:  "user@example.com",
        Role:   "user",
    }, nil
}

// Handlers
func healthCheck(w http.ResponseWriter, r *http.Request) {
    response.OK(w, map[string]string{"status": "healthy"})
}

func login(w http.ResponseWriter, r *http.Request) {
    // Login logic...
    response.OK(w, map[string]string{"token": "jwt-token"})
}

func listOrders(w http.ResponseWriter, r *http.Request, db *Database) {
    userID := r.Context().Value("user_id").(string)
    orders, _ := db.GetOrdersByUser(r.Context(), userID)
    response.OK(w, orders)
}

func createOrder(w http.ResponseWriter, r *http.Request, db *Database) {
    userID := r.Context().Value("user_id").(string)
    // Create order for user...
    response.Created(w, order)
}

func getOrder(w http.ResponseWriter, r *http.Request, db *Database) {
    // Get order...
    response.OK(w, order)
}

func listAllOrders(w http.ResponseWriter, r *http.Request, db *Database) {
    orders, _ := db.GetAllOrders(r.Context())
    response.OK(w, orders)
}

func adminDeleteOrder(w http.ResponseWriter, r *http.Request, db *Database) {
    // Delete order...
    response.NoContent(w)
}
```

---

## What You Learned

Congratulations! You've implemented middleware and authentication. You now know:

- ✅ How middleware works and chains
- ✅ How to create logging middleware
- ✅ How to implement CORS
- ✅ How to add JWT authentication
- ✅ How to implement authorization with roles
- ✅ How to apply middleware globally and per-route
- ✅ How to access user context in handlers
- ✅ Common middleware patterns
- ✅ Testing middleware

---

## Next Steps

### Deploy to Production

Continue to [Production Deployment Tutorial →](07-production-deployment.md) to learn how to deploy your complete application.

### Add More Middleware

```go
// Compression middleware
func CompressionMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if !strings.Contains(r.Header.Get("Accept-Encoding"), "gzip") {
            next.ServeHTTP(w, r)
            return
        }

        gz := gzip.NewWriter(w)
        defer gz.Close()

        gzw := &gzipResponseWriter{Writer: gz, ResponseWriter: w}
        gzw.Header().Set("Content-Encoding", "gzip")

        next.ServeHTTP(gzw, r)
    })
}

// API versioning middleware
func APIVersionMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        version := r.Header.Get("X-API-Version")
        if version == "" {
            version = "v1" // Default
        }
        ctx := context.WithValue(r.Context(), "api_version", version)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

---

## See Also

- [Middleware API Reference](../../reference/sdk/middleware-api/) - Complete middleware documentation
- [Authentication Guide](../../guides/patterns/security-patterns/) - Security patterns
- [Testing Guide](../../guides/testing/) - Test middleware
- [Production Deployment](07-production-deployment.md) - Deploy your app
- [Chi Middleware](https://github.com/go-chi/chi#middlewares) - Additional middleware options

