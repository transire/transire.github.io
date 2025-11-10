---
title: "Testing (Testkit)"
category: sdk
complexity: intermediate
duration: 30 minutes
prerequisites:
  - Understanding of Go testing
  - Familiarity with Transire handlers
mcp_use: template
mcp_operations:
  - add_tests
  - test_handlers
features_covered:
  - HTTP handler testing
  - Queue handler testing
  - Scheduled job testing
  - Integration testing
code_blocks: true
last_updated: 2025-10-30
---

# Testing (Testkit)

## Overview

Transire provides a comprehensive testing toolkit for all handler types. The testkit enables:

- **HTTP testing** - Test handlers with simulated requests
- **Queue testing** - Test batch processing and error handling
- **Schedule testing** - Test scheduled jobs
- **Integration testing** - Test full application flows
- **Local testing** - All tests run locally without cloud dependencies

The same tests run identically in CI/CD and locally.

## Installation

The testkit is included in the main SDK:

```bash
go get github.com/transire/transire-sdk-go
```

Import in test files:

```go
import (
    "testing"
    "github.com/transire/transire-sdk-go/testkit"
)
```

## HTTP Handler Testing

### Basic HTTP Test

```go
import (
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestGetUser(t *testing.T) {
    // Create test request
    req := httptest.NewRequest("GET", "/users/123", nil)

    // Record response
    rr := httptest.NewRecorder()

    // Call handler
    getUser(rr, req)

    // Assert status code
    if rr.Code != http.StatusOK {
        t.Errorf("Expected status 200, got %d", rr.Code)
    }

    // Assert response body
    expected := `{"id":"123","name":"Alice"}`
    if rr.Body.String() != expected {
        t.Errorf("Expected body %s, got %s", expected, rr.Body.String())
    }
}
```

### Using Testkit HTTP Helper

```go
func TestGetUser(t *testing.T) {
    tests := []struct {
        name           string
        userID         string
        expectedStatus int
        expectedBody   string
    }{
        {
            name:           "valid user",
            userID:         "123",
            expectedStatus: http.StatusOK,
            expectedBody:   `{"id":"123","name":"Alice"}`,
        },
        {
            name:           "user not found",
            userID:         "999",
            expectedStatus: http.StatusNotFound,
            expectedBody:   "User not found\n",
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Create request with path params
            req := testkit.NewRequest("GET", "/users/{id}", nil).
                WithPathParam("id", tt.userID)

            // Execute handler
            resp := testkit.Do(req, getUser)

            // Assert status
            resp.AssertStatus(t, tt.expectedStatus)

            // Assert body
            resp.AssertBody(t, tt.expectedBody)
        })
    }
}
```

### Testing JSON Responses

```go
func TestCreateUser(t *testing.T) {
    input := CreateUserInput{
        Name:  "Bob",
        Email: "bob@example.com",
    }

    // Create JSON request
    req := testkit.NewRequest("POST", "/users", input)

    // Execute
    resp := testkit.Do(req, createUser)

    // Assert status
    resp.AssertStatus(t, http.StatusCreated)

    // Decode and assert JSON response
    var user User
    resp.DecodeJSON(t, &user)

    if user.Name != "Bob" {
        t.Errorf("Expected name 'Bob', got '%s'", user.Name)
    }
    if user.Email != "bob@example.com" {
        t.Errorf("Expected email 'bob@example.com', got '%s'", user.Email)
    }
}
```

### Testing with Headers

```go
func TestAuthenticatedRequest(t *testing.T) {
    req := testkit.NewRequest("GET", "/profile", nil).
        WithHeader("Authorization", "Bearer valid-token")

    resp := testkit.Do(req, getProfile)

    resp.AssertStatus(t, http.StatusOK)
}

func TestUnauthorizedRequest(t *testing.T) {
    req := testkit.NewRequest("GET", "/profile", nil)
    // No Authorization header

    resp := testkit.Do(req, getProfile)

    resp.AssertStatus(t, http.StatusUnauthorized)
}
```

### Testing Query Parameters

```go
func TestSearch(t *testing.T) {
    req := testkit.NewRequest("GET", "/search", nil).
        WithQuery("q", "golang").
        WithQuery("limit", "10")

    resp := testkit.Do(req, search)

    resp.AssertStatus(t, http.StatusOK)

    var results SearchResults
    resp.DecodeJSON(t, &results)

    if len(results.Items) > 10 {
        t.Errorf("Expected max 10 results, got %d", len(results.Items))
    }
}
```

### Testing Middleware

```go
func TestAuthMiddleware(t *testing.T) {
    handler := authMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        user := getUser(r.Context())
        json.NewEncoder(w).Encode(user)
    }))

    tests := []struct {
        name        string
        token       string
        wantStatus  int
    }{
        {
            name:       "valid token",
            token:      "Bearer valid-token",
            wantStatus: http.StatusOK,
        },
        {
            name:       "missing token",
            token:      "",
            wantStatus: http.StatusUnauthorized,
        },
        {
            name:       "invalid token",
            token:      "Bearer invalid",
            wantStatus: http.StatusUnauthorized,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            req := testkit.NewRequest("GET", "/test", nil)
            if tt.token != "" {
                req = req.WithHeader("Authorization", tt.token)
            }

            resp := testkit.DoHandler(req, handler)
            resp.AssertStatus(t, tt.wantStatus)
        })
    }
}
```

## Queue Handler Testing

### Basic Queue Test

```go
func TestProcessOrders(t *testing.T) {
    orders := []ProcessOrder{
        {OrderID: "order_1", Total: 99.99, UserID: "user_123"},
        {OrderID: "order_2", Total: 49.99, UserID: "user_456"},
    }

    ctx := context.Background()
    err := processOrders(ctx, orders)

    if err != nil {
        t.Errorf("Expected no error, got %v", err)
    }

    // Verify orders were processed
    for _, order := range orders {
        processed, _ := db.IsOrderProcessed(ctx, order.OrderID)
        if !processed {
            t.Errorf("Order %s was not processed", order.OrderID)
        }
    }
}
```

### Testing Partial Batch Failures

```go
func TestProcessOrdersWithFailures(t *testing.T) {
    orders := []ProcessOrder{
        {OrderID: "order_1", Total: 99.99, UserID: "user_123"},    // Success
        {OrderID: "order_2", Total: -10, UserID: "user_456"},      // Invalid (fail)
        {OrderID: "order_3", Total: 49.99, UserID: "nonexistent"}, // User not found (fail)
        {OrderID: "order_4", Total: 29.99, UserID: "user_789"},    // Success
    }

    ctx := context.Background()
    err := processOrders(ctx, orders)

    // Should return batch result error
    var br *transire.BatchResultError
    if !errors.As(err, &br) {
        t.Fatalf("Expected BatchResultError, got %v", err)
    }

    // Check failed message indices
    failed := br.FailedIndices()
    expected := []int{1, 2}  // orders 2 and 3 failed

    if !reflect.DeepEqual(failed, expected) {
        t.Errorf("Expected failed indices %v, got %v", expected, failed)
    }

    // Verify successful orders were processed
    processed, _ := db.IsOrderProcessed(ctx, "order_1")
    if !processed {
        t.Error("Order 1 should be processed")
    }

    processed, _ = db.IsOrderProcessed(ctx, "order_4")
    if !processed {
        t.Error("Order 4 should be processed")
    }
}
```

### Using Queue Testkit

```go
func TestQueueHandler(t *testing.T) {
    // Create queue test harness
    qt := testkit.NewQueueTest(t)

    // Register handler
    qt.RegisterHandler("process-orders", processOrders)

    // Enqueue messages
    qt.Enqueue("process-orders",
        ProcessOrder{OrderID: "order_1", Total: 99.99, UserID: "user_123"},
        ProcessOrder{OrderID: "order_2", Total: 49.99, UserID: "user_456"},
    )

    // Process queue
    qt.ProcessQueue("process-orders")

    // Assert no messages left
    qt.AssertQueueEmpty("process-orders")

    // Assert no DLQ messages
    qt.AssertDLQEmpty("process-orders")
}
```

### Testing DLQ Behavior

```go
func TestDLQHandling(t *testing.T) {
    qt := testkit.NewQueueTest(t)
    qt.RegisterHandler("process-orders", processOrders)

    // Enqueue message that will fail
    qt.Enqueue("process-orders",
        ProcessOrder{OrderID: "bad_order", Total: -100, UserID: "invalid"},
    )

    // Process with retries
    qt.ProcessQueueWithRetries("process-orders", 3)

    // Assert message moved to DLQ after max retries
    qt.AssertDLQCount("process-orders", 1)

    // Inspect DLQ message
    dlqMessages := qt.GetDLQMessages("process-orders")
    if len(dlqMessages) != 1 {
        t.Fatalf("Expected 1 DLQ message, got %d", len(dlqMessages))
    }

    var order ProcessOrder
    json.Unmarshal(dlqMessages[0].Body, &order)
    if order.OrderID != "bad_order" {
        t.Errorf("Expected bad_order in DLQ, got %s", order.OrderID)
    }
}
```

## Scheduled Job Testing

### Basic Schedule Test

```go
func TestGenerateDailyReport(t *testing.T) {
    ctx := context.Background()
    err := generateDailyReport(ctx)

    if err != nil {
        t.Errorf("Expected no error, got %v", err)
    }

    // Verify report was generated
    exists, _ := s3.ObjectExists(ctx, "reports/2025-10-30/daily.pdf")
    if !exists {
        t.Error("Report was not generated")
    }
}
```

### Testing with Time

```go
func TestScheduledJobWithTime(t *testing.T) {
    // Set fixed time for deterministic testing
    now := time.Date(2025, 10, 30, 2, 0, 0, 0, time.UTC)
    originalNow := timeNow
    timeNow = func() time.Time { return now }
    defer func() { timeNow = originalNow }()

    ctx := context.Background()
    err := generateDailyReport(ctx)

    if err != nil {
        t.Errorf("Expected no error, got %v", err)
    }

    // Verify report for correct date
    expected := "reports/2025-10-29/daily.pdf"  // Previous day
    exists, _ := s3.ObjectExists(ctx, expected)
    if !exists {
        t.Errorf("Report not found at %s", expected)
    }
}
```

### Using Schedule Testkit

```go
func TestScheduledJob(t *testing.T) {
    st := testkit.NewScheduleTest(t)

    // Register handler
    st.RegisterSchedule("0 2 * * ? *", generateDailyReport)

    // Trigger execution
    st.Trigger("generate-daily-report")

    // Assert no errors
    st.AssertNoErrors()

    // Verify side effects...
}
```

### Testing Context Cancellation

```go
func TestScheduledJobCancellation(t *testing.T) {
    ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
    defer cancel()

    err := longRunningJob(ctx)

    if err != context.DeadlineExceeded {
        t.Errorf("Expected context.DeadlineExceeded, got %v", err)
    }
}
```

## Integration Testing

### Full Application Test

```go
func TestOrderFlow(t *testing.T) {
    // Start test app
    app := testkit.NewTestApp(t)
    defer app.Stop()

    // Register handlers
    app.GET("/orders", listOrders)
    app.POST("/orders", createOrder)
    app.RegisterQueue("process-orders", processOrders)

    // Create order via HTTP
    order := CreateOrderInput{
        UserID: "user_123",
        Items:  []string{"item_1", "item_2"},
        Total:  99.99,
    }

    resp := app.POST("/orders", order)
    resp.AssertStatus(t, http.StatusCreated)

    var created Order
    resp.DecodeJSON(t, &created)

    // Process queue (async processing)
    app.ProcessQueues()

    // Verify order was processed
    processed, _ := db.IsOrderProcessed(context.Background(), created.ID)
    if !processed {
        t.Error("Order was not processed")
    }

    // Verify order appears in list
    listResp := app.GET("/orders")
    listResp.AssertStatus(t, http.StatusOK)

    var orders []Order
    listResp.DecodeJSON(t, &orders)

    found := false
    for _, o := range orders {
        if o.ID == created.ID {
            found = true
            break
        }
    }
    if !found {
        t.Error("Created order not found in list")
    }
}
```

### Testing with Dependencies

```go
func TestWithMockDependencies(t *testing.T) {
    // Create mock database
    mockDB := &MockDB{
        users: map[string]User{
            "user_123": {ID: "user_123", Name: "Alice"},
        },
    }

    // Inject mock into handler
    handler := func(w http.ResponseWriter, r *http.Request) {
        getUser(w, r, mockDB)
    }

    req := testkit.NewRequest("GET", "/users/user_123", nil)
    resp := testkit.Do(req, handler)

    resp.AssertStatus(t, http.StatusOK)

    var user User
    resp.DecodeJSON(t, &user)

    if user.Name != "Alice" {
        t.Errorf("Expected name 'Alice', got '%s'", user.Name)
    }
}
```

### Testing with Database

```go
func TestWithTestDatabase(t *testing.T) {
    // Create test database
    db := testkit.NewTestDB(t, "postgres://localhost/test_db")
    defer db.Close()

    // Run migrations
    db.Migrate()

    // Seed test data
    db.Exec("INSERT INTO users (id, name) VALUES ($1, $2)", "user_123", "Alice")

    // Test handler with real database
    req := testkit.NewRequest("GET", "/users/user_123", nil)
    resp := testkit.Do(req, getUser)

    resp.AssertStatus(t, http.StatusOK)
}
```

## Test Helpers

### Custom Assertions

```go
func assertUserEquals(t *testing.T, got, want User) {
    t.Helper()

    if got.ID != want.ID {
        t.Errorf("ID: got %s, want %s", got.ID, want.ID)
    }
    if got.Name != want.Name {
        t.Errorf("Name: got %s, want %s", got.Name, want.Name)
    }
    if got.Email != want.Email {
        t.Errorf("Email: got %s, want %s", got.Email, want.Email)
    }
}

func TestCreateUser(t *testing.T) {
    // ... create user ...

    want := User{ID: "user_123", Name: "Alice", Email: "alice@example.com"}
    assertUserEquals(t, created, want)
}
```

### Test Fixtures

```go
func createTestUser(t *testing.T, db *sql.DB) User {
    t.Helper()

    user := User{
        ID:    "user_" + randomString(10),
        Name:  "Test User",
        Email: "test@example.com",
    }

    _, err := db.Exec(
        "INSERT INTO users (id, name, email) VALUES ($1, $2, $3)",
        user.ID, user.Name, user.Email,
    )
    if err != nil {
        t.Fatalf("Failed to create test user: %v", err)
    }

    return user
}

func TestGetUser(t *testing.T) {
    db := setupTestDB(t)
    user := createTestUser(t, db)

    // Test with fixture...
}
```

### Table-Driven Tests

```go
func TestValidateEmail(t *testing.T) {
    tests := []struct {
        name    string
        email   string
        wantErr bool
    }{
        {
            name:    "valid email",
            email:   "alice@example.com",
            wantErr: false,
        },
        {
            name:    "missing @",
            email:   "alice.example.com",
            wantErr: true,
        },
        {
            name:    "empty email",
            email:   "",
            wantErr: true,
        },
        {
            name:    "no domain",
            email:   "alice@",
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := validateEmail(tt.email)
            if (err != nil) != tt.wantErr {
                t.Errorf("validateEmail() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

## Best Practices

### 1. Use Table-Driven Tests

```go
// ✅ GOOD: Easy to add new test cases
func TestGetUser(t *testing.T) {
    tests := []struct {
        name           string
        userID         string
        expectedStatus int
    }{
        {"valid user", "user_123", http.StatusOK},
        {"missing user", "user_999", http.StatusNotFound},
        {"invalid ID", "invalid", http.StatusBadRequest},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Test implementation...
        })
    }
}
```

### 2. Use Subtests for Clarity

```go
// ✅ GOOD: Clear test output
func TestUserHandlers(t *testing.T) {
    t.Run("Create", func(t *testing.T) {
        // Test create user...
    })

    t.Run("Get", func(t *testing.T) {
        // Test get user...
    })

    t.Run("Update", func(t *testing.T) {
        // Test update user...
    })
}
```

### 3. Clean Up Test Data

```go
func TestWithCleanup(t *testing.T) {
    db := setupTestDB(t)

    // Create test data
    userID := createTestUser(t, db)

    // Ensure cleanup
    t.Cleanup(func() {
        db.Exec("DELETE FROM users WHERE id = $1", userID)
    })

    // Run test...
}
```

### 4. Test Error Cases

```go
func TestCreateUser(t *testing.T) {
    t.Run("Success", func(t *testing.T) {
        // Test successful creation...
    })

    t.Run("Duplicate email", func(t *testing.T) {
        // Test error handling...
    })

    t.Run("Invalid input", func(t *testing.T) {
        // Test validation...
    })
}
```

### 5. Use Helper Functions

```go
func setupTestApp(t *testing.T) *testkit.TestApp {
    t.Helper()

    app := testkit.NewTestApp(t)
    app.Use(loggingMiddleware)
    app.Use(recoveryMiddleware)

    // Register all handlers...

    return app
}
```

## Example: Complete Test Suite

```go
package main_test

import (
    "context"
    "testing"
    "github.com/transire/transire-sdk-go/testkit"
)

func TestOrderAPI(t *testing.T) {
    app := setupTestApp(t)
    defer app.Stop()

    t.Run("Create order", func(t *testing.T) {
        input := CreateOrderInput{
            UserID: "user_123",
            Items:  []string{"item_1"},
            Total:  99.99,
        }

        resp := app.POST("/orders", input)
        resp.AssertStatus(t, http.StatusCreated)

        var order Order
        resp.DecodeJSON(t, &order)

        if order.Total != 99.99 {
            t.Errorf("Expected total 99.99, got %.2f", order.Total)
        }
    })

    t.Run("List orders", func(t *testing.T) {
        resp := app.GET("/orders")
        resp.AssertStatus(t, http.StatusOK)

        var orders []Order
        resp.DecodeJSON(t, &orders)

        if len(orders) == 0 {
            t.Error("Expected at least one order")
        }
    })

    t.Run("Process orders queue", func(t *testing.T) {
        // Enqueue order
        app.Enqueue("process-orders", ProcessOrder{
            OrderID: "order_123",
            Total:   99.99,
            UserID:  "user_123",
        })

        // Process queue
        app.ProcessQueue("process-orders")

        // Verify processed
        processed, _ := db.IsOrderProcessed(context.Background(), "order_123")
        if !processed {
            t.Error("Order was not processed")
        }
    })
}

func setupTestApp(t *testing.T) *testkit.TestApp {
    t.Helper()

    app := testkit.NewTestApp(t)

    // Register HTTP handlers
    app.GET("/orders", listOrders)
    app.POST("/orders", createOrder)

    // Register queue handlers
    app.RegisterQueue("process-orders", processOrders)

    return app
}
```

## See Also

- [HTTP Handlers](/sdk/http.md) - HTTP handler basics
- [Queue Handlers](/sdk/queue.md) - Queue handler basics
- [Scheduled Jobs](/sdk/schedule.md) - Schedule handler basics
- [Testing Guide](/guides/testing.md) - Testing patterns and best practices
