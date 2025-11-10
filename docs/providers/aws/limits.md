---
title: "AWS Limits and Quotas"
category: providers
subcategory: aws
complexity: intermediate
duration: 10 minutes
mcp_use: reference
last_updated: 2025-11-10
---

# AWS Limits and Quotas

Understanding AWS service limits helps you design scalable Transire applications and avoid runtime errors.

## Lambda Limits

### Function Configuration

| Limit | Value | Adjustable |
|-------|-------|------------|
| Memory allocation | 128 MB - 10,240 MB | No |
| Timeout | 1 second - 15 minutes | No |
| Deployment package size (zipped) | 50 MB (direct upload), 250 MB (S3) | No |
| Deployment package size (unzipped) | 250 MB | No |
| Environment variables | 4 KB total | No |
| Ephemeral storage (/tmp) | 512 MB - 10,240 MB | No |

**Transire defaults:**
```yaml
deploy:
  memory_mb: 512
  timeout_s: 30
  architecture: arm64
```

### Invocation Limits

| Limit | Value | Adjustable |
|-------|-------|------------|
| Concurrent executions (per region) | 1,000 | Yes (service quota) |
| Invocation payload (request) | 6 MB (sync), 256 KB (async) | No |
| Invocation payload (response) | 6 MB | No |

**Impact on Transire:**
- HTTP requests: 6 MB limit
- Queue messages: 256 KB limit (SQS constraint)
- Use S3 for larger payloads, pass references

## API Gateway HTTP API Limits

| Limit | Value | Adjustable |
|-------|-------|------------|
| Payload size | 10 MB | No |
| Timeout | 30 seconds | No |
| WebSocket connection duration | 2 hours | No |
| Throttle rate | 10,000 requests/second | Yes (service quota) |
| Burst rate | 5,000 requests | Yes (service quota) |

**Configure in `transire.yaml`:**
```yaml
http:
  max_request_size_mb: 10  # Enforced by API Gateway
  timeout_s: 30            # Max allowed
```

## SQS Queue Limits

### Message Limits

| Limit | Value | Adjustable |
|-------|-------|------------|
| Message size | 256 KB | No |
| Message retention | 1 minute - 14 days | No |
| Visibility timeout | 0 seconds - 12 hours | No |
| Batch size (SendMessageBatch) | 10 messages | No |
| Batch size (ReceiveMessage) | 10 messages | No |
| Inflight messages | 120,000 (standard), 20,000 (FIFO) | No |

**Transire configuration:**
```yaml
queues:
  max_batch_size: 10              # SQS limit
  visibility_timeout_s: 30        # 0 - 43,200
  max_receive_count: 3            # Retries before DLQ
  message_retention_days: 4       # 1 - 14
```

**Important: 256 KB Message Limit**

This is a hard AWS limit. Design around it:

```go
// ❌ BAD: Large message
type OrderCreated struct {
    OrderID   string
    FullOrder Order     // Could be > 256KB
    Images    []byte    // Binary data
}

// ✅ GOOD: Reference only
type OrderCreated struct {
    OrderID string  // Fetch from database
    S3Key   string  // Fetch images from S3
}
```

### Queue Throughput

| Queue Type | Throughput | Latency |
|------------|------------|---------|
| Standard | Unlimited | Milliseconds |
| FIFO | 300 TPS (batched: 3,000 TPS) | Milliseconds |

Transire uses **Standard queues** by default (unlimited throughput).

## EventBridge Scheduler Limits

| Limit | Value | Adjustable |
|-------|-------|------------|
| Schedules per account | 1,000,000 | Yes (service quota) |
| Invocations per second | 3,000 | Yes (service quota) |
| Target payload | 256 KB | No |
| Schedule rate minimum | 1 minute | No |

**Transire schedule expressions:**
```go
// Rate-based (minimum 1 minute)
app.RegisterScheduled("rate(1 minute)", handler)   // OK
// app.RegisterScheduled("rate(30 seconds)", handler) // ERROR

// Cron-based (minute precision)
app.RegisterScheduled("cron(*/15 * * * ? *)", handler)  // Every 15 min
```

## CloudWatch Logs Limits

| Limit | Value | Adjustable |
|-------|-------|------------|
| Log event size | 256 KB | No |
| Batch size | 1 MB or 10,000 events | No |
| Retention | 1 day - 10 years (configurable) | No |

**Configure retention:**
```yaml
logging:
  retention_days: 7  # 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
```

## IAM Limits

| Limit | Value | Adjustable |
|-------|-------|------------|
| Policies per role | 10 managed, 1 inline | Managed: Yes |
| Policy document size | 2,048 characters (inline), 6,144 characters (managed) | No |
| Roles per account | 1,000 | Yes (service quota) |

Transire generates **one IAM role per handler type** to stay within limits.

## Cost-Related Limits

### Free Tier (First 12 Months)

| Service | Free Tier | Period |
|---------|-----------|--------|
| Lambda | 1M requests/month + 400,000 GB-seconds compute | Always free |
| API Gateway | 1M API calls/month | 12 months |
| SQS | 1M requests/month | Always free |
| CloudWatch Logs | 5 GB ingestion, 5 GB storage | Always free |

### Beyond Free Tier

**Lambda pricing (us-east-1, ARM64):**
- Requests: $0.20 per 1M requests
- Compute: $0.0000133334 per GB-second

**Example costs (512 MB, 100ms average):**
- 1M requests/month: ~$5
- 10M requests/month: ~$50
- 100M requests/month: ~$500

**SQS pricing:**
- Standard queue: $0.40 per 1M requests
- FIFO queue: $0.50 per 1M requests

## Regional Availability

Not all services available in all regions. Check:

```bash
# Check Lambda availability
aws lambda list-functions --region ap-southeast-1

# Check API Gateway v2 availability
aws apigatewayv2 get-apis --region ap-southeast-1
```

Transire works in **all regions supporting:**
- Lambda
- API Gateway HTTP API (v2)
- SQS
- EventBridge Scheduler

## Quota Increase Requests

Some limits are adjustable via Service Quotas:

```bash
# List Lambda quotas
aws service-quotas list-service-quotas --service-code lambda

# Request increase for concurrent executions
aws service-quotas request-service-quota-increase \
  --service-code lambda \
  --quota-code L-B99A9384 \
  --desired-value 5000
```

**Common adjustable quotas:**
- Lambda concurrent executions (default: 1,000)
- API Gateway throttle rate (default: 10,000/sec)
- EventBridge schedules per account (default: 1,000,000)

## Monitoring Limits

Set up CloudWatch alarms for approaching limits:

```bash
# Alert when Lambda concurrency > 800 (80% of 1,000)
aws cloudwatch put-metric-alarm \
  --alarm-name high-lambda-concurrency \
  --metric-name ConcurrentExecutions \
  --namespace AWS/Lambda \
  --statistic Maximum \
  --period 60 \
  --evaluation-periods 1 \
  --threshold 800 \
  --comparison-operator GreaterThanThreshold
```

## Best Practices

### Design for Limits

1. **Keep messages small** - Under 256 KB (SQS limit)
2. **Batch operations** - Use batching to reduce request counts
3. **Set appropriate timeouts** - Under 15 minutes (Lambda limit)
4. **Monitor concurrency** - Set up alarms at 80% of quota
5. **Plan for retries** - DLQ capacity for max retries × message volume

### Handle Limit Errors

```go
func handler(ctx context.Context, req *transire.HTTPRequest) (*transire.HTTPResponse, error) {
    // Handle payload too large
    if len(req.Body) > 6*1024*1024 {
        return response.Error(http.StatusRequestEntityTooLarge,
            "Request too large (max 6MB)")
    }

    // Handle timeout
    ctx, cancel := context.WithTimeout(ctx, 14*time.Minute)
    defer cancel()

    // Your logic...
}
```

### Cost Optimization

1. **Use ARM64** - 20% cheaper than x86_64
   ```yaml
   deploy:
     architecture: arm64
   ```

2. **Right-size memory** - More memory = faster = cheaper per invocation
   ```yaml
   deploy:
     memory_mb: 512  # Start here, adjust based on metrics
   ```

3. **Reduce cold starts** - Smaller deployment packages
   - Remove unused dependencies
   - Use lightweight frameworks

4. **Batch queue processing** - Reduce Lambda invocations
   ```yaml
   queues:
     max_batch_size: 10
     batch_window_s: 5
   ```

## See Also

- [AWS Pricing Calculator](https://calculator.aws/)
- [AWS Service Quotas Console](https://console.aws.amazon.com/servicequotas/)
- [Lambda Limits](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)
- [API Gateway Limits](https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html)
- [SQS Limits](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-quotas.html)
