---
title: "Cloud Providers"
category: providers
complexity: beginner
duration: 5 minutes
mcp_use: reference
last_updated: 2025-11-10
---

# Cloud Providers

Transire is cloud-agnostic by design. Write your application once, deploy anywhere.

## Available Providers

### Production Ready

- **[AWS](/providers/aws/overview.md)** - Amazon Web Services
  - Lambda, API Gateway, SQS, EventBridge
  - Battle-tested, production-ready
  - Full feature support

### Coming Soon

- **Azure** - Microsoft Azure
  - Azure Functions, App Service, Storage Queues
  - In development

- **GCP** - Google Cloud Platform
  - Cloud Functions, Cloud Run, Pub/Sub
  - Planned

### Local Development

- **[Local Runtime](/providers/local/overview.md)** - Built-in emulator
  - In-memory queues
  - Fixed-rate scheduler
  - Fast development feedback
  - No cloud account needed

## How Providers Work

Transire uses a **provider abstraction layer** to maintain cloud agnosticism:

```
┌─────────────────────────────────────────┐
│         Your Application Code           │
│    (Cloud-agnostic Transire SDK)        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Transire Runtime                │
│    (Handles HTTP, Queue, Schedule)      │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
┌───────────┐    ┌─────────────┐
│   Local   │    │   Cloud     │
│ Provider  │    │  Provider   │
└───────────┘    └─────────────┘
      │                 │
      ▼                 ▼
 [In-Process]    [AWS/Azure/GCP]
 [Emulation]     [Native Services]
```

## Choosing a Provider

### For Development

Use the **Local Provider**:
- ✅ Fast feedback loop
- ✅ No cloud costs
- ✅ Works offline
- ✅ No configuration needed

```bash
# Just run - no provider installation needed
transire run
```

### For Production

Choose based on your requirements:

#### AWS
- **Best for:** Mature infrastructure, enterprise scale
- **Strengths:** Largest service catalog, global presence
- **Consider:** More complex pricing, steeper learning curve

#### Azure (Coming Soon)
- **Best for:** Microsoft ecosystem integration
- **Strengths:** Excellent .NET support, hybrid cloud
- **Consider:** Regional availability

#### GCP (Coming Soon)
- **Best for:** Data analytics, Kubernetes workloads
- **Strengths:** Modern architecture, competitive pricing
- **Consider:** Smaller service catalog

## Provider Installation

Providers are installed as Go packages:

```bash
# AWS Provider
go get github.com/transire/transire-cloud-aws@latest

# Azure Provider (coming soon)
go get github.com/transire/transire-cloud-azure@latest

# GCP Provider (coming soon)
go get github.com/transire/transire-cloud-gcp@latest
```

## Provider Auto-Registration

Cloud providers auto-register via blank imports:

```go
import (
    "github.com/transire/transire-sdk-go"
    _ "github.com/transire/transire-cloud-aws" // Auto-registers AWS provider
)
```

The runtime automatically detects:
1. **Local development** - Uses local provider when running `transire run`
2. **Cloud deployment** - Uses registered cloud provider when deployed

## Configuration

Configure your provider in `transire.yaml`:

```yaml
service: myapp
runtime: go

# Cloud provider selection happens automatically:
# - Local: When running `transire run`
# - Cloud: Based on which provider package is imported

# Provider-agnostic configuration
deploy:
  architecture: arm64
  memory_mb: 512
  timeout_s: 30

queues:
  max_batch_size: 10
  visibility_timeout_s: 30

# Provider-specific overrides (optional)
providers:
  aws:
    region: us-east-1
    # AWS-specific settings
```

## Feature Parity

All providers support the same core features:

| Feature | Local | AWS | Azure | GCP |
|---------|-------|-----|-------|-----|
| HTTP Handlers | ✅ | ✅ | 🔜 | 🔜 |
| Queue Handlers | ✅ | ✅ | 🔜 | 🔜 |
| Scheduled Jobs | ✅ | ✅ | 🔜 | 🔜 |
| Middleware | ✅ | ✅ | 🔜 | 🔜 |
| Dependency Injection | ✅ | ✅ | 🔜 | 🔜 |
| Environment Variables | ✅ | ✅ | 🔜 | 🔜 |

### Provider-Specific Limits

Some limits vary by provider. Check provider-specific documentation:

- **Message size** - Typically 256KB
- **Request timeout** - Typically 30s for HTTP, 15min for queue/schedule
- **Concurrency** - Provider-dependent auto-scaling

See individual provider docs for exact limits.

## Migration Between Providers

Transire's cloud-agnostic design makes migration straightforward:

```bash
# 1. Install new provider
go get github.com/transire/transire-cloud-azure@latest

# 2. Update import in main.go
# import _ "github.com/transire/transire-cloud-aws"    // Old
import _ "github.com/transire/transire-cloud-azure"  // New

# 3. Update configuration (optional)
# Edit transire.yaml with provider-specific settings

# 4. Deploy to new provider
transire deploy --environment=prod
```

Your application code remains unchanged!

## See Also

- [AWS Provider](/providers/aws/overview.md) - AWS implementation details
- [Local Provider](/providers/local/overview.md) - Local development runtime
- [Deployment Guide](/deployment/overview.md) - How to deploy
- [Configuration Reference](/reference/config-schema.md) - Config options
