# VPC & Existing Resources

Configure networking and connect to existing AWS infrastructure.

!!! tip "TL;DR"
    Use `vpc:` for private networking (RDS, ElastiCache access). Use `existing_resources:` to grant Lambda permissions to existing DynamoDB, S3, Secrets Manager, etc. Both are optional.

---

## VPC Configuration

### Overview

Place Lambda functions in your VPC to access private resources like RDS databases, ElastiCache clusters, or internal APIs.

Source: [`pkg/transire/config.go:49-53`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

---

### Configuration

```yaml
vpc:
  subnet_ids:
    - subnet-abc123  # Private subnet 1
    - subnet-def456  # Private subnet 2
  security_group_ids:
    - sg-xyz789      # Lambda security group
```

**Required fields:**
- `subnet_ids` – List of VPC subnet IDs (minimum 2 for high availability)
- `security_group_ids` – List of security group IDs

---

### Use Cases

| Resource | Configuration | Notes |
|----------|---------------|-------|
| RDS Database | Private subnets + SG with DB access | Must allow outbound 3306/5432 |
| ElastiCache | Private subnets + SG with Redis/Memcached access | Must allow outbound 6379/11211 |
| Internal API | Private subnets + SG with API access | Must allow outbound HTTP/HTTPS |
| VPC Endpoints | Private subnets | For AWS service access without NAT |

---

### Important Considerations

**NAT Gateway Required:**

Lambda functions in VPC cannot access the internet (including AWS APIs) without a NAT Gateway.

```
Lambda (Private Subnet) → NAT Gateway (Public Subnet) → Internet Gateway → AWS APIs
```

**Cost:** ~$32/month per NAT Gateway + data transfer

**Alternative:** VPC Endpoints for AWS services (no NAT required):
- `com.amazonaws.{region}.s3` – S3 access
- `com.amazonaws.{region}.dynamodb` – DynamoDB access
- `com.amazonaws.{region}.secretsmanager` – Secrets Manager access

**Cold Starts:**

VPC Lambda functions have longer cold starts (+1-2 seconds) due to ENI creation.

**Mitigation:**
- Use provisioned concurrency (adds cost)
- Accept slightly longer cold starts
- Use non-VPC functions for public APIs

---

### Complete VPC Example

```yaml
name: my-api

vpc:
  subnet_ids:
    - subnet-0abc123456789  # us-east-1a (private)
    - subnet-0def123456789  # us-east-1b (private)
  security_group_ids:
    - sg-0xyz123456789     # Lambda security group

# Lambda will have access to:
# - RDS in same VPC
# - ElastiCache in same VPC
# - Other Lambda functions in same VPC
# - AWS services via NAT or VPC endpoints
```

---

### Security Group Rules

**Lambda security group (attached to Lambda):**

```
Outbound rules:
- Protocol: TCP, Port: 5432, Destination: RDS security group    # PostgreSQL
- Protocol: TCP, Port: 6379, Destination: Redis security group  # Redis
- Protocol: TCP, Port: 443, Destination: 0.0.0.0/0             # HTTPS for AWS APIs
```

**RDS security group:**

```
Inbound rules:
- Protocol: TCP, Port: 5432, Source: Lambda security group
```

**Redis security group:**

```
Inbound rules:
- Protocol: TCP, Port: 6379, Source: Lambda security group
```

---

## Existing Resources Configuration

### Overview

Grant Lambda functions IAM permissions to access existing AWS resources without recreating them.

Source: [`pkg/transire/config.go:55-67`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

---

### Supported Resource Types

```yaml
existing_resources:
  dynamodb_tables:
    - name: users-table
      arn: "arn:aws:dynamodb:us-east-1:123456789012:table/users"
      permissions: ["read", "write"]

  s3_buckets:
    - name: uploads-bucket
      arn: "arn:aws:s3:::my-uploads-bucket"
      permissions: ["read", "write"]

  secrets:
    - name: api-credentials
      arn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:api-key"
      permissions: ["read"]
```

---

### Permission Values

| Permission | DynamoDB | S3 | Secrets Manager |
|------------|----------|----|----|
| `"read"` | GetItem, Query, Scan, BatchGetItem | GetObject, ListBucket | GetSecretValue |
| `"write"` | PutItem, UpdateItem, DeleteItem, BatchWriteItem | PutObject, DeleteObject | UpdateSecret, PutSecretValue |
| `["read", "write"]` | All read + write actions | All read + write actions | All read + write actions |

---

### DynamoDB Example

```yaml
existing_resources:
  dynamodb_tables:
    - name: users-table
      arn: "arn:aws:dynamodb:us-east-1:123456789012:table/users"
      permissions: ["read", "write"]

    - name: analytics-table
      arn: "arn:aws:dynamodb:us-east-1:123456789012:table/analytics"
      permissions: ["write"]  # Write-only (append logs)
```

**In code:**

```go
import (
    "context"

    "github.com/aws/aws-sdk-go-v2/config"
    "github.com/aws/aws-sdk-go-v2/service/dynamodb"
)

func GetUser(ctx context.Context, userID string) (*User, error) {
    cfg, err := config.LoadDefaultConfig(ctx)
    if err != nil {
        return nil, err
    }

    client := dynamodb.NewFromConfig(cfg)
    result, err := client.GetItem(ctx, &dynamodb.GetItemInput{
        TableName: aws.String("users"),
        Key: map[string]types.AttributeValue{
            "id": &types.AttributeValueMemberS{Value: userID},
        },
    })
    // ... parse and return user
}
```

---

### S3 Example

```yaml
existing_resources:
  s3_buckets:
    - name: uploads-bucket
      arn: "arn:aws:s3:::my-uploads-bucket"
      permissions: ["read", "write"]

    - name: public-assets
      arn: "arn:aws:s3:::public-assets-bucket"
      permissions: ["read"]  # Read-only
```

**In code:**

```go
import (
    "context"
    "io"

    "github.com/aws/aws-sdk-go-v2/config"
    "github.com/aws/aws-sdk-go-v2/service/s3"
)

func UploadFile(ctx context.Context, key string, body io.Reader) error {
    cfg, err := config.LoadDefaultConfig(ctx)
    if err != nil {
        return err
    }

    client := s3.NewFromConfig(cfg)
    _, err = client.PutObject(ctx, &s3.PutObjectInput{
        Bucket: aws.String("my-uploads-bucket"),
        Key:    aws.String(key),
        Body:   body,
    })
    return err
}
```

---

### Secrets Manager Example

```yaml
existing_resources:
  secrets:
    - name: database-credentials
      arn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:db-creds-ABC123"
      permissions: ["read"]

    - name: api-keys
      arn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:api-keys-DEF456"
      permissions: ["read"]
```

**In code:**

```go
import (
    "context"
    "encoding/json"

    "github.com/aws/aws-sdk-go-v2/config"
    "github.com/aws/aws-sdk-go-v2/service/secretsmanager"
)

type DBCredentials struct {
    Username string `json:"username"`
    Password string `json:"password"`
    Host     string `json:"host"`
}

func GetDBCredentials(ctx context.Context) (*DBCredentials, error) {
    cfg, err := config.LoadDefaultConfig(ctx)
    if err != nil {
        return nil, err
    }

    client := secretsmanager.NewFromConfig(cfg)
    result, err := client.GetSecretValue(ctx, &secretsmanager.GetSecretValueInput{
        SecretId: aws.String("database-credentials"),
    })
    if err != nil {
        return nil, err
    }

    var creds DBCredentials
    err = json.Unmarshal([]byte(*result.SecretString), &creds)
    return &creds, err
}
```

---

## Complete Example: VPC + Existing Resources

```yaml
name: my-api
language: go
cloud: aws
runtime: lambda

# VPC configuration for private resource access
vpc:
  subnet_ids:
    - subnet-0abc123  # Private subnet 1a
    - subnet-0def456  # Private subnet 1b
  security_group_ids:
    - sg-0xyz789     # Lambda SG (allows RDS + Redis access)

# Existing AWS resources
existing_resources:
  # RDS database (in same VPC)
  secrets:
    - name: rds-credentials
      arn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:rds-creds"
      permissions: ["read"]

  # DynamoDB tables (no VPC required)
  dynamodb_tables:
    - name: users-table
      arn: "arn:aws:dynamodb:us-east-1:123456789012:table/users"
      permissions: ["read", "write"]

    - name: sessions-table
      arn: "arn:aws:dynamodb:us-east-1:123456789012:table/sessions"
      permissions: ["read", "write", "delete"]

  # S3 buckets (no VPC required, but needs NAT/VPC endpoint)
  s3_buckets:
    - name: user-uploads
      arn: "arn:aws:s3:::my-app-uploads"
      permissions: ["read", "write"]

    - name: static-assets
      arn: "arn:aws:s3:::my-app-assets"
      permissions: ["read"]

# Environment variables with resource references
environment:
  DATABASE_HOST: ${RDS_HOST}
  DATABASE_NAME: myapp
  UPLOADS_BUCKET: my-app-uploads
  SESSIONS_TABLE: sessions
```

---

## Generated CDK Code

Transire generates IAM policies and resource imports:

```typescript
// infrastructure/lib/my-api-stack.ts (generated)

// VPC configuration
const mainFunction = new lambda.Function(this, 'MainFunction', {
  vpc: ec2.Vpc.fromLookup(this, 'ExistingVpc', {
    vpcId: 'vpc-123456',
  }),
  vpcSubnets: {
    subnets: [
      ec2.Subnet.fromSubnetId(this, 'Subnet1', 'subnet-0abc123'),
      ec2.Subnet.fromSubnetId(this, 'Subnet2', 'subnet-0def456'),
    ],
  },
  securityGroups: [
    ec2.SecurityGroup.fromSecurityGroupId(this, 'LambdaSG', 'sg-0xyz789'),
  ],
});

// Existing DynamoDB table
const usersTable = dynamodb.Table.fromTableArn(
  this,
  'UsersTable',
  'arn:aws:dynamodb:us-east-1:123456789012:table/users'
);
usersTable.grantReadWriteData(mainFunction);

// Existing S3 bucket
const uploadsBucket = s3.Bucket.fromBucketArn(
  this,
  'UploadsBucket',
  'arn:aws:s3:::my-app-uploads'
);
uploadsBucket.grantReadWrite(mainFunction);

// Existing secret
const dbSecret = secretsmanager.Secret.fromSecretCompleteArn(
  this,
  'DBSecret',
  'arn:aws:secretsmanager:us-east-1:123456789012:secret:rds-creds'
);
dbSecret.grantRead(mainFunction);
```

Source: CDK generation in [`internal/providers/aws/cdk_generator.go`](https://github.com/transire/transire/blob/main/internal/providers/aws/cdk_generator.go)

---

## Troubleshooting

### Lambda cannot access RDS

**Check 1:** Is Lambda in same VPC as RDS?
```yaml
vpc:
  subnet_ids:
    - subnet-abc123  # Must be in same VPC as RDS
```

**Check 2:** Do security groups allow connection?

Lambda SG must have outbound rule to RDS SG on port 5432 (PostgreSQL) or 3306 (MySQL).

RDS SG must have inbound rule from Lambda SG on database port.

**Check 3:** Is there a NAT Gateway or VPC endpoint?

Lambda needs internet access for AWS SDK calls. Options:
- NAT Gateway in public subnet
- VPC endpoints for AWS services

### Lambda cannot access AWS services

**Cause:** No NAT Gateway or VPC endpoints.

**Solution:**

**Option 1:** Add NAT Gateway (~$32/month)

**Option 2:** Add VPC endpoints (cheaper for high traffic):
```
- com.amazonaws.region.dynamodb
- com.amazonaws.region.s3
- com.amazonaws.region.secretsmanager
```

### "Access Denied" errors for existing resources

**Cause:** Incorrect ARN or insufficient permissions.

**Check:**
1. Verify ARN is correct (copy from AWS console)
2. Check permissions array includes required access
3. Rebuild and redeploy:
   ```bash
   transire build
   transire deploy
   ```

---

## Best Practices

### VPC

1. **Use private subnets** for Lambda
2. **Use at least 2 subnets** in different AZs for HA
3. **Use VPC endpoints** for AWS services to avoid NAT costs
4. **Monitor ENI creation** to avoid subnet IP exhaustion

### Existing Resources

1. **Use least privilege** permissions:
   ```yaml
   permissions: ["read"]  # Only if write not needed
   ```

2. **Document ARNs** in code comments or README

3. **Use Secrets Manager** for credentials, not environment variables

4. **Test locally** with AWS credentials that have same permissions

---

## Next Steps

- [Environment Variables](environment.md) – Configure env vars
- [Custom CDK Extensions](../guides/custom-cdk.md) – Create new resources
- [transire.yaml Reference](transire-yaml.md) – Complete configuration

---

## See Also

- [Lambda Configuration](lambda.md) – Function settings
- [Deploying to AWS](../guides/deploying-to-aws.md) – Deploy with VPC
- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/)
