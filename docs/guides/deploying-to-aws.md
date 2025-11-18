# Deploying to AWS

Learn how to deploy your Transire application to AWS Lambda with API Gateway, SQS, and EventBridge.

!!! tip "TL;DR"
    Run `transire build`, install CDK dependencies with `cd infrastructure && npm install && cd ..`, then `transire deploy`. Transire generates CDK infrastructure, bootstraps AWS if needed, and deploys everything automatically.

---

## Prerequisites

Before deploying, ensure you have:

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Node.js 18+** installed
4. **AWS CDK CLI** installed: `npm install -g aws-cdk`
5. **Built artifacts**: Run `transire build` first

---

## Quick Deploy

### 1. Build Artifacts

```bash
transire build
```

This creates:
- Lambda deployment package (`dist/function.zip`)
- CDK TypeScript infrastructure (`infrastructure/lib/`)

### 2. Install CDK Dependencies

```bash
cd infrastructure
npm install
cd ..
```

This installs the AWS CDK TypeScript dependencies needed for deployment.

### 3. Deploy to AWS

```bash
transire deploy
```

Transire will:
- Bootstrap CDK (first time only)
- Synthesize CloudFormation templates
- Deploy infrastructure
- Upload Lambda code
- Configure resources

**Output:**
```
🚀 Deploying Transire application: my-api
🌎 Target: aws/lambda in us-east-1

✨  Synthesis time: 3.21s

my-api-stack: deploying...
my-api-stack: creating CloudFormation changeset...

 ✅  my-api-stack

Outputs:
my-api-stack.ApiEndpoint = https://abc123.execute-api.us-east-1.amazonaws.com

Stack ARN:
arn:aws:cloudformation:us-east-1:123456789012:stack/my-api-stack/...
```

---

## Detailed Deployment Walkthrough

### Step 1: Configure AWS Credentials

```bash
aws configure
```

Provide:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (`json`)

**Verify credentials:**
```bash
aws sts get-caller-identity
```

---

### Step 2: Build Lambda Artifacts

```bash
transire build
```

**What happens:**
1. **Handler Discovery**: Scans code for HTTP, queue, and schedule handlers
2. **Cross-Compilation**: Builds for Linux ARM64
3. **Build Tags**: Excludes `//go:build local` code
4. **Packaging**: Creates ZIP with Go binary
5. **CDK Generation**: Creates TypeScript infrastructure code

**Verify build:**
```bash
ls -lh dist/
# Should show function.zip

ls infrastructure/lib/
# Should show my-api-stack.ts
```

---

### Step 3: Review Generated Infrastructure

Open `infrastructure/lib/my-api-stack.ts` to see generated resources:

```typescript
// Lambda Function
const mainFunction = new lambda.Function(this, 'MainFunction', {
  runtime: lambda.Runtime.PROVIDED_AL2023,
  handler: 'bootstrap',
  code: lambda.Code.fromAsset('../dist/function.zip'),
  architecture: lambda.Architecture.ARM_64,
  memorySize: 256,
  timeout: cdk.Duration.seconds(30),
});

// API Gateway (if HTTP handlers present)
const api = new apigatewayv2.HttpApi(this, 'HttpApi', {
  defaultIntegration: new HttpLambdaIntegration('Integration', mainFunction),
});

// SQS Queue (if queue handlers present)
const emailQueue = new sqs.Queue(this, 'EmailQueue', {
  queueName: 'email-queue',
  deadLetterQueue: { queue: new sqs.Queue(this, 'EmailQueueDLQ'), maxReceiveCount: 3 },
});

// EventBridge Rule (if schedule handlers present)
const dailyCleanup = new events.Rule(this, 'DailyCleanupRule', {
  schedule: events.Schedule.cron({ minute: '0', hour: '2' }),
});
```

Source: [`internal/providers/aws/cdk_generator.go:92-175`](https://github.com/transire/transire/blob/main/internal/providers/aws/cdk_generator.go)

---

### Step 4: Install CDK Dependencies

Before deploying, install the Node.js dependencies for the CDK project:

```bash
cd infrastructure
npm install
cd ..
```

This step is only needed once after running `transire build` for the first time.

---

### Step 5: Deploy Infrastructure

```bash
transire deploy
```

**First deployment** requires CDK bootstrap:
```bash
cd infrastructure
cdk bootstrap aws://ACCOUNT-ID/REGION
```

Transire will prompt you if bootstrapping is needed.

**What happens during deployment:**
1. **CDK Synthesis**: Converts TypeScript to CloudFormation
2. **Asset Upload**: Uploads Lambda ZIP to S3
3. **Stack Creation**: Creates CloudFormation stack
4. **Resource Provisioning**: Creates Lambda, API Gateway, SQS, EventBridge
5. **Output Display**: Shows API endpoint and resource ARNs

---

### Step 6: Verify Deployment

**Test API Gateway endpoint:**
```bash
curl https://abc123.execute-api.us-east-1.amazonaws.com/health
```

**View CloudFormation stack:**
```bash
aws cloudformation describe-stacks \
  --stack-name my-api-stack \
  --query 'Stacks[0].StackStatus'
```

**View Lambda function:**
```bash
aws lambda get-function \
  --function-name my-api-stack-MainFunction-ABC123
```

**View CloudWatch logs:**
```bash
aws logs tail /aws/lambda/my-api-stack-MainFunction-ABC123 --follow
```

---

## Deployment Options

### Deploy to Specific Region

```bash
transire deploy --region us-west-2
```

### Deploy to Specific Environment

```bash
transire deploy --environment production
```

### Dry Run (Preview Changes)

```bash
transire deploy --dry-run
```

Shows CloudFormation diff without applying:
```
Stack my-api-stack
Resources
[+] AWS::Lambda::Function MainFunction
[+] AWS::ApiGatewayV2::Api HttpApi
[+] AWS::SQS::Queue EmailQueue
```

---

## Deployed Resources

After successful deployment:

### Lambda Functions
- One or more functions (depending on multi-function configuration)
- Lambda alias (`live`) for each function
- IAM execution role with necessary permissions
- CloudWatch Log Group for each function

### API Gateway (if HTTP handlers present)
- HTTP API v2 (cheaper, faster than REST API)
- Default integration to Lambda
- Publicly accessible endpoint
- Automatic logging to CloudWatch

### SQS Queues (if queue handlers present)
- One queue per `QueueHandler`
- Dead Letter Queue (DLQ) for each queue
- Lambda event source mapping
- Visibility timeout from `QueueConfig`

### EventBridge Rules (if schedule handlers present)
- One rule per `SchedulerHandler`
- Cron expression from `Schedule()` method
- Lambda target
- Automatic retries on failure

### IAM Permissions
- Lambda execution role
- Permissions to write CloudWatch Logs
- Permissions to access SQS (if queues present)
- Permissions to be invoked by EventBridge (if schedules present)
- Permissions to existing resources (if configured)

### VPC Configuration (if configured)
- Lambda functions in specified subnets
- Security groups attached
- ENI creation for VPC access

---

## Updating Deployments

To update an existing deployment:

```bash
# 1. Make code changes
vim main.go

# 2. Rebuild
transire build

# 3. Deploy updates
transire deploy
```

**CDK shows diff before deploying:**
```
Stack my-api-stack
IAM Statement Changes
┌───┬────────────┬────────┬────────────┬──────────┬──────────┐
│   │ Resource   │ Effect │ Action     │ Principal│ Condition│
├───┼────────────┼────────┼────────────┼──────────┼──────────┤
│ + │ ${Queue}   │ Allow  │ sqs:Send*  │ Lambda   │          │
└───┴────────────┴────────┴────────────┴──────────┴──────────┘
Resources
[~] AWS::Lambda::Function MainFunction
 └─ [~] Code
     └─ [~] .S3Key:
         ├─ [-] old-hash.zip
         └─ [+] new-hash.zip

Do you wish to deploy these changes (y/n)?
```

---

## Monitoring Deployment

### CloudFormation Stack Events

```bash
aws cloudformation describe-stack-events \
  --stack-name my-api-stack \
  --max-items 10
```

### Lambda Metrics

```bash
# Invocations in last hour
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=my-api-stack-MainFunction-ABC123 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

### API Gateway Metrics

```bash
# Request count in last hour
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=my-api-stack-HttpApi \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

---

## Troubleshooting

### "Unable to resolve AWS account"

**Solution:**
```bash
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### "CDK bootstrap required"

**Solution:**
```bash
cd infrastructure
cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/us-east-1
```

### "Deployment failed: CREATE_FAILED"

**Check CloudFormation events:**
```bash
aws cloudformation describe-stack-events \
  --stack-name my-api-stack \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
```

Common issues:
- **IAM permissions**: Ensure deploying role has adequate permissions
- **Resource limits**: Check Lambda concurrent execution limits
- **VPC configuration**: Verify subnet IDs and security group IDs exist

### "Lambda package too large"

**Solution:**
- Check for large dependencies: `go mod graph`
- Use build tags to exclude dev code
- Consider multi-function architecture to split code
- Remove unused dependencies: `go mod tidy`

### "API Gateway 5XX errors"

**Check Lambda logs:**
```bash
aws logs tail /aws/lambda/my-api-stack-MainFunction-ABC123 --follow
```

Common issues:
- Lambda timeout (increase in `transire.yaml`)
- Lambda memory limit (increase in `transire.yaml`)
- Unhandled exceptions in code
- VPC configuration blocking egress

---

## Cost Optimization

### ARM64 Architecture

Use ARM64 for 20% cost savings:
```yaml
# transire.yaml
lambda:
  architecture: arm64
```

### Right-Size Memory

More memory = more CPU = faster execution = lower cost:
```yaml
lambda:
  memory_mb: 256  # Start here, increase if needed
```

### Reserved Concurrency

Prevent runaway costs:
```yaml
lambda:
  reserved_concurrent_executions: 10
```

### Multi-Function Architecture

Split handlers to optimize memory/timeout per use case:
```yaml
functions:
  web:
    include: [http_handlers: "*"]
    memory_mb: 256
    timeout_seconds: 30
  background:
    include: [queue_handlers: "*", schedule_handlers: "*"]
    memory_mb: 512
    timeout_seconds: 300
```

---

## Deleting Deployment

To delete all resources:

```bash
cd infrastructure
cdk destroy
```

**Warning:** This deletes Lambda functions, API Gateway, queues, and all data. This action cannot be undone.

---

## Next Steps

- [transire deploy CLI Reference](../cli-reference/transire-deploy.md) – Detailed command options
- [Multi-Function Architecture](multi-function-architecture.md) – Advanced deployment patterns
- [Custom CDK Extensions](custom-cdk.md) – Extend generated infrastructure
- [Configuration Reference](../configuration/transire-yaml.md) – Customize deployment settings

---

## See Also

- [transire build](../cli-reference/transire-build.md) – Build deployment artifacts
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/) – Learn more about CDK
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
