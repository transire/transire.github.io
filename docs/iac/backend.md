---
title: "Backend Setup"
category: iac
subcategory: null
complexity: intermediate
duration: 10 minutes
prerequisites:
  - AWS account with credentials configured
  - AWS CLI installed and configured
  - OpenTofu or Terraform installed
mcp_use: reference
mcp_operations:
  - setup_backend
  - configure_state_management
features_covered:
  - S3 backend configuration
  - DynamoDB state locking
  - Backend initialization
  - Team state sharing
code_blocks: true
last_updated: 2025-10-30
---

# Backend Setup

## What is a Backend?

A **backend** determines where OpenTofu stores its state file - the record of your infrastructure's current configuration.

**Local backend (default):**
- State stored in `terraform.tfstate` file
- ✅ Simple for solo development
- ❌ Not shareable across team
- ❌ No concurrent access protection
- ❌ Easily lost or corrupted

**Remote backend (S3 + DynamoDB):**
- State stored in S3 bucket
- ✅ Shared across team
- ✅ Encrypted at rest
- ✅ State locking via DynamoDB
- ✅ Versioned for rollback
- ✅ Production-ready

**For any team project or production deployment, use a remote backend.**

## Why You Need a Backend

### Problem: Concurrent Access

Without state locking, two developers running `tofu apply` simultaneously can corrupt state:

```
Developer A: tofu apply (starts)
Developer B: tofu apply (starts)
Developer A: Writes state
Developer B: Overwrites state (A's changes lost!)
```

### Solution: DynamoDB Locking

DynamoDB provides a distributed lock:

```
Developer A: tofu apply (acquires lock)
Developer B: tofu apply (waits for lock)
Developer A: Completes, releases lock
Developer B: Acquires lock, proceeds safely
```

### Problem: State Loss

Local state files can be:
- Accidentally deleted
- Lost in disk failure
- Not accessible to CI/CD
- Difficult to share with team

### Solution: S3 Storage

S3 provides:
- **Durability:** 99.999999999% (11 9's)
- **Versioning:** Rollback to previous states
- **Encryption:** Automatic encryption at rest
- **Access control:** IAM policies for team members
- **High availability:** Accessible from anywhere

## Backend Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Transire Application                    │
├─────────────────────────────────────────────────────────┤
│  Developer A    Developer B    CI/CD Pipeline            │
│      │              │                │                   │
│      └──────────────┴────────────────┘                   │
│                     │                                    │
│              OpenTofu Operations                         │
│                     │                                    │
│         ┌───────────┴───────────┐                       │
│         │                       │                       │
│    ┌────▼──────┐         ┌──────▼────┐                 │
│    │ S3 Bucket │         │ DynamoDB  │                 │
│    │  (State)  │         │  (Locks)  │                 │
│    └───────────┘         └───────────┘                 │
│   Versioned state        State locking                  │
│   Encrypted at rest      Concurrent control             │
└─────────────────────────────────────────────────────────┘
```

## Quick Setup with Transire

The easiest way to set up a backend is using `transire init`:

```bash
# Initialize backend (creates S3 + DynamoDB)
transire init --backend

# Output:
# ✓ S3 bucket created: transire-tf-state
# ✓ DynamoDB table created: tf-locks
# ✓ Backend configured in transire.yaml
#
# Next steps:
#   1. cd infra/ && tofu init
#   2. tofu apply
```

**What this does:**

1. Reads `transire.yaml` for backend configuration
2. Creates S3 bucket with encryption and versioning
3. Creates DynamoDB table for state locking
4. Configures bucket policies for secure access

**Configuration in `transire.yaml`:**

```yaml
infra:
  backend:
    type: s3
    bucket: transire-tf-state           # S3 bucket name
    dynamodb_table: tf-locks             # DynamoDB table name
    region: us-east-1                    # AWS region
    key_prefix: orders/                  # Optional: state file prefix
```

## Manual Backend Setup

If you prefer to create backend resources manually:

### Step 1: Create S3 Bucket

```bash
# Create bucket
aws s3api create-bucket \
  --bucket transire-tf-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket transire-tf-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket transire-tf-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access (security best practice)
aws s3api put-public-access-block \
  --bucket transire-tf-state \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### Step 2: Create DynamoDB Table

```bash
# Create table for state locking
aws dynamodb create-table \
  --table-name tf-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

**Table schema:**
- Primary key: `LockID` (String)
- Billing mode: PAY_PER_REQUEST (no capacity planning needed)
- Region: Must match S3 bucket region

### Step 3: Configure Backend in OpenTofu

Transire generates this automatically, but here's what it creates:

```hcl
# infra/backend.tf
terraform {
  backend "s3" {
    bucket         = "transire-tf-state"
    key            = "orders/dev/terraform.tfstate"  # Per-environment
    region         = "us-east-1"
    dynamodb_table = "tf-locks"
    encrypt        = true
  }
}
```

### Step 4: Initialize Backend

```bash
cd infra/
tofu init
```

**First time:** Creates backend and uploads state
**Subsequent times:** Verifies backend configuration

## Backend Configuration Options

### Per-Service State Files

Use `key_prefix` to organize state by service:

```yaml
# transire.yaml
service: orders
infra:
  backend:
    bucket: transire-tf-state
    key_prefix: orders/    # State stored at: orders/<env>/terraform.tfstate
```

**Result:** `s3://transire-tf-state/orders/dev/terraform.tfstate`

**Benefits:**
- Isolated state per service
- Clear organization
- Easier to manage multiple services

### Multi-Region Deployments

For multi-region setups, use region-specific buckets:

```yaml
# transire.yaml (us-east-1)
infra:
  backend:
    bucket: transire-tf-state-us-east-1
    region: us-east-1

# transire.yaml (eu-west-1)
infra:
  backend:
    bucket: transire-tf-state-eu-west-1
    region: eu-west-1
```

**Why separate buckets?**
- Lower latency (bucket in same region)
- Data sovereignty requirements
- Simpler disaster recovery

### Encryption Options

**Default (S3-managed keys):**
```hcl
backend "s3" {
  encrypt = true  # Uses S3-managed keys (SSE-S3)
}
```

**KMS-managed keys (more control):**
```hcl
backend "s3" {
  encrypt        = true
  kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/..."
}
```

**Use KMS when:**
- Compliance requires customer-managed keys
- Need audit trail of key usage
- Key rotation policies required

## State File Structure

State files are stored hierarchically in S3:

```
s3://transire-tf-state/
├── orders/
│   ├── dev/
│   │   └── terraform.tfstate
│   ├── staging/
│   │   └── terraform.tfstate
│   └── prod/
│       └── terraform.tfstate
├── users/
│   ├── dev/
│   │   └── terraform.tfstate
│   └── prod/
│       └── terraform.tfstate
└── payments/
    └── prod/
        └── terraform.tfstate
```

**Benefits:**
- Clear service boundaries
- Environment isolation
- Easy to locate specific state

## Sharing State with Team

### Step 1: Grant Team Access

Create IAM policy for team members:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketVersioning"
      ],
      "Resource": "arn:aws:s3:::transire-tf-state"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::transire-tf-state/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/tf-locks"
    }
  ]
}
```

Attach this policy to:
- IAM users (team members)
- IAM roles (CI/CD pipelines)
- IAM groups (engineering team)

### Step 2: Configure AWS Credentials

Each team member needs:

```bash
# Configure AWS CLI
aws configure

# Or use environment variables
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
```

### Step 3: Initialize Local OpenTofu

```bash
# Clone repository
git clone https://github.com/acme/orders.git
cd orders/

# Generate manifest and OpenTofu configs
transire gen

# Initialize backend (downloads remote state)
cd infra/
tofu init

# Verify state access
tofu plan
```

**Team members now share the same state** - changes are synchronized through S3.

## CI/CD Backend Access

Grant your CI/CD pipeline access to backend:

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # For OIDC
      contents: read

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-role
          aws-region: us-east-1

      - name: Deploy
        run: transire deploy
```

**IAM role for GitHub Actions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:acme/orders:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

## Migrating to Remote Backend

Already have local state? Migrate to S3:

### Step 1: Set Up Backend

```bash
# Create backend resources
transire init --backend
```

### Step 2: Configure Backend

Transire updates `infra/backend.tf` automatically.

### Step 3: Migrate State

```bash
cd infra/

# Initialize with new backend config
tofu init

# OpenTofu detects local state and prompts to migrate:
#
# Backend configuration changed!
#
# OpenTofu has detected that the configuration specified for the backend
# has changed. OpenTofu will now check for existing state in the backends.
#
# Do you want to copy existing state to the new backend?
#   Enter a value: yes

# State is uploaded to S3
```

### Step 4: Verify

```bash
# Check S3 for state file
aws s3 ls s3://transire-tf-state/orders/dev/

# Output: terraform.tfstate

# Delete local state (now in S3)
rm terraform.tfstate*
```

**Important:** After migration, commit the updated `backend.tf` so team members use the remote backend.

## State Locking in Action

### Example: Two Concurrent Operations

**Terminal 1:**
```bash
$ tofu apply
Acquiring state lock. This may take a few moments...
# Lock acquired from DynamoDB
# Changes applied
```

**Terminal 2 (simultaneous):**
```bash
$ tofu apply
Acquiring state lock. This may take a few moments...
# Waits for lock...
# Lock acquired after Terminal 1 completes
# Changes applied
```

### Lock Information

View lock details in DynamoDB:

```bash
aws dynamodb get-item \
  --table-name tf-locks \
  --key '{"LockID":{"S":"transire-tf-state/orders/dev/terraform.tfstate-md5"}}'
```

**Lock record contains:**
- Lock ID
- Who acquired lock (user/role)
- When lock acquired
- Operation type (plan/apply)

## Troubleshooting

### "Error: Error acquiring the state lock"

**Cause:** Another operation is running, or previous operation crashed without releasing lock

**Symptoms:**
```
Error: Error acquiring the state lock

Lock Info:
  ID:        abc123...
  Path:      transire-tf-state/orders/dev/terraform.tfstate
  Operation: OperationTypeApply
  Who:       user@example.com
  Created:   2025-10-30 14:30:00 UTC
```

**Fix (if no other operation is running):**
```bash
# Force unlock (use lock ID from error message)
tofu force-unlock abc123...
```

⚠️ **Only force unlock if you're certain no other operation is in progress** - forcing during active operation can corrupt state.

### "Error: Failed to get existing workspaces"

**Cause:** Incorrect AWS credentials or permissions

**Fix:**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Verify S3 access
aws s3 ls s3://transire-tf-state/

# Verify DynamoDB access
aws dynamodb describe-table --table-name tf-locks
```

**Check IAM permissions include:**
- `s3:ListBucket`, `s3:GetObject`, `s3:PutObject`
- `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:DeleteItem`

### "Error: Backend initialization required"

**Cause:** Backend configuration changed or not initialized

**Fix:**
```bash
cd infra/
tofu init
```

**If prompted to migrate state, review carefully before confirming.**

### State File Corrupted

**Cause:** Rare - interrupted operation, bugs, or manual S3 edits

**Recovery:**

```bash
# List state versions in S3
aws s3api list-object-versions \
  --bucket transire-tf-state \
  --prefix orders/dev/terraform.tfstate

# Download previous version
aws s3api get-object \
  --bucket transire-tf-state \
  --key orders/dev/terraform.tfstate \
  --version-id <VERSION_ID> \
  recovered-state.tfstate

# Copy recovered state to current
aws s3 cp recovered-state.tfstate \
  s3://transire-tf-state/orders/dev/terraform.tfstate
```

**Always enable S3 versioning** to make recovery possible.

## Backend Security Best Practices

### 1. Encrypt State at Rest

✅ **Always enable S3 encryption:**
```hcl
backend "s3" {
  encrypt = true
}
```

### 2. Enable S3 Versioning

✅ **Rollback capability:**
```bash
aws s3api put-bucket-versioning \
  --bucket transire-tf-state \
  --versioning-configuration Status=Enabled
```

### 3. Block Public Access

✅ **Prevent accidental exposure:**
```bash
aws s3api put-public-access-block \
  --bucket transire-tf-state \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 4. Restrict IAM Access

✅ **Principle of least privilege:**
- Grant backend access only to team members who need it
- Use IAM roles for CI/CD (not access keys)
- Regularly review and rotate credentials

### 5. Enable Logging

✅ **Audit state access:**
```bash
aws s3api put-bucket-logging \
  --bucket transire-tf-state \
  --bucket-logging-status file://logging.json
```

### 6. Use Separate Backends per Environment

✅ **Isolate environments:**
- Dev: `transire-tf-state/orders/dev/`
- Prod: `transire-tf-state/orders/prod/`

**Never share state between environments** - prevents accidental cross-environment changes.

## Backend Cost Estimation

### S3 Storage

- **State files:** Typically < 1 MB per environment
- **Cost:** ~$0.023/GB/month
- **Example:** 10 services × 3 environments × 500 KB = ~$0.35/month

### DynamoDB

- **Locking:** On-demand pricing, charged per request
- **Cost:** $1.25 per million requests
- **Example:** 100 operations/day = ~$0.04/month

**Total backend cost: < $0.50/month for most teams**

## See Also

- [OpenTofu Overview](/docs/iac/overview.md) - Understanding IaC with Transire
- [Workspaces](/docs/iac/workspaces.md) - Managing multiple environments
- [Deployment Guide](/docs/guides/deployment.md) - Deploying to production
- [Environments](/docs/guides/environments.md) - Environment configuration
- [CLI: transire init](/docs/cli/init.md) - Backend initialization command
