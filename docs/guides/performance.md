---
title: "Performance Guide"
category: guides
subcategory: null
complexity: advanced
duration: null
prerequisites:
  - Production deployment experience
  - Profiling basics
mcp_use: reference
features_covered:
  - Performance optimization
  - Cold start reduction
  - Throughput improvement
code_blocks: true
last_updated: 2025-10-31
---

# Performance Guide

This guide covers performance optimization strategies for Transire applications.

## Local Performance

### Hot Reload Performance

The `transire run --watch` mode is optimized for fast iteration:

```bash
# Start with hot reload
transire run --watch

# Typical reload time: < 1 second
```

**Tips:**
- Keep dependencies minimal
- Use lazy initialization
- Avoid expensive startup operations

### Development Server Tuning

Configure local runtime in `transire.yaml`:

```yaml
runtime:
  http:
    port: 3000
    read_timeout: 30s
    write_timeout: 30s

  queue:
    workers: 4  # Adjust based on CPU cores
    batch_size: 10
    poll_interval: 1s
```

## Cloud Performance

### Cold Start Optimization

#### 1. Use ARM64 Architecture

ARM64 provides better price/performance:

```yaml
deploy:
  lambda:
    architecture: arm64  # 20% better price/performance vs x86_64
    runtime: provided.al2023
```

#### 2. Minimize Dependencies

Smaller packages = faster cold starts:

```bash
# Check binary size
ls -lh bootstrap

# Reduce size with build flags
go build -ldflags="-s -w" -o bootstrap
```

#### 3. Optimize Memory Allocation

Right-size memory for your workload:

```yaml
deploy:
  lambda:
    memory: 512  # Start here, adjust based on metrics
```

**Rule of thumb:**
- API handlers: 256-512 MB
- Data processing: 512-1024 MB
- Heavy compute: 1024+ MB

**Note:** More memory = more CPU, but also more cost

#### 4. Lazy Initialization

Defer expensive initialization:

```go
type Service struct {
    client     *http.Client
    clientOnce sync.Once
}

func (s *Service) getClient() *http.Client {
    s.clientOnce.Do(func() {
        s.client = &http.Client{
            Timeout: 10 * time.Second,
        }
    })
    return s.client
}

func main() {
    app := transire.New()

    // Service created quickly
    app.Provide(func() *Service {
        return &Service{}  // No expensive init
    })

    app.Run()
}
```

#### 5. Connection Pooling

Reuse connections across invocations:

```go
func main() {
    app := transire.New()

    // Database connection pool (singleton)
    app.Provide(func() *sql.DB {
        db, _ := sql.Open("postgres", dsn)

        // Configure pool
        db.SetMaxOpenConns(25)
        db.SetMaxIdleConns(5)
        db.SetConnMaxLifetime(5 * time.Minute)

        return db
    })

    // HTTP client with connection pooling
    app.Provide(func() *http.Client {
        return &http.Client{
            Timeout: 10 * time.Second,
            Transport: &http.Transport{
                MaxIdleConns:        100,
                MaxIdleConnsPerHost: 10,
                IdleConnTimeout:     90 * time.Second,
            },
        }
    })

    app.Run()
}
```

### HTTP Handler Performance

#### Response Streaming

Stream large responses:

```go
func StreamData(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    w.Header().Set("Transfer-Encoding", "chunked")

    encoder := json.NewEncoder(w)

    for item := range dataChannel {
        if err := encoder.Encode(item); err != nil {
            log.Printf("Stream error: %v", err)
            return
        }

        // Flush to client
        if f, ok := w.(http.Flusher); ok {
            f.Flush()
        }
    }
}
```

#### Caching

Implement caching for expensive operations:

```go
type CachedService struct {
    cache *redis.Client
    db    *sql.DB
}

func (s *CachedService) GetUser(ctx context.Context, id string) (*User, error) {
    cacheKey := fmt.Sprintf("user:%s", id)

    // Check cache
    if cached, err := s.cache.Get(ctx, cacheKey).Result(); err == nil {
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
    s.cache.Set(ctx, cacheKey, data, 10*time.Minute)

    return user, nil
}
```

#### Compression

Enable response compression:

```go
func CompressionMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if !strings.Contains(r.Header.Get("Accept-Encoding"), "gzip") {
            next.ServeHTTP(w, r)
            return
        }

        w.Header().Set("Content-Encoding", "gzip")
        gz := gzip.NewWriter(w)
        defer gz.Close()

        gzw := &gzipResponseWriter{Writer: gz, ResponseWriter: w}
        next.ServeHTTP(gzw, r)
    })
}
```

### Queue Handler Performance

#### Batch Processing

Process messages in batches:

```go
func ProcessOrders(ctx context.Context, msgs []Order) error {
    // Process in parallel
    var wg sync.WaitGroup
    errChan := make(chan error, len(msgs))

    for _, order := range msgs {
        wg.Add(1)
        go func(o Order) {
            defer wg.Done()
            if err := processOrder(ctx, o); err != nil {
                errChan <- err
            }
        }(order)
    }

    wg.Wait()
    close(errChan)

    // Collect errors
    var errors []error
    for err := range errChan {
        errors = append(errors, err)
    }

    if len(errors) > 0 {
        return fmt.Errorf("failed to process %d orders", len(errors))
    }

    return nil
}
```

Configure batch size:

```yaml
queues:
  orders:
    batch_size: 10  # Process 10 messages at once
    max_receive_count: 3
```

#### Parallel Processing

Use worker pools:

```go
func ProcessOrdersParallel(ctx context.Context, msgs []Order) error {
    numWorkers := 5
    jobs := make(chan Order, len(msgs))
    results := make(chan error, len(msgs))

    // Start workers
    for w := 0; w < numWorkers; w++ {
        go worker(ctx, jobs, results)
    }

    // Send jobs
    for _, order := range msgs {
        jobs <- order
    }
    close(jobs)

    // Collect results
    var errors []error
    for range msgs {
        if err := <-results; err != nil {
            errors = append(errors, err)
        }
    }

    if len(errors) > 0 {
        return fmt.Errorf("%d messages failed", len(errors))
    }

    return nil
}

func worker(ctx context.Context, jobs <-chan Order, results chan<- error) {
    for order := range jobs {
        results <- processOrder(ctx, order)
    }
}
```

### Database Performance

#### Query Optimization

Use prepared statements:

```go
type UserRepository struct {
    db           *sql.DB
    getUserStmt  *sql.Stmt
    updateStmt   *sql.Stmt
}

func NewUserRepository(db *sql.DB) (*UserRepository, error) {
    getUserStmt, err := db.Prepare("SELECT id, name, email FROM users WHERE id = $1")
    if err != nil {
        return nil, err
    }

    updateStmt, err := db.Prepare("UPDATE users SET name = $1, email = $2 WHERE id = $3")
    if err != nil {
        return nil, err
    }

    return &UserRepository{
        db:          db,
        getUserStmt: getUserStmt,
        updateStmt:  updateStmt,
    }, nil
}

func (r *UserRepository) GetUser(ctx context.Context, id string) (*User, error) {
    var user User
    err := r.getUserStmt.QueryRowContext(ctx, id).Scan(&user.ID, &user.Name, &user.Email)
    return &user, err
}
```

#### Batch Queries

Reduce round trips:

```go
func GetUsersByIDs(ctx context.Context, db *sql.DB, ids []string) ([]User, error) {
    // Build query with placeholders
    query := "SELECT id, name, email FROM users WHERE id = ANY($1)"

    rows, err := db.QueryContext(ctx, query, pq.Array(ids))
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var users []User
    for rows.Next() {
        var user User
        if err := rows.Scan(&user.ID, &user.Name, &user.Email); err != nil {
            return nil, err
        }
        users = append(users, user)
    }

    return users, nil
}
```

#### Index Usage

Ensure queries use indexes:

```sql
-- Check query plan
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'user@example.com';

-- Add index if needed
CREATE INDEX idx_users_email ON users(email);
```

## Profiling

### CPU Profiling

```go
import _ "net/http/pprof"

func main() {
    // Enable pprof endpoint
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()

    app := transire.New()
    app.Run()
}
```

Analyze profile:

```bash
# Capture profile
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# View top functions
(pprof) top

# View call graph
(pprof) web
```

### Memory Profiling

```bash
# Capture heap profile
go tool pprof http://localhost:6060/debug/pprof/heap

# Find memory leaks
(pprof) top
(pprof) list FunctionName
```

## Monitoring

### Key Metrics

Monitor these metrics in production:

1. **Cold Start Duration** - Time to handle first request
2. **Execution Duration** - Handler execution time
3. **Memory Usage** - Peak memory per invocation
4. **Concurrent Executions** - Number of concurrent instances
5. **Throttles** - Rate limiting events
6. **Errors** - Error rate and types

### CloudWatch Metrics

```bash
# View Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=myapp-GetUsers \
  --statistics Average,Maximum \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600
```

## Benchmarking

```go
func BenchmarkGetUser(b *testing.B) {
    // Setup
    tk := testkit.New(b)

    tk.App.Provide(func() *Database {
        return NewMockDatabase()
    })

    // Run benchmark
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        tk.GET("/users/123")
    }
}
```

Run benchmarks:

```bash
# Run benchmarks
go test -bench=. -benchmem

# Compare before/after
go test -bench=. -benchmem > before.txt
# Make changes
go test -bench=. -benchmem > after.txt
benchcmp before.txt after.txt
```

## Best Practices

1. **Measure first** - Profile before optimizing
2. **Right-size resources** - Match memory/CPU to workload
3. **Use ARM64** - Better price/performance
4. **Enable connection pooling** - Reuse connections
5. **Implement caching** - Cache expensive operations
6. **Process in parallel** - Use goroutines for concurrent work
7. **Batch operations** - Reduce overhead
8. **Monitor production** - Track key metrics
9. **Load test** - Test under realistic load
10. **Optimize hot paths** - Focus on frequently-called code

## See Also

- [HTTP Handlers](/docs/sdk/http.md)
- [Queue Handlers](/docs/sdk/queue.md)
- [AWS Deployment](/docs/cloud/aws/deployment.md)
- [DI Patterns](/docs/guides/di-patterns.md)
