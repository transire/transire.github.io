---
title: "Testing"
description: "Write unit, integration, and E2E tests for Transire applications"
keywords:
  - testing
  - unit tests
  - integration tests
  - e2e tests
  - test patterns
category: guides
difficulty: intermediate
estimated_time: 20 minutes
prerequisites:
  - "Understanding of Go testing"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Writing unit tests"
    - "Testing HTTP handlers"
    - "Testing queue and schedule handlers"
  common_questions:
    - "How do I test my handlers?"
    - "How do I mock dependencies?"
    - "How do I test locally vs cloud?"
---

# Testing Your Application

Learn how to test Transire applications locally and write automated tests.

!!! tip "TL;DR"
    Test HTTP handlers with `httptest`, mock `Message` interface for queue handlers, use standard Go testing patterns. Integration tests work with local `transire run`.

---

## Testing Strategies

### 1. Unit Testing HTTP Handlers

HTTP handlers are standard `http.HandlerFunc`, so test them like any Go HTTP handler:

```go
// main_test.go
package main

import (
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestHealthHandler(t *testing.T) {
    req := httptest.NewRequest(http.MethodGet, "/health", nil)
    w := httptest.NewRecorder()

    healthHandler(w, req)

    if w.Code != http.StatusOK {
        t.Errorf("expected status 200, got %d", w.Code)
    }

    expected := `{"status":"healthy"}`
    if w.Body.String() != expected {
        t.Errorf("expected body %q, got %q", expected, w.Body.String())
    }
}
```

**Best practices:**
- Use `httptest.NewRequest()` to create test requests
- Use `httptest.NewRecorder()` to capture responses
- Test status codes, headers, and body content
- Test error cases and edge conditions

---

### 2. Unit Testing Queue Handlers

Mock the `Message` interface:

```go
// handlers_test.go
package main

import (
    "context"
    "testing"

    "github.com/transire/transire/pkg/transire"
)

type mockMessage struct {
    id   string
    body []byte
}

func (m *mockMessage) ID() string                   { return m.id }
func (m *mockMessage) Body() []byte                 { return m.body }
func (m *mockMessage) Attributes() map[string]string { return nil }

func TestEmailQueueHandler(t *testing.T) {
    handler := &EmailQueueHandler{}

    messages := []transire.Message{
        &mockMessage{
            id:   "msg-1",
            body: []byte(`{"to":"test@example.com","subject":"Test","body":"Hello"}`),
        },
    }

    failedIDs, err := handler.HandleMessages(context.Background(), messages)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }

    if len(failedIDs) != 0 {
        t.Errorf("expected no failures, got %d", len(failedIDs))
    }
}
```

**Best practices:**
- Create mock `Message` implementation
- Test with valid and invalid message bodies
- Verify correct messages are returned in `failedIDs`
- Test batch processing logic

---

### 3. Unit Testing Schedule Handlers

```go
// handlers_test.go
func TestCleanupHandler(t *testing.T) {
    handler := &CleanupHandler{}

    event := transire.ScheduleEvent{
        ScheduledTime: time.Now(),
        Name:          "daily-cleanup",
    }

    err := handler.HandleSchedule(context.Background(), event)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
}
```

---

## Integration Testing

### Testing with Local Transire

Run `transire run` and test against localhost endpoints:

```bash
# Terminal 1: Start app
transire run

# Terminal 2: Run tests
go test -tags=integration ./...
```

```go
//go:build integration

package main

import (
    "net/http"
    "testing"
)

func TestHealthEndpoint(t *testing.T) {
    resp, err := http.Get("http://localhost:3000/health")
    if err != nil {
        t.Fatalf("request failed: %v", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        t.Errorf("expected status 200, got %d", resp.StatusCode)
    }
}
```

**Note:** Use build tags (`//go:build integration`) to separate integration tests.

---

### Testing Queue Simulators

**For automated tests,** send messages programmatically:

```go
func TestQueueSimulator(t *testing.T) {
    payload := `{"to":"test@example.com","subject":"Test","body":"Hello"}`

    resp, err := http.Post(
        "http://localhost:4000/queues/email-queue",
        "application/json",
        strings.NewReader(payload),
    )
    if err != nil {
        t.Fatalf("failed to send message: %v", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        t.Errorf("expected status 200, got %d", resp.StatusCode)
    }
}
```

**For manual testing,** use the CLI:
```bash
transire dev queues send email-queue '{"to":"test@example.com","subject":"Test","body":"Hello"}'
```

---

### Testing Schedule Simulators

**For automated tests,** trigger schedules programmatically:

```go
func TestScheduleSimulator(t *testing.T) {
    resp, err := http.Post(
        "http://localhost:4000/schedules/daily-cleanup",
        "application/json",
        nil,
    )
    if err != nil {
        t.Fatalf("failed to trigger schedule: %v", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        t.Errorf("expected status 200, got %d", resp.StatusCode)
    }
}
```

**For manual testing,** use the CLI:
```bash
transire dev schedules execute daily-cleanup
```

---

## Testing with Dependencies

### Mocking AWS Services

For unit tests, mock AWS SDK calls:

```go
import "github.com/aws/aws-sdk-go-v2/service/dynamodb"

type mockDynamoDB struct {
    dynamodbAPI.Client
    GetItemFunc func(context.Context, *dynamodb.GetItemInput, ...func(*dynamodb.Options)) (*dynamodb.GetItemOutput, error)
}

func (m *mockDynamoDB) GetItem(ctx context.Context, input *dynamodb.GetItemInput, opts ...func(*dynamodb.Options)) (*dynamodb.GetItemOutput, error) {
    return m.GetItemFunc(ctx, input, opts...)
}

func TestHandlerWithDynamoDB(t *testing.T) {
    mock := &mockDynamoDB{
        GetItemFunc: func(ctx context.Context, input *dynamodb.GetItemInput, opts ...func(*dynamodb.Options)) (*dynamodb.GetItemOutput, error) {
            // Return mock data
            return &dynamodb.GetItemOutput{}, nil
        },
    }

    handler := &MyHandler{db: mock}
    // Test handler...
}
```

### Using LocalStack

For integration tests with AWS services:

```bash
# Start LocalStack with Docker
docker run --rm -p 4566:4566 localstack/localstack

# Set AWS endpoint
export AWS_ENDPOINT_URL=http://localhost:4566
```

Configure AWS SDK to use LocalStack:

```go
import (
    "github.com/aws/aws-sdk-go-v2/config"
    "github.com/aws/aws-sdk-go-v2/aws"
)

cfg, err := config.LoadDefaultConfig(context.Background(),
    config.WithEndpointResolver(aws.EndpointResolverFunc(
        func(service, region string) (aws.Endpoint, error) {
            return aws.Endpoint{
                URL: "http://localhost:4566",
            }, nil
        },
    )),
)
```

---

## Running Tests

### Run All Tests

```bash
go test ./...
```

### Run Tests with Coverage

```bash
go test -cover ./...
```

Generate coverage report:

```bash
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### Run Integration Tests Only

```bash
go test -tags=integration ./...
```

### Run Unit Tests Only

```bash
go test -short ./...
```

(Use `testing.Short()` in integration tests to skip them)

---

## CI/CD Testing

### GitHub Actions Example

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'

      - name: Run tests
        run: go test -v -cover ./...

      - name: Build
        run: go build -v ./...
```

---

## Best Practices

### 1. Test Independence

Each test should be independent:

```go
func TestHandler(t *testing.T) {
    // Set up fresh state for each test
    handler := NewHandler()

    // Test
    // ...

    // No cleanup needed if using fresh state
}
```

### 2. Table-Driven Tests

For testing multiple scenarios:

```go
func TestHealthHandler(t *testing.T) {
    tests := []struct {
        name           string
        method         string
        expectedStatus int
    }{
        {"GET request", "GET", http.StatusOK},
        {"POST request", "POST", http.StatusMethodNotAllowed},
        {"PUT request", "PUT", http.StatusMethodNotAllowed},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            req := httptest.NewRequest(tt.method, "/health", nil)
            w := httptest.NewRecorder()

            healthHandler(w, req)

            if w.Code != tt.expectedStatus {
                t.Errorf("expected status %d, got %d", tt.expectedStatus, w.Code)
            }
        })
    }
}
```

### 3. Test Helpers

Create helper functions for common setup:

```go
func newTestApp(t *testing.T) *transire.App {
    t.Helper()

    app := transire.New()
    r := app.Router()

    r.Get("/health", healthHandler)
    app.RegisterQueueHandler(&EmailQueueHandler{})

    return app
}

func TestIntegration(t *testing.T) {
    app := newTestApp(t)
    // Use app...
}
```

### 4. Context Timeouts

Always use timeouts in tests:

```go
func TestHandler(t *testing.T) {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    // Use ctx in handler calls
}
```

---

## Next Steps

- [Local Development](local-development.md) – Test during development
- [Deploying to AWS](deploying-to-aws.md) – Test in production
- [Queue Handlers](../core-concepts/queue-handlers.md) – Queue testing patterns
- [CI/CD Guide](https://github.com/transire/transire/blob/main/CONTRIBUTING.md) – Automated testing

---

## See Also

- [Go Testing Documentation](https://pkg.go.dev/testing)
- [httptest Package](https://pkg.go.dev/net/http/httptest)
- [Table-Driven Tests in Go](https://dave.cheney.net/2019/05/07/prefer-table-driven-tests)
