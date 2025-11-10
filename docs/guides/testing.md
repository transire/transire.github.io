---
title: Testing Guide
description: Comprehensive guide to testing Transire applications with testkit, mocks, and integration tests
category: guide
subcategory: testing
complexity: intermediate
duration: 45 minutes
mcp_use: guide
mcp_operations:
  - setup_testing
  - write_unit_tests
  - write_integration_tests
  - mock_dependencies
  - test_http_handlers
  - test_queue_handlers
  - test_scheduled_jobs
features_covered:
  - Unit testing
  - Integration testing
  - Testkit usage
  - Mocking dependencies
  - HTTP testing
  - Queue testing
  - Schedule testing
  - Test coverage
code_blocks: true
last_updated: 2025-11-10
---

# Testing Guide

> **Comprehensive testing strategies** for Transire applications

## Overview

Testing Transire applications involves three layers:

1. **Unit tests** - Test individual functions in isolation
2. **Integration tests** - Test handlers with real dependencies
3. **End-to-end tests** - Test full request→response flows

**Time to read:** 45 minutes

---

## Table of Contents

- [Testing Setup](#testing-setup)
- [Unit Testing](#unit-testing)
- [Integration Testing with Testkit](#integration-testing-with-testkit)
- [Testing HTTP Handlers](#testing-http-handlers)
- [Testing Queue Handlers](#testing-queue-handlers)
- [Testing Scheduled Jobs](#testing-scheduled-jobs)
- [Mocking Dependencies](#mocking-dependencies)
- [Test Coverage](#test-coverage)
- [Testing Patterns](#testing-patterns)
- [CI/CD Integration](#cicd-integration)

---

## Testing Setup

### Project Structure

```
my-app/
├── main.go
├── handlers/
│   ├── orders.go
│   └── orders_test.go       # Handler tests
├── services/
│   ├── database.go
│   └── database_test.go     # Service tests
├── models/
│   └── order.go
├── testutil/
│   ├── fixtures.go           # Test data
│   └── mocks.go              # Mock implementations
└── integration_test.go       # Integration tests
```

### Install Testing Dependencies

```bash
# Testkit (included in SDK)
go get github.com/transire/sdk-go/testkit

# Optional: Testify for assertions
go get github.com/stretchr/testify/assert
go get github.com/stretchr/testify/require

# Optional: gomock for mocking
go install github.com/golang/mock/mockgen@latest
```

### Basic Test File

```go
package handlers

import (
    "testing"
    "github.com/transire/sdk-go/testkit"
)

func TestListOrders(t *testing.T) {
    // Test implementation
}
```

---

## Unit Testing

### Testing Pure Functions

Test business logic without external dependencies:

```go
// orders.go
package services

type Order struct {
    ID       string
    Quantity int
    Price    float64
}

func CalculateTotal(orders []Order) float64 {
    total := 0.0
    for _, order := range orders {
        total += float64(order.Quantity) * order.Price
    }
    return total
}
```

```go
// orders_test.go
package services

import (
    "testing"
)

func TestCalculateTotal(t *testing.T) {
    orders := []Order{
        {ID: "1", Quantity: 2, Price: 10.0},
        {ID: "2", Quantity: 3, Price: 5.0},
    }

    total := CalculateTotal(orders)

    expected := 35.0
    if total != expected {
        t.Errorf("Expected %f, got %f", expected, total)
    }
}

func TestCalculateTotalEmpty(t *testing.T) {
    orders := []Order{}
    total := CalculateTotal(orders)

    if total != 0.0 {
        t.Errorf("Expected 0.0, got %f", total)
    }
}
```

### Using Testify Assertions

```go
import (
    "testing"
    "github.com/stretchr/testify/assert"
)

func TestCalculateTotal(t *testing.T) {
    orders := []Order{
        {ID: "1", Quantity: 2, Price: 10.0},
        {ID: "2", Quantity: 3, Price: 5.0},
    }

    total := CalculateTotal(orders)

    assert.Equal(t, 35.0, total, "Total should be 35.0")
}

func TestCalculateTotalEmpty(t *testing.T) {
    orders := []Order{}
    total := CalculateTotal(orders)

    assert.Zero(t, total, "Empty orders should have zero total")
}
```

### Table-Driven Tests

Test multiple scenarios efficiently:

```go
func TestCalculateTotal(t *testing.T) {
    tests := []struct {
        name     string
        orders   []Order
        expected float64
    }{
        {
            name:     "single order",
            orders:   []Order{{ID: "1", Quantity: 2, Price: 10.0}},
            expected: 20.0,
        },
        {
            name: "multiple orders",
            orders: []Order{
                {ID: "1", Quantity: 2, Price: 10.0},
                {ID: "2", Quantity: 3, Price: 5.0},
            },
            expected: 35.0,
        },
        {
            name:     "empty orders",
            orders:   []Order{},
            expected: 0.0,
        },
        {
            name:     "zero quantity",
            orders:   []Order{{ID: "1", Quantity: 0, Price: 10.0}},
            expected: 0.0,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            total := CalculateTotal(tt.orders)
            assert.Equal(t, tt.expected, total)
        })
    }
}
```

---

## Integration Testing with Testkit

### Testkit Overview

Testkit provides:
- HTTP request/response testing
- Queue message enqueueing and draining
- Schedule trigger simulation
- Dependency injection support
- Assertion helpers

### Basic Testkit Usage

```go
import (
    "testing"
    "github.com/transire/sdk-go/testkit"
)

func TestCreateOrder(t *testing.T) {
    tk := testkit.New(t)

    // Register handler
    tk.POST("/orders", createOrder)

    // Make request
    resp := tk.POST("/orders").
        JSON(map[string]interface{}{
            "product":  "Widget",
            "quantity": 5,
            "price":    99.99,
        }).
        Send()

    // Assert response
    resp.ExpectStatus(201)
    resp.ExpectHeader("Content-Type", "application/json")
    resp.ExpectJSONPath("$.product", "Widget")
    resp.ExpectJSONPath("$.quantity", 5)
}
```

### Testkit with Dependencies

```go
func TestListOrders(t *testing.T) {
    tk := testkit.New(t)

    // Setup mock database
    mockDB := &MockDatabase{
        orders: []Order{
            {ID: "1", Product: "Widget A"},
            {ID: "2", Product: "Widget B"},
        },
    }

    // Provide mock to DI container
    transire.Provide(func() *Database { return mockDB })

    // Register handler
    tk.GET("/orders", listOrders)

    // Make request
    resp := tk.GET("/orders").Send()

    // Assert response
    resp.ExpectStatus(200)
    resp.ExpectJSONLength("$", 2)
    resp.ExpectJSONPath("$[0].product", "Widget A")
}
```

---

## Testing HTTP Handlers

### GET Requests

```go
func TestGetOrder(t *testing.T) {
    tk := testkit.New(t)

    // Setup data
    mockDB := &MockDatabase{
        orders: []Order{
            {ID: "123", Product: "Widget", Quantity: 5},
        },
    }
    transire.Provide(func() *Database { return mockDB })

    // Register handler
    tk.GET("/orders/{id}", getOrder)

    // Test success
    resp := tk.GET("/orders/123").Send()
    resp.ExpectStatus(200)
    resp.ExpectJSONPath("$.id", "123")
    resp.ExpectJSONPath("$.product", "Widget")

    // Test not found
    resp = tk.GET("/orders/999").Send()
    resp.ExpectStatus(404)
    resp.ExpectJSONPath("$.error", "Order not found")
}
```

### POST Requests

```go
func TestCreateOrder(t *testing.T) {
    tk := testkit.New(t)

    mockDB := &MockDatabase{}
    transire.Provide(func() *Database { return mockDB })

    tk.POST("/orders", createOrder)

    // Test valid request
    resp := tk.POST("/orders").
        JSON(map[string]interface{}{
            "product":  "Widget",
            "quantity": 5,
            "price":    99.99,
        }).
        Send()

    resp.ExpectStatus(201)
    resp.ExpectJSONPath("$.id", testkit.NotEmpty)
    resp.ExpectJSONPath("$.product", "Widget")

    // Verify database interaction
    assert.Equal(t, 1, len(mockDB.orders))

    // Test validation error
    resp = tk.POST("/orders").
        JSON(map[string]interface{}{
            "product": "",  // Invalid: empty product
        }).
        Send()

    resp.ExpectStatus(400)
    resp.ExpectJSONPath("$.error", "Product is required")
}
```

### PUT Requests

```go
func TestUpdateOrder(t *testing.T) {
    tk := testkit.New(t)

    mockDB := &MockDatabase{
        orders: []Order{
            {ID: "123", Product: "Widget", Status: "pending"},
        },
    }
    transire.Provide(func() *Database { return mockDB })

    tk.PUT("/orders/{id}", updateOrder)

    // Test partial update
    resp := tk.PUT("/orders/123").
        JSON(map[string]interface{}{
            "status": "fulfilled",
        }).
        Send()

    resp.ExpectStatus(200)
    resp.ExpectJSONPath("$.status", "fulfilled")
    resp.ExpectJSONPath("$.product", "Widget") // Unchanged

    // Verify database
    assert.Equal(t, "fulfilled", mockDB.orders[0].Status)
}
```

### DELETE Requests

```go
func TestDeleteOrder(t *testing.T) {
    tk := testkit.New(t)

    mockDB := &MockDatabase{
        orders: []Order{
            {ID: "123", Product: "Widget"},
        },
    }
    transire.Provide(func() *Database { return mockDB })

    tk.DELETE("/orders/{id}", deleteOrder)

    // Test successful deletion
    resp := tk.DELETE("/orders/123").Send()
    resp.ExpectStatus(204)

    // Verify database
    assert.Equal(t, 0, len(mockDB.orders))

    // Test not found
    resp = tk.DELETE("/orders/999").Send()
    resp.ExpectStatus(404)
}
```

### Testing Query Parameters

```go
func TestListOrdersWithFilters(t *testing.T) {
    tk := testkit.New(t)

    mockDB := &MockDatabase{
        orders: []Order{
            {ID: "1", Status: "pending"},
            {ID: "2", Status: "fulfilled"},
            {ID: "3", Status: "pending"},
        },
    }
    transire.Provide(func() *Database { return mockDB })

    tk.GET("/orders", listOrders)

    // Test with status filter
    resp := tk.GET("/orders").
        Query("status", "pending").
        Send()

    resp.ExpectStatus(200)
    resp.ExpectJSONLength("$", 2)

    // Test with pagination
    resp = tk.GET("/orders").
        Query("limit", "10").
        Query("offset", "0").
        Send()

    resp.ExpectStatus(200)
    resp.ExpectHeader("X-Total-Count", "3")
}
```

### Testing Headers

```go
func TestAuthenticatedRequest(t *testing.T) {
    tk := testkit.New(t)

    tk.GET("/orders", listOrders)

    // Test with valid token
    resp := tk.GET("/orders").
        Header("Authorization", "Bearer valid-token").
        Send()

    resp.ExpectStatus(200)

    // Test without token
    resp = tk.GET("/orders").Send()
    resp.ExpectStatus(401)
    resp.ExpectJSONPath("$.error", "Unauthorized")

    // Test with invalid token
    resp = tk.GET("/orders").
        Header("Authorization", "Bearer invalid-token").
        Send()

    resp.ExpectStatus(401)
}
```

---

## Testing Queue Handlers

### Basic Queue Test

```go
func TestFulfillOrders(t *testing.T) {
    tk := testkit.New(t)

    mockDB := &MockDatabase{}
    transire.Provide(func() *Database { return mockDB })

    // Register queue handler
    tk.Queue("fulfill-orders", fulfillOrders)

    // Enqueue message
    order := Order{ID: "123", Product: "Widget", Status: "pending"}
    tk.Enqueue("fulfill-orders", order)

    // Drain queue (process all messages)
    tk.DrainQueue("fulfill-orders")

    // Verify order was fulfilled
    assert.Equal(t, 1, len(mockDB.orders))
    assert.Equal(t, "fulfilled", mockDB.orders[0].Status)
}
```

### Testing Batch Processing

```go
func TestFulfillOrdersBatch(t *testing.T) {
    tk := testkit.New(t)

    mockDB := &MockDatabase{}
    transire.Provide(func() *Database { return mockDB })

    tk.Queue("fulfill-orders", fulfillOrders)

    // Enqueue multiple messages
    orders := []Order{
        {ID: "1", Product: "Widget A"},
        {ID: "2", Product: "Widget B"},
        {ID: "3", Product: "Widget C"},
    }

    for _, order := range orders {
        tk.Enqueue("fulfill-orders", order)
    }

    // Process batch
    tk.DrainQueue("fulfill-orders")

    // Verify all processed
    assert.Equal(t, 3, len(mockDB.orders))
}
```

### Testing Partial Batch Failures

```go
func TestFulfillOrdersPartialFailure(t *testing.T) {
    tk := testkit.New(t)

    mockDB := &MockDatabase{
        shouldFail: map[string]bool{
            "2": true,  // Order 2 will fail
        },
    }
    transire.Provide(func() *Database { return mockDB })

    tk.Queue("fulfill-orders", fulfillOrders)

    // Enqueue batch
    orders := []Order{
        {ID: "1", Product: "Widget A"},
        {ID: "2", Product: "Widget B"},  // Will fail
        {ID: "3", Product: "Widget C"},
    }

    for _, order := range orders {
        tk.Enqueue("fulfill-orders", order)
    }

    // Process batch
    result := tk.DrainQueue("fulfill-orders")

    // Verify partial success
    assert.Equal(t, 2, result.SuccessCount)
    assert.Equal(t, 1, result.FailureCount)

    // Verify successful orders processed
    assert.Equal(t, 2, len(mockDB.orders))
    assert.NotContains(t, mockDB.orders, Order{ID: "2"})
}
```

### Testing Queue Retries

```go
func TestQueueRetryBehavior(t *testing.T) {
    tk := testkit.New(t)

    attempts := 0
    mockDB := &MockDatabase{
        fulfillFunc: func(id string) error {
            attempts++
            if attempts < 3 {
                return errors.New("temporary failure")
            }
            return nil
        },
    }
    transire.Provide(func() *Database { return mockDB })

    tk.Queue("fulfill-orders", fulfillOrders)

    // Enqueue message
    order := Order{ID: "123", Product: "Widget"}
    tk.Enqueue("fulfill-orders", order)

    // Drain with retries
    tk.DrainQueueWithRetries("fulfill-orders", 3)

    // Verify succeeded after retries
    assert.Equal(t, 3, attempts)
    assert.Equal(t, 1, len(mockDB.orders))
}
```

### Testing DLQ Behavior

```go
func TestQueueDLQ(t *testing.T) {
    tk := testkit.New(t)

    mockDB := &MockDatabase{
        alwaysFail: true,
    }
    transire.Provide(func() *Database { return mockDB })

    tk.Queue("fulfill-orders", fulfillOrders)
    tk.Queue("fulfill-orders-dlq", handleDLQ)

    // Enqueue message
    order := Order{ID: "123", Product: "Widget"}
    tk.Enqueue("fulfill-orders", order)

    // Drain with max retries
    tk.DrainQueueWithRetries("fulfill-orders", 3)

    // Verify moved to DLQ
    dlqMessages := tk.GetDLQMessages("fulfill-orders")
    assert.Equal(t, 1, len(dlqMessages))
}
```

---

## Testing Scheduled Jobs

### Basic Schedule Test

```go
func TestGenerateDailyReport(t *testing.T) {
    tk := testkit.New(t)

    mockDB := &MockDatabase{}
    transire.Provide(func() *Database { return mockDB })

    // Register schedule
    tk.Schedule("daily-report", "@daily 09:00", generateDailyReport)

    // Trigger manually
    err := tk.TriggerSchedule("daily-report")
    assert.NoError(t, err)

    // Verify report generated
    assert.Equal(t, 1, mockDB.reportsGenerated)
}
```

### Testing Idempotency

```go
func TestScheduleIdempotency(t *testing.T) {
    tk := testkit.New(t)

    mockDB := &MockDatabase{}
    transire.Provide(func() *Database { return mockDB })

    tk.Schedule("daily-report", "@daily 09:00", generateDailyReport)

    // Trigger twice (simulating duplicate execution)
    tk.TriggerSchedule("daily-report")
    tk.TriggerSchedule("daily-report")

    // Should only generate once (idempotent)
    assert.Equal(t, 1, mockDB.reportsGenerated)
}
```

### Testing Schedule Errors

```go
func TestScheduleErrorHandling(t *testing.T) {
    tk := testkit.New(t)

    mockDB := &MockDatabase{
        reportShouldFail: true,
    }
    transire.Provide(func() *Database { return mockDB })

    tk.Schedule("daily-report", "@daily 09:00", generateDailyReport)

    // Trigger
    err := tk.TriggerSchedule("daily-report")

    // Verify error returned
    assert.Error(t, err)
    assert.Equal(t, 0, mockDB.reportsGenerated)
}
```

---

## Mocking Dependencies

### Manual Mocks

```go
// testutil/mocks.go
package testutil

type MockDatabase struct {
    orders          []Order
    shouldFail      map[string]bool
    alwaysFail      bool
    fulfillFunc     func(string) error
    reportsGenerated int
    reportShouldFail bool
}

func (m *MockDatabase) GetOrders(ctx context.Context) ([]Order, error) {
    if m.alwaysFail {
        return nil, errors.New("database error")
    }
    return m.orders, nil
}

func (m *MockDatabase) GetOrder(ctx context.Context, id string) (*Order, error) {
    for _, order := range m.orders {
        if order.ID == id {
            return &order, nil
        }
    }
    return nil, errors.New("order not found")
}

func (m *MockDatabase) CreateOrder(ctx context.Context, order *Order) error {
    if m.alwaysFail {
        return errors.New("database error")
    }
    m.orders = append(m.orders, *order)
    return nil
}

func (m *MockDatabase) FulfillOrder(ctx context.Context, id string) error {
    if m.fulfillFunc != nil {
        return m.fulfillFunc(id)
    }

    if m.shouldFail != nil && m.shouldFail[id] {
        return errors.New("fulfillment failed")
    }

    for i, order := range m.orders {
        if order.ID == id {
            m.orders[i].Status = "fulfilled"
            return nil
        }
    }

    return errors.New("order not found")
}

func (m *MockDatabase) GenerateReport(ctx context.Context) error {
    if m.reportShouldFail {
        return errors.New("report generation failed")
    }
    m.reportsGenerated++
    return nil
}
```

### Using Interfaces

```go
// services/database.go
type Database interface {
    GetOrders(ctx context.Context) ([]Order, error)
    GetOrder(ctx context.Context, id string) (*Order, error)
    CreateOrder(ctx context.Context, order *Order) error
    FulfillOrder(ctx context.Context, id string) error
}

// Real implementation
type PostgresDatabase struct {
    db *sql.DB
}

func (p *PostgresDatabase) GetOrders(ctx context.Context) ([]Order, error) {
    // Real database query
}

// Test with mock
func TestWithMock(t *testing.T) {
    var db Database = &MockDatabase{}  // Mock implements interface
    // Test with mock...
}
```

### gomock for Complex Mocks

Generate mocks:
```bash
mockgen -source=services/database.go -destination=testutil/mock_database.go
```

Use in tests:
```go
import (
    "testing"
    "github.com/golang/mock/gomock"
    "myapp/testutil"
)

func TestWithGomock(t *testing.T) {
    ctrl := gomock.NewController(t)
    defer ctrl.Finish()

    mockDB := testutil.NewMockDatabase(ctrl)

    // Set expectations
    mockDB.EXPECT().
        GetOrder(gomock.Any(), "123").
        Return(&Order{ID: "123", Product: "Widget"}, nil)

    // Use in handler
    transire.Provide(func() Database { return mockDB })

    // Test...
}
```

---

## Test Coverage

### Run with Coverage

```bash
# Run tests with coverage
go test ./... -cover

# Generate coverage report
go test ./... -coverprofile=coverage.out

# View in browser
go tool cover -html=coverage.out
```

### Coverage by Package

```bash
# Show coverage per package
go test ./... -cover -coverprofile=coverage.out
go tool cover -func=coverage.out

# Output:
# myapp/handlers/orders.go:15:    listOrders      100.0%
# myapp/handlers/orders.go:30:    getOrder        100.0%
# myapp/handlers/orders.go:45:    createOrder     85.7%
# total:                          (statements)    92.3%
```

### Coverage Thresholds

```bash
# Fail if coverage < 80%
go test ./... -cover -coverprofile=coverage.out
coverage=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
if (( $(echo "$coverage < 80" | bc -l) )); then
    echo "Coverage $coverage% is below 80%"
    exit 1
fi
```

### CI/CD Coverage Enforcement

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v4
        with:
          go-version: '1.22'

      - name: Run tests with coverage
        run: go test ./... -coverprofile=coverage.out

      - name: Check coverage threshold
        run: |
          coverage=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
          echo "Coverage: $coverage%"
          if (( $(echo "$coverage < 80" | bc -l) )); then
            echo "❌ Coverage below 80%"
            exit 1
          fi
          echo "✅ Coverage above 80%"

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.out
```

---

## Testing Patterns

### Setup and Teardown

```go
func TestMain(m *testing.M) {
    // Setup
    setupTestDatabase()

    // Run tests
    code := m.Run()

    // Teardown
    cleanupTestDatabase()

    os.Exit(code)
}

func setupTestDatabase() {
    // Create test database
}

func cleanupTestDatabase() {
    // Drop test database
}
```

### Test Fixtures

```go
// testutil/fixtures.go
package testutil

func NewTestOrder() Order {
    return Order{
        ID:       "test-123",
        Product:  "Test Widget",
        Quantity: 5,
        Price:    99.99,
        Status:   "pending",
    }
}

func NewTestOrders(count int) []Order {
    orders := make([]Order, count)
    for i := 0; i < count; i++ {
        orders[i] = Order{
            ID:       fmt.Sprintf("test-%d", i+1),
            Product:  fmt.Sprintf("Widget %d", i+1),
            Quantity: i + 1,
            Price:    float64(i+1) * 10.0,
        }
    }
    return orders
}
```

Use in tests:
```go
func TestWithFixtures(t *testing.T) {
    order := testutil.NewTestOrder()
    // Use order in test...
}
```

### Helper Functions

```go
// testutil/helpers.go
package testutil

func AssertOrderEqual(t *testing.T, expected, actual Order) {
    t.Helper()
    assert.Equal(t, expected.ID, actual.ID)
    assert.Equal(t, expected.Product, actual.Product)
    assert.Equal(t, expected.Quantity, actual.Quantity)
    assert.Equal(t, expected.Price, actual.Price)
}

func AssertHTTPError(t *testing.T, resp *testkit.Response, code int, message string) {
    t.Helper()
    resp.ExpectStatus(code)
    resp.ExpectJSONPath("$.error", message)
}
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v4
        with:
          go-version: '1.22'

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
        run: |
          go test ./... -v -race -coverprofile=coverage.out

      - name: Check coverage
        run: |
          go tool cover -func=coverage.out

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.out
```

### Pre-Commit Hook

```bash
#!/bin/sh
# .git/hooks/pre-commit

set -e

echo "Running tests..."
go test ./... -short

echo "Running linter..."
golangci-lint run ./...

echo "✓ Pre-commit checks passed"
```

```bash
chmod +x .git/hooks/pre-commit
```

---

## See Also

- [Testkit API Reference](../reference/sdk/testkit/) - Complete testkit documentation
- [Local Development Guide](development/local-development/) - Development workflow
- [CI/CD Setup](deployment/ci-cd-setup/) - Continuous integration
- [HTTP API Reference](../reference/sdk/http-api/) - HTTP handler signatures
- [Queue API Reference](../reference/sdk/queue-api/) - Queue handler signatures
- [Schedule API Reference](../reference/sdk/schedule-api/) - Schedule handler signatures
