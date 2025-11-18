# transire run

Start your Transire application in local development mode with hot reload.

!!! tip "TL;DR"
    `transire run` builds your Go app, starts local HTTP/queue/schedule servers, and watches for file changes to auto-reload.

---

## Synopsis

```bash
transire run
```

**Note:** This command currently has **no flags**. Configuration is read from `transire.yaml`.

---

## Description

The `transire run` command:

1. **Builds** your Go application automatically
2. **Starts** the application with `RuntimeLocal` ([`pkg/transire/local_runtime.go`](https://github.com/transire/transire/blob/main/pkg/transire/local_runtime.go))
3. **Starts HTTP server** (default port: 3000)
4. **Starts queue simulator** (default port: 4000)
5. **Starts schedule simulator** (default port: 5000)
6. **Watches** `*.go` and `*.yaml` files for changes ([`internal/cli/runner/`](https://github.com/transire/transire/blob/main/internal/cli/runner/) using [`github.com/fsnotify/fsnotify`](https://github.com/fsnotify/fsnotify))
7. **On file change:** kills process, rebuilds, restarts (with debouncing)

Source: [`internal/cli/commands/run.go:8-41`](https://github.com/transire/transire/blob/main/internal/cli/commands/run.go)

---

## Hot Reload Implementation

Hot reload is implemented via [`internal/cli/runner/`](https://github.com/transire/transire/blob/main/internal/cli/runner/):

1. **File watcher** monitors `*.go` and `*.yaml` files using `github.com/fsnotify/fsnotify`
2. **Debouncing** batches rapid changes (~500ms window)
3. **Process management:**
   - Kills running application process
   - Rebuilds Go binary
   - Restarts application
4. **Error handling:** Build errors are displayed; saves trigger retry

---

## Configuration

Ports and behavior are configured via `transire.yaml`:

```yaml
development:
  http_port: 3000       # HTTP server port
  queue_port: 4000      # Queue simulator port
  scheduler_port: 5000  # Schedule simulator port
  auto_reload: true     # Enable hot reload
  log_level: debug      # Log verbosity
```

Source: [`pkg/transire/config.go:74-82`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

**Defaults:**
- `http_port`: 3000
- `queue_port`: 4000
- `scheduler_port`: 5000
- `auto_reload`: true
- `log_level`: "info"

---

## Example Output

```bash
$ transire run
[INFO] Transire starting in local mode
[INFO] Discovered handlers:
[INFO]   HTTP: 5 routes
[INFO]   Queues: 2 handlers (email-queue, notification-queue)
[INFO]   Schedules: 1 handler (daily-cleanup)
[INFO] Starting HTTP server on :3000
[INFO] Starting queue simulator on :4000
[INFO] Starting scheduler simulator on :5000
[INFO] Ready! Watching for file changes...
```

---

## Testing Your Application

When running locally via `transire run`, you can test your application in multiple ways:

### HTTP API

**URL:** `http://localhost:3000`

Test your Chi routes with standard HTTP clients:

```bash
curl http://localhost:3000/health
# => OK

curl http://localhost:3000/api/v1/users
# => [...]
```

### Queue Handlers

Use the `transire dev queues` commands to test queue handlers:

```bash
# List registered queues
transire dev queues list

# Send test message
transire dev queues send email-queue '{"to":"test@example.com","subject":"Test","body":"Hello"}'
```

The message body (JSON) is passed to `HandleMessages()` as `Message.Body()`.

[:octicons-arrow-right-24: Learn more about queue testing](transire-dev.md#queue-commands)

### Schedule Handlers

Use the `transire dev schedules` commands to trigger scheduled tasks:

```bash
# List registered schedules
transire dev schedules list

# Execute schedule immediately (don't wait for cron)
transire dev schedules execute daily-cleanup
```

Your `SchedulerHandler.HandleSchedule()` method will execute immediately.

[:octicons-arrow-right-24: Learn more about schedule testing](transire-dev.md#schedule-commands)

Source: [`pkg/transire/local_runtime.go`](https://github.com/transire/transire/blob/main/pkg/transire/local_runtime.go)

---

## Hot Reload Behavior

Hot reload triggers on changes to:

- **`*.go`** files (all Go source files in project)
- **`*.yaml`** files (e.g., `transire.yaml`)

### Debouncing

Rapid changes within ~500ms are batched into a single reload to avoid excessive rebuilds.

### What's excluded from builds

Code tagged with `//go:build local` is **included** in local builds but **excluded** from Lambda builds.

Use this for:
- Local development utilities
- Debug endpoints
- Test helpers

```go
//go:build local

package main

// This file is only compiled for local development
func init() {
    // Register debug routes
}
```

**Note:** Hot reload is only for local development. It is **not** included in Lambda deployments.

---

## Troubleshooting

### Port already in use

**Error:**
```
Error: failed to start HTTP server: listen tcp :3000: bind: address already in use
```

**Solution:**
Change the port in `transire.yaml`:

```yaml
development:
  http_port: 8080  # Use a different port
  queue_port: 8081
```

### Build errors

Transire shows build output. Fix errors in your code and save – hot reload will retry automatically.

Example:
```
[ERROR] Build failed:
./main.go:25:2: undefined: nonExistentFunction
[INFO] Waiting for file changes to retry...
```

### "transire: command not found"

Ensure `$GOPATH/bin` is in your `$PATH`:

```bash
export PATH=$PATH:$(go env GOPATH)/bin
```

Add this to your `~/.bashrc` or `~/.zshrc` to make it permanent.

### Hot reload not working

**Check:**
1. `transire.yaml` has `auto_reload: true` (default)
2. File changes are being saved (check editor auto-save settings)
3. File extensions are `.go` or `.yaml`

### Changes not reflected

**Try:**
1. Stop `transire run` (Ctrl+C)
2. Delete build artifacts: `rm -rf ./transire-app`
3. Restart: `transire run`

---

## Comparison: `transire run` vs Manual

### With `transire run`

```bash
transire run
# ✅ Auto-builds
# ✅ Auto-restarts on changes
# ✅ Queue/schedule simulators included
# ✅ Single command
```

### Without `transire run` (manual)

```bash
go build -o app .
./app
# ❌ Manual rebuild required
# ❌ Manual restart required
# ❌ No simulators
# ❌ Multiple steps
```

**Recommendation:** Always use `transire run` for local development.

---

## Advanced: Custom Build Tags

Pass build tags via environment variable (future feature):

```bash
TRANSIRE_BUILD_TAGS="debug,experimental" transire run
```

This would compile with `-tags debug,experimental`.

**Note:** Not currently implemented. Configuration is read from `transire.yaml` only.

---

## Next Steps

### Deploy to AWS

Ready to deploy your app?

[:octicons-arrow-right-24: transire build](transire-build.md) – Build Lambda artifacts

[:octicons-arrow-right-24: transire deploy](transire-deploy.md) – Deploy to AWS

### Learn More About Local Development

Best practices for local dev workflow:

[:octicons-arrow-right-24: Local Development Guide](../guides/local-development.md)

### Configure Your App

Customize ports, logging, and more:

[:octicons-arrow-right-24: Configuration Reference](../configuration/transire-yaml.md)

### Test Your Application

Write tests for your Transire app:

[:octicons-arrow-right-24: Testing Guide](../guides/testing.md)

---

## See Also

- [transire init](transire-init.md) – Initialize a new project
- [transire build](transire-build.md) – Build deployment artifacts
- [transire deploy](transire-deploy.md) – Deploy to AWS
- [Local Development Guide](../guides/local-development.md) – Best practices
