---
title: "Custom CDK Extensions"
description: "Extend generated infrastructure with custom AWS CDK code"
keywords:
  - cdk
  - custom infrastructure
  - aws resources
  - extensions
  - customization
category: guides
difficulty: advanced
estimated_time: 25 minutes
prerequisites:
  - "CDK knowledge"
  - "TypeScript basics"
related_docs: []
mcp_metadata:
  primary_use_cases:
    - "Adding custom AWS resources"
    - "Modifying generated infrastructure"
    - "Integrating existing resources"
  common_questions:
    - "How do I add custom CDK code?"
    - "How do I modify generated infrastructure?"
    - "Can I add custom AWS resources?"
---

# Custom CDK Extensions

Learn how to extend Transire's generated CDK infrastructure with custom AWS resources and configurations.

!!! tip "TL;DR"
    Add custom CDK TypeScript extensions via `cdk_extensions` in `transire.yaml`. Extensions receive the CDK stack and Lambda functions, allowing you to add databases, caches, monitoring, custom domains, and more.

---

## Overview

Transire generates AWS CDK TypeScript infrastructure in `.transire/cdk/`. You can extend this infrastructure with custom resources:

- **Databases** – RDS, DynamoDB, Aurora
- **Caching** – ElastiCache (Redis, Memcached)
- **Storage** – S3 buckets, EFS file systems
- **Monitoring** – CloudWatch dashboards, alarms, X-Ray
- **Networking** – Custom VPCs, security groups, NAT gateways
- **DNS** – Route53 domains, certificates
- **Secrets** – Secrets Manager, Parameter Store

**Why customize?**
- Add AWS resources not covered by Transire defaults
- Implement organization-specific patterns
- Integrate with existing infrastructure
- Advanced monitoring and alerting
- Custom security configurations

---

## How It Works

### 1. Transire Generates Base CDK

When you run `transire build`, Transire generates:

```
.transire/
├── cdk/
│   ├── bin/
│   │   └── cdk.ts           # CDK app entry point
│   ├── lib/
│   │   └── my-api-dev.ts    # Generated stack
│   ├── cdk.json             # CDK configuration
│   ├── package.json         # Node.js dependencies
│   └── tsconfig.json        # TypeScript config
└── ...
```

**Generated stack includes**:
- Lambda functions (from your Go handlers)
- API Gateway HTTP API (for HTTP handlers)
- SQS queues (for queue handlers)
- EventBridge rules (for schedule handlers)
- IAM roles and policies
- CloudWatch log groups

---

### 2. You Add Extension Files

Create TypeScript files to extend the stack:

**Extension format:**
```typescript
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';

export function extend(
  stack: cdk.Stack,
  functions: Map<string, lambda.Function>
) {
  // Add custom resources here
}
```

**Key parameters:**
- `stack` – The CDK Stack instance
- `functions` – Map of function names to Lambda Function constructs

---

### 3. Register in transire.yaml

Tell Transire about your extensions:

```yaml
name: my-api

cdk_extensions:
  - file: "extensions/database.ts"
  - file: "extensions/monitoring.ts"
```

Paths are relative to project root.

---

### 4. Build and Deploy

```bash
transire build   # Generates CDK + includes extensions
transire deploy  # Deploys extended infrastructure
```

---

## Extension Examples

### Example 1: Add PostgreSQL Database

Create `extensions/database.ts`:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as lambda from 'aws-cdk-lib/aws-lambda';

export function extend(
  stack: cdk.Stack,
  functions: Map<string, lambda.Function>
) {
  // Get or create VPC
  const vpc = new ec2.Vpc(stack, 'Vpc', {
    maxAzs: 2,
    natGateways: 1,
  });

  // Create database
  const db = new rds.DatabaseInstance(stack, 'Database', {
    engine: rds.DatabaseInstanceEngine.postgres({
      version: rds.PostgresEngineVersion.VER_15,
    }),
    instanceType: ec2.InstanceType.of(
      ec2.InstanceClass.T3,
      ec2.InstanceSize.MICRO,
    ),
    vpc: vpc,
    vpcSubnets: {
      subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
    },
    multiAz: false,
    allocatedStorage: 20,
    maxAllocatedStorage: 100,
    databaseName: 'myapp',
    credentials: rds.Credentials.fromGeneratedSecret('postgres'),
  });

  // Grant Lambda access to database
  const mainFunction = functions.get('main');
  if (mainFunction) {
    db.connections.allowFrom(mainFunction, ec2.Port.tcp(5432));
    db.secret?.grantRead(mainFunction);

    // Add database URL to Lambda environment
    mainFunction.addEnvironment('DATABASE_URL',
      `postgres://${db.secret?.secretValueFromJson('username')}:${db.secret?.secretValueFromJson('password')}@${db.dbInstanceEndpointAddress}:${db.dbInstanceEndpointPort}/${db.instanceIdentifier}`
    );
  }

  // Output connection info
  new cdk.CfnOutput(stack, 'DatabaseEndpoint', {
    value: db.dbInstanceEndpointAddress,
  });

  new cdk.CfnOutput(stack, 'DatabaseSecretArn', {
    value: db.secret?.secretArn || '',
  });
}
```

---

### Example 2: Add Redis Cache

Create `extensions/cache.ts`:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as elasticache from 'aws-cdk-lib/aws-elasticache';
import * as lambda from 'aws-cdk-lib/aws-lambda';

export function extend(
  stack: cdk.Stack,
  functions: Map<string, lambda.Function>
) {
  // Assume VPC exists (from database.ts or config)
  const vpc = ec2.Vpc.fromLookup(stack, 'Vpc', {
    isDefault: false,
  });

  // Create security group for Redis
  const redisSg = new ec2.SecurityGroup(stack, 'RedisSG', {
    vpc: vpc,
    description: 'Security group for Redis cluster',
  });

  // Create subnet group
  const subnetGroup = new elasticache.CfnSubnetGroup(stack, 'RedisSubnetGroup', {
    description: 'Subnet group for Redis',
    subnetIds: vpc.privateSubnets.map(subnet => subnet.subnetId),
  });

  // Create Redis cluster
  const redis = new elasticache.CfnCacheCluster(stack, 'RedisCluster', {
    engine: 'redis',
    cacheNodeType: 'cache.t3.micro',
    numCacheNodes: 1,
    vpcSecurityGroupIds: [redisSg.securityGroupId],
    cacheSubnetGroupName: subnetGroup.ref,
  });

  // Grant Lambda access
  const mainFunction = functions.get('main');
  if (mainFunction) {
    redisSg.addIngressRule(
      ec2.Peer.securityGroupId(mainFunction.connections.securityGroups[0].securityGroupId),
      ec2.Port.tcp(6379),
      'Allow Lambda to access Redis'
    );

    // Add Redis URL to Lambda
    mainFunction.addEnvironment('REDIS_URL',
      `redis://${redis.attrRedisEndpointAddress}:${redis.attrRedisEndpointPort}`
    );
  }

  // Output
  new cdk.CfnOutput(stack, 'RedisEndpoint', {
    value: redis.attrRedisEndpointAddress,
  });
}
```

---

### Example 3: Add S3 Bucket

Create `extensions/storage.ts`:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';

export function extend(
  stack: cdk.Stack,
  functions: Map<string, lambda.Function>
) {
  // Create S3 bucket
  const bucket = new s3.Bucket(stack, 'UploadsBucket', {
    bucketName: `${stack.stackName}-uploads`,
    encryption: s3.BucketEncryption.S3_MANAGED,
    blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    versioned: true,
    lifecycleRules: [
      {
        id: 'DeleteOldVersions',
        noncurrentVersionExpiration: cdk.Duration.days(30),
      },
    ],
    cors: [
      {
        allowedMethods: [
          s3.HttpMethods.GET,
          s3.HttpMethods.PUT,
          s3.HttpMethods.POST,
        ],
        allowedOrigins: ['*'],
        allowedHeaders: ['*'],
      },
    ],
  });

  // Grant Lambda read/write access
  const mainFunction = functions.get('main');
  if (mainFunction) {
    bucket.grantReadWrite(mainFunction);

    // Add bucket name to Lambda environment
    mainFunction.addEnvironment('UPLOADS_BUCKET', bucket.bucketName);
  }

  // Output
  new cdk.CfnOutput(stack, 'UploadsBucketName', {
    value: bucket.bucketName,
  });

  new cdk.CfnOutput(stack, 'UploadsBucketArn', {
    value: bucket.bucketArn,
  });
}
```

---

### Example 4: Add CloudWatch Dashboard

Create `extensions/monitoring.ts`:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as lambda from 'aws-cdk-lib/aws-lambda';

export function extend(
  stack: cdk.Stack,
  functions: Map<string, lambda.Function>
) {
  // Create dashboard
  const dashboard = new cloudwatch.Dashboard(stack, 'Dashboard', {
    dashboardName: `${stack.stackName}-metrics`,
  });

  // Add widgets for each Lambda function
  functions.forEach((fn, name) => {
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: `${name} - Invocations`,
        left: [fn.metricInvocations()],
      }),
      new cloudwatch.GraphWidget({
        title: `${name} - Duration`,
        left: [fn.metricDuration()],
      }),
      new cloudwatch.GraphWidget({
        title: `${name} - Errors`,
        left: [fn.metricErrors()],
      }),
    );

    // Add alarms
    const errorAlarm = fn.metricErrors({
      statistic: 'sum',
      period: cdk.Duration.minutes(5),
    }).createAlarm(stack, `${name}ErrorAlarm`, {
      threshold: 10,
      evaluationPeriods: 1,
      alarmDescription: `Alarm when ${name} has more than 10 errors in 5 minutes`,
    });

    const durationAlarm = fn.metricDuration({
      statistic: 'avg',
      period: cdk.Duration.minutes(5),
    }).createAlarm(stack, `${name}DurationAlarm`, {
      threshold: 5000, // 5 seconds
      evaluationPeriods: 2,
      alarmDescription: `Alarm when ${name} average duration exceeds 5s`,
    });
  });

  // Output
  new cdk.CfnOutput(stack, 'DashboardURL', {
    value: `https://console.aws.amazon.com/cloudwatch/home?region=${stack.region}#dashboards:name=${dashboard.dashboardName}`,
  });
}
```

---

### Example 5: Add Custom Domain

Create `extensions/domain.ts`:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as apigatewayv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as certificatemanager from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as route53targets from 'aws-cdk-lib/aws-route53-targets';

export function extend(
  stack: cdk.Stack,
  functions: Map<string, lambda.Function>
) {
  const domainName = 'api.example.com';

  // Look up hosted zone
  const hostedZone = route53.HostedZone.fromLookup(stack, 'HostedZone', {
    domainName: 'example.com',
  });

  // Create certificate
  const certificate = new certificatemanager.Certificate(stack, 'Certificate', {
    domainName: domainName,
    validation: certificatemanager.CertificateValidation.fromDns(hostedZone),
  });

  // Get API Gateway (created by Transire)
  const api = apigatewayv2.HttpApi.fromHttpApiAttributes(stack, 'Api', {
    httpApiId: stack.node.tryGetContext('apiId'),
  });

  // Create custom domain
  const customDomain = new apigatewayv2.DomainName(stack, 'CustomDomain', {
    domainName: domainName,
    certificate: certificate,
  });

  // Map to API
  new apigatewayv2.ApiMapping(stack, 'ApiMapping', {
    api: api,
    domainName: customDomain,
  });

  // Create DNS record
  new route53.ARecord(stack, 'AliasRecord', {
    zone: hostedZone,
    recordName: domainName,
    target: route53.RecordTarget.fromAlias(
      new route53targets.ApiGatewayv2DomainProperties(
        customDomain.regionalDomainName,
        customDomain.regionalHostedZoneId
      )
    ),
  });

  // Output
  new cdk.CfnOutput(stack, 'CustomDomainURL', {
    value: `https://${domainName}`,
  });
}
```

---

## Configuration

Register extensions in `transire.yaml`:

### Basic Configuration

```yaml
name: my-api

cdk_extensions:
  - file: "extensions/database.ts"
```

---

### Multiple Extensions

```yaml
name: my-api

cdk_extensions:
  - file: "extensions/database.ts"
  - file: "extensions/cache.ts"
  - file: "extensions/storage.ts"
  - file: "extensions/monitoring.ts"
```

**Execution order**: Extensions run in the order listed.

---

### Multi-Function Extensions

Access specific functions:

```yaml
name: my-api

functions:
  web:
    include:
      - http_handlers: "*"
  workers:
    include:
      - queue_handlers: "*"

cdk_extensions:
  - file: "extensions/database.ts"  # Grants access to 'web' function only
```

**Extension code:**
```typescript
export function extend(
  stack: cdk.Stack,
  functions: Map<string, lambda.Function>
) {
  // Access specific functions
  const webFunction = functions.get('web');
  const workersFunction = functions.get('workers');

  // Grant different permissions
  if (webFunction) {
    db.grantRead(webFunction);  // Read-only for web
  }
  if (workersFunction) {
    db.grantReadWrite(workersFunction);  // Full access for workers
  }
}
```

---

## Best Practices

### 1. Organize by Resource Type

Create separate files per resource category:

```
extensions/
├── database.ts      # RDS, DynamoDB
├── cache.ts         # ElastiCache
├── storage.ts       # S3, EFS
├── monitoring.ts    # CloudWatch, X-Ray
├── networking.ts    # VPC, security groups
└── domain.ts        # Route53, certificates
```

---

### 2. Use Environment Variables

Pass resource info to Lambda via environment variables:

```typescript
export function extend(
  stack: cdk.Stack,
  functions: Map<string, lambda.Function>
) {
  const bucket = new s3.Bucket(stack, 'Bucket', {});

  functions.forEach((fn) => {
    fn.addEnvironment('BUCKET_NAME', bucket.bucketName);
    fn.addEnvironment('BUCKET_ARN', bucket.bucketArn);
  });
}
```

**Access in Go:**
```go
bucketName := os.Getenv("BUCKET_NAME")
```

---

### 3. Output Important Values

Use CDK outputs for post-deployment info:

```typescript
new cdk.CfnOutput(stack, 'DatabaseEndpoint', {
  value: db.dbInstanceEndpointAddress,
  description: 'PostgreSQL database endpoint',
});

new cdk.CfnOutput(stack, 'BucketName', {
  value: bucket.bucketName,
  exportName: `${stack.stackName}-bucket-name`,
});
```

**View outputs:**
```bash
transire deploy
# Outputs:
# DatabaseEndpoint = mydb.abc123.us-east-1.rds.amazonaws.com
# BucketName = my-api-dev-uploads
```

---

### 4. Grant Minimal IAM Permissions

Follow principle of least privilege:

```typescript
// Bad: Full access
bucket.grantReadWrite(fn);

// Good: Specific permissions
bucket.grantRead(fn);
bucket.grantPut(fn, 'uploads/*');  // Only /uploads prefix
```

---

### 5. Use CDK Context for Configuration

```typescript
export function extend(
  stack: cdk.Stack,
  functions: Map<string, lambda.Function>
) {
  const env = stack.node.tryGetContext('environment') || 'dev';
  const dbInstance = env === 'prod'
    ? ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.SMALL)
    : ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO);

  const db = new rds.DatabaseInstance(stack, 'Database', {
    instanceType: dbInstance,
    // ...
  });
}
```

**Deploy:**
```bash
transire deploy -c environment=prod
```

---

### 6. Tag Resources

```typescript
cdk.Tags.of(stack).add('Project', 'my-api');
cdk.Tags.of(stack).add('Environment', 'production');
cdk.Tags.of(db).add('Type', 'database');
```

---

## Testing Extensions

### 1. Synthesize CloudFormation

Verify generated CloudFormation without deploying:

```bash
transire build
cd .transire/cdk
cdk synth
```

**Output:** CloudFormation template YAML

---

### 2. Deploy to Development

Test in dev environment first:

```bash
transire deploy -c environment=dev
```

---

### 3. Use CDK Diff

See what will change:

```bash
cd .transire/cdk
cdk diff
```

---

## Troubleshooting

### Extension File Not Found

**Problem:** `Error: Cannot find module 'extensions/database.ts'`

**Solutions:**
1. Verify path is relative to project root
2. Check file exists: `ls extensions/database.ts`
3. Ensure extension is registered in `transire.yaml`

---

### TypeScript Compilation Error

**Problem:** `error TS2345: Argument of type 'X' is not assignable to parameter of type 'Y'`

**Solutions:**
1. Check CDK version compatibility: `cdk --version`
2. Verify imports match CDK v2 syntax
3. Run `npm install` in `.transire/cdk/`
4. Check TypeScript version: `npx tsc --version`

---

### Function Not Found

**Problem:** `functions.get('main')` returns undefined

**Solutions:**
1. Check function name matches `transire.yaml` config
2. For multi-function: Use correct function name ('web', 'workers', etc.)
3. Print available functions:
   ```typescript
   console.log('Available functions:', Array.from(functions.keys()));
   ```

---

### Resource Already Exists

**Problem:** `Resource of type 'AWS::EC2::VPC' with identifier 'Vpc' already exists`

**Solutions:**
1. Don't create VPC if it exists:
   ```typescript
   const vpc = ec2.Vpc.fromLookup(stack, 'ExistingVpc', {
     vpcId: 'vpc-abc123',
   });
   ```

2. Use unique construct IDs:
   ```typescript
   const vpc = new ec2.Vpc(stack, 'MyCustomVpc', {});
   ```

---

### IAM Permission Denied

**Problem:** Lambda can't access resource despite `grant*` call

**Solutions:**
1. Verify security group rules (for VPC resources)
2. Check IAM policy was created:
   ```bash
   aws iam get-role-policy --role-name my-api-MainFunctionRole --policy-name <policy>
   ```

3. Test IAM permissions:
   ```bash
   aws iam simulate-principal-policy \
     --policy-source-arn arn:aws:iam::123456789012:role/my-api-MainFunctionRole \
     --action-names s3:GetObject \
     --resource-arns arn:aws:s3:::my-bucket/*
   ```

---

## Advanced Patterns

### Pattern 1: Conditional Resources

Deploy different resources per environment:

```typescript
export function extend(
  stack: cdk.Stack,
  functions: Map<string, lambda.Function>
) {
  const env = stack.node.tryGetContext('environment') || 'dev';

  if (env === 'prod') {
    // Production: Multi-AZ RDS
    const db = new rds.DatabaseInstance(stack, 'Database', {
      multiAz: true,
      backupRetention: cdk.Duration.days(7),
    });
  } else {
    // Development: Single-AZ RDS
    const db = new rds.DatabaseInstance(stack, 'Database', {
      multiAz: false,
      backupRetention: cdk.Duration.days(1),
    });
  }
}
```

---

### Pattern 2: Cross-Stack References

Share resources between stacks:

```typescript
// In extensions/database.ts
const db = new rds.DatabaseInstance(stack, 'Database', {});

// Export for other stacks
new cdk.CfnOutput(stack, 'DatabaseSecretArn', {
  value: db.secret?.secretArn || '',
  exportName: `${stack.stackName}-db-secret`,
});

// In extensions/worker.ts
const dbSecretArn = cdk.Fn.importValue(`${stack.stackName}-db-secret`);
```

---

### Pattern 3: Shared VPC

Reuse VPC across extensions:

```typescript
// extensions/_shared.ts
export function getOrCreateVpc(stack: cdk.Stack): ec2.IVpc {
  // Try to get existing VPC from context
  const existingVpc = stack.node.tryGetContext('vpcId');

  if (existingVpc) {
    return ec2.Vpc.fromLookup(stack, 'Vpc', {
      vpcId: existingVpc,
    });
  }

  // Create new VPC
  return new ec2.Vpc(stack, 'Vpc', {
    maxAzs: 2,
    natGateways: 1,
  });
}

// extensions/database.ts
import { getOrCreateVpc } from './_shared';

export function extend(stack: cdk.Stack, functions: Map<string, lambda.Function>) {
  const vpc = getOrCreateVpc(stack);

  const db = new rds.DatabaseInstance(stack, 'Database', {
    vpc: vpc,
  });
}

// extensions/cache.ts
import { getOrCreateVpc } from './_shared';

export function extend(stack: cdk.Stack, functions: Map<string, lambda.Function>) {
  const vpc = getOrCreateVpc(stack);

  const redis = new elasticache.CfnCacheCluster(stack, 'Redis', {
    // uses same VPC
  });
}
```

---

### Pattern 4: Lambda Layers

Add Lambda layers for shared dependencies:

```typescript
export function extend(
  stack: cdk.Stack,
  functions: Map<string, lambda.Function>
) {
  // Create layer from local directory
  const layer = new lambda.LayerVersion(stack, 'SharedLayer', {
    code: lambda.Code.fromAsset('lambda-layers/shared'),
    compatibleRuntimes: [lambda.Runtime.PROVIDED_AL2023],
    description: 'Shared libraries',
  });

  // Add layer to all functions
  functions.forEach((fn) => {
    fn.addLayers(layer);
  });
}
```

---

## Common Use Cases

### Use Case 1: Serverless Database Stack

Complete database setup with migrations:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as customresources from 'aws-cdk-lib/custom-resources';

export function extend(
  stack: cdk.Stack,
  functions: Map<string, lambda.Function>
) {
  const vpc = new ec2.Vpc(stack, 'Vpc', { maxAzs: 2 });

  // Create database
  const db = new rds.DatabaseInstance(stack, 'Database', {
    engine: rds.DatabaseInstanceEngine.postgres({
      version: rds.PostgresEngineVersion.VER_15,
    }),
    instanceType: ec2.InstanceType.of(
      ec2.InstanceClass.T3,
      ec2.InstanceSize.MICRO
    ),
    vpc: vpc,
    databaseName: 'myapp',
    credentials: rds.Credentials.fromGeneratedSecret('postgres'),
  });

  // Grant access to Lambda
  const mainFunction = functions.get('main');
  if (mainFunction) {
    db.connections.allowFrom(mainFunction, ec2.Port.tcp(5432));
    db.secret?.grantRead(mainFunction);

    // Run migrations on deploy
    const migrationsFunction = new lambda.Function(stack, 'MigrationsFunction', {
      runtime: lambda.Runtime.PROVIDED_AL2023,
      handler: 'bootstrap',
      code: lambda.Code.fromAsset('../migrations'),
      vpc: vpc,
      environment: {
        DATABASE_URL: `postgres://${db.secret?.secretValueFromJson('username')}:${db.secret?.secretValueFromJson('password')}@${db.dbInstanceEndpointAddress}:5432/myapp`,
      },
    });

    db.connections.allowFrom(migrationsFunction, ec2.Port.tcp(5432));

    // Trigger migrations on deploy
    new customresources.AwsCustomResource(stack, 'RunMigrations', {
      onCreate: {
        service: 'Lambda',
        action: 'invoke',
        parameters: {
          FunctionName: migrationsFunction.functionName,
        },
        physicalResourceId: customresources.PhysicalResourceId.of('MigrationsRunner'),
      },
      policy: customresources.AwsCustomResourcePolicy.fromSdkCalls({
        resources: [migrationsFunction.functionArn],
      }),
    });
  }
}
```

---

### Use Case 2: Complete Monitoring Stack

```typescript
import * as cdk from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as lambda from 'aws-cdk-lib/aws-lambda';

export function extend(
  stack: cdk.Stack,
  functions: Map<string, lambda.Function>
) {
  // Create SNS topic for alarms
  const alarmTopic = new sns.Topic(stack, 'AlarmTopic', {
    displayName: 'API Alarms',
  });

  // Subscribe email
  alarmTopic.addSubscription(
    new subscriptions.EmailSubscription('alerts@example.com')
  );

  // Create dashboard
  const dashboard = new cloudwatch.Dashboard(stack, 'Dashboard', {
    dashboardName: `${stack.stackName}-metrics`,
  });

  // Monitor each function
  functions.forEach((fn, name) => {
    // Widgets
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: `${name} - Invocations`,
        left: [fn.metricInvocations()],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: `${name} - Duration`,
        left: [
          fn.metricDuration({ statistic: 'avg' }),
          fn.metricDuration({ statistic: 'p99' }),
        ],
        width: 12,
      })
    );

    // Alarms
    fn.metricErrors().createAlarm(stack, `${name}ErrorAlarm`, {
      threshold: 5,
      evaluationPeriods: 1,
      alarmDescription: `${name} has errors`,
    }).addAlarmAction(new cloudwatchactions.SnsAction(alarmTopic));

    fn.metricThrottles().createAlarm(stack, `${name}ThrottleAlarm`, {
      threshold: 1,
      evaluationPeriods: 1,
      alarmDescription: `${name} is throttled`,
    }).addAlarmAction(new cloudwatchactions.SnsAction(alarmTopic));
  });

  // Output
  new cdk.CfnOutput(stack, 'DashboardURL', {
    value: `https://console.aws.amazon.com/cloudwatch/home?region=${stack.region}#dashboards:name=${dashboard.dashboardName}`,
  });
}
```

---

## Next Steps

- **[Deploying to AWS](deploying-to-aws.md)** – Deploy extended infrastructure
- **[Multi-Function Architecture](multi-function-architecture.md)** – Split handlers across functions
- **[Configuration Reference](../configuration/transire-yaml.md)** – Full transire.yaml options

---

## See Also

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- [CDK TypeScript API Reference](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-construct-library.html)
- [CDK Patterns](https://cdkpatterns.com/)
- [AWS Architecture Blog](https://aws.amazon.com/blogs/architecture/)
