---
title: "Middleware Patterns"
category: guides
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - HTTP handler experience
  - Middleware basics
mcp_use: reference
features_covered:
  - Middleware patterns
  - Request/response processing
  - Cross-cutting concerns
code_blocks: true
last_updated: 2025-10-31
---

# Middleware Patterns

This guide covers common middleware patterns for Transire applications.

## Overview

Middleware in Transire wraps HTTP handlers to add cross-cutting concerns like:
- Authentication
- Logging
- Rate limiting
- CORS
- Request tracing
- Error handling

## Basic Middleware

### Simple Middleware

Standard Go middleware pattern:

```go
func LoggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()

        log.Printf("Started %s %s", r.Method, r.URL.Path)

        next.ServeHTTP(w, r)

        log.Printf("Completed in %v", time.Since(start))
    })
}

func main() {
    app := transire.New()

    // Apply globally
    app.Use(LoggingMiddleware)

    app.GET("/users", GetUsers)
    app.Run()
}
```

### Response Writer Wrapping

Capture response details:

```go
type ResponseRecorder struct {
    http.ResponseWriter
    StatusCode int
    BytesWritten int
}

func (r *ResponseRecorder) WriteHeader(statusCode int) {
    r.StatusCode = statusCode
    r.ResponseWriter.WriteHeader(statusCode)
}

func (r *ResponseRecorder) Write(b []byte) (int, error) {
    n, err := r.ResponseWriter.Write(b)
    r.BytesWritten += n
    return n, err
}

func MetricsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        recorder := &ResponseRecorder{
            ResponseWriter: w,
            StatusCode: 200,
        }

        start := time.Now()
        next.ServeHTTP(recorder, r)
        duration := time.Since(start)

        // Record metrics
        metrics.RecordRequest(
            r.Method,
            r.URL.Path,
            recorder.StatusCode,
            duration,
            recorder.BytesWritten,
        )
    })
}
```

## Authentication Middleware

### Bearer Token Authentication

```go
func AuthMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        authHeader := r.Header.Get("Authorization")
        if authHeader == "" {
            response.Text(w, http.StatusUnauthorized, "Missing authorization header")
            return
        }

        parts := strings.Split(authHeader, " ")
        if len(parts) != 2 || parts[0] != "Bearer" {
            response.Text(w, http.StatusUnauthorized, "Invalid authorization header")
            return
        }

        token := parts[1]

        // Validate token
        claims, err := validateToken(token)
        if err != nil {
            response.Text(w, http.StatusUnauthorized, "Invalid token")
            return
        }

        // Add claims to context
        ctx := context.WithValue(r.Context(), "user_id", claims.UserID)
        ctx = context.WithValue(ctx, "user_role", claims.Role)

        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// Apply to specific routes
func main() {
    app := transire.New()

    // Public routes
    app.GET("/health", HealthCheck)

    // Protected routes - apply auth middleware
    protected := app.Group("/api")
    protected.Use(AuthMiddleware)
    protected.GET("/users", GetUsers)
    protected.POST("/orders", CreateOrder)

    app.Run()
}
```

### Role-Based Access Control

```go
func RequireRole(roles ...string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            userRole := r.Context().Value("user_role").(string)

            hasRole := false
            for _, role := range roles {
                if role == userRole {
                    hasRole = true
                    break
                }
            }

            if !hasRole {
                response.Text(w, http.StatusForbidden, "Insufficient permissions")
                return
            }

            next.ServeHTTP(w, r)
        })
    }
}

func main() {
    app := transire.New()

    // Admin-only routes
    admin := app.Group("/admin")
    admin.Use(AuthMiddleware)
    admin.Use(RequireRole("admin"))
    admin.GET("/users", ListAllUsers)
    admin.DELETE("/users/{id}", DeleteUser)

    app.Run()
}
```

## Rate Limiting

### Token Bucket Rate Limiter

```go
type RateLimiter struct {
    requests map[string]*bucket
    mu       sync.Mutex
}

type bucket struct {
    tokens    int
    lastRefill time.Time
}

func NewRateLimiter() *RateLimiter {
    return &RateLimiter{
        requests: make(map[string]*bucket),
    }
}

func (rl *RateLimiter) Allow(key string, rate int, per time.Duration) bool {
    rl.mu.Lock()
    defer rl.mu.Unlock()

    b, exists := rl.requests[key]
    if !exists {
        b = &bucket{
            tokens:    rate,
            lastRefill: time.Now(),
        }
        rl.requests[key] = b
    }

    // Refill tokens
    now := time.Now()
    elapsed := now.Sub(b.lastRefill)
    tokensToAdd := int(elapsed / per)
    if tokensToAdd > 0 {
        b.tokens = min(rate, b.tokens+tokensToAdd)
        b.lastRefill = now
    }

    // Check if request allowed
    if b.tokens > 0 {
        b.tokens--
        return true
    }

    return false
}

func RateLimitMiddleware(limiter *RateLimiter) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            // Use IP or user ID as key
            key := r.RemoteAddr

            if !limiter.Allow(key, 100, time.Minute) {
                response.Text(w, http.StatusTooManyRequests, "Rate limit exceeded")
                return
            }

            next.ServeHTTP(w, r)
        })
    }
}

func main() {
    app := transire.New()

    limiter := NewRateLimiter()
    app.Use(RateLimitMiddleware(limiter))

    app.Run()
}
```

## CORS Middleware

```go
func CORSMiddleware(allowedOrigins []string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            origin := r.Header.Get("Origin")

            // Check if origin is allowed
            allowed := false
            for _, o := range allowedOrigins {
                if o == "*" || o == origin {
                    allowed = true
                    break
                }
            }

            if allowed {
                w.Header().Set("Access-Control-Allow-Origin", origin)
                w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
                w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
                w.Header().Set("Access-Control-Max-Age", "86400")
            }

            // Handle preflight
            if r.Method == "OPTIONS" {
                w.WriteHeader(http.StatusNoContent)
                return
            }

            next.ServeHTTP(w, r)
        })
    }
}

func main() {
    app := transire.New()

    app.Use(CORSMiddleware([]string{
        "https://example.com",
        "https://app.example.com",
    }))

    app.Run()
}
```

## Request Tracing

### Trace ID Propagation

```go
func TraceMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Get or generate trace ID
        traceID := r.Header.Get("X-Trace-ID")
        if traceID == "" {
            traceID = generateTraceID()
        }

        // Add to response headers
        w.Header().Set("X-Trace-ID", traceID)

        // Add to context
        ctx := context.WithValue(r.Context(), "trace_id", traceID)

        // Add to logger
        logger := &Logger{TraceID: traceID}
        ctx = context.WithValue(ctx, "logger", logger)

        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

func generateTraceID() string {
    return fmt.Sprintf("%d-%s", time.Now().UnixNano(), randomString(8))
}
```

## Request Validation

### JSON Validation Middleware

```go
func ValidateJSONMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if r.Method != "GET" && r.Method != "DELETE" {
            contentType := r.Header.Get("Content-Type")
            if !strings.Contains(contentType, "application/json") {
                response.BadRequest(w, "Content-Type must be application/json")
                return
            }

            // Check if body is valid JSON
            var js json.RawMessage
            if err := json.NewDecoder(r.Body).Decode(&js); err != nil {
                response.BadRequest(w, "Invalid JSON")
                return
            }

            // Reset body for handler
            r.Body = io.NopCloser(bytes.NewBuffer(js))
        }

        next.ServeHTTP(w, r)
    })
}
```

## Timeout Middleware

```go
func TimeoutMiddleware(timeout time.Duration) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            ctx, cancel := context.WithTimeout(r.Context(), timeout)
            defer cancel()

            done := make(chan struct{})

            go func() {
                next.ServeHTTP(w, r.WithContext(ctx))
                close(done)
            }()

            select {
            case <-done:
                // Handler completed
            case <-ctx.Done():
                // Timeout exceeded
                response.Text(w, http.StatusRequestTimeout, "Request timeout")
            }
        })
    }
}

func main() {
    app := transire.New()

    // 30 second timeout for all requests
    app.Use(TimeoutMiddleware(30 * time.Second))

    app.Run()
}
```

## Panic Recovery

```go
func RecoveryMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                log.Printf("Panic: %v\n%s", err, debug.Stack())

                // Send error to monitoring service
                reportError(fmt.Errorf("panic: %v", err))

                response.InternalServerError(w, "Internal server error")
            }
        }()

        next.ServeHTTP(w, r)
    })
}
```

## Middleware Chaining

### Compose Multiple Middleware

```go
func Chain(middlewares ...func(http.Handler) http.Handler) func(http.Handler) http.Handler {
    return func(final http.Handler) http.Handler {
        for i := len(middlewares) - 1; i >= 0; i-- {
            final = middlewares[i](final)
        }
        return final
    }
}

func main() {
    app := transire.New()

    // Apply multiple middleware at once
    app.Use(Chain(
        RecoveryMiddleware,
        LoggingMiddleware,
        TraceMiddleware,
        CORSMiddleware([]string{"*"}),
    ))

    app.Run()
}
```

## Conditional Middleware

```go
func ConditionalMiddleware(condition func(*http.Request) bool, mw func(http.Handler) http.Handler) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            if condition(r) {
                mw(next).ServeHTTP(w, r)
            } else {
                next.ServeHTTP(w, r)
            }
        })
    }
}

// Example: Only apply auth to /api routes
func main() {
    app := transire.New()

    app.Use(ConditionalMiddleware(
        func(r *http.Request) bool {
            return strings.HasPrefix(r.URL.Path, "/api")
        },
        AuthMiddleware,
    ))

    app.Run()
}
```

## Best Practices

1. **Order matters** - Apply middleware in correct order (recovery → logging → auth)
2. **Keep middleware focused** - One responsibility per middleware
3. **Avoid heavy operations** - Middleware runs on every request
4. **Use context for sharing** - Pass data through context, not globals
5. **Handle errors gracefully** - Don't panic in middleware
6. **Test middleware independently** - Unit test each middleware
7. **Document side effects** - Clearly document what middleware does
8. **Consider performance** - Profile middleware impact

## Testing Middleware

```go
func TestAuthMiddleware(t *testing.T) {
    // Create test handler
    handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        userID := r.Context().Value("user_id").(string)
        w.Write([]byte(userID))
    })

    // Wrap with middleware
    wrapped := AuthMiddleware(handler)

    // Test without auth
    req := httptest.NewRequest("GET", "/test", nil)
    w := httptest.NewRecorder()
    wrapped.ServeHTTP(w, req)

    if w.Code != http.StatusUnauthorized {
        t.Errorf("Expected 401, got %d", w.Code)
    }

    // Test with valid auth
    req = httptest.NewRequest("GET", "/test", nil)
    req.Header.Set("Authorization", "Bearer valid-token")
    w = httptest.NewRecorder()
    wrapped.ServeHTTP(w, req)

    if w.Code != http.StatusOK {
        t.Errorf("Expected 200, got %d", w.Code)
    }
}
```

## See Also

- [Middleware](/sdk/middleware.md)
- [HTTP Handlers](/sdk/http.md)
- [Testing Guide](/sdk/testkit.md)
- [DI Patterns](/guides/di-patterns.md)
