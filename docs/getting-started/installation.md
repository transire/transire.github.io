---
title: Installation
category: getting-started
complexity: beginner
duration: 5 minutes
prerequisites:
  - Go 1.22 or later
  - AWS CLI (for cloud deployment)
mcp_use: reference
---

# Installation

This guide covers installing the Transire CLI and setting up your development environment.

## Prerequisites

Before installing Transire, ensure you have:

### Required

- **Go 1.22 or later** - [Download from golang.org](https://golang.org/dl/)
- **Git** - For version control

### For Cloud Deployment

- **AWS CLI** - [Installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **AWS Account** - [Sign up](https://aws.amazon.com/free/)
- **AWS Credentials** - Configured via `aws configure`

## Install Transire CLI

### macOS (Homebrew)

```bash
brew tap transire/tap
brew install transire
```

### Linux/macOS (Install Script)

```bash
curl -fsSL https://get.transire.dev | sh
```

### Manual Installation

Download the binary for your platform from [GitHub Releases](https://github.com/transire/transire-cli/releases):

```bash
# Download (replace VERSION with latest version, e.g., v1.0.0)
curl -LO https://github.com/transire/transire-cli/releases/download/VERSION/transire-linux-amd64.tar.gz

# Extract
tar -xzf transire-linux-amd64.tar.gz

# Move to PATH
sudo mv transire /usr/local/bin/

# Make executable
sudo chmod +x /usr/local/bin/transire
```

### From Source

```bash
go install github.com/transire/transire-cli/cmd/transire@latest
```

**Note:** Installing from source requires Go 1.22+ and installs to `$GOPATH/bin`.

## Verify Installation

Confirm Transire is installed correctly:

```bash
$ transire version
Transire CLI v1.0.0
Go runtime: go1.22.0
OS/Arch: darwin/arm64
```

## Configure AWS Credentials

For cloud deployment, configure AWS credentials:

### Option 1: AWS CLI Configuration

```bash
$ aws configure
AWS Access Key ID [None]: YOUR_ACCESS_KEY
AWS Secret Access Key [None]: YOUR_SECRET_KEY
Default region name [None]: us-east-1
Default output format [None]: json
```

### Option 2: Environment Variables

```bash
export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
export AWS_DEFAULT_REGION=us-east-1
```

### Option 3: IAM Role (Recommended for CI/CD)

Use IAM roles with GitHub Actions OIDC or EC2 instance profiles. No credentials required.

### Verify AWS Access

```bash
$ aws sts get-caller-identity
{
    "UserId": "AIDACKCEVSQ6C2EXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

## Update Transire

### Homebrew

```bash
brew upgrade transire
```

### Install Script

Run the install script again:

```bash
curl -fsSL https://get.transire.dev | sh
```

### Manual Update

Download the latest release and replace the binary:

```bash
# Download latest
curl -LO https://github.com/transire/transire-cli/releases/latest/download/transire-linux-amd64.tar.gz

# Replace existing binary
tar -xzf transire-linux-amd64.tar.gz
sudo mv transire /usr/local/bin/
```

## Uninstall Transire

### Homebrew

```bash
brew uninstall transire
brew untap transire/tap
```

### Manual Uninstall

```bash
sudo rm /usr/local/bin/transire
```

## Platform Support

Transire CLI supports the following platforms:

| OS | Architecture | Status |
|----|--------------|--------|
| **macOS** | arm64 (M1/M2/M3) | ✅ Supported |
| **macOS** | amd64 (Intel) | ✅ Supported |
| **Linux** | amd64 | ✅ Supported |
| **Linux** | arm64 | ✅ Supported |
| **Windows** | amd64 | ⚠️ Experimental |

**Note:** Windows support is experimental. We recommend using [WSL2](https://docs.microsoft.com/en-us/windows/wsl/install) for the best experience.

## Troubleshooting

### Command Not Found

If you get `command not found: transire`:

1. Ensure the binary is in your `PATH`:
   ```bash
   echo $PATH
   ```

2. Add to PATH if needed:
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="/usr/local/bin:$PATH"

   # Reload shell
   source ~/.bashrc  # or source ~/.zshrc
   ```

### Permission Denied

If you get `permission denied`:

```bash
chmod +x /path/to/transire
```

### AWS Credentials Issues

If `transire deploy` fails with AWS errors:

1. Verify credentials:
   ```bash
   aws sts get-caller-identity
   ```

2. Check IAM permissions (requires CloudFormation, Lambda, API Gateway, SQS, EventBridge, IAM):
   ```bash
   aws iam get-user
   ```

3. Use `aws configure` to reset credentials

### Version Mismatch

If you encounter version compatibility issues:

1. Check CLI version:
   ```bash
   transire version
   ```

2. Check SDK version in your `go.mod`:
   ```go
   require github.com/transire/sdk-go v1.0.0
   ```

3. Update SDK:
   ```bash
   go get github.com/transire/sdk-go@latest
   ```

## Next Steps

Now that Transire is installed:

**[Project Setup →](project-setup.md){ .md-button .md-button--primary }**

Learn how to create your first Transire project.

## See Also

- [Quick Start](quickstart.md) - Deploy your first app in 15 minutes
- [Project Setup](project-setup.md) - Create a new Transire project
- [Troubleshooting Guide](../guides/troubleshooting.md) - Common issues and solutions
