---
title: "Middleware"
category: sdk
complexity: intermediate
duration: 20 minutes
prerequisites:
  - Basic understanding of HTTP handlers
  - Familiarity with Transire SDK
mcp_use: reference
mcp_operations:
  - add_middleware
  - create_custom_middleware
features_covered:
  - Global middleware
  - Route-specific middleware
  - Middleware chains
  - Custom middleware
code_blocks: true
last_updated: 2025-10-30
---

# Middleware

## Overview

Middleware provides cross-cutting functionality that runs before and after your HTTP handlers. Common use cases:

- **Authentication/Authorization** - Verify user identity and permissions
- **Logging** - Record request/response details
- **CORS** - Handle cross-origin requests
- **Request validation** - Validate input before handler
- **Error recovery** - Catch panics and return proper errors
- **Rate limiting** - Throttle excessive requests

Transire middleware works identically in local and cloud modes.

## Basic Usage

### Global Middleware

Apply to all routes:

```go
package main

import (
    "log"
    "net/http"
    "time"
    "github.com/transire/transire-sdk-go"
)

func main() {
    app := transire.New()

    // Apply logging middleware to all routes
    app.Use(loggingMiddleware)

    // Apply authentication to all routes
    app.Use(authMiddleware)

    // Define routes
    app.GET("/users/{id}", getUser)
    app.POST("/users", createUser)

    app.Run()
}

func loggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()

        // Before handler
        log.Printf("Request: %s %s", r.Method, r.URL.Path)

        // Call next handler
        next.ServeHTTP(w, r)

        // After handler
        log.Printf("Completed in %v", time.Since(start))
    })
}
```

### Route-Specific Middleware

Apply to specific routes:

```go
func main() {
    app := transire.New()

    // Public routes (no auth)
    app.GET("/health", healthCheck)
    app.GET("/public/data", getPublicData)

    // Protected routes (with auth middleware)
    app.With(authMiddleware).Group(func(r chi.Router) {
        r.Get("/users/{id}", getUser)
        r.Post("/users", createUser)
        r.Delete("/users/{id}", deleteUser)
    })

    app.Run()
}
```

### Middleware Chains

Multiple middlewares execute in order:

```go
func main() {
    app := transire.New()

    // Global: logging → CORS → recovery
    app.Use(loggingMiddleware)
    app.Use(corsMiddleware)
    app.Use(recoveryMiddleware)

    // Admin routes: add auth + admin check
    app.With(authMiddleware, adminMiddleware).Group(func(r chi.Router) {
        r.Get("/admin/users", listAllUsers)
        r.Delete("/admin/users/{id}", deleteUser)
    })

    app.Run()
}
```

**Execution order:**
```
Request
  ↓
loggingMiddleware (before)
  ↓
corsMiddleware (before)
  ↓
recoveryMiddleware (before)
  ↓
authMiddleware (before)
  ↓
adminMiddleware (before)
  ↓
Handler (getUser)
  ↓
adminMiddleware (after)
  ↓
authMiddleware (after)
  ↓
recoveryMiddleware (after)
  ↓
corsMiddleware (after)
  ↓
loggingMiddleware (after)
  ↓
Response
```

## Built-in Middleware

### Recovery Middleware

Catch panics and return 500 errors:

```go
import "github.com/transire/transire-sdk-go/middleware"

func main() {
    app := transire.New()

    // Add panic recovery
    app.Use(middleware.Recoverer)

    app.GET("/risky", riskyHandler)
    app.Run()
}

func riskyHandler(w http.ResponseWriter, r *http.Request) {
    panic("something went wrong!")
    // Recovery middleware catches this, logs stack trace,
    // returns 500 Internal Server Error
}
```

### Request ID Middleware

Add unique ID to each request:

```go
import (
    "github.com/transire/transire-sdk-go/middleware"
    "github.com/google/uuid"
)

func main() {
    app := transire.New()

    // Add request ID to context
    app.Use(middleware.RequestID)

    // Access in handlers
    app.GET("/users/{id}", getUser)
    app.Run()
}

func getUser(w http.ResponseWriter, r *http.Request) {
    requestID := middleware.GetRequestID(r.Context())
    log.Printf("[%s] Fetching user", requestID)

    // Use requestID for tracing, logging, etc.
}
```

### Timeout Middleware

Set maximum request duration:

```go
import (
    "github.com/transire/transire-sdk-go/middleware"
    "time"
)

func main() {
    app := transire.New()

    // Timeout all requests after 30 seconds
    app.Use(middleware.Timeout(30 * time.Second))

    app.GET("/slow", slowHandler)
    app.Run()
}

func slowHandler(w http.ResponseWriter, r *http.Request) {
    select {
    case <-time.After(45 * time.Second):
        // This never completes
        w.Write([]byte("Done"))
    case <-r.Context().Done():
        // Timeout middleware cancels context after 30s
        log.Println("Request timed out")
        return
    }
}
```

### Real IP Middleware

Extract client IP from headers:

```go
import "github.com/transire/transire-sdk-go/middleware"

func main() {
    app := transire.New()

    // Extract real IP from X-Forwarded-For, X-Real-IP, etc.
    app.Use(middleware.RealIP)

    app.GET("/users/{id}", getUser)
    app.Run()
}

func getUser(w http.ResponseWriter, r *http.Request) {
    clientIP := r.RemoteAddr  // Now contains real IP (not proxy IP)
    log.Printf("Request from %s", clientIP)
}
```

## Custom Middleware

### Authentication Middleware

```go
import (
    "context"
    "net/http"
    "strings"
)

type contextKey string

const userContextKey contextKey = "user"

func authMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Extract token from Authorization header
        authHeader := r.Header.Get("Authorization")
        if authHeader == "" {
            http.Error(w, "Unauthorized", http.StatusUnauthorized)
            return
        }

        // Validate token (Bearer token)
        token := strings.TrimPrefix(authHeader, "Bearer ")
        user, err := validateToken(token)
        if err != nil {
            http.Error(w, "Invalid token", http.StatusUnauthorized)
            return
        }

        // Add user to context
        ctx := context.WithValue(r.Context(), userContextKey, user)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// Helper to get user from context
func getUser(ctx context.Context) (*User, bool) {
    user, ok := ctx.Value(userContextKey).(*User)
    return user, ok
}

// Usage in handler
func getProfile(w http.ResponseWriter, r *http.Request) {
    user, ok := getUser(r.Context())
    if !ok {
        http.Error(w, "Unauthorized", http.StatusUnauthorized)
        return
    }

    json.NewEncoder(w).Encode(user)
}
```

### Authorization Middleware

```go
func requireRole(role string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            user, ok := getUser(r.Context())
            if !ok {
                http.Error(w, "Unauthorized", http.StatusUnauthorized)
                return
            }

            if !user.HasRole(role) {
                http.Error(w, "Forbidden", http.StatusForbidden)
                return
            }

            next.ServeHTTP(w, r)
        })
    }
}

// Usage
func main() {
    app := transire.New()

    // Admin-only routes
    app.With(authMiddleware, requireRole("admin")).Group(func(r chi.Router) {
        r.Get("/admin/users", listAllUsers)
        r.Delete("/admin/users/{id}", deleteUser)
    })

    app.Run()
}
```

### CORS Middleware

```go
func corsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Set CORS headers
        w.Header().Set("Access-Control-Allow-Origin", "*")
        w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

        // Handle preflight requests
        if r.Method == "OPTIONS" {
            w.WriteHeader(http.StatusOK)
            return
        }

        next.ServeHTTP(w, r)
    })
}
```

### Rate Limiting Middleware

```go
import (
    "sync"
    "time"
)

type rateLimiter struct {
    mu       sync.Mutex
    requests map[string][]time.Time
    limit    int
    window   time.Duration
}

func newRateLimiter(limit int, window time.Duration) *rateLimiter {
    return &rateLimiter{
        requests: make(map[string][]time.Time),
        limit:    limit,
        window:   window,
    }
}

func (rl *rateLimiter) middleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        clientIP := r.RemoteAddr

        rl.mu.Lock()
        defer rl.mu.Unlock()

        now := time.Now()
        cutoff := now.Add(-rl.window)

        // Remove old requests
        var recent []time.Time
        for _, t := range rl.requests[clientIP] {
            if t.After(cutoff) {
                recent = append(recent, t)
            }
        }

        // Check limit
        if len(recent) >= rl.limit {
            http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
            return
        }

        // Record this request
        recent = append(recent, now)
        rl.requests[clientIP] = recent

        next.ServeHTTP(w, r)
    })
}

// Usage
func main() {
    app := transire.New()

    // 100 requests per minute per IP
    limiter := newRateLimiter(100, time.Minute)
    app.Use(limiter.middleware)

    app.GET("/api/data", getData)
    app.Run()
}
```

### Request Validation Middleware

```go
func validateJSONMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Only validate POST/PUT/PATCH
        if r.Method != "POST" && r.Method != "PUT" && r.Method != "PATCH" {
            next.ServeHTTP(w, r)
            return
        }

        // Check Content-Type
        contentType := r.Header.Get("Content-Type")
        if !strings.HasPrefix(contentType, "application/json") {
            http.Error(w, "Content-Type must be application/json", http.StatusBadRequest)
            return
        }

        // Validate body is valid JSON (peek without consuming)
        body, err := io.ReadAll(r.Body)
        if err != nil {
            http.Error(w, "Failed to read body", http.StatusBadRequest)
            return
        }
        defer r.Body.Close()

        if !json.Valid(body) {
            http.Error(w, "Invalid JSON", http.StatusBadRequest)
            return
        }

        // Restore body for handler
        r.Body = io.NopCloser(bytes.NewBuffer(body))

        next.ServeHTTP(w, r)
    })
}
```

### Logging Middleware

```go
import (
    "log"
    "net/http"
    "time"
)

type responseWriter struct {
    http.ResponseWriter
    statusCode int
    bytesWritten int
}

func (rw *responseWriter) WriteHeader(statusCode int) {
    rw.statusCode = statusCode
    rw.ResponseWriter.WriteHeader(statusCode)
}

func (rw *responseWriter) Write(b []byte) (int, error) {
    n, err := rw.ResponseWriter.Write(b)
    rw.bytesWritten += n
    return n, err
}

func loggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()

        // Wrap response writer to capture status code
        rw := &responseWriter{
            ResponseWriter: w,
            statusCode:     http.StatusOK,
        }

        // Call next handler
        next.ServeHTTP(rw, r)

        // Log request details
        log.Printf(
            "%s %s %d %d bytes %v",
            r.Method,
            r.URL.Path,
            rw.statusCode,
            rw.bytesWritten,
            time.Since(start),
        )
    })
}
```

### Structured Logging Middleware

```go
import (
    "encoding/json"
    "log"
    "net/http"
    "time"
)

func structuredLoggingMiddleware(next http.Handler) http.Handler {
    return http.Handler Func(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()

        rw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
        next.ServeHTTP(rw, r)

        // Log as JSON
        logEntry := map[string]interface{}{
            "timestamp":    time.Now().Unix(),
            "method":       r.Method,
            "path":         r.URL.Path,
            "status":       rw.statusCode,
            "duration_ms":  time.Since(start).Milliseconds(),
            "bytes":        rw.bytesWritten,
            "user_agent":   r.UserAgent(),
            "remote_addr":  r.RemoteAddr,
        }

        if requestID := middleware.GetRequestID(r.Context()); requestID != "" {
            logEntry["request_id"] = requestID
        }

        json.NewEncoder(os.Stdout).Encode(logEntry)
    })
}
```

## Middleware Patterns

### Conditional Middleware

```go
func conditionalMiddleware(condition func(*http.Request) bool, mw func(http.Handler) http.Handler) func(http.Handler) http.Handler {
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

// Usage: Only log non-health-check requests
func main() {
    app := transire.New()

    app.Use(conditionalMiddleware(
        func(r *http.Request) bool {
            return r.URL.Path != "/health"
        },
        loggingMiddleware,
    ))

    app.GET("/health", healthCheck)
    app.GET("/users/{id}", getUser)
    app.Run()
}
```

### Middleware with Configuration

```go
type LoggerConfig struct {
    SkipPaths   []string
    LogHeaders  bool
    LogBody     bool
}

func loggerMiddleware(config LoggerConfig) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            // Skip logging for certain paths
            for _, path := range config.SkipPaths {
                if r.URL.Path == path {
                    next.ServeHTTP(w, r)
                    return
                }
            }

            log.Printf("Request: %s %s", r.Method, r.URL.Path)

            if config.LogHeaders {
                log.Printf("Headers: %v", r.Header)
            }

            if config.LogBody && r.Method != "GET" {
                body, _ := io.ReadAll(r.Body)
                log.Printf("Body: %s", string(body))
                r.Body = io.NopCloser(bytes.NewBuffer(body))
            }

            next.ServeHTTP(w, r)
        })
    }
}

// Usage
func main() {
    app := transire.New()

    app.Use(loggerMiddleware(LoggerConfig{
        SkipPaths:  []string{"/health", "/metrics"},
        LogHeaders: true,
        LogBody:    false,
    }))

    app.Run()
}
```

### Dependency Injection in Middleware

```go
func authMiddleware(authService *AuthService) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            token := r.Header.Get("Authorization")
            user, err := authService.ValidateToken(r.Context(), token)
            if err != nil {
                http.Error(w, "Unauthorized", http.StatusUnauthorized)
                return
            }

            ctx := context.WithValue(r.Context(), userContextKey, user)
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}

// Usage
func main() {
    app := transire.New()

    // Inject dependencies into middleware
    authService := NewAuthService()
    app.Use(authMiddleware(authService))

    app.Run()
}
```

## Testing Middleware

### Unit Testing

```go
import (
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestAuthMiddleware(t *testing.T) {
    tests := []struct {
        name           string
        authHeader     string
        expectedStatus int
    }{
        {
            name:           "valid token",
            authHeader:     "Bearer valid-token",
            expectedStatus: http.StatusOK,
        },
        {
            name:           "missing token",
            authHeader:     "",
            expectedStatus: http.StatusUnauthorized,
        },
        {
            name:           "invalid token",
            authHeader:     "Bearer invalid-token",
            expectedStatus: http.StatusUnauthorized,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Create test handler
            handler := authMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
                w.WriteHeader(http.StatusOK)
            }))

            // Create test request
            req := httptest.NewRequest("GET", "/test", nil)
            if tt.authHeader != "" {
                req.Header.Set("Authorization", tt.authHeader)
            }

            // Record response
            rr := httptest.NewRecorder()
            handler.ServeHTTP(rr, req)

            // Assert status code
            if rr.Code != tt.expectedStatus {
                t.Errorf("Expected status %d, got %d", tt.expectedStatus, rr.Code)
            }
        })
    }
}
```

## See Also

- [HTTP Handlers](/sdk/http.md) - HTTP handler basics
- [Error Handling](/sdk/errors.md) - Error handling patterns
- [Testing](/sdk/testkit.md) - Testing middleware and handlers
- [Middleware Patterns Guide](/guides/middleware-patterns.md) - Advanced patterns
