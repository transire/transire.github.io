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
last_updated: 2025-10-31
---

# CLI Overview

## Introduction

The Transire CLI (`transire`) is the command-line tool for building, running, and deploying Transire applications.

## Core Commands

### Development Commands

- **`transire gen`** - Generate manifest from your Go code
- **`transire run`** - Start local development server
- **`transire run --watch`** - Start with hot reload

### Deployment Commands

- **`transire deploy`** - Deploy to cloud via OpenTofu
- **`transire init --backend`** - Bootstrap cloud backend

## Installation

See the [Installation Guide](/getting-started/installation.md) for detailed installation instructions.

## Command Reference

- [transire gen](/cli/gen.md) - Manifest generation
- [transire run](/cli/run.md) - Local development
- [transire deploy](/cli/deploy.md) - Cloud deployment
- [transire init](/cli/init.md) - Backend initialization

## Typical Workflow

### Local Development

```bash
# Generate manifest from code
transire gen

# Start local server with hot reload
transire run --watch
```

### Deploying to Cloud

```bash
# First time: Initialize backend
transire init --backend

# Deploy to default (dev) environment
transire deploy

# Deploy to production
transire deploy --env production
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

- [Generate Manifest](/cli/gen.md) - Learn about manifest generation
- [Local Development](/cli/run.md) - Run your app locally
- [Deploy to Cloud](/cli/deploy.md) - Deploy your application
