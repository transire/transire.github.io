---
title: "Dependency Injection Patterns"
category: guides
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - Basic DI understanding
  - Handler implementation experience
mcp_use: reference
features_covered:
  - DI patterns
  - Service management
  - Testing strategies
code_blocks: true
last_updated: 2025-10-31
---

# Dependency Injection Patterns

This guide covers advanced patterns for using Transire's dependency injection system.

## Overview

Transire provides two DI scopes:

- **Singleton** - Created once, shared across all requests
- **Request-scoped** - Created per request, cleaned up after

## Basic Patterns

### Singleton Services

Use for stateless services and connection pools:

```go
func main() {
    app := transire.New()

    // Database connection pool (singleton)
    app.Provide(func() *sql.DB {
        db, _ := sql.Open("postgres", dsn)
        db.SetMaxOpenConns(25)
        return db
    })

    // Redis client (singleton)
    app.Provide(func() *redis.Client {
        return redis.NewClient(&redis.Options{
            Addr: "localhost:6379",
        })
    })

    app.Run()
}
```

### Request-Scoped Services

Use for request-specific state:

```go
func main() {
    app := transire.New()

    // Request-scoped logger with trace ID
    app.ProvideRequest(func(ctx context.Context) *Logger {
        traceID := getTraceID(ctx)
        return NewLogger(traceID)
    })

    app.GET("/users", GetUsers)
    app.Run()
}

func GetUsers(w http.ResponseWriter, r *http.Request) {
    logger := transire.MustGet[*Logger](r.Context())
    logger.Info("Fetching users")  // Includes trace ID
}
```

## Advanced Patterns

### Service Composition

Build complex services from simpler ones:

```go
// Domain services
type UserService struct {
    db    *sql.DB
    cache *redis.Client
}

type OrderService struct {
    db          *sql.DB
    userService *UserService
}

func main() {
    app := transire.New()

    // Register infrastructure
    app.Provide(func() *sql.DB {
        db, _ := sql.Open("postgres", dsn)
        return db
    })

    app.Provide(func() *redis.Client {
        return redis.NewClient(&redis.Options{})
    })

    // Register domain services (depend on infrastructure)
    app.Provide(func(ctx context.Context) *UserService {
        db := transire.MustGet[*sql.DB](ctx)
        cache := transire.MustGet[*redis.Client](ctx)
        return &UserService{db: db, cache: cache}
    })

    app.Provide(func(ctx context.Context) *OrderService {
        db := transire.MustGet[*sql.DB](ctx)
        users := transire.MustGet[*UserService](ctx)
        return &OrderService{
            db:          db,
            userService: users,
        }
    })

    app.Run()
}
```

### Configuration-Based Services

Create services based on configuration:

```go
type Config struct {
    DatabaseURL string
    CacheEnabled bool
}

func main() {
    app := transire.New()

    // Register config
    app.Provide(func() *Config {
        return &Config{
            DatabaseURL: os.Getenv("DATABASE_URL"),
            CacheEnabled: os.Getenv("CACHE_ENABLED") == "true",
        }
    })

    // Services depend on config
    app.Provide(func(ctx context.Context) *sql.DB {
        config := transire.MustGet[*Config](ctx)
        db, _ := sql.Open("postgres", config.DatabaseURL)
        return db
    })

    app.Provide(func(ctx context.Context) Cache {
        config := transire.MustGet[*Config](ctx)
        if config.CacheEnabled {
            return NewRedisCache()
        }
        return NewNoOpCache()
    })

    app.Run()
}
```

### Interface-Based Services

Program to interfaces for testability:

```go
// Define interfaces
type UserRepository interface {
    GetUser(ctx context.Context, id string) (*User, error)
    CreateUser(ctx context.Context, user *User) error
}

// Production implementation
type PostgresUserRepository struct {
    db *sql.DB
}

func (r *PostgresUserRepository) GetUser(ctx context.Context, id string) (*User, error) {
    // Implementation
}

// Register interface with concrete implementation
func main() {
    app := transire.New()

    app.Provide(func() *sql.DB {
        db, _ := sql.Open("postgres", dsn)
        return db
    })

    app.Provide(func(ctx context.Context) UserRepository {
        db := transire.MustGet[*sql.DB](ctx)
        return &PostgresUserRepository{db: db}
    })

    app.GET("/users/{id}", GetUser)
    app.Run()
}

func GetUser(w http.ResponseWriter, r *http.Request) {
    repo := transire.MustGet[UserRepository](r.Context())
    user, _ := repo.GetUser(r.Context(), transire.URLParam(r, "id"))
    response.OK(w, user)
}
```

## Testing Patterns

### Mock Dependencies

Replace real services with mocks in tests:

```go
// Mock implementation
type MockUserRepository struct {
    users map[string]*User
}

func (m *MockUserRepository) GetUser(ctx context.Context, id string) (*User, error) {
    user, ok := m.users[id]
    if !ok {
        return nil, ErrNotFound
    }
    return user, nil
}

func TestGetUser(t *testing.T) {
    tk := testkit.New(t)

    // Register mock
    tk.App.Provide(func() UserRepository {
        return &MockUserRepository{
            users: map[string]*User{
                "123": {ID: "123", Name: "Alice"},
            },
        }
    })

    resp := tk.GET("/users/123")

    tk.AssertStatus(resp, 200)
    tk.AssertJSONContains(resp, `{"name": "Alice"}`)
}
```

### Test Fixtures

Create reusable test fixtures:

```go
type TestFixture struct {
    App  *transire.App
    DB   *TestDB
    Mock *MockServices
}

func NewTestFixture(t *testing.T) *TestFixture {
    tk := testkit.New(t)

    testDB := NewTestDB(t)
    mockServices := NewMockServices()

    tk.App.Provide(func() *sql.DB {
        return testDB.DB
    })

    tk.App.Provide(func() ExternalAPI {
        return mockServices.API
    })

    return &TestFixture{
        App:  tk.App,
        DB:   testDB,
        Mock: mockServices,
    }
}

func TestComplexScenario(t *testing.T) {
    fixture := NewTestFixture(t)

    // Setup test data
    fixture.DB.Insert("users", user)
    fixture.Mock.API.SetResponse(expectedResponse)

    // Test
    resp := fixture.App.TestRequest("GET", "/users/123")
    // Assertions...
}
```

## Performance Patterns

### Lazy Initialization

Defer expensive initialization until first use:

```go
type Service struct {
    db     *sql.DB
    client *http.Client
    once   sync.Once
}

func (s *Service) init() {
    s.once.Do(func() {
        // Expensive initialization only happens once
        s.client = &http.Client{
            Timeout: 10 * time.Second,
        }
    })
}

func (s *Service) DoWork() {
    s.init()
    // Use s.client
}

func main() {
    app := transire.New()

    app.Provide(func(ctx context.Context) *Service {
        db := transire.MustGet[*sql.DB](ctx)
        return &Service{db: db}  // No expensive init yet
    })

    app.Run()
}
```

### Connection Pooling

Properly configure connection pools:

```go
func main() {
    app := transire.New()

    app.Provide(func() *sql.DB {
        db, _ := sql.Open("postgres", dsn)

        // Configure pool
        db.SetMaxOpenConns(25)
        db.SetMaxIdleConns(5)
        db.SetConnMaxLifetime(5 * time.Minute)

        return db
    })

    app.Run()
}
```

### Caching

Implement caching for expensive operations:

```go
type CachedUserService struct {
    db    *sql.DB
    cache *redis.Client
}

func (s *CachedUserService) GetUser(ctx context.Context, id string) (*User, error) {
    // Check cache first
    if cached, err := s.cache.Get(ctx, "user:"+id).Result(); err == nil {
        var user User
        json.Unmarshal([]byte(cached), &user)
        return &user, nil
    }

    // Cache miss - query database
    user, err := s.queryDB(ctx, id)
    if err != nil {
        return nil, err
    }

    // Store in cache
    data, _ := json.Marshal(user)
    s.cache.Set(ctx, "user:"+id, data, 10*time.Minute)

    return user, nil
}
```

## Error Handling

### Graceful Degradation

Handle dependency failures gracefully:

```go
func main() {
    app := transire.New()

    // Primary cache
    app.Provide(func() Cache {
        client, err := redis.NewClient(&redis.Options{})
        if err != nil {
            // Fallback to in-memory cache
            log.Println("Redis unavailable, using in-memory cache")
            return NewInMemoryCache()
        }
        return NewRedisCache(client)
    })

    app.Run()
}
```

### Optional Dependencies

Make dependencies optional:

```go
func main() {
    app := transire.New()

    // Optional metrics service
    if metricsURL := os.Getenv("METRICS_URL"); metricsURL != "" {
        app.Provide(func() *MetricsClient {
            return NewMetricsClient(metricsURL)
        })
    }

    app.Run()
}

func Handler(w http.ResponseWriter, r *http.Request) {
    // Safely check for optional dependency
    if metrics, err := transire.Get[*MetricsClient](r.Context()); err == nil {
        metrics.Increment("handler.calls")
    }

    // Continue even if metrics unavailable
}
```

## Best Practices

1. **Use interfaces** for testability and flexibility
2. **Singleton for stateless** services and pools
3. **Request-scoped for state** that shouldn't be shared
4. **Fail fast** - Let `MustGet` panic on critical dependencies
5. **Graceful fallback** for optional dependencies using `Get`
6. **Lazy initialization** for expensive operations
7. **Test with mocks** to isolate unit tests
8. **Document dependencies** in service constructors

## See Also

- [Dependency Injection](/sdk/di.md)
- [Testing Guide](/sdk/testkit.md)
- [Error Handling](/guides/error-handling.md)
- [Performance Guide](/guides/performance.md)
