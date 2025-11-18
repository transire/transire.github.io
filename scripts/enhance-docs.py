#!/usr/bin/env python3
"""
Batch enhance documentation files with frontmatter metadata.
Usage: python3 scripts/enhance-docs.py
"""

import os
import sys
from pathlib import Path

# Metadata templates for each category
METADATA_TEMPLATES = {
    "guides/local-development.md": {
        "title": "Local Development",
        "description": "Develop and test Transire applications locally with hot reload",
        "keywords": ["local development", "hot reload", "testing", "transire run", "development workflow"],
        "category": "guides",
        "difficulty": "beginner",
        "estimated_time": "15 minutes",
        "prerequisites": ["Completed Quickstart"],
        "use_cases": [
            "Setting up local development environment",
            "Testing locally with hot reload",
            "Debugging Transire applications"
        ],
        "questions": [
            "How do I run my app locally?",
            "How does hot reload work?",
            "How do I test queues and schedules locally?"
        ]
    },
    "guides/testing.md": {
        "title": "Testing",
        "description": "Write unit, integration, and E2E tests for Transire applications",
        "keywords": ["testing", "unit tests", "integration tests", "e2e tests", "test patterns"],
        "category": "guides",
        "difficulty": "intermediate",
        "estimated_time": "20 minutes",
        "prerequisites": ["Understanding of Go testing"],
        "use_cases": [
            "Writing unit tests",
            "Testing HTTP handlers",
            "Testing queue and schedule handlers"
        ],
        "questions": [
            "How do I test my handlers?",
            "How do I mock dependencies?",
            "How do I test locally vs cloud?"
        ]
    },
    "guides/deploying-to-aws.md": {
        "title": "Deploying to AWS",
        "description": "Deploy Transire applications to AWS Lambda with CDK",
        "keywords": ["deployment", "aws", "lambda", "cdk", "cloudformation", "production"],
        "category": "guides",
        "difficulty": "intermediate",
        "estimated_time": "20 minutes",
        "prerequisites": ["AWS account", "AWS CLI configured"],
        "use_cases": [
            "Deploying to AWS for the first time",
            "Understanding AWS infrastructure",
            "Managing deployments"
        ],
        "questions": [
            "How do I deploy to AWS?",
            "What AWS resources are created?",
            "How do I update my deployment?"
        ]
    },
    "guides/queue-processing.md": {
        "title": "Queue Processing",
        "description": "Advanced patterns for processing messages with queue handlers",
        "keywords": ["queues", "sqs", "message processing", "async", "patterns", "best practices"],
        "category": "guides",
        "difficulty": "intermediate",
        "estimated_time": "25 minutes",
        "prerequisites": ["Understanding of queue handlers"],
        "use_cases": [
            "Processing async tasks",
            "Handling failures and retries",
            "Scaling queue processing"
        ],
        "questions": [
            "What are queue processing best practices?",
            "How do I handle failed messages?",
            "How do I scale queue processing?"
        ]
    },
    "guides/scheduled-tasks.md": {
        "title": "Scheduled Tasks",
        "description": "Run periodic tasks and cron jobs with schedule handlers",
        "keywords": ["scheduled tasks", "cron", "periodic tasks", "eventbridge", "timers"],
        "category": "guides",
        "difficulty": "intermediate",
        "estimated_time": "15 minutes",
        "prerequisites": ["Understanding of cron syntax"],
        "use_cases": [
            "Running periodic tasks",
            "Scheduling maintenance jobs",
            "Understanding cron patterns"
        ],
        "questions": [
            "How do I schedule tasks?",
            "What cron expressions are supported?",
            "How do I test scheduled tasks?"
        ]
    },
    "guides/multi-function-architecture.md": {
        "title": "Multi-Function Architecture",
        "description": "Split your application into multiple Lambda functions for optimal resource usage",
        "keywords": ["multi-function", "architecture", "optimization", "lambda functions", "resource allocation"],
        "category": "guides",
        "difficulty": "advanced",
        "estimated_time": "30 minutes",
        "prerequisites": ["Understanding of Lambda architecture"],
        "use_cases": [
            "Optimizing resource usage",
            "Scaling specific handlers",
            "Reducing cold start times"
        ],
        "questions": [
            "When should I use multiple functions?",
            "How do I split my application?",
            "What are the benefits?"
        ]
    },
    "guides/custom-cdk.md": {
        "title": "Custom CDK Extensions",
        "description": "Extend generated infrastructure with custom AWS CDK code",
        "keywords": ["cdk", "custom infrastructure", "aws resources", "extensions", "customization"],
        "category": "guides",
        "difficulty": "advanced",
        "estimated_time": "25 minutes",
        "prerequisites": ["CDK knowledge", "TypeScript basics"],
        "use_cases": [
            "Adding custom AWS resources",
            "Modifying generated infrastructure",
            "Integrating existing resources"
        ],
        "questions": [
            "How do I add custom CDK code?",
            "How do I modify generated infrastructure?",
            "Can I add custom AWS resources?"
        ]
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
    for prereq in metadata["prerequisites"]:
        fm.append(f'  - "{prereq}"')
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

    for rel_path, metadata in METADATA_TEMPLATES.items():
        filepath = docs_dir / rel_path
        if enhance_file(filepath, metadata):
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
