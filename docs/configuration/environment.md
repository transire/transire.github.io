# Environment Variables

Configure environment variables for your Transire Lambda functions.

!!! tip "TL;DR"
    Add environment variables in `transire.yaml` under `environment:` key. Use literal values, `${VAR}` for local env vars, or `!Ref` for CloudFormation references. Access via `os.Getenv()` in Go code.

---

## Overview

Environment variables are passed to your Lambda functions and accessible via standard Go `os.Getenv()`. Configure them in `transire.yaml`.

Source: [`pkg/transire/config.go`](https://github.com/transire/transire/blob/main/pkg/transire/config.go)

---

## Configuration Syntax

```yaml
environment:
  # Literal values
  LOG_LEVEL: info
  SERVICE_NAME: my-api

  # From local environment variables
  DATABASE_URL: ${DATABASE_URL}
  API_KEY: ${API_KEY}

  # CloudFormation references (in generated CDK)
  TABLE_NAME: !Ref UsersTable
  BUCKET_NAME: !Ref UploadsBucket
```

Source: Example from [`examples/simple-api/transire.yaml:25-28`](https://github.com/transire/transire/blob/main/examples/simple-api/transire.yaml)

---

## Value Types

### 1. Literal Values

```yaml
environment:
  LOG_LEVEL: debug
  REGION: us-east-1
  MAX_RETRIES: "3"  # Quote numbers to avoid YAML interpretation
```

**Use for:**
- Configuration constants
- Feature flags
- Non-sensitive settings

---

### 2. Local Environment Variables

```yaml
environment:
  DATABASE_URL: ${DATABASE_URL}
  STRIPE_API_KEY: ${STRIPE_API_KEY}
```

**How it works:**
- Transire reads `DATABASE_URL` from your **local** environment during `transire build`
- Value is embedded in CDK-generated Lambda configuration
- Use for secrets that shouldn't be committed to git

**Setting local variables:**

```bash
# In your shell
export DATABASE_URL="postgres://..."
export STRIPE_API_KEY="sk_test_..."

# Then build and deploy
transire build
transire deploy
```

**For CI/CD:**

```yaml
# .github/workflows/deploy.yml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  STRIPE_API_KEY: ${{ secrets.STRIPE_API_KEY }}

steps:
  - name: Build
    run: transire build
```

---

### 3. CloudFormation References

```yaml
environment:
  TABLE_NAME: !Ref UsersTable
  QUEUE_URL: !GetAtt EmailQueue.QueueUrl
```

**Use with CDK extensions:**

```typescript
// extensions/database.ts
export function extendStack(stack: cdk.Stack, functions: Map<string, lambda.Function>) {
  const table = new dynamodb.Table(stack, 'UsersTable', {
    partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
  });

  // Add table name to environment
  const mainFunction = functions.get('main');
  mainFunction.addEnvironment('TABLE_NAME', table.tableName);

  // Grant permissions
  table.grantReadWriteData(mainFunction);
}
```

---

## Using Environment Variables in Code

### Basic Usage

```go
package main

import (
    "log"
    "os"
)

func main() {
    // Read environment variables
    logLevel := os.Getenv("LOG_LEVEL")
    if logLevel == "" {
        logLevel = "info"  // Default
    }

    dbURL := os.Getenv("DATABASE_URL")
    if dbURL == "" {
        log.Fatal("DATABASE_URL not set")
    }

    log.Printf("Starting service with log level: %s", logLevel)
}
```

### With Defaults and Validation

```go
package main

import (
    "fmt"
    "os"
    "strconv"
)

type Config struct {
    LogLevel    string
    DatabaseURL string
    MaxRetries  int
}

func LoadConfig() (*Config, error) {
    cfg := &Config{
        LogLevel:   getEnvOrDefault("LOG_LEVEL", "info"),
        MaxRetries: getEnvAsIntOrDefault("MAX_RETRIES", 3),
    }

    // Required variables
    cfg.DatabaseURL = os.Getenv("DATABASE_URL")
    if cfg.DatabaseURL == "" {
        return nil, fmt.Errorf("DATABASE_URL is required")
    }

    return cfg, nil
}

func getEnvOrDefault(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}

func getEnvAsIntOrDefault(key string, defaultValue int) int {
    if value := os.Getenv(key); value != "" {
        if intVal, err := strconv.Atoi(value); err == nil {
            return intVal
        }
    }
    return defaultValue
}
```

---

## Secrets Management

### Option 1: AWS Secrets Manager (Recommended)

Store secrets in AWS Secrets Manager, grant access via `existing_resources`:

```yaml
# transire.yaml
existing_resources:
  secrets:
    - name: database-credentials
      arn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:db-creds"
      permissions: ["read"]
    - name: api-keys
      arn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:api-keys"
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

type DatabaseCredentials struct {
    Username string `json:"username"`
    Password string `json:"password"`
    Host     string `json:"host"`
    Database string `json:"database"`
}

func GetDatabaseCredentials(ctx context.Context) (*DatabaseCredentials, error) {
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

    var creds DatabaseCredentials
    if err := json.Unmarshal([]byte(*result.SecretString), &creds); err != nil {
        return nil, err
    }

    return &creds, nil
}
```

---

### Option 2: AWS Systems Manager Parameter Store

```yaml
existing_resources:
  parameters:
    - name: /my-api/database-url
      arn: "arn:aws:ssm:us-east-1:123456789012:parameter/my-api/database-url"
      permissions: ["read"]
```

**In code:**

```go
import (
    "context"

    "github.com/aws/aws-sdk-go-v2/config"
    "github.com/aws/aws-sdk-go-v2/service/ssm"
)

func GetParameter(ctx context.Context, name string) (string, error) {
    cfg, err := config.LoadDefaultConfig(ctx)
    if err != nil {
        return "", err
    }

    client := ssm.NewFromConfig(cfg)
    result, err := client.GetParameter(ctx, &ssm.GetParameterInput{
        Name:           aws.String(name),
        WithDecryption: aws.Bool(true),
    })
    if err != nil {
        return "", err
    }

    return *result.Parameter.Value, nil
}
```

---

### Option 3: Environment Variables (Not Recommended for Secrets)

```yaml
environment:
  API_KEY: ${API_KEY}  # From local env during build
```

**Risks:**
- ❌ Secrets visible in CloudFormation console
- ❌ Secrets visible in Lambda console
- ❌ Secrets in deployment artifacts
- ❌ No rotation support

**Better:** Use Secrets Manager or Parameter Store.

---

## Complete Example

```yaml
# transire.yaml
name: my-api

environment:
  # Application settings
  LOG_LEVEL: info
  SERVICE_NAME: my-api
  REGION: us-east-1

  # Feature flags
  ENABLE_CACHING: "true"
  ENABLE_METRICS: "true"

  # Database (from local env)
  DATABASE_URL: ${DATABASE_URL}

  # Secrets Manager ARNs (accessed in code)
  SECRETS_ARN: "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-api"

existing_resources:
  secrets:
    - name: api-credentials
      arn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-api"
      permissions: ["read"]

  dynamodb_tables:
    - name: users-table
      arn: "arn:aws:dynamodb:us-east-1:123456789012:table/users"
      permissions: ["read", "write"]
```

---

## Local Development

### Using `.env` Files

Create a `.env` file (add to `.gitignore`):

```bash
# .env
DATABASE_URL=postgres://localhost:5432/mydb
API_KEY=test_key_123
LOG_LEVEL=debug
```

Load before running:

```bash
# Option 1: Export manually
export $(cat .env | xargs)
transire run

# Option 2: Use direnv
echo 'dotenv' > .envrc
direnv allow
transire run

# Option 3: Use godotenv in code
```

**In code (optional):**

```go
import _ "github.com/joho/godotenv/autoload"  // Auto-loads .env

func main() {
    // DATABASE_URL now available via os.Getenv()
}
```

---

## Per-Function Environment Variables

Different functions can have different environment variables:

```yaml
functions:
  web:
    include:
      - http_handlers: "*"
    environment:
      LOG_LEVEL: info
      MAX_CONNECTIONS: "100"

  background:
    include:
      - queue_handlers: "*"
    environment:
      LOG_LEVEL: debug
      BATCH_SIZE: "50"
```

**Note:** Currently not fully implemented. Use global `environment:` for MVP.

---

## Troubleshooting

### Environment variable not set

**Check 1:** Is it in `transire.yaml`?
```yaml
environment:
  MY_VAR: value
```

**Check 2:** For `${VAR}` syntax, is it set locally?
```bash
echo $MY_VAR
```

**Check 3:** Check Lambda console

AWS Console → Lambda → Functions → Configuration → Environment variables

### Different behavior local vs Lambda

**Cause:** Environment variable set locally but not in Lambda.

**Solution:**
Add to `transire.yaml`:
```yaml
environment:
  MY_VAR: ${MY_VAR}
```

Then rebuild and redeploy:
```bash
transire build
transire deploy
```

---

## Best Practices

1. **Never commit secrets to git**
   - Use `${VAR}` syntax
   - Add `.env` to `.gitignore`

2. **Use Secrets Manager for production**
   - Automatic rotation
   - Audit logging
   - Fine-grained access control

3. **Validate required variables on startup**
   ```go
   func validateConfig() error {
       required := []string{"DATABASE_URL", "API_KEY"}
       for _, key := range required {
           if os.Getenv(key) == "" {
               return fmt.Errorf("%s not set", key)
           }
       }
       return nil
   }
   ```

4. **Use sensible defaults**
   ```go
   logLevel := getEnvOrDefault("LOG_LEVEL", "info")
   ```

5. **Document required variables**
   ```markdown
   # README.md

   ## Required Environment Variables

   - `DATABASE_URL` - PostgreSQL connection string
   - `API_KEY` - Third-party API key
   ```

---

## Next Steps

- [VPC & Existing Resources](vpc-existing.md) – Connect to AWS resources
- [transire.yaml Reference](transire-yaml.md) – Complete configuration reference
- [Deploying to AWS](../guides/deploying-to-aws.md) – Deploy with environment variables

---

## See Also

- [Lambda Configuration](lambda.md) – Function settings
- [Queue Configuration](queues.md) – Queue settings
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
