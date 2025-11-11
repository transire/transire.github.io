---
title: "CLI Overview"
category: cli
subcategory: null
complexity: beginner
duration: null
prerequisites:
  - Transire CLI installed
mcp_use: reference
features_covered:
  - CLI commands
  - Development workflow
  - Deployment workflow
code_blocks: false
last_updated: 2025-11-11
---

# CLI Overview

## Introduction

The Transire CLI (`transire`) is the command-line tool for building, running, and deploying Transire applications.

## Core Commands

### Workspace Commands

- **`transire init`** - Initialize workspace and configuration
- **`transire init backend`** - Initialize cloud backend for state storage

### Development Commands

- **`transire gen`** - Generate manifest from your Go code
- **`transire run`** - Start local development server
- **`transire run --watch`** - (Coming in v1.1) Hot reload

### Deployment Commands

- **`transire plan`** - Preview deployment infrastructure
- **`transire deploy`** - Deploy to cloud via OpenTofu
- **`transire deploy --output json`** - Deploy with JSON output for CI/CD

## Installation

See the [Installation Guide](/getting-started/installation.md) for detailed installation instructions.

## Command Reference

- [transire init](/cli/init.md) - Workspace and backend initialization
- [transire gen](/cli/gen.md) - Manifest generation
- [transire run](/cli/run.md) - Local development
- [transire plan](/cli/plan.md) - Deployment planning
- [transire deploy](/cli/deploy.md) - Cloud deployment

## Typical Workflow

### First-Time Setup

```bash
# Initialize workspace (creates .transire/ and transire.yaml)
transire init

# Create your application code (main.go)
# ... write your handlers ...

# Generate manifest from code
transire gen

# Preview what will be deployed (optional)
transire plan
```

### Local Development

```bash
# Start local server
transire run

# Or with hot reload (coming in v1.1)
transire run --watch
```

### Deploying to Cloud

```bash
# First time: Initialize backend for state storage
transire init backend

# Preview deployment plan
transire plan

# Deploy to default (dev) environment
transire deploy

# Deploy to production with JSON output
transire deploy --environment production --output json
```

## Configuration

The CLI reads configuration from `transire.yaml` in your project root. See the [Config Schema Reference](/reference/config-schema.md) for details.

## Getting Help

Use `--help` on any command for detailed usage:

```bash
transire --help
transire deploy --help
```

## Next Steps

- [Initialize Workspace](/cli/init.md) - Start a new project
- [Generate Manifest](/cli/gen.md) - Learn about manifest generation
- [Local Development](/cli/run.md) - Run your app locally
- [Preview Deployment](/cli/plan.md) - Plan your infrastructure
- [Deploy to Cloud](/cli/deploy.md) - Deploy your application
