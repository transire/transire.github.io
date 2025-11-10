---
title: "GitHub Actions CI/CD"
category: ci
subcategory: null
complexity: intermediate
duration: null
prerequisites:
  - GitHub repository
  - AWS account with OIDC configured
  - Transire project with transire.yaml
mcp_use: template
mcp_operations:
  - generate_ci_workflow
  - setup_github_actions
features_covered:
  - GitHub Actions workflows
  - Branch-based deployment
  - Manual approval gates
  - Secrets management
  - Multi-environment CI/CD
code_blocks: true
last_updated: 2025-10-30
---

# GitHub Actions CI/CD

## Overview

Transire integrates with GitHub Actions to provide automated CI/CD pipelines for your serverless applications. The framework generates workflow files that handle testing, building, and deploying your application across multiple environments.

**Key features:**
- Branch-based deployment (main → production, develop → staging)
- Manual approval gates for production
- Secure secrets management via GitHub Secrets and AWS OIDC
- Separate CI and CD workflows for flexibility
- Guard blocks to prevent accidental production deployments

## Generated Workflow Structure

Transire generates two GitHub Actions workflows:

1. **CI Workflow** (`.github/workflows/ci.yml`) - Runs on every push and pull request
2. **CD Workflow** (`.github/workflows/cd.yml`) - Deploys to cloud environments

### CI Workflow (Continuous Integration)

The CI workflow runs tests and validation on every push:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.22'

      - name: Download dependencies
        run: go mod download

      - name: Generate manifest
        run: transire gen

      - name: Run tests
        run: go test -v ./...

      - name: Build
        run: go build -v ./...
```

### CD Workflow (Continuous Deployment)

The CD workflow deploys your application to AWS:

```yaml
name: CD

on:
  push:
    branches:
      - main      # Deploys to production
      - develop   # Deploys to staging

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.22'

      - name: Install Transire CLI
        run: |
          curl -L https://github.com/transire/cli/releases/latest/download/transire-linux-amd64 -o transire
          chmod +x transire
          sudo mv transire /usr/local/bin/

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Determine environment
        id: env
        run: |
          if [ "${{ github.ref }}" = "refs/heads/main" ]; then
            echo "environment=prod" >> $GITHUB_OUTPUT
          else
            echo "environment=dev" >> $GITHUB_OUTPUT
          fi

      - name: Deploy
        run: |
          transire deploy --env ${{ steps.env.outputs.environment }}
```

## Branch-Based Deployment

Transire uses a branch-based deployment strategy:

| Branch | Environment | Approval Required | Auto-Deploy |
|--------|-------------|-------------------|-------------|
| `main` | Production | Yes (recommended) | Optional |
| `develop` | Staging | No | Yes |
| Feature branches | N/A | N/A | No (CI only) |

### Workflow Triggers

```yaml
on:
  push:
    branches:
      - main      # → production
      - develop   # → staging
  pull_request:
    branches:
      - main
      - develop
```

**Branch protection rules (recommended):**
- Require pull request reviews before merging to `main`
- Require status checks to pass (CI workflow)
- Require branches to be up to date

## Manual Approval for Production

For production deployments, add a manual approval gate using GitHub Environments:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    # Add environment with protection rules
    environment:
      name: ${{ steps.env.outputs.environment }}
      url: ${{ steps.deploy.outputs.api_url }}

    steps:
      - name: Determine environment
        id: env
        run: |
          if [ "${{ github.ref }}" = "refs/heads/main" ]; then
            echo "environment=production" >> $GITHUB_OUTPUT
          else
            echo "environment=staging" >> $GITHUB_OUTPUT
          fi

      # ... deployment steps ...
```

**Setting up manual approval:**

1. Go to your repository **Settings → Environments**
2. Create an environment named `production`
3. Enable **Required reviewers** and add team members
4. Optionally add **Wait timer** (e.g., 5 minutes)

Now deployments to production will pause and wait for approval.

## Secrets Management

### AWS Credentials via OIDC (Recommended)

OIDC allows GitHub Actions to authenticate with AWS without storing long-lived credentials:

**1. Create IAM OIDC Identity Provider in AWS:**

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

**2. Create IAM role for GitHub Actions:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_ORG/YOUR_REPO:*"
        }
      }
    }
  ]
}
```

**3. Attach deployment permissions policy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*",
        "apigateway:*",
        "sqs:*",
        "events:*",
        "iam:*",
        "s3:*"
      ],
      "Resource": "*"
    }
  ]
}
```

**4. Add role ARN to GitHub Secrets:**

Go to **Settings → Secrets and variables → Actions** and add:
- **Name:** `AWS_ROLE_ARN`
- **Value:** `arn:aws:iam::ACCOUNT_ID:role/GitHubActionsRole`

### Alternative: Static Credentials

If OIDC is not available, you can use static AWS credentials:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1
```

Add to GitHub Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

**Warning:** OIDC is more secure and recommended for production.

## Multi-Environment Deployment

Deploy to different environments based on branch:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - branch: develop
            environment: dev
            aws_region: us-east-1
          - branch: main
            environment: prod
            aws_region: us-west-2

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets[format('AWS_ROLE_ARN_{0}', matrix.environment)] }}
          aws-region: ${{ matrix.aws_region }}

      - name: Deploy
        run: transire deploy --env ${{ matrix.environment }}
```

**Environment-specific secrets:**
- `AWS_ROLE_ARN_DEV`
- `AWS_ROLE_ARN_PROD`

## Guard Blocks for Production

Guard blocks prevent accidental deployments to production:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      # ... setup steps ...

      - name: Production deployment guard
        if: github.ref == 'refs/heads/main'
        run: |
          echo "⚠️  PRODUCTION DEPLOYMENT"
          echo "Branch: ${{ github.ref }}"
          echo "Commit: ${{ github.sha }}"
          echo "Actor: ${{ github.actor }}"
          echo ""
          echo "This will deploy to PRODUCTION environment."
          echo "Ensure all tests pass and changes are reviewed."

      - name: Require manual trigger for production
        if: github.ref == 'refs/heads/main' && github.event_name != 'workflow_dispatch'
        run: |
          echo "❌ Production deployments must be triggered manually"
          exit 1
```

With this guard, production deployments require manual workflow dispatch:

```yaml
on:
  push:
    branches: [develop]  # Auto-deploy staging
  workflow_dispatch:     # Manual trigger for production
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        type: choice
        options:
          - prod
```

## Complete Example Workflow

Here's a complete production-ready workflow:

```yaml
name: Deploy

on:
  push:
    branches: [develop]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        type: choice
        options:
          - dev
          - prod

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: ${{ github.event.inputs.environment || (github.ref == 'refs/heads/main' && 'prod' || 'dev') }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.22'
          cache: true

      - name: Install Transire CLI
        run: |
          curl -L https://github.com/transire/cli/releases/latest/download/transire-linux-amd64 -o transire
          chmod +x transire
          sudo mv transire /usr/local/bin/
          transire version

      - name: Determine environment
        id: env
        run: |
          if [ "${{ github.event.inputs.environment }}" != "" ]; then
            ENV="${{ github.event.inputs.environment }}"
          elif [ "${{ github.ref }}" = "refs/heads/main" ]; then
            ENV="prod"
          else
            ENV="dev"
          fi
          echo "environment=${ENV}" >> $GITHUB_OUTPUT
          echo "Deploying to: ${ENV}"

      - name: Production deployment guard
        if: steps.env.outputs.environment == 'prod'
        run: |
          echo "⚠️  PRODUCTION DEPLOYMENT"
          echo "Environment: prod"
          echo "Branch: ${{ github.ref }}"
          echo "Commit: ${{ github.sha }}"
          echo "Triggered by: ${{ github.actor }}"

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets[format('AWS_ROLE_ARN_{0}', steps.env.outputs.environment)] }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Generate manifest
        run: transire gen

      - name: Run tests
        run: go test -v ./...

      - name: Deploy to AWS
        id: deploy
        run: |
          transire deploy --env ${{ steps.env.outputs.environment }}
          # Capture API URL from output
          echo "api_url=$(transire deploy --env ${{ steps.env.outputs.environment }} --output-url)" >> $GITHUB_OUTPUT

      - name: Deployment summary
        run: |
          echo "✅ Deployment successful"
          echo "Environment: ${{ steps.env.outputs.environment }}"
          echo "API URL: ${{ steps.deploy.outputs.api_url }}"

      - name: Notify on failure
        if: failure()
        run: |
          echo "❌ Deployment failed"
          echo "Check logs above for details"
```

## Troubleshooting Failed Deployments

### Common Issues

**1. Authentication failures:**

```
Error: failed to assume role
```

**Solution:** Verify OIDC provider is configured and role trust policy allows your repository.

**2. Manifest generation errors:**

```
Error: failed to generate manifest: E1002
```

**Solution:** Ensure `transire gen` runs locally without errors. Check handler signatures match expected patterns.

**3. OpenTofu state lock errors:**

```
Error: acquiring state lock
```

**Solution:** Another deployment may be in progress. Wait and retry. If stuck, manually unlock:

```bash
aws dynamodb delete-item \
  --table-name tf-locks \
  --key '{"LockID": {"S": "orders/prod/terraform.tfstate"}}'
```

**4. Resource quota exceeded:**

```
Error: LimitExceededException
```

**Solution:** Request AWS service quota increases or clean up unused resources.

### Debugging Workflows

**Enable debug logging:**

Add repository secrets:
- `ACTIONS_RUNNER_DEBUG`: `true`
- `ACTIONS_STEP_DEBUG`: `true`

**Check deployment logs:**

```bash
# View Lambda logs
aws logs tail /aws/lambda/orders-prod-http --follow

# View deployment events
aws cloudformation describe-stack-events --stack-name orders-prod
```

## Best Practices

1. **Use OIDC for authentication** - More secure than static credentials
2. **Require manual approval for production** - Prevent accidental deployments
3. **Test locally before pushing** - Run `transire gen` and `go test` first
4. **Use branch protection rules** - Require reviews and status checks
5. **Monitor deployment metrics** - Track success rate and duration
6. **Set up notifications** - Alert team on deployment failures
7. **Version your workflows** - Pin action versions (e.g., `@v4` not `@latest`)
8. **Use GitHub Environments** - Manage secrets and approval gates per environment
9. **Run CI on pull requests** - Catch issues before merging
10. **Keep workflows DRY** - Use composite actions for repeated logic

## See Also

- [Deployment Guide](/docs/guides/deployment.md) - Complete deployment workflow
- [Environments Guide](/docs/guides/environments.md) - Multi-environment setup
- [AWS Overview](/docs/cloud/aws/overview.md) - AWS-specific configuration
- [OpenTofu Backend](/docs/iac/backend.md) - Backend state management
