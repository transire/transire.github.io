---
title: "Workspaces"
category: iac
subcategory: null
complexity: intermediate
duration: 15 minutes
prerequisites:
  - Backend configured (S3 + DynamoDB)
  - Understanding of OpenTofu basics
  - Deployed to at least one environment
mcp_use: reference
mcp_operations:
  - manage_environments
  - configure_workspaces
  - deploy_multi_env
features_covered:
  - OpenTofu workspaces
  - Environment isolation
  - Multi-environment deployment
  - Workspace best practices
code_blocks: true
last_updated: 2025-10-30
---

# Workspaces

## What are Workspaces?

**Workspaces** are OpenTofu's mechanism for managing multiple instances of the same infrastructure configuration. Each workspace has its own state file, allowing you to deploy the same application to different environments.

**Common workspaces:**
- `dev` - Development environment
- `staging` - Pre-production testing
- `prod` - Production environment

**Key concept:** Same OpenTofu code, different state per workspace.

```
┌──────────────────────────────────────────────────────┐
│              OpenTofu Configuration                   │
│              (infra/*.tf files)                       │
│                                                       │
│  Routes, Queues, Schedules, IAM, etc.               │
└──────────┬────────────────┬───────────────┬─────────┘
           │                │               │
      ┌────▼────┐      ┌────▼────┐     ┌───▼─────┐
      │   Dev   │      │ Staging │     │  Prod   │
      │Workspace│      │Workspace│     │Workspace│
      └────┬────┘      └────┬────┘     └────┬────┘
           │                │                │
      ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
      │dev.tfst │      │staging. │     │prod.    │
      │  ate    │      │ tfstate │     │tfstate  │
      └─────────┘      └─────────┘     └─────────┘
    Dev resources    Staging resources  Prod resources
```

## Why Use Workspaces?

### Problem: Managing Multiple Environments

Without workspaces, you'd need:
- Separate directories for each environment
- Duplicate OpenTofu configurations
- Manual coordination to keep configs in sync

**Error-prone and hard to maintain.**

### Solution: Single Configuration, Multiple States

With workspaces:
- ✅ One set of `.tf` files
- ✅ Environment-specific variables
- ✅ Isolated state per environment
- ✅ Easy environment promotion
- ✅ Consistent infrastructure across environments

## Workspaces in Transire

Transire manages workspaces automatically through `transire.yaml`:

```yaml
version: 1
service: orders
runtime: go
cloud: aws

# Environment configurations
env:
  - name: dev
    workspace: dev        # OpenTofu workspace name
    variables:
      LOG_LEVEL: debug
      DB_POOL_SIZE: "5"

  - name: staging
    workspace: staging
    variables:
      LOG_LEVEL: info
      DB_POOL_SIZE: "10"

  - name: prod
    workspace: prod
    variables:
      LOG_LEVEL: warn
      DB_POOL_SIZE: "20"
```

**When you run `transire deploy --env=prod`:**
1. Selects `prod` workspace
2. Uses `prod` variables
3. Deploys to `prod` state

## Creating Workspaces

### Default Workspace

OpenTofu starts with a `default` workspace (Transire typically uses `dev` instead):

```bash
cd infra/

# View current workspace
tofu workspace show
# Output: default (or dev if already created)

# List all workspaces
tofu workspace list
# Output:
#   default
# * dev
```

### Creating New Workspaces

Create workspaces for your environments:

```bash
# Create dev workspace
tofu workspace new dev

# Create staging workspace
tofu workspace new staging

# Create production workspace
tofu workspace new prod
```

**Transire creates workspaces automatically** when deploying to new environments:

```bash
# First deploy to dev (creates dev workspace)
transire deploy --env=dev

# First deploy to prod (creates prod workspace)
transire deploy --env=prod
```

## Switching Between Workspaces

### Using OpenTofu

```bash
# Switch to dev
tofu workspace select dev

# View current workspace
tofu workspace show
# Output: dev

# Deploy changes
tofu apply
```

### Using Transire

```bash
# Deploy to specific environment (automatically selects workspace)
transire deploy --env=dev
transire deploy --env=staging
transire deploy --env=prod

# Default environment is 'dev' if not specified
transire deploy
```

## Workspace State Storage

Each workspace has its own state file in S3:

```
s3://transire-tf-state/
└── orders/                          # Service name
    ├── dev/
    │   └── terraform.tfstate        # Dev workspace state
    ├── staging/
    │   └── terraform.tfstate        # Staging workspace state
    └── prod/
        └── terraform.tfstate        # Prod workspace state
```

**Benefits:**
- Complete environment isolation
- Independent deployments
- No risk of cross-environment changes
- Easy rollback per environment

## Environment-Specific Configuration

### Variables per Environment

Configure different values per environment in `transire.yaml`:

```yaml
env:
  - name: dev
    workspace: dev
    variables:
      # Development settings
      LOG_LEVEL: debug
      HTTP_TIMEOUT: "60"
      QUEUE_WORKERS: "2"
      ENABLE_DEBUG: "true"

  - name: prod
    workspace: prod
    variables:
      # Production settings
      LOG_LEVEL: warn
      HTTP_TIMEOUT: "30"
      QUEUE_WORKERS: "10"
      ENABLE_DEBUG: "false"
```

**These variables become Lambda environment variables:**

```go
// Access in your Go code
logLevel := os.Getenv("LOG_LEVEL")  // "debug" in dev, "warn" in prod
timeout := os.Getenv("HTTP_TIMEOUT") // "60" in dev, "30" in prod
```

### Deployment Configuration per Environment

Different deployment settings per environment:

```yaml
deploy:
  dev:
    arch: arm64
    memory_mb: 256        # Lower memory for dev
    timeout_s: 30

  prod:
    arch: arm64
    memory_mb: 1024       # More memory for prod
    timeout_s: 60
```

### Resource Naming per Workspace

Transire automatically includes workspace in resource names:

```
# Dev workspace
orders-dev-http                      # HTTP Lambda
orders-dev-queue-order-created      # Queue consumer
orders-dev-order-created            # SQS queue

# Prod workspace
orders-prod-http                     # HTTP Lambda
orders-prod-queue-order-created     # Queue consumer
orders-prod-order-created           # SQS queue
```

**No naming conflicts** - resources clearly labeled by environment.

## Deploying to Multiple Environments

### Progressive Deployment Strategy

**Recommended workflow:**

1. **Develop locally** - Iterate fast with `transire run`
2. **Deploy to dev** - Test in cloud environment
3. **Deploy to staging** - Pre-production validation
4. **Deploy to prod** - Production rollout

```bash
# Local development
transire run

# Test changes in dev
transire deploy --env=dev

# Promote to staging
transire deploy --env=staging

# Deploy to production
transire deploy --env=prod
```

### CI/CD Pipeline with Workspaces

Automate deployments using GitHub Actions:

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main, staging, production]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Deploy to dev
        if: github.ref == 'refs/heads/main'
        run: transire deploy --env=dev

      - name: Deploy to staging
        if: github.ref == 'refs/heads/staging'
        run: transire deploy --env=staging

      - name: Deploy to production
        if: github.ref == 'refs/heads/production'
        run: transire deploy --env=prod
```

**Branch-based deployment:**
- `main` → deploys to `dev`
- `staging` → deploys to `staging`
- `production` → deploys to `prod`

### Manual Approval for Production

Add manual approval gate for production deployments:

```yaml
# .github/workflows/deploy-prod.yml
name: Deploy to Production

on:
  workflow_dispatch:  # Manual trigger only

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://api.example.com

    steps:
      - name: Deploy to production
        run: transire deploy --env=prod
```

**GitHub Environment Protection:**
- Require approval from team members
- Restrict to specific branches
- Add deployment delay
- Require status checks to pass

## Workspace Best Practices

### 1. One Service = One Set of Workspaces

**Do:** Each service manages its own workspaces
```
orders/      → dev, staging, prod workspaces
users/       → dev, staging, prod workspaces
payments/    → dev, staging, prod workspaces
```

**Don't:** Share workspaces across services (creates coupling)

### 2. Environment Naming Consistency

**Use consistent workspace names across services:**
- `dev` (not `development`, `devel`, `dev-env`)
- `staging` (not `stage`, `preprod`, `uat`)
- `prod` (not `production`, `live`, `master`)

**Benefits:**
- Clear communication
- Simpler automation
- Fewer mistakes

### 3. Isolate Production State

**Separate state storage for production:**

```yaml
# Dev/staging - shared backend
infra:
  backend:
    bucket: transire-tf-state-nonprod

# Production - dedicated backend
infra:
  backend:
    bucket: transire-tf-state-prod
```

**Extra protection for production:**
- Different S3 bucket
- Stricter IAM permissions
- Additional backups
- Separate AWS account (advanced)

### 4. Test in Staging Before Production

**Always deploy to staging first:**

```bash
# Deploy to staging
transire deploy --env=staging

# Run integration tests
./scripts/test-staging.sh

# If tests pass, deploy to production
transire deploy --env=prod
```

**Staging should mirror production:**
- Same configuration (smaller resources OK)
- Same data structure
- Same integrations

### 5. Use Workspace-Specific Variables

**Don't hardcode environment values:**

```go
// ❌ BAD: Hardcoded
if os.Getenv("ENV") == "prod" {
    dbPool = 20
}

// ✅ GOOD: Configured
dbPool, _ := strconv.Atoi(os.Getenv("DB_POOL_SIZE"))
```

**Configure in `transire.yaml`:**
```yaml
env:
  - name: prod
    workspace: prod
    variables:
      DB_POOL_SIZE: "20"
```

### 6. Document Environment Differences

**Maintain an environment matrix:**

| Setting | Dev | Staging | Prod |
|---------|-----|---------|------|
| Memory | 256 MB | 512 MB | 1024 MB |
| Timeout | 30s | 30s | 60s |
| Log Level | debug | info | warn |
| Queue Workers | 2 | 5 | 10 |
| Retry Count | 1 | 2 | 3 |

**Keep in README.md or docs/** for team reference.

## Common Workspace Operations

### List All Workspaces

```bash
cd infra/
tofu workspace list

# Output:
#   default
# * dev
#   staging
#   prod
```

`*` indicates current workspace.

### Show Current Workspace

```bash
tofu workspace show

# Output: dev
```

### Delete Workspace

```bash
# Delete workspace (must not be current workspace)
tofu workspace select default
tofu workspace delete dev
```

⚠️ **Warning:** This deletes the workspace state. Resources remain in AWS but are no longer managed by OpenTofu.

**To properly tear down resources:**
```bash
# Select workspace
tofu workspace select dev

# Destroy resources
tofu destroy

# Then delete workspace
tofu workspace select default
tofu workspace delete dev
```

## Viewing Workspace State

### Show Resources in Current Workspace

```bash
# Switch to workspace
tofu workspace select prod

# List all resources
tofu state list

# Output:
# aws_lambda_function.http
# aws_api_gateway_v2.main
# aws_sqs_queue.order_created
# ...
```

### Compare Workspaces

View differences between environments:

```bash
# Show dev resources
tofu workspace select dev
tofu state list > dev-resources.txt

# Show prod resources
tofu workspace select prod
tofu state list > prod-resources.txt

# Compare
diff dev-resources.txt prod-resources.txt
```

**Helps identify drift between environments.**

## Troubleshooting

### "Error: workspace already exists"

**Cause:** Trying to create workspace that already exists

**Fix:**
```bash
# List workspaces
tofu workspace list

# Select existing workspace instead
tofu workspace select dev
```

### "Error: Workspace 'prod' does not exist"

**Cause:** Trying to select non-existent workspace

**Fix:**
```bash
# Create workspace first
tofu workspace new prod

# Or use Transire to create automatically
transire deploy --env=prod
```

### Resources Created in Wrong Workspace

**Cause:** Deployed while in wrong workspace

**Fix:**

1. **Identify current workspace:**
   ```bash
   tofu workspace show
   ```

2. **Switch to correct workspace:**
   ```bash
   tofu workspace select dev
   ```

3. **Import resources into correct state:**
   ```bash
   # Import Lambda
   tofu import aws_lambda_function.http orders-dev-http

   # Import API Gateway
   tofu import aws_api_gateway_v2.main abc123xyz
   ```

4. **Destroy resources in wrong workspace:**
   ```bash
   tofu workspace select prod
   tofu destroy
   ```

### State File Not Found

**Cause:** Workspace state doesn't exist in S3

**Fix:**

```bash
# Verify backend configuration
cat infra/backend.tf

# Check S3 for state files
aws s3 ls s3://transire-tf-state/orders/ --recursive

# If state missing, recreate or import resources
```

## Environment Promotion Strategy

### Code Promotion

**Option 1: Git branches per environment**
```
main → dev deployment
staging → staging deployment
production → prod deployment
```

**Option 2: Git tags for production**
```
main → dev/staging deployment
v1.2.3 tag → prod deployment
```

### Configuration Management

**Keep environment configs in version control:**

```yaml
# transire.yaml (committed)
env:
  - name: dev
    workspace: dev
    variables:
      LOG_LEVEL: debug

  - name: prod
    workspace: prod
    variables:
      LOG_LEVEL: warn
```

**Never commit secrets** - use AWS Secrets Manager:

```yaml
# transire.yaml
env:
  - name: prod
    workspace: prod
    variables:
      DB_HOST: prod-db.example.com
      DB_SECRET_ARN: arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/db-password
```

### Rollback Strategy

**If production deployment fails:**

1. **Revert to previous commit:**
   ```bash
   git revert HEAD
   git push origin production
   # CI/CD redeploys previous version
   ```

2. **Manual rollback:**
   ```bash
   # Check out previous commit
   git checkout <PREVIOUS_COMMIT>

   # Deploy
   transire deploy --env=prod
   ```

3. **State rollback (last resort):**
   ```bash
   # Download previous state version from S3
   aws s3api get-object \
     --bucket transire-tf-state \
     --key orders/prod/terraform.tfstate \
     --version-id <PREVIOUS_VERSION> \
     recovered-state.tfstate

   # Copy back to current
   aws s3 cp recovered-state.tfstate \
     s3://transire-tf-state/orders/prod/terraform.tfstate
   ```

## Multi-Account Strategy (Advanced)

For large organizations, use separate AWS accounts per environment:

```
Dev Account     → dev workspace
Staging Account → staging workspace
Prod Account    → prod workspace
```

**Benefits:**
- Complete security isolation
- Separate billing/cost tracking
- Regulatory compliance
- Blast radius limitation

**Implementation:**

```yaml
# transire.yaml
env:
  - name: dev
    workspace: dev
    aws_account_id: "111111111111"
    aws_role_arn: arn:aws:iam::111111111111:role/transire-deploy

  - name: prod
    workspace: prod
    aws_account_id: "999999999999"
    aws_role_arn: arn:aws:iam::999999999999:role/transire-deploy
```

**Deployment assumes role in target account:**
```bash
# Automatically assumes correct role per environment
transire deploy --env=prod
```

## Workspace Cost Management

### Tag Resources by Workspace

Transire automatically tags resources with workspace:

```hcl
# Generated in infra/*.tf
resource "aws_lambda_function" "http" {
  # ...

  tags = {
    Environment = terraform.workspace  # "dev", "staging", or "prod"
    Service     = "orders"
    ManagedBy   = "transire"
  }
}
```

### Track Costs per Workspace

Use AWS Cost Explorer:
- Filter by tag `Environment:dev`
- Filter by tag `Environment:prod`
- Compare costs across workspaces

### Dev Cost Optimization

**Reduce costs in non-production workspaces:**

```yaml
deploy:
  dev:
    memory_mb: 256        # Smaller memory
    timeout_s: 30         # Shorter timeout
    provisioned_concurrency: 0  # No warm instances

  prod:
    memory_mb: 1024       # Production memory
    timeout_s: 60
    provisioned_concurrency: 5  # Keep warm
```

## See Also

- [OpenTofu Overview](/iac/overview.md) - Understanding IaC basics
- [Backend Setup](/iac/backend.md) - Configuring remote state
- [Deployment Guide](/guides/deployment.md) - Production deployment strategies
- [Environments](/guides/environments.md) - Environment configuration best practices
- [AWS Deployment](/cloud/aws/deployment.md) - AWS-specific deployment details
- [CLI: transire deploy](/cli/deploy.md) - Deploy command reference
