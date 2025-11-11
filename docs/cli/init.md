---
title: "transire init"
category: cli
subcategory: null
complexity: beginner
duration: null
prerequisites:
  - Go 1.22+
mcp_use: reference
mcp_operations:
  - initialize_workspace
  - setup_configuration
  - initialize_backend
  - setup_state_storage
features_covered:
  - Workspace initialization
  - Configuration file creation
  - Provider configuration
  - Backend initialization (optional)
  - State storage setup (optional)
code_blocks: true
last_updated: 2025-11-11
---

# transire init

## Overview

`transire init` initializes a new Transire workspace in your project directory. This is the **first command** you run when starting a new Transire project.

**Purpose:**
- Create `.transire/` workspace directory
- Generate default `transire.yaml` configuration
- Create `.gitignore` for workspace artifacts
- Configure cloud, IaC, and CI providers
- Optionally initialize cloud backend for state storage

## Usage

### Initialize Workspace (Default)

```bash
transire init
```

Creates a new Transire workspace with default providers (AWS, OpenTofu, GitHub).

### Initialize with Custom Providers

```bash
transire init --cloud azure --iac terraform --ci gitlab
```

Customize cloud, IaC, and CI providers during initialization.

### Force Re-initialization

```bash
transire init --force
```

Reinitialize an existing workspace (overwrites configuration files).

### Initialize Backend (Subcommand)

```bash
transire init backend
```

Initialize cloud backend for state storage (S3 bucket and DynamoDB table for AWS). This is a separate, optional step after workspace initialization.

## Workspace Initialization

### When to Run

Run `transire init`:

- ✅ **Once per project** - First command when starting a new Transire project
- ✅ **After cloning** - When setting up a project on a new machine
- ✅ **After updates** - Use `--force` to regenerate configuration with new defaults
- ❌ **Not needed** - If `.transire/` directory and `transire.yaml` already exist

### What It Does

When you run `transire init`, the CLI:

#### 1. Creates Workspace Directory

Creates `.transire/` directory structure:

```
.transire/
├── workspace.lock        # Locks workspace to prevent accidental operations
├── .gitignore           # Ignores workspace artifacts (manifest.json, etc.)
└── (manifest.json)      # Created later by 'transire gen'
```

#### 2. Generates Default Configuration

Creates `transire.yaml` with sensible defaults:

```yaml
service: my-project        # From directory name
runtime: go
cloud: aws                 # Default cloud provider
iac: opentofu             # Default IaC provider
ci: github                # Default CI provider
timezone: UTC

deploy:
  architecture: arm64      # Cost-effective ARM64
  memory_mb: 256          # Reasonable default
  timeout_seconds: 30

queues:
  visibility_timeout_seconds: 30
  max_receive_count: 3

observability:
  logging:
    level: info
    format: json
```

#### 3. Creates .gitignore

Adds workspace-specific ignores to `.transire/.gitignore`:

```gitignore
# Transire workspace artifacts
manifest.json
*.lock
*.tmp
```

#### 4. Validates Inputs

- Checks provider names against supported providers
- Prevents path traversal and injection attacks
- Validates file permissions

#### 5. Confirms Success

Displays created files and next steps.

### Example Output

```bash
$ transire init
✓ Workspace initialized successfully

Workspace root: /Users/you/projects/orders-api

Created:
  • .transire/  (workspace directory)
  • .transire/workspace.lock
  • .transire/.gitignore
  • transire.yaml  (configuration file)

Configured providers:
  • Cloud: aws
  • IaC: opentofu
  • CI: github

Next steps:
  1. Review and customize transire.yaml
  2. Create your application code (main.go)
  3. Run 'transire gen' to generate the manifest
  4. Run 'transire run' to start local development
  5. Run 'transire init backend' if deploying to cloud
```

### Provider Configuration

Customize providers during initialization:

#### Cloud Providers

```bash
transire init --cloud aws      # Amazon Web Services (default)
transire init --cloud azure    # Microsoft Azure (coming soon)
transire init --cloud gcp      # Google Cloud Platform (coming soon)
```

#### IaC Providers

```bash
transire init --iac opentofu   # OpenTofu (default, Terraform-compatible)
transire init --iac terraform  # HashiCorp Terraform
```

#### CI Providers

```bash
transire init --ci github      # GitHub Actions (default)
transire init --ci gitlab      # GitLab CI (coming soon)
transire init --ci jenkins     # Jenkins (coming soon)
```

### Command-Line Options

#### `--cloud` (default: aws)

```bash
transire init --cloud aws
```

Cloud provider for deployment.

#### `--iac` (default: opentofu)

```bash
transire init --iac opentofu
```

Infrastructure as Code provider.

#### `--ci` (default: github)

```bash
transire init --ci github
```

CI/CD provider for automated deployments.

#### `--force` (default: false)

```bash
transire init --force
```

Force re-initialization, overwriting existing configuration files.

**Warning:** This will overwrite `transire.yaml`. Make sure to back up any custom configuration first.

---

## Backend Initialization (Subcommand)

After initializing your workspace, you can optionally initialize a cloud backend for state storage. This is only needed if you're deploying to the cloud and want shared state management.

### When to Run

Run `transire init backend`:

- ✅ **Once per project** - Before your first cloud deployment
- ✅ **For team collaboration** - Enable shared state with locking
- ❌ **Not needed for local development** - Local development doesn't require backend
- ❌ **Not needed if backend exists** - Check with your team first

### Usage

```bash
transire init backend
```

### With Custom Backend Name

```bash
transire init backend --bucket my-custom-state-bucket
```

### Dry Run

```bash
transire init backend --dry-run
```

Shows what resources would be created without creating them.

### What It Does

When you run `transire init backend`, the CLI:

### 1. Loads Configuration

Reads `transire.yaml` to get backend settings:

```yaml
infra:
  backend:
    type: s3
    bucket: transire-tf-state        # Created by init
    dynamodb_table: tf-locks          # Created by init
    key_prefix: orders/               # Namespace for this project
```

### 2. Checks Cloud Credentials

Verifies you have valid cloud credentials:

```bash
$ aws sts get-caller-identity
{
  "UserId": "AIDAI...",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:user/alice"
}
```

### 3. Creates S3 Bucket

Creates bucket for state storage with:

- **Versioning enabled** - Track state history
- **Encryption enabled** - AES-256 encryption at rest
- **Private access** - No public access
- **Lifecycle rules** - Optional, for old version cleanup

### 4. Creates DynamoDB Table

Creates table for state locking with:

- **Table name:** From config (e.g., `tf-locks`)
- **Primary key:** `LockID` (string)
- **Billing mode:** PAY_PER_REQUEST (cost-effective)
- **Point-in-time recovery:** Enabled

### 5. Updates Configuration

Optionally updates `transire.yaml` with created resources:

```yaml
infra:
  backend:
    type: s3
    bucket: transire-tf-state         # Confirmed to exist
    dynamodb_table: tf-locks          # Confirmed to exist
    region: us-east-1                 # Added
    key_prefix: orders/
```

### 6. Verifies Setup

Tests backend access:

- Write test state file
- Acquire and release lock
- Confirm permissions

## Example

### First-Time Setup

```bash
$ transire init --backend
✓ Configuration loaded
✓ Cloud provider: AWS (us-east-1)

Initializing backend...

Creating S3 bucket: transire-tf-state
  ✓ Bucket created
  ✓ Versioning enabled
  ✓ Encryption enabled
  ✓ Public access blocked

Creating DynamoDB table: tf-locks
  ✓ Table created
  ✓ Point-in-time recovery enabled

Backend initialized successfully!

You can now run:
  transire deploy
```

### Already Initialized

```bash
$ transire init --backend
✓ Configuration loaded
✓ Cloud provider: AWS (us-east-1)

Checking backend...
  ✓ S3 bucket exists: transire-tf-state
  ✓ DynamoDB table exists: tf-locks
  ✓ Permissions verified

Backend already initialized. No changes needed.
```

## Backend Configuration

Configure backend in `transire.yaml`:

```yaml
service: orders
cloud: aws

infra:
  backend:
    type: s3                          # Backend type (s3 for AWS)
    bucket: transire-tf-state         # S3 bucket name
    dynamodb_table: tf-locks          # DynamoDB table for locking
    key_prefix: orders/               # Namespace (prevents conflicts)
    region: us-east-1                 # AWS region (optional, uses default)
    encrypt: true                     # Enable encryption (default: true)
```

### Key Fields

| Field | Description | Required | Default |
|-------|-------------|----------|---------|
| `type` | Backend type | Yes | `s3` |
| `bucket` | S3 bucket name | Yes | Generated |
| `dynamodb_table` | DynamoDB table name | Yes | `tf-locks` |
| `key_prefix` | Namespace prefix | No | `${service}/` |
| `region` | AWS region | No | From AWS config |
| `encrypt` | Enable encryption | No | `true` |

## State Storage

### State File Structure

State files are organized by environment:

```
s3://transire-tf-state/
  orders/                      # key_prefix
    dev/
      terraform.tfstate        # Dev environment state
    staging/
      terraform.tfstate        # Staging environment state
    prod/
      terraform.tfstate        # Prod environment state
```

### State Versioning

S3 versioning tracks state history:

```bash
# List state versions
aws s3api list-object-versions \
  --bucket transire-tf-state \
  --prefix orders/prod/terraform.tfstate

# Restore previous version
aws s3api get-object \
  --bucket transire-tf-state \
  --key orders/prod/terraform.tfstate \
  --version-id <version-id> \
  terraform.tfstate
```

## State Locking

DynamoDB prevents concurrent modifications:

### How It Works

1. `transire deploy` starts
2. Attempts to acquire lock in DynamoDB
3. If lock exists, waits or fails
4. Acquires lock, applies changes
5. Releases lock on completion

### Lock Table Structure

| LockID | Info | Digest |
|--------|------|--------|
| `orders-dev` | `{"Operation":"OperationTypeApply","Info":"","Who":"alice@laptop","Version":"1.6.0","Created":"2025-10-30T10:30:00Z"}` | `abc123...` |

### Viewing Locks

```bash
# List all locks
aws dynamodb scan --table-name tf-locks

# Check specific lock
aws dynamodb get-item \
  --table-name tf-locks \
  --key '{"LockID": {"S": "orders-dev"}}'
```

### Force Unlock (Use with Caution)

If deployment crashes and lock isn't released:

```bash
tofu force-unlock <lock-id>
```

⚠️ **Warning:** Only force unlock if you're certain no other deployment is running.

## Multi-Project Setup

### Shared Backend

Multiple projects can share a backend with unique `key_prefix`:

**Project 1 (orders):**
```yaml
infra:
  backend:
    bucket: company-tf-state
    key_prefix: orders/
```

**Project 2 (payments):**
```yaml
infra:
  backend:
    bucket: company-tf-state
    key_prefix: payments/
```

State files:
```
s3://company-tf-state/
  orders/dev/terraform.tfstate
  orders/prod/terraform.tfstate
  payments/dev/terraform.tfstate
  payments/prod/terraform.tfstate
```

### Separate Backends

Or use separate backends per project:

**Orders:**
```yaml
infra:
  backend:
    bucket: orders-tf-state
```

**Payments:**
```yaml
infra:
  backend:
    bucket: payments-tf-state
```

## Security

### Bucket Permissions

S3 bucket should have:

✅ **Block public access** - Always enabled
✅ **Versioning** - Track changes
✅ **Encryption** - AES-256 or KMS
✅ **Access logs** - Optional, for audit trail

### IAM Permissions

Users/roles need these permissions:

**S3:**
- `s3:ListBucket` - List state files
- `s3:GetObject` - Read state
- `s3:PutObject` - Write state
- `s3:DeleteObject` - Delete old state versions

**DynamoDB:**
- `dynamodb:GetItem` - Check lock
- `dynamodb:PutItem` - Acquire lock
- `dynamodb:DeleteItem` - Release lock

**Example IAM Policy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::transire-tf-state",
        "arn:aws:s3:::transire-tf-state/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/tf-locks"
    }
  ]
}
```

## Cost

Backend resources are very low cost:

### S3 Bucket

- **Storage:** ~$0.023/GB/month (Standard)
- **Typical state size:** < 1MB
- **Monthly cost:** < $0.01

### DynamoDB Table

- **Pricing:** PAY_PER_REQUEST
- **Read/write:** $0.25/$1.25 per million requests
- **Typical usage:** < 100 requests/month
- **Monthly cost:** < $0.01

**Total:** ~$0.02/month per project

## Troubleshooting

### "Bucket name already taken"

**Problem:** S3 bucket names are globally unique

**Solution:** Use custom bucket name:

```bash
transire init --backend --bucket my-unique-bucket-name-12345
```

Or update `transire.yaml`:

```yaml
infra:
  backend:
    bucket: my-unique-bucket-name-12345
```

### "Access denied"

**Problem:** Insufficient IAM permissions

**Solution:** Verify permissions:

```bash
aws iam get-user-policy --user-name $USER --policy-name TransireBackend
```

Ensure you have S3 and DynamoDB permissions.

### "Table already exists"

**Problem:** DynamoDB table exists from previous init

**Solution:** Verify table:

```bash
aws dynamodb describe-table --table-name tf-locks
```

If correct, backend is ready:

```bash
transire deploy
```

If wrong schema, delete and recreate:

```bash
aws dynamodb delete-table --table-name tf-locks
transire init --backend
```

### "Cannot initialize backend"

**Problem:** Invalid configuration

**Solution:** Validate `transire.yaml`:

```bash
transire gen  # Validates config
```

Check for:
- Missing `infra.backend` section
- Invalid `type` (must be `s3` for AWS)
- Invalid bucket name (3-63 chars, lowercase, no underscores)

## Best Practices

### Use Company-Wide Bucket

Share backend bucket across projects:

```yaml
infra:
  backend:
    bucket: company-transire-state  # Shared
    key_prefix: ${service}/         # Unique per project
```

Benefits:
- Centralized state management
- Easier backup and monitoring
- Cost-effective (one bucket for all projects)

### Enable Versioning

Always enable S3 versioning (default in `transire init`):

```bash
aws s3api put-bucket-versioning \
  --bucket transire-tf-state \
  --versioning-configuration Status=Enabled
```

Allows state recovery if corrupted.

### Restrict Access

Use IAM policies to limit who can:
- **Read state:** All team members
- **Write state:** CI/CD + senior engineers only
- **Delete state:** Admins only

### Monitor Backend Health

Set up CloudWatch alarms:

- **S3:** Monitor failed requests
- **DynamoDB:** Monitor throttled requests
- **State size:** Alert if state grows unexpectedly large

### Backup State

While S3 versioning provides backup, consider additional backups:

```bash
# Manual backup
aws s3 cp s3://transire-tf-state/ ./state-backup/ --recursive

# Automated backup (S3 replication)
aws s3api put-bucket-replication --bucket transire-tf-state --replication-configuration file://replication.json
```

## See Also

- [transire gen](/cli/gen.md) - Generate manifest from code
- [transire plan](/cli/plan.md) - Preview deployment plan
- [transire deploy](/cli/deploy.md) - Deploy to cloud
- [transire run](/cli/run.md) - Run locally
- [OpenTofu Backend](/iac/backend.md) - Backend configuration details
- [Environments](/guides/environments.md) - Multi-environment state management
- [AWS Overview](/cloud/aws/overview.md) - AWS-specific details
