---
title: Production Deployment Checklist
description: Complete checklist for launching Transire applications to production
category: guide
subcategory: deployment
complexity: intermediate
duration: 60 minutes
mcp_use: guide
features_covered:
  - Production readiness
  - Security hardening
  - Performance optimization
  - Monitoring setup
  - Disaster recovery
code_blocks: true
last_updated: 2025-11-10
---

# Production Deployment Checklist

> **Comprehensive checklist** to ensure your Transire application is production-ready

## Overview

Use this checklist before launching to production. Each item includes:
- ✅ Action item
- Why it matters
- How to implement
- Verification steps

**Estimated time:** 60 minutes

---

## Phase 1: Code Quality

### Code Review

- [ ] **All code reviewed by at least one other developer**

  **Why:** Catch bugs, improve design, share knowledge

  **How:**
  ```bash
  # Create PR for review
  git checkout -b feature/my-feature
  git push origin feature/my-feature
  # Open PR on GitHub/GitLab
  ```

- [ ] **No TODO comments in production code**

  **Why:** TODOs indicate incomplete work

  **How:**
  ```bash
  # Find TODOs
  grep -r "TODO" . --exclude-dir=node_modules --exclude-dir=.git
  ```

- [ ] **Dead code removed**

  **Why:** Reduce maintenance burden, improve clarity

  **How:**
  ```bash
  # Check for unused functions
  go run golang.org/x/tools/cmd/deadcode@latest ./...
  ```

### Testing

- [ ] **Unit tests passing with >80% coverage**

  **Why:** Catch regressions, document behavior

  **How:**
  ```bash
  # Run tests with coverage
  go test -cover ./...

  # Generate coverage report
  go test -coverprofile=coverage.out ./...
  go tool cover -html=coverage.out -o coverage.html
  ```

  **Verify:**
  ```bash
  go test ./... -v
  ```

- [ ] **Integration tests passing**

  **Why:** Verify components work together

  **How:**
  ```go
  func TestOrdersAPI(t *testing.T) {
      tk := testkit.New(t)
      // Test full workflows
  }
  ```

- [ ] **Load testing completed**

  **Why:** Ensure app handles expected traffic

  **How:**
  ```bash
  # Using k6
  k6 run --vus 100 --duration 5m loadtest.js
  ```

  **Target:** p95 < 500ms, error rate < 0.1%

### Code Quality Tools

- [ ] **Linter passing (golangci-lint)**

  **How:**
  ```bash
  golangci-lint run ./...
  ```

- [ ] **Security scan passing (gosec)**

  **How:**
  ```bash
  gosec ./...
  ```

- [ ] **Dependencies up to date**

  **How:**
  ```bash
  go list -u -m all | grep '\['
  go get -u ./...
  ```

---

## Phase 2: Configuration

### Environment Configuration

- [ ] **Production environment configured in transire.yaml**

  **How:**
  ```yaml
  environments:
    prod:
      deploy:
        region: us-east-1
        memory_mb: 1024
        timeout_s: 60
      env:
        ENVIRONMENT: production
        LOG_LEVEL: info
  ```

- [ ] **Secrets moved to AWS Secrets Manager**

  **Why:** Never commit secrets to git

  **How:**
  ```bash
  # Create secret
  aws secretsmanager create-secret \
    --name orders-api/database \
    --secret-string '{"password":"xxx"}'

  # Access in code
  secret := secretsManager.GetSecret(ctx, "orders-api/database")
  ```

- [ ] **Environment variables documented**

  **How:** Create `ENV.md`:
  ```markdown
  # Environment Variables

  ## Required
  - `DATABASE_URL` - PostgreSQL connection string
  - `STRIPE_API_KEY` - Stripe secret key

  ## Optional
  - `LOG_LEVEL` - Logging level (default: info)
  ```

### Deployment Settings

- [ ] **Lambda memory optimized**

  **Why:** Balance cost and performance

  **How:**
  ```bash
  # Test different memory sizes
  transire deploy --env staging --memory 256
  transire deploy --env staging --memory 512
  transire deploy --env staging --memory 1024

  # Check metrics
  transire metrics --env staging
  ```

  **Target:** 50-75% memory utilization

- [ ] **Lambda timeout appropriate**

  **Why:** Prevent hung requests

  **How:**
  ```yaml
  deploy:
    timeout_s: 30  # Adjust based on p99 latency
  ```

- [ ] **Lambda architecture set (ARM64 recommended)**

  **Why:** 20% cost savings

  **How:**
  ```yaml
  deploy:
    arch: arm64
  ```

---

## Phase 3: Security

### Authentication & Authorization

- [ ] **Authentication implemented**

  **How:**
  ```go
  app.Use(AuthMiddleware)

  func AuthMiddleware(next http.Handler) http.Handler {
      return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
          token := r.Header.Get("Authorization")
          if !validateToken(token) {
              response.Unauthorized(w, "Invalid token")
              return
          }
          next.ServeHTTP(w, r)
      })
  }
  ```

- [ ] **Authorization checks in place**

  **How:**
  ```go
  func deleteOrder(w http.ResponseWriter, r *http.Request) {
      userRole := r.Context().Value("role").(string)
      if userRole != "admin" {
          response.Forbidden(w, "Admin access required")
          return
      }
      // Delete order
  }
  ```

- [ ] **API keys rotated**

  **Why:** Reduce risk of compromised keys

  **How:**
  ```bash
  # Rotate keys every 90 days
  aws secretsmanager rotate-secret \
    --secret-id orders-api/api-key
  ```

### Input Validation

- [ ] **All inputs validated**

  **Why:** Prevent injection attacks

  **How:**
  ```go
  func createOrder(w http.ResponseWriter, r *http.Request) {
      var req CreateOrderRequest
      if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
          response.BadRequest(w, "Invalid JSON")
          return
      }

      // Validate
      if req.Quantity <= 0 {
          response.BadRequest(w, "Quantity must be positive")
          return
      }
      if len(req.Product) == 0 || len(req.Product) > 255 {
          response.BadRequest(w, "Invalid product name")
          return
      }
  }
  ```

- [ ] **SQL injection prevention verified**

  **How:** Always use parameterized queries:
  ```go
  // ✅ Safe
  db.QueryContext(ctx, "SELECT * FROM orders WHERE id = $1", id)

  // ❌ Unsafe
  db.QueryContext(ctx, "SELECT * FROM orders WHERE id = '"+id+"'")
  ```

- [ ] **XSS prevention implemented**

  **How:**
  ```go
  import "html/template"

  // Escape HTML in responses
  safeHTML := template.HTMLEscapeString(userInput)
  ```

### Security Headers

- [ ] **Security headers configured**

  **How:**
  ```go
  func SecurityHeadersMiddleware(next http.Handler) http.Handler {
      return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
          w.Header().Set("X-Content-Type-Options", "nosniff")
          w.Header().Set("X-Frame-Options", "DENY")
          w.Header().Set("X-XSS-Protection", "1; mode=block")
          w.Header().Set("Strict-Transport-Security", "max-age=31536000")
          next.ServeHTTP(w, r)
      })
  }
  ```

### HTTPS & TLS

- [ ] **HTTPS enforced**

  **How:** API Gateway enforces HTTPS by default

- [ ] **TLS 1.2+ required**

  **How:** Configure in API Gateway:
  ```yaml
  http:
    tls:
      minimum_version: "TLS_1_2"
  ```

### IAM Permissions

- [ ] **Least privilege IAM policies**

  **Why:** Minimize blast radius of compromised credentials

  **Verify:**
  ```bash
  # Review Lambda role permissions
  aws iam get-role-policy \
    --role-name orders-api-prod-execution-role \
    --policy-name orders-api-prod-policy
  ```

- [ ] **No hardcoded credentials**

  **How:**
  ```bash
  # Scan for secrets
  git secrets --scan

  # Or use truffleHog
  trufflehog filesystem .
  ```

---

## Phase 4: Observability

### Logging

- [ ] **Structured logging implemented**

  **Why:** Easier to query and analyze

  **How:**
  ```go
  import "go.uber.org/zap"

  logger.Info("Order created",
      zap.String("order_id", order.ID),
      zap.String("user_id", user.ID),
      zap.Float64("total", order.Total),
  )
  ```

- [ ] **Log levels configured**

  **How:**
  ```yaml
  observability:
    logging:
      level: info        # production
      format: json       # structured
  ```

- [ ] **Sensitive data not logged**

  **Why:** PCI/HIPAA compliance

  **Check:**
  ```bash
  # Search for potential issues
  grep -r "password\|credit_card\|ssn" . --exclude-dir=.git
  ```

### Metrics

- [ ] **Custom metrics instrumented**

  **How:**
  ```go
  import "github.com/prometheus/client_golang/prometheus"

  var ordersCreated = prometheus.NewCounter(
      prometheus.CounterOpts{
          Name: "orders_created_total",
          Help: "Total orders created",
      },
  )

  func createOrder(...) {
      ordersCreated.Inc()
  }
  ```

- [ ] **CloudWatch dashboard created**

  **How:**
  ```bash
  # Create dashboard
  aws cloudwatch put-dashboard \
    --dashboard-name orders-api-prod \
    --dashboard-body file://dashboard.json
  ```

### Alerting

- [ ] **Critical alerts configured**

  **Why:** Know when things break

  **How:**
  ```yaml
  observability:
    alarms:
      enabled: true
      email: ops@company.com

      lambda_errors:
        threshold: 10
        period_minutes: 5

      http_5xx:
        threshold: 5
        period_minutes: 5
  ```

- [ ] **On-call rotation established**

  **How:**
  - PagerDuty integration
  - Slack alerts
  - Escalation policy

### Tracing

- [ ] **Distributed tracing enabled**

  **How:**
  ```yaml
  observability:
    tracing:
      enabled: true
      sample_rate: 0.1  # 10% of requests
  ```

---

## Phase 5: Performance

### Database

- [ ] **Database connection pooling configured**

  **How:**
  ```go
  db.SetMaxOpenConns(25)
  db.SetMaxIdleConns(5)
  db.SetConnMaxLifetime(5 * time.Minute)
  ```

- [ ] **Database indexes created**

  **Why:** Fast queries

  **How:**
  ```sql
  CREATE INDEX idx_orders_user_id ON orders(user_id);
  CREATE INDEX idx_orders_status ON orders(status);
  CREATE INDEX idx_orders_created_at ON orders(created_at);
  ```

- [ ] **Slow queries identified and optimized**

  **How:**
  ```bash
  # Enable slow query log
  # Review with EXPLAIN
  EXPLAIN ANALYZE SELECT * FROM orders WHERE status = 'pending';
  ```

### Caching

- [ ] **Caching strategy implemented**

  **How:**
  ```go
  // Redis cache
  cache.Set(ctx, "order:"+id, order, 5*time.Minute)

  // HTTP cache headers
  w.Header().Set("Cache-Control", "public, max-age=300")
  ```

- [ ] **Cache invalidation working**

  **Why:** Prevent stale data

  **How:**
  ```go
  func updateOrder(ctx context.Context, order *Order) error {
      // Update database
      db.UpdateOrder(ctx, order)

      // Invalidate cache
      cache.Delete(ctx, "order:"+order.ID)

      return nil
  }
  ```

### Lambda Optimization

- [ ] **Cold start optimized**

  **How:**
  ```bash
  # Minimize binary size
  go build -ldflags="-s -w"

  # Lazy initialization
  var db *Database
  func getDB() *Database {
      if db == nil {
          db = connectDB()
      }
      return db
  }
  ```

- [ ] **Memory tuning completed**

  **How:**
  ```bash
  transire analyze --env prod

  # Output shows recommendations:
  # HTTP handler: Reduce to 512MB (currently 1024MB)
  ```

---

## Phase 6: Reliability

### Error Handling

- [ ] **All errors handled gracefully**

  **How:**
  ```go
  func getOrder(w http.ResponseWriter, r *http.Request) {
      order, err := db.GetOrder(ctx, id)
      if err != nil {
          if errors.Is(err, sql.ErrNoRows) {
              response.NotFound(w, "Order not found")
              return
          }
          log.Printf("Database error: %v", err)
          response.InternalServerError(w, "Failed to fetch order")
          return
      }
      response.OK(w, order)
  }
  ```

- [ ] **Panic recovery implemented**

  **How:**
  ```go
  app.Use(RecoveryMiddleware)
  ```

### Retries

- [ ] **Retry logic for external services**

  **How:**
  ```go
  func callExternalAPI(ctx context.Context) error {
      return RetryWithBackoff(ctx, RetryConfig{
          MaxRetries:   3,
          InitialDelay: 100 * time.Millisecond,
          MaxDelay:     5 * time.Second,
      }, func() error {
          return httpClient.Get(apiURL)
      })
  }
  ```

- [ ] **Queue batch failures handled**

  **How:**
  ```go
  func processOrders(ctx context.Context, orders []Order) error {
      br := transire.NewBatchResult(len(orders))

      for i, order := range orders {
          if err := process(order); err != nil {
              br.Fail(i, err)
              continue
          }
      }

      return br.ToCloudPartialBatchResponse()
  }
  ```

### Timeouts

- [ ] **Request timeouts configured**

  **How:**
  ```go
  client := &http.Client{
      Timeout: 30 * time.Second,
  }
  ```

- [ ] **Database query timeouts**

  **How:**
  ```go
  ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
  defer cancel()

  rows, err := db.QueryContext(ctx, query)
  ```

### Rate Limiting

- [ ] **Rate limiting implemented**

  **Why:** Prevent abuse

  **How:**
  ```go
  app.Use(RateLimitMiddleware(RateLimitConfig{
      RequestsPerMinute: 60,
      BurstSize:         10,
  }))
  ```

---

## Phase 7: Data Management

### Backups

- [ ] **Database backups automated**

  **How:**
  ```bash
  # RDS automatic backups
  aws rds modify-db-instance \
    --db-instance-identifier orders-db \
    --backup-retention-period 7 \
    --preferred-backup-window "03:00-04:00"
  ```

- [ ] **Backup restoration tested**

  **Why:** Verify backups work before disaster

  **How:**
  ```bash
  # Restore to test instance
  aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier test-restore \
    --db-snapshot-identifier snapshot-123
  ```

### Data Privacy

- [ ] **PII data encrypted at rest**

  **How:**
  ```yaml
  deploy:
    encryption:
      enabled: true
      kms_key_arn: arn:aws:kms:...
  ```

- [ ] **Data retention policy implemented**

  **How:**
  ```go
  // Schedule: Delete data older than 90 days
  app.Schedule("cleanup", "@daily 02:00", func(ctx context.Context, db *Database) error {
      cutoff := time.Now().Add(-90 * 24 * time.Hour)
      return db.DeleteOldRecords(ctx, cutoff)
  })
  ```

---

## Phase 8: Deployment Process

### Version Control

- [ ] **Main branch protected**

  **How:** GitHub branch protection rules

- [ ] **Merge requires approval**

  **Why:** Prevent accidental deploys

### CI/CD

- [ ] **CI pipeline running**

  **How:**
  ```yaml
  # .github/workflows/ci.yml
  name: CI
  on: [push, pull_request]

  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-go@v4
        - run: go test ./...
        - run: golangci-lint run ./...
  ```

- [ ] **CD pipeline configured for production**

  **How:**
  ```yaml
  # .github/workflows/deploy.yml
  name: Deploy
  on:
    push:
      branches: [main]

  jobs:
    deploy:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - name: Deploy
          run: transire deploy --env prod
  ```

### Deployment Safety

- [ ] **Blue-green deployment strategy**

  **Why:** Zero-downtime deploys

  **How:** Use Lambda aliases

- [ ] **Rollback plan documented**

  **How:**
  ```bash
  # Rollback command
  transire rollback --env prod
  ```

- [ ] **Deployment monitoring**

  **Why:** Catch issues early

  **How:** Monitor error rates for 30 minutes post-deploy

---

## Phase 9: Documentation

### Code Documentation

- [ ] **README.md complete**

  **Include:**
  - Project description
  - Setup instructions
  - Development guide
  - Deployment guide

- [ ] **API documented**

  **How:** OpenAPI/Swagger spec
  ```yaml
  openapi: 3.0.0
  info:
    title: Orders API
    version: 1.0.0
  paths:
    /orders:
      get:
        summary: List orders
        responses:
          200:
            description: List of orders
  ```

### Runbooks

- [ ] **Runbook created for common issues**

  **Include:**
  - Deployment failures
  - Database connection errors
  - High error rates
  - Performance degradation

- [ ] **Disaster recovery plan documented**

  **Include:**
  - Backup restoration
  - Failover procedures
  - Contact information

---

## Phase 10: Legal & Compliance

### Compliance

- [ ] **GDPR compliance verified** (if applicable)

  **Requirements:**
  - Right to access
  - Right to deletion
  - Data portability
  - Consent management

- [ ] **PCI DSS compliance** (if handling payments)

  **Requirements:**
  - Never store card data
  - Use payment processor (Stripe, etc.)
  - Audit logging

### Legal

- [ ] **Terms of Service created**

- [ ] **Privacy Policy created**

- [ ] **Data Processing Agreement** (if applicable)

---

## Final Pre-Launch Checklist

### 24 Hours Before Launch

- [ ] Full system test in staging
- [ ] Load test at 2x expected traffic
- [ ] Verify monitoring and alerts
- [ ] Backup database
- [ ] Review rollback plan
- [ ] Notify team of launch

### Launch Day

- [ ] Deploy to production
- [ ] Verify health checks
- [ ] Monitor error rates (30 min)
- [ ] Monitor performance metrics
- [ ] Test critical user flows
- [ ] Update status page

### Post-Launch (24 hours)

- [ ] Review logs for errors
- [ ] Check performance metrics
- [ ] Verify monitoring alerts working
- [ ] Review cost estimates
- [ ] Document any issues
- [ ] Team retrospective

---

## Verification Commands

### Quick Health Check

```bash
# Verify deployment
transire info --env prod

# Check health endpoint
curl https://api.yourdomain.com/health

# View recent logs
transire logs --env prod --since 10m

# Check metrics
transire metrics --env prod

# Verify no errors
transire logs --env prod --filter ERROR --since 1h
```

### AWS Resource Verification

```bash
# Lambda functions
aws lambda list-functions | grep orders-api-prod

# API Gateway
aws apigatewayv2 get-apis | grep orders-api-prod

# CloudWatch alarms
aws cloudwatch describe-alarms --alarm-name-prefix orders-api-prod

# Secrets Manager
aws secretsmanager list-secrets | grep orders-api
```

---

## Post-Launch Monitoring

### Week 1

- [ ] Daily log review
- [ ] Daily metrics review
- [ ] Monitor costs
- [ ] Address user feedback

### Month 1

- [ ] Review performance trends
- [ ] Optimize based on usage
- [ ] Update documentation
- [ ] Security audit

---

## See Also

- [First Deployment Guide](first-deployment/) - Deploy basics
- [Production Tutorial](../../learn/tutorials/07-production-deployment/) - Advanced deployment
- [Monitoring Guide](../observability/monitoring/) - Set up monitoring
- [Troubleshooting](../troubleshooting/) - Common issues
- [Security Guide](../security/) - Security best practices

