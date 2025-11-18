#!/usr/bin/env python3
"""
Batch enhance ALL remaining documentation files with frontmatter metadata.
Usage: python3 scripts/enhance-all-docs.py
"""

import os
import sys
from pathlib import Path

# Comprehensive metadata templates for all remaining files
METADATA_TEMPLATES = {
    # Configuration docs
    "configuration/transire-yaml.md": {
        "title": "transire.yaml Reference",
        "description": "Complete reference for the Transire configuration file",
        "keywords": ["transire.yaml", "configuration", "config file", "yaml", "settings"],
        "category": "configuration",
        "difficulty": "all",
        "estimated_time": "10 minutes",
        "prerequisites": ["Basic YAML knowledge"],
        "use_cases": ["Configuring project settings", "Understanding config options", "Customizing behavior"],
        "questions": ["What goes in transire.yaml?", "What config options are available?", "How do I customize settings?"]
    },
    "configuration/lambda.md": {
        "title": "Lambda Settings",
        "description": "Configure AWS Lambda function settings for your Transire application",
        "keywords": ["lambda", "aws lambda", "function settings", "memory", "timeout", "architecture"],
        "category": "configuration",
        "difficulty": "intermediate",
        "estimated_time": "10 minutes",
        "prerequisites": ["Basic Lambda knowledge"],
        "use_cases": ["Configuring Lambda resources", "Optimizing performance", "Setting timeouts"],
        "questions": ["How do I configure Lambda?", "What memory should I use?", "How do I set timeout?"]
    },
    "configuration/queues.md": {
        "title": "Queue Configuration",
        "description": "Configure SQS queue settings for message processing",
        "keywords": ["queue configuration", "sqs", "batch size", "visibility timeout", "dlq"],
        "category": "configuration",
        "difficulty": "intermediate",
        "estimated_time": "10 minutes",
        "prerequisites": ["Understanding of queues"],
        "use_cases": ["Configuring queue behavior", "Setting batch sizes", "Configuring retries"],
        "questions": ["How do I configure queues?", "What is visibility timeout?", "How do I set batch size?"]
    },
    "configuration/schedules.md": {
        "title": "Schedule Configuration",
        "description": "Configure scheduled task settings and cron expressions",
        "keywords": ["schedule configuration", "cron", "eventbridge", "timezone", "enabled"],
        "category": "configuration",
        "difficulty": "intermediate",
        "estimated_time": "10 minutes",
        "prerequisites": ["Understanding of cron syntax"],
        "use_cases": ["Configuring scheduled tasks", "Setting timezones", "Enabling/disabling schedules"],
        "questions": ["How do I configure schedules?", "How do I set timezone?", "How do I disable a schedule?"]
    },
    "configuration/environment.md": {
        "title": "Environment Variables",
        "description": "Configure environment variables for your Transire application",
        "keywords": ["environment variables", "env vars", "configuration", "secrets", "settings"],
        "category": "configuration",
        "difficulty": "beginner",
        "estimated_time": "5 minutes",
        "prerequisites": [],
        "use_cases": ["Setting environment variables", "Managing secrets", "Configuration per environment"],
        "questions": ["How do I set env vars?", "How do I manage secrets?", "Where do env vars go?"]
    },
    "configuration/vpc-existing.md": {
        "title": "VPC & Existing Resources",
        "description": "Configure VPC networking and reference existing AWS resources",
        "keywords": ["vpc", "networking", "existing resources", "subnets", "security groups", "dynamodb", "s3"],
        "category": "configuration",
        "difficulty": "advanced",
        "estimated_time": "15 minutes",
        "prerequisites": ["AWS VPC knowledge", "Understanding of AWS resources"],
        "use_cases": ["Connecting to VPC", "Using existing resources", "Private networking"],
        "questions": ["How do I use VPC?", "How do I reference existing resources?", "How do I access private resources?"]
    },
    # CLI Reference docs
    "cli-reference/index.md": {
        "title": "CLI Reference Overview",
        "description": "Overview of Transire CLI commands",
        "keywords": ["cli", "command line", "commands", "reference"],
        "category": "cli-reference",
        "difficulty": "all",
        "estimated_time": "5 minutes",
        "prerequisites": [],
        "use_cases": ["Understanding CLI commands", "Quick reference"],
        "questions": ["What commands are available?", "How do I use the CLI?"]
    },
    "cli-reference/transire-init.md": {
        "title": "transire init",
        "description": "Initialize a new Transire project",
        "keywords": ["transire init", "initialize", "new project", "scaffold", "setup"],
        "category": "cli-reference",
        "difficulty": "beginner",
        "estimated_time": "5 minutes",
        "prerequisites": [],
        "use_cases": ["Creating new projects", "Scaffolding applications"],
        "questions": ["How do I create a new project?", "What does init create?", "What flags are available?"]
    },
    "cli-reference/transire-run.md": {
        "title": "transire run",
        "description": "Run Transire application locally with hot reload",
        "keywords": ["transire run", "local development", "hot reload", "dev server"],
        "category": "cli-reference",
        "difficulty": "beginner",
        "estimated_time": "5 minutes",
        "prerequisites": [],
        "use_cases": ["Running locally", "Development workflow", "Testing"],
        "questions": ["How do I run locally?", "What does run do?", "How do I change the port?"]
    },
    "cli-reference/transire-dev.md": {
        "title": "transire dev",
        "description": "Development utilities for testing queues and schedules",
        "keywords": ["transire dev", "development tools", "testing", "queues", "schedules"],
        "category": "cli-reference",
        "difficulty": "intermediate",
        "estimated_time": "10 minutes",
        "prerequisites": [],
        "use_cases": ["Testing queues locally", "Triggering schedules", "Development utilities"],
        "questions": ["How do I test queues?", "How do I trigger schedules?", "What dev commands exist?"]
    },
    "cli-reference/transire-build.md": {
        "title": "transire build",
        "description": "Build deployment artifacts for AWS Lambda",
        "keywords": ["transire build", "build", "artifacts", "deployment", "lambda"],
        "category": "cli-reference",
        "difficulty": "intermediate",
        "estimated_time": "5 minutes",
        "prerequisites": [],
        "use_cases": ["Building for deployment", "Creating artifacts", "Preparing for AWS"],
        "questions": ["How do I build for deployment?", "What does build create?", "Where are artifacts stored?"]
    },
    "cli-reference/transire-deploy.md": {
        "title": "transire deploy",
        "description": "Deploy Transire application to AWS",
        "keywords": ["transire deploy", "deployment", "aws", "cdk", "cloudformation"],
        "category": "cli-reference",
        "difficulty": "intermediate",
        "estimated_time": "10 minutes",
        "prerequisites": ["AWS CLI configured"],
        "use_cases": ["Deploying to AWS", "Updating deployment", "Production deployment"],
        "questions": ["How do I deploy to AWS?", "How do I update?", "What does deploy do?"]
    },
    # API Reference docs
    "api-reference/index.md": {
        "title": "API Reference Overview",
        "description": "Overview of Transire Go packages and APIs",
        "keywords": ["api reference", "go packages", "documentation", "api"],
        "category": "api-reference",
        "difficulty": "intermediate",
        "estimated_time": "5 minutes",
        "prerequisites": ["Go basics"],
        "use_cases": ["Understanding APIs", "Package reference"],
        "questions": ["What packages are available?", "How do I use the API?"]
    },
    "api-reference/transire.md": {
        "title": "Package transire",
        "description": "Core Transire package with App, Runtime, and main types",
        "keywords": ["package transire", "App", "Runtime", "core types", "api"],
        "category": "api-reference",
        "difficulty": "intermediate",
        "estimated_time": "10 minutes",
        "prerequisites": ["Go basics"],
        "use_cases": ["Using core APIs", "Understanding App", "Runtime detection"],
        "questions": ["What is in package transire?", "How do I use App?", "What types are available?"]
    },
    "api-reference/handlers.md": {
        "title": "Handlers",
        "description": "Handler interfaces for HTTP, queues, and schedules",
        "keywords": ["handlers", "QueueHandler", "SchedulerHandler", "interfaces", "api"],
        "category": "api-reference",
        "difficulty": "intermediate",
        "estimated_time": "10 minutes",
        "prerequisites": ["Go interfaces"],
        "use_cases": ["Implementing handlers", "Understanding interfaces"],
        "questions": ["What handler interfaces exist?", "How do I implement handlers?", "What methods are required?"]
    },
    "api-reference/messages.md": {
        "title": "Messages & Events",
        "description": "Message and event types for queue and schedule handlers",
        "keywords": ["messages", "events", "Message", "ScheduleEvent", "types", "api"],
        "category": "api-reference",
        "difficulty": "intermediate",
        "estimated_time": "5 minutes",
        "prerequisites": ["Go basics"],
        "use_cases": ["Understanding message types", "Working with events"],
        "questions": ["What message types exist?", "How do I access message data?", "What is ScheduleEvent?"]
    },
    "api-reference/config.md": {
        "title": "Configuration Types",
        "description": "Configuration structs and types",
        "keywords": ["configuration types", "config structs", "types", "api"],
        "category": "api-reference",
        "difficulty": "intermediate",
        "estimated_time": "5 minutes",
        "prerequisites": ["Go structs"],
        "use_cases": ["Understanding config types", "Programmatic configuration"],
        "questions": ["What config types exist?", "How do I use config programmatically?"]
    },
    # Examples docs
    "examples/simple-api.md": {
        "title": "Simple API Example",
        "description": "Complete example of a REST API with queues and schedules",
        "keywords": ["example", "simple api", "rest", "queues", "schedules", "tutorial"],
        "category": "examples",
        "difficulty": "beginner",
        "estimated_time": "20 minutes",
        "prerequisites": ["Completed Quickstart"],
        "use_cases": ["Learning by example", "Understanding complete app", "REST API patterns"],
        "questions": ["How do I build a REST API?", "Show me a complete example", "How do handlers work together?"]
    },
    "examples/todo-app.md": {
        "title": "Todo App Example",
        "description": "Todo application with database integration",
        "keywords": ["example", "todo app", "database", "crud", "full app"],
        "category": "examples",
        "difficulty": "intermediate",
        "estimated_time": "30 minutes",
        "prerequisites": ["Understanding of databases"],
        "use_cases": ["Building CRUD apps", "Database integration", "Complete application"],
        "questions": ["How do I integrate a database?", "Show me a real app", "How do I structure my code?"]
    },
    "examples/full-app.md": {
        "title": "Full Application Example",
        "description": "Production-ready application with all Transire features",
        "keywords": ["example", "full application", "production", "complete", "advanced"],
        "category": "examples",
        "difficulty": "advanced",
        "estimated_time": "45 minutes",
        "prerequisites": ["Completed other examples"],
        "use_cases": ["Production patterns", "Complete feature set", "Best practices"],
        "questions": ["Show me a production app", "What does a complete app look like?", "What are best practices?"]
    },
    # Other pages
    "index.md": {
        "title": "Transire Documentation",
        "description": "Cloud-agnostic Go framework for building production APIs with Chi routing",
        "keywords": ["transire", "go framework", "lambda", "chi router", "cloud-agnostic", "serverless"],
        "category": "other",
        "difficulty": "all",
        "estimated_time": "5 minutes",
        "prerequisites": [],
        "use_cases": ["Getting started", "Understanding Transire", "Overview"],
        "questions": ["What is Transire?", "Why use Transire?", "How do I get started?"]
    },
    "faq.md": {
        "title": "FAQ",
        "description": "Frequently asked questions about Transire",
        "keywords": ["faq", "questions", "troubleshooting", "help", "common issues"],
        "category": "other",
        "difficulty": "all",
        "estimated_time": "10 minutes",
        "prerequisites": [],
        "use_cases": ["Finding answers", "Troubleshooting", "Common questions"],
        "questions": ["Where can I find answers?", "How do I troubleshoot?", "What are common issues?"]
    },
    "contributing.md": {
        "title": "Contributing",
        "description": "Guide for contributing to Transire",
        "keywords": ["contributing", "development", "pull requests", "issues", "community"],
        "category": "other",
        "difficulty": "intermediate",
        "estimated_time": "10 minutes",
        "prerequisites": ["Go development"],
        "use_cases": ["Contributing code", "Reporting issues", "Development setup"],
        "questions": ["How do I contribute?", "How do I report issues?", "How do I set up development?"]
    }
}

def create_frontmatter(metadata):
    """Generate YAML frontmatter from metadata dict."""
    fm = ["---"]
    fm.append(f'title: "{metadata["title"]}"')
    fm.append(f'description: "{metadata["description"]}"')
    fm.append("keywords:")
    for kw in metadata["keywords"]:
        fm.append(f'  - {kw}')
    fm.append(f'category: {metadata["category"]}')
    fm.append(f'difficulty: {metadata["difficulty"]}')
    fm.append(f'estimated_time: {metadata["estimated_time"]}')
    fm.append("prerequisites:")
    if metadata["prerequisites"]:
        for prereq in metadata["prerequisites"]:
            fm.append(f'  - "{prereq}"')
    else:
        fm.append("  []")
    fm.append("related_docs: []")
    fm.append("mcp_metadata:")
    fm.append("  primary_use_cases:")
    for uc in metadata["use_cases"]:
        fm.append(f'    - "{uc}"')
    fm.append("  common_questions:")
    for q in metadata["questions"]:
        fm.append(f'    - "{q}"')
    fm.append("---")
    return "\n".join(fm)

def enhance_file(filepath, metadata):
    """Add frontmatter to a documentation file."""
    path = Path(filepath)
    if not path.exists():
        print(f"❌ File not found: {filepath}")
        return False

    # Read current content
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already has frontmatter
    if content.startswith('---'):
        print(f"✓ {filepath} already has frontmatter")
        return True

    # Generate and prepend frontmatter
    frontmatter = create_frontmatter(metadata)
    new_content = frontmatter + "\n\n" + content

    # Write back
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ Enhanced {filepath}")
    return True

def main():
    """Enhance all files in METADATA_TEMPLATES."""
    docs_dir = Path(__file__).parent.parent / "docs"
    success_count = 0
    total_count = len(METADATA_TEMPLATES)

    print(f"\n🚀 Enhancing {total_count} documentation files...\n")

    # Process by category
    categories = {
        "Configuration": [k for k in METADATA_TEMPLATES if k.startswith("configuration/")],
        "CLI Reference": [k for k in METADATA_TEMPLATES if k.startswith("cli-reference/")],
        "API Reference": [k for k in METADATA_TEMPLATES if k.startswith("api-reference/")],
        "Examples": [k for k in METADATA_TEMPLATES if k.startswith("examples/")],
        "Other": [k for k in METADATA_TEMPLATES if not any(k.startswith(p) for p in ["configuration/", "cli-reference/", "api-reference/", "examples/"])]
    }

    for category, files in categories.items():
        print(f"\n📁 {category} ({len(files)} files)")
        for rel_path in files:
            filepath = docs_dir / rel_path
            if enhance_file(filepath, METADATA_TEMPLATES[rel_path]):
                success_count += 1

    print(f"\n✨ Enhanced {success_count}/{total_count} files")

    if success_count == total_count:
        print("✅ All files enhanced successfully!")
        return 0
    else:
        print(f"⚠️  {total_count - success_count} files failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
