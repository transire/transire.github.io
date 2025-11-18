# Todo App Example

A comprehensive example application demonstrating database integration, authentication, and real-world patterns.

!!! tip "TL;DR"
    The todo-app example shows a complete todo list application with user authentication, database persistence, queue-based notifications, and scheduled reminders. Perfect for learning real-world Transire patterns.

---

## Overview

The **todo-app** example demonstrates:

- **Database Integration** – PostgreSQL with migrations
- **Authentication** – JWT-based auth
- **CRUD Operations** – Todo item management
- **Queue Processing** – Email notifications
- **Scheduled Tasks** – Daily reminder emails
- **Error Handling** – Production-ready patterns

**Location:** [`examples/todo-app/`](https://github.com/transire/transire/tree/main/examples/todo-app)

---

## Features

### User Authentication
- User registration and login
- JWT token generation and validation
- Password hashing with bcrypt
- Protected routes with middleware

### Todo Management
- Create, read, update, delete todos
- Mark todos as complete
- List todos with filters
- User-specific todos

### Background Processing
- Welcome email on registration (queue)
- Todo completion notifications (queue)
- Daily reminder emails (scheduler)

### Database
- PostgreSQL with connection pooling
- Database migrations
- Transaction support
- Prepared statements

---

## Project Structure

```
todo-app/
├── main.go                  # Application entry point
├── handlers/
│   ├── auth.go             # Authentication handlers
│   ├── todos.go            # Todo CRUD handlers
│   └── middleware.go       # Auth middleware
├── models/
│   ├── user.go             # User model
│   └── todo.go             # Todo model
├── db/
│   ├── database.go         # Database connection
│   └── migrations/         # SQL migrations
├── queues/
│   ├── email.go            # Email queue handler
│   └── notification.go     # Notification queue handler
├── schedulers/
│   └── reminders.go        # Daily reminder scheduler
├── transire.yaml           # Configuration
└── go.mod                  # Dependencies
```

---

## Key Implementation Patterns

### Authentication Middleware

```go
// From handlers/middleware.go
func AuthMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Extract JWT token from Authorization header
        authHeader := r.Header.Get("Authorization")
        if authHeader == "" {
            http.Error(w, "Unauthorized", http.StatusUnauthorized)
            return
        }

        // Validate token
        token := strings.TrimPrefix(authHeader, "Bearer ")
        userID, err := validateJWT(token)
        if err != nil {
            http.Error(w, "Invalid token", http.StatusUnauthorized)
            return
        }

        // Add user ID to context
        ctx := context.WithValue(r.Context(), "userID", userID)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

### Database Integration

```go
// From db/database.go
func NewDatabase(dsn string) (*sql.DB, error) {
    db, err := sql.Open("postgres", dsn)
    if err != nil {
        return nil, err
    }

    // Configure connection pool
    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(5)
    db.SetConnMaxLifetime(5 * time.Minute)

    // Test connection
    if err := db.Ping(); err != nil {
        return nil, err
    }

    return db, nil
}
```

### Todo CRUD Operations

```go
// From handlers/todos.go
func CreateTodoHandler(db *sql.DB) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        userID := r.Context().Value("userID").(string)

        var req CreateTodoRequest
        if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
            http.Error(w, "Invalid JSON", http.StatusBadRequest)
            return
        }

        // Insert todo
        query := `
            INSERT INTO todos (user_id, title, description, completed)
            VALUES ($1, $2, $3, false)
            RETURNING id, created_at
        `

        var todo Todo
        err := db.QueryRow(query, userID, req.Title, req.Description).
            Scan(&todo.ID, &todo.CreatedAt)

        if err != nil {
            log.Printf("Failed to create todo: %v", err)
            http.Error(w, "Internal error", http.StatusInternalServerError)
            return
        }

        // Populate response
        todo.UserID = userID
        todo.Title = req.Title
        todo.Description = req.Description
        todo.Completed = false

        w.Header().Set("Content-Type", "application/json")
        w.WriteHeader(http.StatusCreated)
        json.NewEncoder(w).Encode(todo)
    }
}
```

### Email Queue Handler

```go
// From queues/email.go
type EmailQueueHandler struct {
    emailService *EmailService
}

func (h *EmailQueueHandler) HandleMessages(ctx context.Context, messages []transire.Message) ([]string, error) {
    var failedIDs []string

    for _, msg := range messages {
        var emailReq EmailRequest
        if err := json.Unmarshal(msg.Body(), &emailReq); err != nil {
            log.Printf("Failed to parse email: %v", err)
            continue // Skip malformed messages
        }

        // Send email with retries
        if err := h.sendEmailWithRetry(ctx, emailReq); err != nil {
            log.Printf("Failed to send email after retries: %v", err)
            failedIDs = append(failedIDs, msg.ID())
        }
    }

    return failedIDs, nil
}

func (h *EmailQueueHandler) sendEmailWithRetry(ctx context.Context, req EmailRequest) error {
    maxRetries := 3
    for i := 0; i < maxRetries; i++ {
        err := h.emailService.Send(ctx, req)
        if err == nil {
            return nil
        }

        if !isTransientError(err) {
            return err // Permanent error, don't retry
        }

        time.Sleep(time.Duration(i+1) * time.Second)
    }

    return fmt.Errorf("max retries exceeded")
}
```

### Daily Reminders Scheduler

```go
// From schedulers/reminders.go
type DailyRemindersHandler struct {
    db           *sql.DB
    queueService *QueueService
}

func (h *DailyRemindersHandler) HandleSchedule(ctx context.Context, event transire.ScheduleEvent) error {
    log.Println("Starting daily reminders job")

    // Find users with incomplete todos due today
    query := `
        SELECT DISTINCT u.email, u.name
        FROM users u
        JOIN todos t ON t.user_id = u.id
        WHERE t.completed = false
        AND t.due_date = CURRENT_DATE
    `

    rows, err := h.db.QueryContext(ctx, query)
    if err != nil {
        return fmt.Errorf("failed to query users: %w", err)
    }
    defer rows.Close()

    count := 0
    for rows.Next() {
        var email, name string
        if err := rows.Scan(&email, &name); err != nil {
            log.Printf("Failed to scan row: %v", err)
            continue
        }

        // Queue reminder email
        emailReq := EmailRequest{
            To:      email,
            Subject: "Daily Todo Reminders",
            Body:    fmt.Sprintf("Hi %s, you have todos due today!", name),
        }

        if err := h.queueService.SendEmail(ctx, emailReq); err != nil {
            log.Printf("Failed to queue email for %s: %v", email, err)
            continue
        }

        count++
    }

    log.Printf("Queued %d reminder emails", count)
    return nil
}
```

---

## Running Locally

### Setup

1. **Start PostgreSQL:**
```bash
docker run -d \
  --name todo-postgres \
  -e POSTGRES_DB=todos \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15
```

2. **Set environment variables:**
```bash
export DATABASE_URL="postgres://user:password@localhost:5432/todos?sslmode=disable"
export JWT_SECRET="your-secret-key"
```

3. **Run migrations:**
```bash
cd examples/todo-app
go run db/migrations/migrate.go up
```

4. **Start application:**
```bash
transire run
```

---

### Test the API

**Register user:**
```bash
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123","name":"John Doe"}'
```

Response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

**Login:**
```bash
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123"}'
```

**Create todo (requires auth):**
```bash
TOKEN="your-jwt-token"

curl -X POST http://localhost:3000/api/v1/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "due_date": "2025-01-20"
  }'
```

**List todos:**
```bash
curl http://localhost:3000/api/v1/todos \
  -H "Authorization: Bearer $TOKEN"
```

**Complete todo:**
```bash
curl -X PATCH http://localhost:3000/api/v1/todos/todo-uuid/complete \
  -H "Authorization: Bearer $TOKEN"
```

---

## Deployment

### Configuration

Create `transire.yaml`:
```yaml
name: todo-app

lambda:
  memory_mb: 512
  timeout_seconds: 30

environment:
  DATABASE_URL: ${DATABASE_URL}
  JWT_SECRET: ${JWT_SECRET}

# Use RDS PostgreSQL in production
existing_resources:
  secrets:
    - name: database-credentials
      arn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:db-creds"
      permissions: ["read"]

# VPC for RDS access
vpc:
  subnet_ids:
    - subnet-abc123
    - subnet-def456
  security_group_ids:
    - sg-xyz789
```

### Deploy

```bash
transire build
transire deploy --environment production
```

---

## Key Learnings

### 1. Database Management
- Use connection pooling for Lambda
- Set appropriate pool sizes
- Use prepared statements
- Handle connection errors gracefully

### 2. Authentication
- Use JWT for stateless auth
- Store user context in request
- Protect routes with middleware
- Validate tokens on every request

### 3. Queue Processing
- Use idempotency for email sending
- Implement retry logic
- Distinguish transient vs permanent errors
- Track delivery status

### 4. Scheduled Tasks
- Use schedules for batch operations
- Process in batches to avoid timeouts
- Queue individual notifications
- Monitor execution time

---

## Next Steps

- **[Testing Guide](../guides/testing.md)** – Test database operations
- **[Custom CDK Extensions](../guides/custom-cdk.md)** – Add RDS database

---

## See Also

- [Todo App Source Code](https://github.com/transire/transire/tree/main/examples/todo-app)
- [Simple API Example](simple-api.md)
- [Full App Example](full-app.md)
