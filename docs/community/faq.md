---
title: "Frequently Asked Questions"
category: community
subcategory: null
complexity: beginner
duration: null
prerequisites: []
mcp_use: reference
features_covered:
  - Common questions
  - Troubleshooting
  - Best practices
code_blocks: true
last_updated: 2025-10-31
---

# Frequently Asked Questions

## General

### What is Transire?

Transire is a cloud-native development framework for Go that enables you to write code once and run it anywhere - locally or in the cloud. It provides a simple API for building applications with HTTP endpoints, message queues, and scheduled tasks.

### How is Transire different from other frameworks?

Transire focuses on:
- **Zero boilerplate** - Minimal API surface
- **Standard Go** - Uses standard library patterns
- **Local development** - Full emulation of cloud services
- **Cloud-agnostic** - Pluggable cloud providers

### What cloud providers are supported?

Currently:
- AWS (Lambda, SQS, EventBridge, API Gateway)

More providers are planned for future releases.

## Development

### Do I need Docker to develop locally?

No. Transire's local runtime runs as a single Go process with in-memory emulation of cloud services. No containers or external services required.

### Can I use my existing Go code?

Yes. Transire uses standard Go HTTP handlers and can integrate with any Go library.

### How do I debug my application?

Use standard Go debugging tools:
- Add breakpoints in your IDE
- Use `fmt.Println` or logging
- Run tests with `go test -v`

The `transire run` command runs your code as a normal Go process.

### Can I use middleware?

Yes. Transire supports standard Go HTTP middleware. See the [Middleware Guide](/sdk/middleware.md).

## Deployment

### How does deployment work?

The `transire deploy` command:
1. Analyzes your manifest
2. Generates OpenTofu infrastructure code
3. Packages your handlers for cloud execution
4. Deploys via OpenTofu

See the [Deployment Guide](/guides/deployment.md) for details.

### Can I customize the infrastructure?

Yes. Transire generates OpenTofu files in `infra/resources/` which you can customize. You can also add override files in `infra/overrides/`.

### How do I manage environments?

Use OpenTofu workspaces. See [Environments Guide](/guides/environments.md).

### What about CI/CD?

Transire can generate CI/CD workflows. See [GitHub Actions](/ci/github-actions.md) for details.

## Testing

### How do I test my handlers?

Use the built-in test kit:

```go
import "github.com/transire/transire-sdk-go/testkit"

func TestMyHandler(t *testing.T) {
    tk := testkit.New(t)

    resp := tk.GET("/users/123")

    tk.AssertStatus(resp, 200)
    tk.AssertJSON(resp, expectedUser)
}
```

See the [Testing Guide](/sdk/testkit.md) for more examples.

### Can I write integration tests?

Yes. The test kit supports:
- HTTP request testing
- Queue message injection
- Schedule trigger simulation

See the [Testing Guide](/sdk/testkit.md).

## Performance

### What are the performance characteristics?

- **Local:** Single-process, fast iteration
- **Cloud:** Serverless, auto-scaling, pay-per-use

### How do I optimize cold starts?

- Use ARM64 architecture (default)
- Minimize dependencies
- Use dependency injection for lazy initialization

See the [Performance Guide](/guides/performance.md).

### Can I use connection pooling?

Yes. Use the DI system to create singleton services with connection pools:

```go
func main() {
    app := transire.New()

    app.Provide(func() *sql.DB {
        db, _ := sql.Open("postgres", dsn)
        return db
    })

    // DB connection is reused across requests
}
```

## Troubleshooting

### My handler isn't being called

1. Check `transire gen` output for errors
2. Verify handler signature matches expected pattern
3. Check routes in generated manifest

### Queue messages aren't processing

1. Check queue name matches between `Enqueue` and `Queue` registration
2. Verify message type matches handler signature
3. Check logs for errors

### Deployment fails

1. Check AWS credentials are configured
2. Verify OpenTofu backend is initialized (`transire init --backend`)
3. Review error messages in deployment output

For more troubleshooting help, see the [Troubleshooting Guide](/guides/troubleshooting.md).

## Getting Help

### Where can I get support?

- Check this FAQ
- Review the [documentation](/docs/)
- Read the [Troubleshooting Guide](/guides/troubleshooting.md)
- Open an issue on GitHub

### How can I contribute?

See the [Contributing Guide](/community/contributing.md).

### Where's the changelog?

See the [Changelog](/community/changelog.md) for release notes and version history.
