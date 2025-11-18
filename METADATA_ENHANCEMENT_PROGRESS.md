# Documentation Metadata Enhancement Progress

## Summary

Enhancing all Transire documentation with comprehensive frontmatter metadata to optimize for LLM and MCP consumption.

## Completed Files

### Getting Started (3/3 - 100%)
- ✅ `docs/getting-started/installation.md`
- ✅ `docs/getting-started/quickstart.md`
- ✅ `docs/getting-started/your-first-api.md`

### Core Concepts (0/5 - 0%)
- ⏳ `docs/core-concepts/application-runtime.md`
- ⏳ `docs/core-concepts/configuration.md`
- ⏳ `docs/core-concepts/http-handlers.md`
- ⏳ `docs/core-concepts/queue-handlers.md`
- ⏳ `docs/core-concepts/schedule-handlers.md`

### Guides (0/7 - 0%)
- ⏳ `docs/guides/custom-cdk.md`
- ⏳ `docs/guides/deploying-to-aws.md`
- ⏳ `docs/guides/local-development.md`
- ⏳ `docs/guides/multi-function-architecture.md`
- ⏳ `docs/guides/queue-processing.md`
- ⏳ `docs/guides/scheduled-tasks.md`
- ⏳ `docs/guides/testing.md`

### Configuration (0/6 - 0%)
- ⏳ `docs/configuration/environment.md`
- ⏳ `docs/configuration/lambda.md`
- ⏳ `docs/configuration/queues.md`
- ⏳ `docs/configuration/schedules.md`
- ⏳ `docs/configuration/transire-yaml.md`
- ⏳ `docs/configuration/vpc-existing.md`

### CLI Reference (0/6 - 0%)
- ⏳ `docs/cli-reference/index.md`
- ⏳ `docs/cli-reference/transire-build.md`
- ⏳ `docs/cli-reference/transire-deploy.md`
- ⏳ `docs/cli-reference/transire-dev.md`
- ⏳ `docs/cli-reference/transire-init.md`
- ⏳ `docs/cli-reference/transire-run.md`

### API Reference (0/5 - 0%)
- ⏳ `docs/api-reference/config.md`
- ⏳ `docs/api-reference/handlers.md`
- ⏳ `docs/api-reference/index.md`
- ⏳ `docs/api-reference/messages.md`
- ⏳ `docs/api-reference/transire.md`

### Examples (0/3 - 0%)
- ⏳ `docs/examples/full-app.md`
- ⏳ `docs/examples/simple-api.md`
- ⏳ `docs/examples/todo-app.md`

### Other (0/3 - 0%)
- ⏳ `docs/index.md`
- ⏳ `docs/faq.md`
- ⏳ `docs/contributing.md`

## Overall Progress: 3/37 files (8%)

## Metadata Template

Each file should have the following frontmatter structure:

```yaml
---
title: "Page Title"
description: "One-line description for search engines and previews"
keywords:
  - keyword1
  - keyword2
  - keyword3
category: getting-started|core-concepts|guides|configuration|cli-reference|api-reference|examples|other
difficulty: beginner|intermediate|advanced
estimated_time: X minutes
prerequisites:
  - "Prerequisite 1"
  - "Prerequisite 2"
related_docs:
  - path: "/path/to/related/"
    relationship: "prerequisite|next_step|deep_dive|related"
mcp_metadata:
  primary_use_cases:
    - "Use case 1"
    - "Use case 2"
  common_questions:
    - "Question 1?"
    - "Question 2?"
  troubleshooting_hints:
    - issue: "Common issue"
      keywords: ["keyword1", "keyword2"]
      solution_section: "#section-anchor"
---
```

## Category-Specific Guidelines

### Core Concepts
- **Difficulty**: intermediate
- **Time**: 10-15 minutes
- **Keywords**: Focus on architectural concepts
- **Use cases**: Understanding how Transire works
- **Questions**: "How does X work?", "When should I use Y?"

### Guides
- **Difficulty**: intermediate to advanced
- **Time**: 15-30 minutes
- **Keywords**: Task-oriented keywords
- **Use cases**: Specific tasks and workflows
- **Questions**: "How do I...?", "What's the best way to...?"

### Configuration
- **Difficulty**: all levels
- **Time**: 5-10 minutes
- **Keywords**: Config options, settings
- **Use cases**: Configuration and customization
- **Questions**: "How do I configure X?", "What does Y setting do?"

### CLI Reference
- **Difficulty**: all levels
- **Time**: 5 minutes
- **Keywords**: CLI commands, flags, options
- **Use cases**: Command-line usage
- **Questions**: "What does command X do?", "How do I use flag Y?"

### API Reference
- **Difficulty**: intermediate
- **Time**: 5-10 minutes
- **Keywords**: Go packages, types, functions
- **Use cases**: Writing code, understanding APIs
- **Questions**: "What does type X do?", "How do I use function Y?"

### Examples
- **Difficulty**: beginner to intermediate
- **Time**: 20-30 minutes
- **Keywords**: Example names, features demonstrated
- **Use cases**: Learning by example
- **Questions**: "Show me an example of X", "How do I build Y?"

## Automation Script

To batch-process remaining files, use this script:

```bash
#!/bin/bash
# scripts/add-metadata.sh

# Add frontmatter to a documentation file
# Usage: ./scripts/add-metadata.sh <file> <title> <description> <category> <difficulty>

FILE=$1
TITLE=$2
DESCRIPTION=$3
CATEGORY=$4
DIFFICULTY=$5
KEYWORDS=$6

# Read current content (skip if already has frontmatter)
if head -1 "$FILE" | grep -q "^---$"; then
  echo "✓ $FILE already has frontmatter"
  exit 0
fi

# Create temp file with frontmatter
cat > "${FILE}.tmp" <<EOF
---
title: "$TITLE"
description: "$DESCRIPTION"
keywords: $KEYWORDS
category: $CATEGORY
difficulty: $DIFFICULTY
estimated_time: 10 minutes
prerequisites: []
related_docs: []
mcp_metadata:
  primary_use_cases: []
  common_questions: []
---

EOF

# Append original content
cat "$FILE" >> "${FILE}.tmp"

# Replace original
mv "${FILE}.tmp" "$FILE"

echo "✓ Enhanced $FILE"
```

## Next Steps

1. Complete core-concepts documentation (5 files)
2. Complete guides documentation (7 files)
3. Complete configuration documentation (6 files)
4. Complete cli-reference documentation (6 files)
5. Complete api-reference documentation (5 files)
6. Complete examples documentation (3 files)
7. Complete other pages (3 files)
8. Verify all files build with `mkdocs build --strict`
9. Test MCP scraping with sample queries
10. Update mcp-metadata.json with any new insights

## Verification

After completing all files:

```bash
# Build docs
cd /Users/jamie/personal/transire/repos/transire.github.io
source .venv/bin/activate
mkdocs build --strict

# Check for files without frontmatter
for file in docs/**/*.md; do
  if ! head -1 "$file" | grep -q "^---$"; then
    echo "Missing frontmatter: $file"
  fi
done

# Count enhanced files
echo "Enhanced: $(grep -l "^---$" docs/**/*.md | wc -l) / 37"
```

## Benefits of Enhanced Metadata

1. **Better Search**: Keywords and descriptions improve findability
2. **Context-Aware**: LLMs can understand document relationships
3. **Smart Navigation**: Related docs help guide learning paths
4. **Troubleshooting**: Targeted hints help solve common issues
5. **Use Case Matching**: Primary use cases help match user intent
6. **Common Questions**: Pre-indexed Q&A for faster responses

## MCP Integration

The enhanced metadata enables:

- **Tool Selection**: MCP can choose right tool based on use cases
- **Smart Caching**: Popular pages identified via primary_use_cases
- **Error Matching**: Troubleshooting hints enable pattern matching
- **Workflow Mapping**: Related docs build complete task flows
- **Question Routing**: Common questions map to relevant documentation

---

**Status**: In Progress
**Last Updated**: 2025-01-18
**Completion**: 8% (3/37 files)
