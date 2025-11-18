# Installation

Learn how to install the Transire CLI.

!!! tip "TL;DR"
    Install with `go install github.com/transire/transire/cmd/transire@latest`. Requires Go 1.21+, Node.js 18+ (for deployment), and AWS CLI (for AWS deployment).

---

## Prerequisites

**Required:**
- **Go 1.21 or higher** – [Install Go](https://go.dev/doc/install)
- **Git** – For cloning repositories

**For AWS deployment:**
- **Node.js 18+** – [Install Node.js](https://nodejs.org/)
- **AWS CLI 2.x** – [Install AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **AWS CDK CLI 2.x** – Installed via npm (see below)
- **AWS credentials** – Configure via `aws configure`

---

## Install Transire CLI

### Using `go install` (Recommended)

```bash
go install github.com/transire/transire/cmd/transire@latest
```

This installs the `transire` binary to `$GOPATH/bin` (usually `~/go/bin`).

---

### Verify Installation

```bash
transire --version
# Output: transire version v0.1.0
```

If command not found, add `$GOPATH/bin` to your `PATH`:

```bash
# Add to ~/.bashrc, ~/.zshrc, or equivalent
export PATH=$PATH:$(go env GOPATH)/bin
```

---

### Install Specific Version

```bash
go install github.com/transire/transire/cmd/transire@v0.1.0
```

---

### Build from Source

```bash
# Clone repository
git clone https://github.com/transire/transire.git
cd transire

# Build and install
go install ./cmd/transire

# Verify
transire --version
```

---

## Install AWS CDK CLI (for Deployment)

Required for deploying infrastructure to AWS.

```bash
npm install -g aws-cdk
```

**Verify:**
```bash
cdk --version
# Should show: 2.x.x
```

---

## Configure AWS Credentials

Required for deploying to AWS.

```bash
aws configure
```

Provide:
- **AWS Access Key ID**: Your AWS access key
- **AWS Secret Access Key**: Your AWS secret key
- **Default region**: e.g., `us-east-1`
- **Default output format**: `json`

**Verify credentials:**
```bash
aws sts get-caller-identity
```

Should show your AWS account ID and user ARN.

---

## Bootstrap CDK (First Time Only)

If deploying to a new AWS account/region for the first time:

```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

Replace `ACCOUNT-ID` and `REGION` with your AWS account ID and target region.

**Example:**
```bash
cdk bootstrap aws://123456789012/us-east-1
```

This creates the necessary S3 buckets and IAM roles for CDK deployments.

---

## Verify Complete Setup

Run this checklist to verify everything is ready:

```bash
# Required
go version          # Go 1.21+
transire --version  # Latest version

# For deployment
node --version      # Node 18+
npm --version       # npm 9+
aws --version       # AWS CLI 2.x
cdk --version       # CDK 2.x
aws sts get-caller-identity  # AWS credentials configured
```

---

## Troubleshooting

### Command not found: transire

**Solutions:**

1. Add `$GOPATH/bin` to PATH:
   ```bash
   export PATH=$PATH:$(go env GOPATH)/bin
   ```

2. Verify installation location:
   ```bash
   ls $(go env GOPATH)/bin/transire
   ```

3. Reinstall:
   ```bash
   go install github.com/transire/transire/cmd/transire@latest
   ```

---

### AWS credentials not configured

**Problem:** `Unable to locate credentials`

**Solutions:**

1. Run `aws configure`
2. Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_DEFAULT_REGION=us-east-1
   ```

3. Verify: `aws sts get-caller-identity`

---

### CDK bootstrap required

**Problem:** `This stack uses assets, so the toolkit stack must be deployed`

**Solution:**
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

See [AWS CDK Bootstrap documentation](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html) for details.

---

## Upgrading Transire

### Upgrade to Latest Version

```bash
go install github.com/transire/transire/cmd/transire@latest
```

### Upgrade to Specific Version

```bash
go install github.com/transire/transire/cmd/transire@v0.2.0
```

### Check Current Version

```bash
transire --version
```

Compare with latest release: [github.com/transire/transire/releases](https://github.com/transire/transire/releases)

---

## Next Steps

Now that you have Transire installed:

- **[Quickstart](quickstart.md)** – Build your first app in 5 minutes
- **[Your First API](your-first-api.md)** – Detailed walkthrough
- **[CLI Reference](../cli-reference/transire-init.md)** – Learn CLI commands

---

## See Also

- [Go Installation Guide](https://go.dev/doc/install)
- [AWS CLI Installation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [AWS CDK Getting Started](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)
- [Node.js Installation](https://nodejs.org/en/download/)
