---
title: "transire dev"
description: "Development utilities for testing queues and schedules"
keywords:
  - transire dev
  - development tools
  - testing
  - queues
  - schedules
category: cli-reference
difficulty: intermediate
estimated_time: 10 minutes
prerequisites:
  []
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Testing queues locally"
    - "Triggering schedules"
    - "Development utilities"
  common_questions:
    - "How do I test queues?"
    - "How do I trigger schedules?"
    - "What dev commands exist?"
---

# transire dev

Development utilities for testing queues and schedules during local development.

!!! tip "TL;DR"
    `transire dev` provides commands to list and test your queue and schedule handlers without curl. Use `transire dev queues send` to test queue handlers and `transire dev schedules execute` to trigger scheduled tasks.

---

## Synopsis

```bash
transire dev queues list
transire dev queues send <queue-name> <json-message>
transire dev schedules list
transire dev schedules execute <schedule-name>
```

---

## Description

The `transire dev` command group provides utilities for interacting with your running Transire application during local development. These commands replace the need to manually send HTTP requests to the queue and schedule simulator endpoints.

**Requirements:**
- Your app must be running via `transire run` in another terminal
- Commands communicate with the dev API at `http://localhost:3000/__dev/` (or your configured HTTP port)

Source: [`internal/cli/commands/dev.go`](https://github.com/transire/transire/blob/main/internal/cli/commands/dev.go)

---

## Queue Commands

### List Registered Queues

```bash
transire dev queues list
```

**Description:** Shows all registered queue handlers in your running application.

**Example Output:**
```
Registered Queues:
  - email-queue
  - notification-queue
  - image-processing-queue
```

**Use Cases:**
- Verify your queue handlers are registered correctly
- Check queue names before sending test messages
- Debug handler discovery issues

---

### Send Test Message to Queue

```bash
transire dev queues send <queue-name> <json-message>
```

**Description:** Sends a test message to the specified queue handler. The message is processed by your `HandleMessages()` method exactly as it would be in production with SQS.

**Arguments:**
- `<queue-name>` – Name of the queue (must match `QueueHandler.QueueName()`)
- `<json-message>` – JSON message body (will be parsed as `Message.Body()`)

**Examples:**

Simple message:
```bash
transire dev queues send email-queue '{"to":"user@example.com","subject":"Test","body":"Hello!"}'
```

Complex message with nested data:
```bash
transire dev queues send notification-queue '{
  "user_id": "123",
  "type": "welcome",
  "metadata": {
    "campaign": "onboarding",
    "priority": "high"
  }
}'
```

**What Happens:**
1. Message is sent to the dev API endpoint `POST http://localhost:3000/__dev/queues/send`
2. The message body is wrapped in a `Message` struct
3. Your `QueueHandler.HandleMessages()` is called with the message
4. Success/failure response is shown in the terminal

**Output on Success:**
```
✓ Message sent to queue 'email-queue'
✓ Handler processed message successfully
```

**Output on Failure:**
```
✗ Error sending message to queue 'email-queue':
  Handler returned error: failed to send email: connection timeout
```

---

## Schedule Commands

### List Registered Schedules

```bash
transire dev schedules list
```

**Description:** Shows all registered schedule handlers in your running application.

**Example Output:**
```
Registered Schedules:
  - daily-cleanup (cron: 0 0 * * *)
  - hourly-report (cron: 0 * * * *)
  - weekly-summary (cron: 0 0 * * 0)
```

**Use Cases:**
- Verify your schedule handlers are registered correctly
- Check schedule names and cron expressions
- Debug handler discovery issues

---

### Execute Schedule Manually

```bash
transire dev schedules execute <schedule-name>
```

**Description:** Triggers a schedule handler immediately, without waiting for the cron schedule. Useful for testing scheduled tasks during development.

**Arguments:**
- `<schedule-name>` – Name of the schedule (must match `SchedulerHandler.Name()`)

**Examples:**

Trigger daily cleanup task:
```bash
transire dev schedules execute daily-cleanup
```

Test hourly report generation:
```bash
transire dev schedules execute hourly-report
```

**What Happens:**
1. Command sends request to `POST http://localhost:3000/__dev/schedules/execute`
2. A `ScheduleEvent` is created with the current timestamp
3. Your `SchedulerHandler.HandleSchedule()` method is called
4. Success/failure response is shown in the terminal

**Output on Success:**
```
✓ Schedule 'daily-cleanup' executed successfully
✓ Completed in 1.23s
```

**Output on Failure:**
```
✗ Error executing schedule 'daily-cleanup':
  Handler returned error: database connection failed
```

---

## Configuration

### Custom Ports

If you've configured a custom HTTP port in `transire.yaml`:

```yaml
development:
  http_port: 8080
```

The `transire dev` commands automatically detect and use the correct port.

**Manual Port Override:**
```bash
TRANSIRE_PORT=8080 transire dev queues list
```

---

## Workflow Examples

### Testing Queue Handler End-to-End

```bash
# Terminal 1: Start app
transire run

# Terminal 2: Verify handler is registered
transire dev queues list
# => email-queue

# Terminal 2: Send test message
transire dev queues send email-queue '{"to":"test@example.com","subject":"Test"}'
# => ✓ Message sent to queue 'email-queue'

# Terminal 1: See handler logs
# [INFO] Processing message: test@example.com
# [INFO] Email sent successfully
```

---

### Testing Schedule Handler

```bash
# Terminal 1: Start app
transire run

# Terminal 2: Verify handler is registered
transire dev schedules list
# => daily-cleanup (cron: 0 0 * * *)

# Terminal 2: Execute immediately (don't wait for cron)
transire dev schedules execute daily-cleanup
# => ✓ Schedule 'daily-cleanup' executed successfully

# Terminal 1: See handler logs
# [INFO] Starting daily cleanup...
# [INFO] Deleted 42 expired records
# [INFO] Cleanup complete
```

---

### Debugging Queue Processing

```bash
# Test with invalid JSON to see error handling
transire dev queues send email-queue 'invalid-json'
# => ✗ Error: invalid JSON in message body

# Test with missing fields
transire dev queues send email-queue '{}'
# => ✗ Error: missing required field 'to'

# Fix and retry
transire dev queues send email-queue '{"to":"test@example.com","subject":"Test","body":"Hello"}'
# => ✓ Message sent successfully
```

---

## Comparison: CLI Commands vs curl

### Before (using curl)

**Queue testing:**
```bash
curl -X POST http://localhost:4000/queues/email-queue \
  -H "Content-Type: application/json" \
  -d '{"to":"test@example.com","subject":"Test"}'
```

**Schedule testing:**
```bash
curl -X POST http://localhost:4000/schedules/daily-cleanup
```

**Problems:**
- ❌ Need to remember port numbers (4000, 5000)
- ❌ Need to remember endpoint paths
- ❌ Need to set Content-Type header
- ❌ Verbose curl syntax
- ❌ No validation before sending

### After (using transire dev)

**Queue testing:**
```bash
transire dev queues send email-queue '{"to":"test@example.com","subject":"Test"}'
```

**Schedule testing:**
```bash
transire dev schedules execute daily-cleanup
```

**Benefits:**
- ✅ No need to remember ports
- ✅ No need to remember endpoint paths
- ✅ No headers required
- ✅ Concise, readable syntax
- ✅ Validates queue/schedule exists before sending
- ✅ Better error messages
- ✅ List commands to discover handlers

---

## Troubleshooting

### "Failed to connect to dev server"

**Error:**
```
✗ Error: failed to connect to dev server at http://localhost:3000
```

**Solutions:**
1. Ensure `transire run` is running in another terminal
2. Check that your app started successfully (look for "Ready!" message)
3. Verify the port matches your `transire.yaml` configuration
4. Try with explicit port: `TRANSIRE_PORT=3000 transire dev queues list`

---

### "Queue not found"

**Error:**
```
✗ Error: queue 'my-queue' not found
```

**Solutions:**
1. List registered queues to check the name:
   ```bash
   transire dev queues list
   ```

2. Verify handler registration in `main.go`:
   ```go
   app.RegisterQueueHandler(&MyQueueHandler{})
   ```

3. Check handler's `QueueName()` method returns correct name:
   ```go
   func (h *MyQueueHandler) QueueName() string {
       return "my-queue" // Must match CLI command
   }
   ```

4. Restart `transire run` to re-discover handlers

---

### "Schedule not found"

**Error:**
```
✗ Error: schedule 'my-schedule' not found
```

**Solutions:**
1. List registered schedules to check the name:
   ```bash
   transire dev schedules list
   ```

2. Verify handler registration in `main.go`:
   ```go
   app.RegisterScheduleHandler(&MyScheduleHandler{})
   ```

3. Check handler's `Name()` method returns correct name:
   ```go
   func (h *MyScheduleHandler) Name() string {
       return "my-schedule" // Must match CLI command
   }
   ```

4. Restart `transire run` to re-discover handlers

---

### "Invalid JSON in message"

**Error:**
```
✗ Error: invalid JSON in message body
```

**Solutions:**
1. Ensure JSON is properly quoted:
   ```bash
   # Wrong (shell interprets special chars)
   transire dev queues send my-queue {"foo":"bar"}

   # Correct (single quotes around entire JSON)
   transire dev queues send my-queue '{"foo":"bar"}'
   ```

2. Use proper JSON escaping for nested quotes:
   ```bash
   transire dev queues send my-queue '{"msg":"Say \"hello\""}'
   ```

3. For complex JSON, use a file:
   ```bash
   cat message.json | xargs -0 transire dev queues send my-queue
   ```

---

## Advanced Usage

### Sending Batch Messages

Send multiple messages in sequence:

```bash
for i in {1..5}; do
  transire dev queues send email-queue "{\"to\":\"user${i}@example.com\",\"subject\":\"Test ${i}\"}"
done
```

---

### Testing Error Handling

Send intentionally malformed data to test error handling:

```bash
# Missing required fields
transire dev queues send email-queue '{}'

# Invalid email format
transire dev queues send email-queue '{"to":"not-an-email","subject":"Test"}'

# Null values
transire dev queues send email-queue '{"to":null,"subject":"Test"}'
```

Your handler should gracefully handle these cases and return appropriate errors.

---

### Scripted Testing

Create a test script `test-queues.sh`:

```bash
#!/bin/bash
set -e

echo "Testing email queue..."
transire dev queues send email-queue '{"to":"test@example.com","subject":"Test"}'

echo "Testing notification queue..."
transire dev queues send notification-queue '{"user_id":"123","type":"welcome"}'

echo "Testing schedules..."
transire dev schedules execute daily-cleanup

echo "✓ All tests passed"
```

Run with:
```bash
chmod +x test-queues.sh
./test-queues.sh
```

---

### Integration with CI/CD

Use dev commands in integration tests:

```bash
# Start app in background
transire run &
APP_PID=$!

# Wait for app to be ready
sleep 5

# Run tests
transire dev queues send email-queue '{"to":"test@example.com","subject":"CI Test"}'
EXIT_CODE=$?

# Cleanup
kill $APP_PID

exit $EXIT_CODE
```

---

## Next Steps

### Learn Local Development Workflow

Master the complete local development experience:

[:octicons-arrow-right-24: Local Development Guide](../guides/local-development.md)

### Understand Queue Handlers

Learn how to implement queue handlers:

[:octicons-arrow-right-24: Queue Handlers Guide](../core-concepts/queue-handlers.md)

### Understand Schedule Handlers

Learn how to implement schedule handlers:

[:octicons-arrow-right-24: Schedule Handlers Guide](../core-concepts/schedule-handlers.md)

### Write Automated Tests

Test your handlers with automated tests:

[:octicons-arrow-right-24: Testing Guide](../guides/testing.md)

---

## See Also

- [transire run](transire-run.md) – Start local development server
- [Local Development Guide](../guides/local-development.md) – Complete local workflow
- [Queue Processing Guide](../guides/queue-processing.md) – Working with queues
- [Scheduled Tasks Guide](../guides/scheduled-tasks.md) – Working with schedules
