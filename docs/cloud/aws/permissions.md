---
title: "AWS Permissions"
category: cloud
subcategory: aws
complexity: intermediate
duration: null
prerequisites:
  - AWS basics
  - IAM understanding
mcp_use: reference
features_covered:
  - IAM roles
  - Permissions policies
  - Security best practices
code_blocks: true
last_updated: 2025-10-31
---

# AWS Permissions

## Overview

Transire automatically generates least-privilege IAM policies for your Lambda functions based on the handlers and resources your application uses.

## Generated Permissions

### HTTP Handler Permissions

HTTP handlers receive minimal permissions by default:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### Queue Handler Permissions

Queue handlers receive permissions to:
- Read messages from their queue
- Delete messages after processing
- Send messages to DLQ on failure

```json
{
  "Effect": "Allow",
  "Action": [
    "sqs:ReceiveMessage",
    "sqs:DeleteMessage",
    "sqs:GetQueueAttributes",
    "sqs:ChangeMessageVisibility"
  ],
  "Resource": "arn:aws:sqs:region:account:queue-name"
}
```

### Scheduled Handler Permissions

Scheduled handlers receive CloudWatch Logs permissions only.

## Additional Permissions

### Enqueueing Messages

Handlers that enqueue messages automatically receive:

```json
{
  "Effect": "Allow",
  "Action": [
    "sqs:SendMessage",
    "sqs:GetQueueUrl"
  ],
  "Resource": "arn:aws:sqs:region:account:target-queue"
}
```

### Cross-Service Permissions

If your handlers interact with other AWS services, permissions are automatically added. For example, if you:

- Query DynamoDB → DynamoDB permissions added
- Read from S3 → S3 GetObject permissions added
- Publish to SNS → SNS Publish permissions added

## Custom Permissions

### Adding Custom Permissions

To add custom permissions, create a policy override file:

**infra/overrides/policies/custom-permissions.json:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/MyTable"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::my-bucket/*"
    }
  ]
}
```

This policy will be merged with auto-generated permissions.

### Function-Specific Permissions

To add permissions to specific functions:

**infra/overrides/policies/GetUser-permissions.json:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "dynamodb:GetItem",
      "Resource": "arn:aws:dynamodb:*:*:table/Users"
    }
  ]
}
```

## Security Best Practices

### 1. Principle of Least Privilege

Only grant permissions that are actually needed:

```json
// ✗ Too broad
{
  "Effect": "Allow",
  "Action": "dynamodb:*",
  "Resource": "*"
}

// ✓ Specific
{
  "Effect": "Allow",
  "Action": ["dynamodb:GetItem", "dynamodb:Query"],
  "Resource": "arn:aws:dynamodb:region:account:table/SpecificTable"
}
```

### 2. Use Resource-Specific Policies

Don't use wildcards unless necessary:

```json
// ✗ Too broad
"Resource": "*"

// ✓ Specific
"Resource": "arn:aws:s3:::my-specific-bucket/*"
```

### 3. Separate Environments

Use different AWS accounts or regions for dev/staging/prod:

```yaml
env:
  dev:
    AWS_REGION: us-east-1
    AWS_ACCOUNT: "111111111111"

  production:
    AWS_REGION: us-west-2
    AWS_ACCOUNT: "222222222222"
```

### 4. Monitor Permissions Usage

Use AWS IAM Access Analyzer to identify:
- Unused permissions
- Overly permissive policies
- External access

### 5. Enable CloudTrail

Log all API calls for auditing:

```bash
aws cloudtrail create-trail \
  --name my-trail \
  --s3-bucket-name my-audit-bucket
```

## Common Permission Patterns

### Database Access

```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:PutItem",
    "dynamodb:UpdateItem",
    "dynamodb:Query",
    "dynamodb:Scan"
  ],
  "Resource": [
    "arn:aws:dynamodb:region:account:table/TableName",
    "arn:aws:dynamodb:region:account:table/TableName/index/*"
  ]
}
```

### S3 Access

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject"
  ],
  "Resource": "arn:aws:s3:::bucket-name/*"
}
```

### Secrets Manager Access

```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue"
  ],
  "Resource": "arn:aws:secretsmanager:region:account:secret:secret-name-*"
}
```

## Viewing Current Permissions

### Via AWS Console

1. Go to Lambda console
2. Select your function
3. Click "Configuration" → "Permissions"
4. View execution role and policies

### Via AWS CLI

```bash
# Get function role
aws lambda get-function --function-name myapp-GetUsers \
  --query 'Configuration.Role' --output text

# Get role policies
aws iam list-attached-role-policies --role-name role-name

# Get policy document
aws iam get-policy-version \
  --policy-arn policy-arn \
  --version-id v1
```

## Debugging Permission Issues

### Access Denied Errors

If you see "Access Denied" errors:

1. **Check CloudWatch Logs** for specific permission missing:
   ```
   AccessDeniedException: User: arn:aws:sts::123:assumed-role/role-name
   is not authorized to perform: dynamodb:GetItem
   ```

2. **Add missing permission** to override file

3. **Redeploy**:
   ```bash
   transire deploy
   ```

### Testing Permissions

Test permissions locally before deploying:

```bash
# Simulate Lambda execution
aws lambda invoke \
  --function-name myapp-GetUsers \
  --payload '{"test": true}' \
  response.json

# Check response
cat response.json
```

## Permission Boundaries

For organizations using permission boundaries:

**infra/overrides/permission-boundary.json:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": ["us-east-1", "us-west-2"]
        }
      }
    }
  ]
}
```

## See Also

- [AWS Deployment](/docs/cloud/aws/deployment.md)
- [Security Best Practices (AWS)](https://docs.aws.amazon.com/lambda/latest/dg/security.html)
- [IAM Overview](/docs/iac/overview.md)
- [Troubleshooting Guide](/docs/guides/troubleshooting.md)
