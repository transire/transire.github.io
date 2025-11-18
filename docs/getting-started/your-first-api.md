# Your First API

Build a complete REST API for a todo list application with Transire.

!!! tip "TL;DR"
    Build a todo API with CRUD operations, database integration, and proper error handling. This tutorial takes ~20 minutes and teaches you Transire fundamentals through a practical example.

---

## What You'll Build

A **Todo List API** with:

- **CRUD operations** (Create, Read, Update, Delete)
- **PostgreSQL database** integration
- **Input validation** and error handling
- **Chi router** patterns
- **Local testing** with hot reload
- **AWS deployment** ready

**API Endpoints:**
- `GET /todos` – List all todos
- `GET /todos/{id}` – Get single todo
- `POST /todos` – Create todo
- `PUT /todos/{id}` – Update todo
- `DELETE /todos/{id}` – Delete todo

---

## Prerequisites

1. **Complete [Installation](installation.md)** – Go, Transire CLI installed
2. **PostgreSQL** – Local install or Docker
3. **[Quickstart](quickstart.md)** completed (recommended)

---

## Step 1: Project Setup

### Create Project

```bash
mkdir todo-api
cd todo-api
transire init
```

**Output:**
```
✓ Created transire.yaml
✓ Created main.go
✓ Created go.mod
✓ Created .gitignore

Next steps:
  1. Run 'go mod tidy' to install dependencies
  2. Run 'transire run' to start development server
```

---

### Install Dependencies

```bash
go mod tidy
go get github.com/lib/pq  # PostgreSQL driver
```

---

### Setup Database

**Using Docker:**
```bash
docker run --name postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=todos \
  -p 5432:5432 \
  -d postgres:15
```

**Using local PostgreSQL:**
```bash
createdb todos
```

---

### Create Database Schema

Create `schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS todos (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_todos_completed ON todos(completed);
```

**Apply schema:**
```bash
psql -d todos < schema.sql
```

---

## Step 2: Database Connection

### Create Database Package

Create `db/db.go`:

```go
package db

import (
    "database/sql"
    "fmt"
    "os"

    _ "github.com/lib/pq"
)

var DB *sql.DB

func Connect() error {
    dbURL := os.Getenv("DATABASE_URL")
    if dbURL == "" {
        dbURL = "postgres://postgres:postgres@localhost:5432/todos?sslmode=disable"
    }

    var err error
    DB, err = sql.Open("postgres", dbURL)
    if err != nil {
        return fmt.Errorf("failed to open database: %w", err)
    }

    if err := DB.Ping(); err != nil {
        return fmt.Errorf("failed to ping database: %w", err)
    }

    return nil
}

func Close() error {
    if DB != nil {
        return DB.Close()
    }
    return nil
}
```

---

## Step 3: Todo Model

Create `models/todo.go`:

```go
package models

import "time"

type Todo struct {
    ID          int       `json:"id"`
    Title       string    `json:"title"`
    Description string    `json:"description"`
    Completed   bool      `json:"completed"`
    CreatedAt   time.Time `json:"created_at"`
    UpdatedAt   time.Time `json:"updated_at"`
}

type CreateTodoRequest struct {
    Title       string `json:"title"`
    Description string `json:"description"`
}

func (r *CreateTodoRequest) Validate() error {
    if r.Title == "" {
        return ErrTitleRequired
    }
    return nil
}

type UpdateTodoRequest struct {
    Title       *string `json:"title,omitempty"`
    Description *string `json:"description,omitempty"`
    Completed   *bool   `json:"completed,omitempty"`
}

// Errors
var (
    ErrTitleRequired = fmt.Errorf("title is required")
    ErrTodoNotFound  = fmt.Errorf("todo not found")
)
```

---

## Step 4: Todo Repository

Create `repository/todo.go`:

```go
package repository

import (
    "context"
    "database/sql"
    "time"

    "todo-api/db"
    "todo-api/models"
)

func ListTodos(ctx context.Context) ([]models.Todo, error) {
    query := `
        SELECT id, title, description, completed, created_at, updated_at
        FROM todos
        ORDER BY created_at DESC
    `

    rows, err := db.DB.QueryContext(ctx, query)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var todos []models.Todo
    for rows.Next() {
        var todo models.Todo
        if err := rows.Scan(
            &todo.ID,
            &todo.Title,
            &todo.Description,
            &todo.Completed,
            &todo.CreatedAt,
            &todo.UpdatedAt,
        ); err != nil {
            return nil, err
        }
        todos = append(todos, todo)
    }

    return todos, rows.Err()
}

func GetTodo(ctx context.Context, id int) (*models.Todo, error) {
    query := `
        SELECT id, title, description, completed, created_at, updated_at
        FROM todos
        WHERE id = $1
    `

    var todo models.Todo
    err := db.DB.QueryRowContext(ctx, query, id).Scan(
        &todo.ID,
        &todo.Title,
        &todo.Description,
        &todo.Completed,
        &todo.CreatedAt,
        &todo.UpdatedAt,
    )

    if err == sql.ErrNoRows {
        return nil, models.ErrTodoNotFound
    }
    if err != nil {
        return nil, err
    }

    return &todo, nil
}

func CreateTodo(ctx context.Context, req models.CreateTodoRequest) (*models.Todo, error) {
    query := `
        INSERT INTO todos (title, description)
        VALUES ($1, $2)
        RETURNING id, title, description, completed, created_at, updated_at
    `

    var todo models.Todo
    err := db.DB.QueryRowContext(ctx, query, req.Title, req.Description).Scan(
        &todo.ID,
        &todo.Title,
        &todo.Description,
        &todo.Completed,
        &todo.CreatedAt,
        &todo.UpdatedAt,
    )

    if err != nil {
        return nil, err
    }

    return &todo, nil
}

func UpdateTodo(ctx context.Context, id int, req models.UpdateTodoRequest) (*models.Todo, error) {
    // Build dynamic update query
    query := `UPDATE todos SET updated_at = $1`
    args := []interface{}{time.Now()}
    argPos := 2

    if req.Title != nil {
        query += fmt.Sprintf(", title = $%d", argPos)
        args = append(args, *req.Title)
        argPos++
    }
    if req.Description != nil {
        query += fmt.Sprintf(", description = $%d", argPos)
        args = append(args, *req.Description)
        argPos++
    }
    if req.Completed != nil {
        query += fmt.Sprintf(", completed = $%d", argPos)
        args = append(args, *req.Completed)
        argPos++
    }

    query += fmt.Sprintf(" WHERE id = $%d RETURNING id, title, description, completed, created_at, updated_at", argPos)
    args = append(args, id)

    var todo models.Todo
    err := db.DB.QueryRowContext(ctx, query, args...).Scan(
        &todo.ID,
        &todo.Title,
        &todo.Description,
        &todo.Completed,
        &todo.CreatedAt,
        &todo.UpdatedAt,
    )

    if err == sql.ErrNoRows {
        return nil, models.ErrTodoNotFound
    }
    if err != nil {
        return nil, err
    }

    return &todo, nil
}

func DeleteTodo(ctx context.Context, id int) error {
    query := `DELETE FROM todos WHERE id = $1`

    result, err := db.DB.ExecContext(ctx, query, id)
    if err != nil {
        return err
    }

    rows, err := result.RowsAffected()
    if err != nil {
        return err
    }

    if rows == 0 {
        return models.ErrTodoNotFound
    }

    return nil
}
```

---

## Step 5: HTTP Handlers

Create `handlers/todos.go`:

```go
package handlers

import (
    "encoding/json"
    "net/http"
    "strconv"

    "github.com/go-chi/chi/v5"

    "todo-api/models"
    "todo-api/repository"
)

func ListTodos(w http.ResponseWriter, r *http.Request) {
    todos, err := repository.ListTodos(r.Context())
    if err != nil {
        respondError(w, "Failed to list todos", http.StatusInternalServerError)
        return
    }

    respondJSON(w, todos, http.StatusOK)
}

func GetTodo(w http.ResponseWriter, r *http.Request) {
    id, err := strconv.Atoi(chi.URLParam(r, "id"))
    if err != nil {
        respondError(w, "Invalid todo ID", http.StatusBadRequest)
        return
    }

    todo, err := repository.GetTodo(r.Context(), id)
    if err == models.ErrTodoNotFound {
        respondError(w, "Todo not found", http.StatusNotFound)
        return
    }
    if err != nil {
        respondError(w, "Failed to get todo", http.StatusInternalServerError)
        return
    }

    respondJSON(w, todo, http.StatusOK)
}

func CreateTodo(w http.ResponseWriter, r *http.Request) {
    var req models.CreateTodoRequest

    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        respondError(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    if err := req.Validate(); err != nil {
        respondError(w, err.Error(), http.StatusBadRequest)
        return
    }

    todo, err := repository.CreateTodo(r.Context(), req)
    if err != nil {
        respondError(w, "Failed to create todo", http.StatusInternalServerError)
        return
    }

    respondJSON(w, todo, http.StatusCreated)
}

func UpdateTodo(w http.ResponseWriter, r *http.Request) {
    id, err := strconv.Atoi(chi.URLParam(r, "id"))
    if err != nil {
        respondError(w, "Invalid todo ID", http.StatusBadRequest)
        return
    }

    var req models.UpdateTodoRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        respondError(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    todo, err := repository.UpdateTodo(r.Context(), id, req)
    if err == models.ErrTodoNotFound {
        respondError(w, "Todo not found", http.StatusNotFound)
        return
    }
    if err != nil {
        respondError(w, "Failed to update todo", http.StatusInternalServerError)
        return
    }

    respondJSON(w, todo, http.StatusOK)
}

func DeleteTodo(w http.ResponseWriter, r *http.Request) {
    id, err := strconv.Atoi(chi.URLParam(r, "id"))
    if err != nil {
        respondError(w, "Invalid todo ID", http.StatusBadRequest)
        return
    }

    if err := repository.DeleteTodo(r.Context(), id); err == models.ErrTodoNotFound {
        respondError(w, "Todo not found", http.StatusNotFound)
        return
    } else if err != nil {
        respondError(w, "Failed to delete todo", http.StatusInternalServerError)
        return
    }

    w.WriteHeader(http.StatusNoContent)
}

// Helper functions
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

## Step 6: Main Application

Update `main.go`:

```go
package main

import (
    "context"
    "log"

    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
    "github.com/transire/transire/pkg/transire"

    "todo-api/db"
    "todo-api/handlers"
)

func main() {
    // Connect to database
    if err := db.Connect(); err != nil {
        log.Fatalf("Failed to connect to database: %v", err)
    }
    defer db.Close()

    // Create Transire app
    app := transire.New()
    r := app.Router()

    // Middleware
    r.Use(middleware.Logger)
    r.Use(middleware.Recoverer)
    r.Use(middleware.RequestID)

    // Routes
    r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        w.Write([]byte("OK"))
    })

    r.Route("/todos", func(r chi.Router) {
        r.Get("/", handlers.ListTodos)
        r.Post("/", handlers.CreateTodo)
        r.Get("/{id}", handlers.GetTodo)
        r.Put("/{id}", handlers.UpdateTodo)
        r.Delete("/{id}", handlers.DeleteTodo)
    })

    // Run app
    app.Run(context.Background())
}
```

---

## Step 7: Configuration

Update `transire.yaml`:

```yaml
name: todo-api

development:
  http_port: 3000
  auto_reload: true
  log_level: debug

lambda:
  architecture: arm64
  timeout_seconds: 30
  memory_mb: 256

environment:
  DATABASE_URL: ${DATABASE_URL}
```

---

## Step 8: Local Testing

### Start Development Server

```bash
export DATABASE_URL="postgres://postgres:postgres@localhost:5432/todos?sslmode=disable"
transire run
```

**Output:**
```
[INFO] Transire starting in local mode
[INFO] Starting HTTP server on :3000
[INFO] Ready! Watching for file changes...
```

---

### Test Endpoints

**Health check:**
```bash
curl http://localhost:3000/health
# => OK
```

**Create todo:**
```bash
curl -X POST http://localhost:3000/todos \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy groceries","description":"Milk, eggs, bread"}'
```

**Response:**
```json
{
  "id": 1,
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "completed": false,
  "created_at": "2025-01-18T10:00:00Z",
  "updated_at": "2025-01-18T10:00:00Z"
}
```

**List todos:**
```bash
curl http://localhost:3000/todos
```

**Get single todo:**
```bash
curl http://localhost:3000/todos/1
```

**Update todo:**
```bash
curl -X PUT http://localhost:3000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed":true}'
```

**Delete todo:**
```bash
curl -X DELETE http://localhost:3000/todos/1
```

---

## Step 9: Add Tests

Create `handlers/todos_test.go`:

```go
package handlers

import (
    "bytes"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/go-chi/chi/v5"
)

func TestCreateTodo(t *testing.T) {
    // Setup
    payload := map[string]string{
        "title":       "Test todo",
        "description": "Test description",
    }
    body, _ := json.Marshal(payload)

    req := httptest.NewRequest(http.MethodPost, "/todos", bytes.NewReader(body))
    req.Header.Set("Content-Type", "application/json")
    w := httptest.NewRecorder()

    // Execute
    CreateTodo(w, req)

    // Assert
    if w.Code != http.StatusCreated {
        t.Errorf("expected status 201, got %d", w.Code)
    }

    var response map[string]interface{}
    json.NewDecoder(w.Body).Decode(&response)

    if response["title"] != "Test todo" {
        t.Errorf("expected title 'Test todo', got %v", response["title"])
    }
}
```

**Run tests:**
```bash
go test ./...
```

---

## Step 10: Deploy to AWS

### Build

```bash
transire build
```

### Deploy

```bash
# Configure AWS credentials first
aws configure

# Deploy
transire deploy
```

**Output:**
```
✅  todo-api-stack

Outputs:
todo-api-stack.ApiEndpoint = https://abc123.execute-api.us-east-1.amazonaws.com
```

### Setup RDS Database

For production, use AWS RDS instead of local PostgreSQL.

---

## What You Learned

✅ **Project structure** – Organize code with models, repositories, handlers
✅ **Database integration** – Connect to PostgreSQL, execute queries
✅ **REST API patterns** – CRUD operations, error handling, validation
✅ **Chi router** – URL parameters, routing, middleware
✅ **Testing** – Unit tests for HTTP handlers
✅ **Local development** – Hot reload, testing endpoints
✅ **AWS deployment** – Build and deploy to Lambda + API Gateway

---

## Next Steps

### Enhance Your API

- **[Add queue processing](../guides/queue-processing.md)** – Background jobs
- **[Add scheduled tasks](../core-concepts/schedule-handlers.md)** – Daily cleanup, reports

### Learn More

- **[HTTP Handlers](../core-concepts/http-handlers.md)** – Advanced routing patterns
- **[Testing Guide](../guides/testing.md)** – Comprehensive testing strategies
- **[Deploying to AWS](../guides/deploying-to-aws.md)** – Production deployment best practices

---

## Complete Code

The complete working code for this tutorial is available at:

[github.com/transire/transire/tree/main/examples/todo-api](https://github.com/transire/transire/tree/main/examples/todo-api)

---

## Troubleshooting

### Database Connection Failed

**Problem:** `failed to connect to database`

**Solutions:**
- Verify PostgreSQL is running: `docker ps` or `pg_isready`
- Check DATABASE_URL is correct
- Ensure database exists: `createdb todos`

---

### Handler Not Found

**Problem:** `404 Not Found` for valid endpoints

**Solutions:**
- Restart `transire run` to re-discover routes
- Verify route registration in `main.go`
- Check for typos in URL paths

---

### Hot Reload Not Working

**Problem:** Code changes don't trigger rebuild

**Solutions:**
- Check `auto_reload: true` in `transire.yaml`
- Ensure you're editing `.go` files (not other files)
- Restart `transire run`

---

## See Also

- [Quickstart Guide](quickstart.md) – 5-minute introduction
- [Application & Runtime](../core-concepts/application-runtime.md) – How Transire works
- [HTTP Handlers](../core-concepts/http-handlers.md) – HTTP patterns
- [Simple API Example](../examples/simple-api.md) – Another complete example
