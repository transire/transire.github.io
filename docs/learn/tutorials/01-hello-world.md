---
title: "Tutorial: Hello World"
description: Build your first Transire app in 5 minutes
category: learn
subcategory: tutorial
complexity: beginner
duration: 5 minutes
prerequisites:
  - Go 1.22+
mcp_use: template
mcp_operations:
  - scaffold_minimal_project
  - validate_setup
features_covered:
  - HTTP handlers
  - Local development
  - Basic routing
code_blocks: true
last_updated: 2025-11-10
---

# Tutorial: Hello World

> **Quick Summary:** Build and run your first Transire HTTP endpoint in 5 minutes

## What You'll Build

A simple HTTP API that responds to requests:

```bash
$ curl http://localhost:8080/hello
{"message": "Hello, World!"}
```

**Time:** 5 minutes • **Difficulty:** Beginner

---

## Prerequisites

- [x] **Go 1.22+** - [Download](https://golang.org/dl/)
- [x] **Text editor** - VS Code, GoLand, or any editor

**Quick check:**

```bash
$ go version
go version go1.22.0 darwin/arm64
```

---

## Step 1: Create Project

Create a new directory and initialize Go module:

```bash
# Create project directory
mkdir hello-transire
cd hello-transire

# Initialize Go module
go mod init github.com/yourusername/hello-transire

# Install Transire SDK
go get github.com/transire/transire-sdk-go@latest
```

**Expected output:**

```
go: added github.com/transire/transire-sdk-go v1.0.0
```

---

## Step 2: Write Your App

Create `main.go`:

```go
package main

import (
    "net/http"

    "github.com/transire/transire-sdk-go"
    "github.com/transire/transire-sdk-go/response"
)

func main() {
    // Create Transire app
    app := transire.New()

    // Register HTTP handler
    app.GET("/hello", helloWorld)

    // Start the server
    app.Run()
}

// helloWorld is a standard Go HTTP handler
func helloWorld(w http.ResponseWriter, r *http.Request) {
    response.OK(w, map[string]string{
        "message": "Hello, World!",
    })
}
```

**What's happening here?**

| Line | What it does |
|------|--------------|
| `app := transire.New()` | Creates a new Transire application |
| `app.GET("/hello", helloWorld)` | Registers GET /hello → helloWorld |
| `app.Run()` | Starts the local HTTP server on :8080 |
| `response.OK(w, data)` | Sends 200 OK with JSON body |

---

## Step 3: Run Locally

Start your application:

```bash
$ go run main.go
```

**You should see:**

```
✓ Starting HTTP server on :8080
→ Ready: http://localhost:8080
```

Your server is now running! 🎉

---

## Step 4: Test It

Open a new terminal and make a request:

```bash
$ curl http://localhost:8080/hello
```

**Response:**

```json
{
  "message": "Hello, World!"
}
```

**Try in your browser:** Visit [http://localhost:8080/hello](http://localhost:8080/hello)

---

## Understanding the Code

### Standard Go HTTP Handler

Transire uses **standard Go HTTP handlers**. If you know `net/http`, you already know Transire:

```go
// This is just a standard Go HTTP handler
func helloWorld(w http.ResponseWriter, r *http.Request) {
    // Write response using helper (or use stdlib directly)
    response.OK(w, map[string]string{
        "message": "Hello, World!",
    })
}
```

You can also use stdlib directly:

```go
func helloWorld(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{
        "message": "Hello, World!",
    })
}
```

### HTTP Verb Helpers

Transire provides helpers for common HTTP verbs:

```go
app.GET("/resource", getHandler)       // GET requests
app.POST("/resource", createHandler)   // POST requests
app.PUT("/resource", updateHandler)    // PUT requests
app.DELETE("/resource", deleteHandler) // DELETE requests
app.PATCH("/resource", patchHandler)   // PATCH requests
```

---

## Next Steps

### Add More Endpoints

Try adding another endpoint:

```go
func main() {
    app := transire.New()

    app.GET("/hello", helloWorld)
    app.GET("/goodbye", goodbye)  // New endpoint

    app.Run()
}

func goodbye(w http.ResponseWriter, r *http.Request) {
    response.OK(w, map[string]string{
        "message": "Goodbye!",
    })
}
```

Test it:

```bash
$ curl http://localhost:8080/goodbye
{"message": "Goodbye!"}
```

### Use URL Parameters

Add a personalized greeting:

```go
func main() {
    app := transire.New()

    app.GET("/hello/{name}", helloName)  // {name} is a URL parameter

    app.Run()
}

func helloName(w http.ResponseWriter, r *http.Request) {
    // Extract URL parameter
    name := transire.URLParam(r, "name")

    response.OK(w, map[string]string{
        "message": "Hello, " + name + "!",
    })
}
```

Test it:

```bash
$ curl http://localhost:8080/hello/Alice
{"message": "Hello, Alice!"}

$ curl http://localhost:8080/hello/Bob
{"message": "Hello, Bob!"}
```

---

## Common Patterns

### Multiple Response Types

Return different response types:

```go
func handler(w http.ResponseWriter, r *http.Request) {
    // JSON response (most common)
    response.OK(w, map[string]string{"status": "ok"})

    // Plain text response
    response.Text(w, http.StatusOK, "Plain text response")

    // Custom status code
    response.JSON(w, http.StatusCreated, data)
}
```

### Error Responses

Handle errors gracefully:

```go
func getUser(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")

    user, err := fetchUser(id)
    if err != nil {
        // Return 500 Internal Server Error
        response.InternalServerError(w, "Failed to fetch user")
        return
    }

    if user == nil {
        // Return 404 Not Found
        response.NotFound(w, "User not found")
        return
    }

    // Return 200 OK with user data
    response.OK(w, user)
}
```

---

## Troubleshooting

### Port Already in Use

**Error:** `address already in use`

**Solution:** Another process is using port 8080. Either:

1. Stop the other process
2. Change the port in `transire.yaml` (we'll cover this in the next tutorial)

### Import Errors

**Error:** `could not import github.com/transire/transire-sdk-go`

**Solution:** Run `go mod download` to fetch dependencies:

```bash
go mod download
```

### 404 Not Found

**Issue:** `curl` returns 404 even though the server is running

**Solution:** Check that:

1. Your URL matches the registered path exactly
2. The HTTP method matches (GET vs POST)
3. The server is running without errors

---

## What You Learned

Congratulations! You've built your first Transire application. 🎉

You now know how to:

- ✅ Create a Transire project
- ✅ Register HTTP handlers
- ✅ Use URL parameters
- ✅ Return JSON responses
- ✅ Handle errors

---

## Next Tutorial

Ready to build a real API?

**[Tutorial 2: REST API →](02-rest-api/)** - Build a complete orders API with CRUD operations (15 minutes)

Or jump directly to:

- [Queue Processing Tutorial →](03-queue-processing/) - Add async processing
- [Deployment Guide →](../../guides/deployment/first-deployment/) - Deploy to AWS

---

## See Also

- [HTTP Handlers Reference](../../reference/sdk/http-api/) - Complete HTTP API documentation
- [Core Concepts](../introduction/concepts/) - Understand Transire's architecture
- [Beginner Learning Path](../curriculum/beginner-path/) - Structured learning journey

---

## Complete Code

Here's the complete `main.go` with all examples:

```go
package main

import (
    "net/http"

    "github.com/transire/transire-sdk-go"
    "github.com/transire/transire-sdk-go/response"
)

func main() {
    app := transire.New()

    // Basic endpoint
    app.GET("/hello", helloWorld)

    // Endpoint with URL parameter
    app.GET("/hello/{name}", helloName)

    // Multiple endpoints
    app.GET("/goodbye", goodbye)

    app.Run()
}

func helloWorld(w http.ResponseWriter, r *http.Request) {
    response.OK(w, map[string]string{
        "message": "Hello, World!",
    })
}

func helloName(w http.ResponseWriter, r *http.Request) {
    name := transire.URLParam(r, "name")
    response.OK(w, map[string]string{
        "message": "Hello, " + name + "!",
    })
}

func goodbye(w http.ResponseWriter, r *http.Request) {
    response.OK(w, map[string]string{
        "message": "Goodbye!",
    })
}
```

**Download:** [hello-transire.zip](../../examples/hello-world/)
