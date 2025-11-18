# HTTP Handlers

Learn how to build HTTP APIs with Transire using the Chi router and standard Go HTTP patterns.

!!! tip "TL;DR"
    Transire uses the Chi router. Access it via `app.Router()` and use standard `http.HandlerFunc`, Chi middleware, and routing patterns you already know.

---

## Overview

Transire provides a fully-featured HTTP router via the **Chi router** ([`github.com/go-chi/chi/v5`](https://github.com/go-chi/chi)):

- **Standard Go patterns** – Use `http.HandlerFunc`, `http.Handler`, standard library patterns
- **Chi middleware** – Leverage Chi's extensive middleware ecosystem
- **RESTful routing** – Support for URL parameters, subrouters, method routing
- **Zero runtime abstraction** – Works identically in local development and AWS Lambda

Source: [`pkg/transire/app.go:25-30`](https://github.com/transire/transire/blob/main/pkg/transire/app.go)

---

## Basic HTTP Handler

### Simple Handler

```go
package main

import (
    "net/http"
    "github.com/transire/transire/pkg/transire"
)

func main() {
    app := transire.New()
    r := app.Router()

    r.Get("/health", healthHandler)

    app.Run(context.Background())
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("OK"))
}
```

---

### JSON Response

```go
import "encoding/json"

func getUserHandler(w http.ResponseWriter, r *http.Request) {
    user := map[string]interface{}{
        "id":    "123",
        "name":  "Alice",
        "email": "alice@example.com",
    }

    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(user)
}
```

---

### Reading Request Body

```go
type CreateUserRequest struct {
    Name  string `json:"name"`
    Email string `json:"email"`
}

func createUserHandler(w http.ResponseWriter, r *http.Request) {
    var req CreateUserRequest

    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    // Validate
    if req.Name == "" || req.Email == "" {
        http.Error(w, "Name and email required", http.StatusBadRequest)
        return
    }

    // Create user...
    user := map[string]interface{}{
        "id":    "new-id",
        "name":  req.Name,
        "email": req.Email,
    }

    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(user)
}
```

---

## Chi Router Features

### URL Parameters

```go
r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) {
    userID := chi.URLParam(r, "id")

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]string{
        "id": userID,
    })
})
```

---

### Method-Specific Routing

```go
// Different handlers for different HTTP methods
r.Get("/users/{id}", getUserHandler)
r.Put("/users/{id}", updateUserHandler)
r.Delete("/users/{id}", deleteUserHandler)

// Or handle multiple methods in one handler
r.HandleFunc("/users/{id}", func(w http.ResponseWriter, r *http.Request) {
    switch r.Method {
    case http.MethodGet:
        getUserHandler(w, r)
    case http.MethodPut:
        updateUserHandler(w, r)
    case http.MethodDelete:
        deleteUserHandler(w, r)
    default:
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
    }
})
```

---

### Subrouters

```go
r.Route("/api/v1", func(r chi.Router) {
    // All routes here are prefixed with /api/v1

    r.Get("/health", healthHandler)

    r.Route("/users", func(r chi.Router) {
        // Prefix: /api/v1/users
        r.Get("/", listUsersHandler)       // GET /api/v1/users
        r.Post("/", createUserHandler)     // POST /api/v1/users
        r.Get("/{id}", getUserHandler)     // GET /api/v1/users/{id}
        r.Put("/{id}", updateUserHandler)  // PUT /api/v1/users/{id}
        r.Delete("/{id}", deleteUserHandler) // DELETE /api/v1/users/{id}
    })
})
```

---

### Regexp Patterns

```go
// Only match numeric IDs
r.Get("/users/{id:[0-9]+}", getUserHandler)

// Match specific formats
r.Get("/files/{filename:[a-z0-9-]+\\.pdf}", getFileHandler)
```

---

## Middleware

### Built-in Chi Middleware

```go
import (
    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
)

func main() {
    app := transire.New()
    r := app.Router()

    // Apply middleware globally
    r.Use(middleware.Logger)          // Request logging
    r.Use(middleware.Recoverer)       // Recover from panics
    r.Use(middleware.RequestID)       // Add request ID header
    r.Use(middleware.RealIP)          // Detect real IP from headers
    r.Use(middleware.Compress(5))     // Gzip compression

    // Routes...
    r.Get("/health", healthHandler)

    app.Run(context.Background())
}
```

**Popular Chi middleware:**
- `middleware.Logger` – Log all requests
- `middleware.Recoverer` – Recover from panics
- `middleware.RequestID` – Generate unique request IDs
- `middleware.Timeout` – Request timeouts
- `middleware.Throttle` – Rate limiting
- `middleware.Compress` – Gzip compression

See: [Chi Middleware Documentation](https://github.com/go-chi/chi/tree/master/middleware)

---

### Custom Middleware

```go
func authMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")

        if token == "" {
            http.Error(w, "Unauthorized", http.StatusUnauthorized)
            return
        }

        // Validate token...
        if !isValidToken(token) {
            http.Error(w, "Invalid token", http.StatusUnauthorized)
            return
        }

        // Token valid, continue
        next.ServeHTTP(w, r)
    })
}

// Apply globally
r.Use(authMiddleware)

// Or apply to specific routes
r.Group(func(r chi.Router) {
    r.Use(authMiddleware)
    r.Get("/admin/users", listUsersHandler)
    r.Post("/admin/users", createUserHandler)
})
```

---

### Context Values in Middleware

```go
type contextKey string

const userContextKey contextKey = "user"

func authMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")

        // Validate and decode token
        user, err := validateToken(token)
        if err != nil {
            http.Error(w, "Unauthorized", http.StatusUnauthorized)
            return
        }

        // Add user to request context
        ctx := context.WithValue(r.Context(), userContextKey, user)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// Use in handler
func getUserHandler(w http.ResponseWriter, r *http.Request) {
    user := r.Context().Value(userContextKey).(*User)

    // User is authenticated, continue...
}
```

---

## Error Handling

### Standard Error Responses

```go
func getUserHandler(w http.ResponseWriter, r *http.Request) {
    userID := chi.URLParam(r, "id")

    user, err := db.GetUser(userID)
    if err == sql.ErrNoRows {
        http.Error(w, "User not found", http.StatusNotFound)
        return
    }
    if err != nil {
        http.Error(w, "Internal server error", http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(user)
}
```

---

### Structured Error Responses

```go
type ErrorResponse struct {
    Error   string `json:"error"`
    Message string `json:"message"`
    Code    int    `json:"code"`
}

func respondError(w http.ResponseWriter, message string, code int) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(code)
    json.NewEncoder(w).Encode(ErrorResponse{
        Error:   http.StatusText(code),
        Message: message,
        Code:    code,
    })
}

func getUserHandler(w http.ResponseWriter, r *http.Request) {
    userID := chi.URLParam(r, "id")

    user, err := db.GetUser(userID)
    if err == sql.ErrNoRows {
        respondError(w, "User not found", http.StatusNotFound)
        return
    }
    if err != nil {
        respondError(w, "Failed to fetch user", http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(user)
}
```

---

### Panic Recovery

Use Chi's `Recoverer` middleware:

```go
r.Use(middleware.Recoverer)
```

This catches panics and returns a 500 error instead of crashing your app.

---

## Request Validation

### Query Parameters

```go
func listUsersHandler(w http.ResponseWriter, r *http.Request) {
    // Parse query params
    limit := r.URL.Query().Get("limit")
    offset := r.URL.Query().Get("offset")

    // Set defaults
    limitInt := 10
    offsetInt := 0

    if limit != "" {
        if val, err := strconv.Atoi(limit); err == nil {
            limitInt = val
        }
    }

    if offset != "" {
        if val, err := strconv.Atoi(offset); err == nil {
            offsetInt = val
        }
    }

    // Fetch users with pagination
    users, err := db.ListUsers(limitInt, offsetInt)
    if err != nil {
        http.Error(w, "Failed to list users", http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(users)
}
```

---

### Request Body Validation

```go
type CreateUserRequest struct {
    Name  string `json:"name"`
    Email string `json:"email"`
}

func (r *CreateUserRequest) Validate() error {
    if r.Name == "" {
        return errors.New("name is required")
    }
    if r.Email == "" {
        return errors.New("email is required")
    }
    // Email format validation...
    if !strings.Contains(r.Email, "@") {
        return errors.New("invalid email format")
    }
    return nil
}

func createUserHandler(w http.ResponseWriter, r *http.Request) {
    var req CreateUserRequest

    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        respondError(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    if err := req.Validate(); err != nil {
        respondError(w, err.Error(), http.StatusBadRequest)
        return
    }

    // Create user...
}
```

---

## CORS Support

Use the Chi CORS middleware:

```go
import "github.com/go-chi/cors"

func main() {
    app := transire.New()
    r := app.Router()

    // CORS configuration
    r.Use(cors.Handler(cors.Options{
        AllowedOrigins:   []string{"https://*", "http://*"},
        AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
        AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type"},
        ExposedHeaders:   []string{"Link"},
        AllowCredentials: true,
        MaxAge:           300,
    }))

    // Routes...
    r.Get("/api/v1/users", listUsersHandler)

    app.Run(context.Background())
}
```

---

## Content Negotiation

### Accept Header

```go
func getUserHandler(w http.ResponseWriter, r *http.Request) {
    user := getUserFromDB(chi.URLParam(r, "id"))

    accept := r.Header.Get("Accept")

    switch accept {
    case "application/json":
        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(user)
    case "application/xml":
        w.Header().Set("Content-Type", "application/xml")
        xml.NewEncoder(w).Encode(user)
    default:
        // Default to JSON
        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(user)
    }
}
```

---

## Complete Example

```go
package main

import (
    "context"
    "encoding/json"
    "net/http"

    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
    "github.com/transire/transire/pkg/transire"
)

func main() {
    app := transire.New()
    r := app.Router()

    // Global middleware
    r.Use(middleware.Logger)
    r.Use(middleware.Recoverer)
    r.Use(middleware.RequestID)

    // Routes
    r.Get("/health", healthHandler)

    // API v1
    r.Route("/api/v1", func(r chi.Router) {
        // Users
        r.Route("/users", func(r chi.Router) {
            r.Get("/", listUsersHandler)
            r.Post("/", createUserHandler)
            r.Get("/{id}", getUserHandler)
            r.Put("/{id}", updateUserHandler)
            r.Delete("/{id}", deleteUserHandler)
        })

        // Posts (authenticated only)
        r.Group(func(r chi.Router) {
            r.Use(authMiddleware)
            r.Post("/posts", createPostHandler)
            r.Put("/posts/{id}", updatePostHandler)
            r.Delete("/posts/{id}", deletePostHandler)
        })
    })

    app.Run(context.Background())
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("OK"))
}

func listUsersHandler(w http.ResponseWriter, r *http.Request) {
    users := []map[string]string{
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"},
    }
    respondJSON(w, users, http.StatusOK)
}

func getUserHandler(w http.ResponseWriter, r *http.Request) {
    userID := chi.URLParam(r, "id")
    user := map[string]string{
        "id":   userID,
        "name": "Alice",
    }
    respondJSON(w, user, http.StatusOK)
}

func createUserHandler(w http.ResponseWriter, r *http.Request) {
    var req map[string]string
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        respondError(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    user := map[string]string{
        "id":   "new-id",
        "name": req["name"],
    }
    respondJSON(w, user, http.StatusCreated)
}

func updateUserHandler(w http.ResponseWriter, r *http.Request) {
    userID := chi.URLParam(r, "id")
    // Update logic...
    user := map[string]string{"id": userID, "name": "Updated"}
    respondJSON(w, user, http.StatusOK)
}

func deleteUserHandler(w http.ResponseWriter, r *http.Request) {
    userID := chi.URLParam(r, "id")
    // Delete logic...
    w.WriteHeader(http.StatusNoContent)
}

func authMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")
        if token == "" {
            respondError(w, "Unauthorized", http.StatusUnauthorized)
            return
        }
        next.ServeHTTP(w, r)
    })
}

func respondJSON(w http.ResponseWriter, data interface{}, status int) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(data)
}

func respondError(w http.ResponseWriter, message string, status int) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(map[string]string{"error": message})
}
```

---

## Testing HTTP Handlers

See the [Testing Guide](../guides/testing.md) for comprehensive HTTP handler testing patterns.

**Quick example:**

```go
import (
    "net/http/httptest"
    "testing"
)

func TestHealthHandler(t *testing.T) {
    req := httptest.NewRequest(http.MethodGet, "/health", nil)
    w := httptest.NewRecorder()

    healthHandler(w, req)

    if w.Code != http.StatusOK {
        t.Errorf("expected 200, got %d", w.Code)
    }
}
```

---

## Best Practices

### 1. Use Structured Logging

```go
import "log/slog"

func getUserHandler(w http.ResponseWriter, r *http.Request) {
    userID := chi.URLParam(r, "id")

    slog.Info("Fetching user", "user_id", userID)

    user, err := db.GetUser(userID)
    if err != nil {
        slog.Error("Failed to fetch user", "user_id", userID, "error", err)
        http.Error(w, "Internal server error", http.StatusInternalServerError)
        return
    }

    respondJSON(w, user, http.StatusOK)
}
```

---

### 2. Use Context for Cancellation

```go
func getUserHandler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context() // Use request context

    user, err := db.GetUserWithContext(ctx, chi.URLParam(r, "id"))
    if err != nil {
        http.Error(w, "Failed to fetch user", http.StatusInternalServerError)
        return
    }

    respondJSON(w, user, http.StatusOK)
}
```

---

### 3. Set Appropriate Timeouts

Lambda has a maximum execution time. Set reasonable timeouts:

```go
import "github.com/go-chi/chi/v5/middleware"

r.Use(middleware.Timeout(30 * time.Second))
```

Configure in `transire.yaml`:

```yaml
lambda:
  timeout_seconds: 30
```

---

### 4. Return Consistent Error Responses

Use a standard error response format:

```go
type ErrorResponse struct {
    Error   string `json:"error"`
    Message string `json:"message,omitempty"`
    Code    int    `json:"code"`
}
```

---

### 5. Validate All User Input

Never trust user input. Always validate:

- Request body JSON structure
- Required fields
- Field formats (email, phone, etc.)
- Field lengths
- Allowed values

---

## Next Steps

- [Queue Handlers](queue-handlers.md) – Process background tasks
- [Schedule Handlers](schedule-handlers.md) – Run cron jobs
- [Testing Guide](../guides/testing.md) – Test your HTTP handlers
- [Local Development](../guides/local-development.md) – Test locally with hot reload

---

## See Also

- [Chi Router Documentation](https://github.com/go-chi/chi)
- [Go HTTP Package](https://pkg.go.dev/net/http)
- [Chi Middleware](https://github.com/go-chi/chi/tree/master/middleware)
- [RESTful API Design](https://restfulapi.net/)
