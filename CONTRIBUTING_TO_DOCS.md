## Contributing to Transire Documentation

**Quick Start for Contributors**

---

## 📝 Page Template

Every documentation page should follow this structure:

```markdown
---
# Required metadata
title: "Page Title"
description: "One-sentence description for search/preview"
category: learn|guide|reference|plugin|example|community
subcategory: tutorial|development|deployment|etc

# User experience
complexity: beginner|intermediate|advanced
duration: "X minutes" (for tutorials/guides)
prerequisites:
  - Go 1.22+
  - Basic HTTP knowledge

# MCP optimization
mcp_use: template|reference|guide|example|troubleshooting_guide
mcp_operations:
  - scaffold_project
  - validate_setup
features_covered:
  - HTTP handlers
  - Queue processing

# Navigation (optional but recommended)
related_pages:
  - path: /path/to/related
    title: Related Doc
    context: "Why this is related"

# Flags
code_blocks: true|false
last_updated: YYYY-MM-DD
---

# Page Title

> **Quick Summary:** One-sentence TL;DR for MCP/AI assistants

## At a Glance

- **What:** Brief description
- **When to use:** Use cases
- **Time to learn:** Duration (for tutorials)
- **Prerequisites:** What you need to know

## Quick Start (for how-to pages)

Minimal working example that can be copy-pasted.

## Detailed Explanation

Progressive disclosure - start simple, add complexity gradually.

### Section 1

Content...

### Section 2

Content...

## Common Patterns

Reusable code patterns for this feature.

## Troubleshooting

Common issues and solutions.

## See Also

- [Related Doc 1](/path) - Context about why it's relevant
- [Related Doc 2](/path) - Context about why it's relevant
```

---

## ✍️ Writing Style Guide

### Voice & Tone

- **Active voice:** "Deploy your app" not "Your app can be deployed"
- **Second person:** "You configure" not "One configures"
- **Present tense:** "Transire uses" not "Transire will use"
- **Direct:** "Do X" not "You might want to consider doing X"
- **Confident but humble:** No marketing speak, no condescension

### Code Examples

All code examples MUST be:

- ✅ **Complete** - All imports, no missing context
- ✅ **Runnable** - Copy-paste should work
- ✅ **Realistic** - Real-world names, not foo/bar
- ✅ **Commented** - Explain non-obvious parts
- ✅ **Idiomatic** - Follow Go conventions

**Good Example:**

```go
package main

import (
    "context"
    "net/http"
    "github.com/transire/sdk-go"
    "github.com/transire/sdk-go/response"
)

func main() {
    app := transire.New()
    app.GET("/orders/{id}", getOrder)
    app.Run()
}

// getOrder retrieves a single order by ID
func getOrder(w http.ResponseWriter, r *http.Request) {
    // Extract ID from URL parameters
    id := transire.URLParam(r, "id")

    // TODO: Fetch from database
    order := &Order{ID: id}

    // Return 200 OK with JSON
    response.OK(w, order)
}

type Order struct {
    ID      string `json:"id"`
    Product string `json:"product"`
}
```

**Bad Example:**

```go
// Missing imports
// Missing context
func handler() {
    // Does something
    foo := bar  // What is bar?
}
```

### Developer Persona

Our audience is **experienced developers**. Write accordingly:

- Assume competence (don't explain what HTTP GET is)
- Provide clear explanations (do explain how Transire routing works)
- Show code first, explain after
- Use realistic scenarios
- Walk through, don't spoon-feed

---

## 📂 Where to Add Content

Check `IMPLEMENTATION_STATUS.md` for incomplete pages. Common additions:

### Tutorials (`learn/tutorials/`)

**Structure:**
1. What you'll build (with screenshot if applicable)
2. Prerequisites checklist
3. Step-by-step instructions (numbered)
4. What you learned (summary)
5. Next steps (links)

**Naming:** `XX-topic-name.md` (e.g., `02-rest-api.md`)

### Guides (`guides/`)

**Categories:**
- `development/` - Local dev practices
- `deployment/` - Deployment strategies
- `architecture/` - System design
- `patterns/` - Code patterns
- `troubleshooting/` - Problem solving

**Structure:**
1. Overview (what & why)
2. Quick example
3. Detailed explanation
4. Common patterns
5. Troubleshooting

### Reference (`reference/`)

**Categories:**
- `sdk/` - API documentation
- `cli/` - Command reference
- `config/` - Configuration
- `manifest/` - Manifest schema

**Structure:**
1. Overview
2. API listing (table)
3. Detailed docs for each API
4. Examples
5. Edge cases

### Examples (`examples/`)

**Structure:**
1. Overview (what it does)
2. Architecture diagram
3. Complete code (with repo link)
4. Key concepts explained
5. How to run it

---

## 🎨 Visual Elements

### Mermaid Diagrams

Use for:
- Architecture flows
- Decision trees
- Sequence diagrams
- Journey maps

**Example:**

```markdown
\`\`\`mermaid
graph LR
    A[HTTP Request] --> B[API Gateway]
    B --> C[Lambda Function]
    C --> D[SQS Queue]
    D --> E[Queue Lambda]
\`\`\`
```

### Tables

Use for:
- API reference
- Comparisons
- Quick lookups

**Example:**

```markdown
| HTTP Method | Handler | Description |
|-------------|---------|-------------|
| GET | `listOrders` | List all orders |
| POST | `createOrder` | Create new order |
```

### Callouts

Use MkDocs admonitions:

```markdown
!!! note "Developer Note"
    This feature requires Go 1.22+

!!! warning "Production Consideration"
    Always use S3 backend in production

!!! tip "Pro Tip"
    Use `--watch` flag for hot reload
```

### Code Annotations

```go
func handler(w http.ResponseWriter, r *http.Request) {
    id := transire.URLParam(r, "id")  // (1)!
    response.OK(w, data)  // (2)!
}
```

1. Extract URL parameter from path
2. Return 200 OK with JSON body

---

## 🧪 Testing Your Changes

Before submitting:

1. **Test code examples:**

   ```bash
   # Run all code examples to ensure they work
   cd example-code
   go run main.go
   ```

2. **Check links:**

   ```bash
   # Install link checker
   pip install linkchecker

   # Check all links
   linkchecker docs/
   ```

3. **Preview locally:**

   ```bash
   # Install MkDocs
   pip install -r requirements.txt

   # Serve locally
   mkdocs serve

   # Visit http://localhost:8000
   ```

4. **Verify formatting:**
   - All code blocks have language specified
   - All tables are properly formatted
   - All lists use consistent style
   - All headings follow hierarchy (H1 → H2 → H3)

---

## 🚀 Submission Checklist

Before creating a Pull Request:

- [ ] Page follows template structure
- [ ] Metadata (YAML frontmatter) is complete
- [ ] Code examples are complete and tested
- [ ] Links point to correct pages
- [ ] Spelling and grammar checked
- [ ] Previewed locally with `mkdocs serve`
- [ ] Mermaid diagrams render correctly
- [ ] Tables display properly
- [ ] Added to `mkdocs.yml` navigation
- [ ] Updated `IMPLEMENTATION_STATUS.md` if completing a planned page

---

## 📋 PR Description Template

```markdown
## Summary

Brief description of changes (1-2 sentences)

## Type of Change

- [ ] New page
- [ ] Content update
- [ ] Bug fix (typo, broken link, etc.)
- [ ] Enhancement (improve existing page)

## Pages Changed

- `docs/path/to/page.md` - What changed

## Checklist

- [ ] Tested all code examples
- [ ] Checked all links
- [ ] Previewed locally
- [ ] Updated navigation in mkdocs.yml
- [ ] Followed style guide

## Screenshots (if applicable)

Before / After screenshots

## Related Issues

Closes #123
```

---

## 🎯 Quality Standards

### Must Have

- ✅ Complete, runnable code examples
- ✅ Clear prerequisites
- ✅ Proper metadata
- ✅ Working internal links

### Should Have

- ✅ Visual diagrams (Mermaid)
- ✅ Troubleshooting section
- ✅ "See Also" links
- ✅ Time estimates (for tutorials)

### Nice to Have

- ✅ Interactive examples
- ✅ Video walkthrough
- ✅ Multiple approaches shown
- ✅ Performance notes

---

## 🐛 Common Mistakes

### ❌ Don't Do This

```markdown
# Bad: No metadata
No YAML frontmatter

# Bad: Incomplete code
func handler() {
    // Missing imports, context
}

# Bad: Broken links
See [this page](/broken-link)

# Bad: No explanation
Just code with no context

# Bad: Foo/bar examples
func processFoo(bar string) {}
```

### ✅ Do This Instead

```markdown
---
title: "Proper Page"
description: "Clear description"
category: guide
complexity: beginner
# ... complete metadata
---

# Proper Page

> Quick summary here

## Overview

Clear explanation...

## Example

\`\`\`go
// Complete, runnable code
package main

import (
    "context"
    "github.com/transire/sdk-go"
)

func main() {
    // Realistic example
    app := transire.New()
    app.GET("/orders", listOrders)
    app.Run()
}
\`\`\`

## See Also

- [Related Page](../path/to/page/) - Why it's relevant
```

---

## 💡 Tips for Great Documentation

1. **Start with why** - Why does this feature exist?
2. **Show, don't tell** - Code before explanation
3. **Be specific** - "20 minutes" not "a while"
4. **Link liberally** - Help users discover related content
5. **Test everything** - If code doesn't run, users get stuck
6. **Write for scanning** - Use lists, tables, headings
7. **Add troubleshooting** - Anticipate problems
8. **Keep it current** - Update `last_updated` date

---

## 📚 Resources

- **Style Guide:** `CLAUDE.md` in repo root
- **Architecture:** `HLD.md` for technical details
- **Status:** `IMPLEMENTATION_STATUS.md` for what's needed
- **Examples:** Look at `docs/learn/tutorials/01-hello-world.md`
- **MkDocs:** https://squidfunk.github.io/mkdocs-material/

---

## 🤝 Getting Help

- **Questions:** Open a GitHub Discussion
- **Bug reports:** Create an issue with "documentation" label
- **Suggestions:** Comment on existing issues or create new ones

---

## 🎉 Thank You!

Your contributions make Transire documentation better for everyone. Every tutorial, every fix, every diagram helps developers build better applications faster.

**Happy documenting!** 📝
