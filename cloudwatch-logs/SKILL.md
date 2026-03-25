---
name: cloudwatch-logs
description: Find and read CloudWatch logs for AWS Lambda functions. Use when the user asks about logs, Lambda errors, debugging Lambda functions, CloudWatch, or mentions "show me logs", "check logs", "recent errors", or any Dfinitiv service logs (savvy-guides, mojo-users, savvy-metadata, mojo-offers, savvy-geo, savvy-media).
---

# CloudWatch Logs Skill

You are an expert at finding and reading CloudWatch log groups for AWS CDK-based Lambda functions in the Dfinitiv architecture using the AWS CLI.

## Dfinitiv Architecture Pattern

**ALL Dfinitiv projects follow the same standardized structure:**

- `{service-name}/lib/routes/` contains endpoint and event definitions
- All stacks extend `SavvyStack` and use `NestedApiStack`/`NestedEventStack`
- CloudWatch log groups follow consistent naming conventions

## Context Understanding

When the user asks about logs for ANY Dfinitiv service (e.g., "savvy-guides", "mojo-users", "savvy-metadata", "mojo-offers", "savvy-geo", "savvy-media"):

1. **Identify the Stack Name**: Extract from the service name using these patterns:
   - "savvy-guides" → "Guides"
   - "mojo-users" → "Users"
   - "savvy-metadata" → "Metadata"
   - "mojo-offers" → "Offers"
   - "savvy-geo" → "Geo"
   - "savvy-media" → "Media"
   - Pattern: Take the service suffix and capitalize it

2. **Locate Route Files**: Check `{service}/lib/routes/` for:
   - `endpoints-internal.ts` - Internal API endpoints (IAM auth)
   - `endpoints-ios.ts` or other API variants - Public/client API endpoints
   - `events.ts` - EventBridge handlers
   - Any other `endpoints-*.ts` files

3. **Parse Lambda Names**: From these files, extract the `name` field from each endpoint/event configuration

## Log Group Naming Convention

CloudWatch log groups follow this pattern:
```
/aws/lambda/{StackName}-{NestedStackId}-{LambdaName}
```

Where:
- **StackName**: Usually a PascalCase version of the service (e.g., "Guides", "Metadata", "Users")
- **NestedStackId**: The CDK nested stack identifier (e.g., "guides-internal", "guides-ios", "events")
- **LambdaName**: The kebab-case name from the route configuration

### Examples Across Different Services:

**savvy-guides:**
- Stack: `Guides`
- Internal endpoint `list-guides` → `/aws/lambda/Guides-guides-internal-list-guides`
- iOS endpoint `get-guides` → `/aws/lambda/Guides-guides-ios-get-guides`
- Event handler `guide-decorate-item-types` → `/aws/lambda/Guides-events-guide-decorate-item-types`
- CDC function → `/aws/lambda/Guides-GuidesTableCDCFn`

**mojo-users:**
- Stack: `Users`
- Internal endpoint `get-user` → `/aws/lambda/Users-users-internal-get-user`
- iOS endpoint `post-user` → `/aws/lambda/Users-users-ios-post-user`
- Event handler `user-created` → `/aws/lambda/Users-events-user-created`

**savvy-metadata:**
- Stack: `Metadata`
- Internal endpoint `get-brand` → `/aws/lambda/Metadata-metadata-internal-get-brand`
- Event handler `brand-updated` → `/aws/lambda/Metadata-events-brand-updated`

**Pattern applies to ALL Dfinitiv services:**
- mojo-offers, savvy-geo, savvy-media, etc. all follow this exact same structure

## AWS CLI Commands

Use the AWS CLI for all CloudWatch Logs operations:

### 1. List Log Groups

```bash
# List all log groups for a service (e.g., Guides)
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/lambda/Guides-" \
  --region us-east-1 \
  --query 'logGroups[].logGroupName' \
  --output text
```

### 2. CloudWatch Logs Insights Query (Recommended for complex queries)

This is a two-step process:

**Step 1: Start the query**
```bash
# Start a Logs Insights query (returns a queryId)
aws logs start-query \
  --log-group-names "/aws/lambda/Guides-guides-internal-list-guides" \
  --start-time $(date -v-1H +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 50' \
  --region us-east-1
```

**Step 2: Get results (poll until status is "Complete")**
```bash
# Get query results using the queryId from step 1
aws logs get-query-results \
  --query-id "YOUR_QUERY_ID" \
  --region us-east-1
```

### 3. Filter Log Events (Simpler, for quick checks)

```bash
# Get recent logs from a specific log group
aws logs filter-log-events \
  --log-group-name "/aws/lambda/Guides-guides-internal-list-guides" \
  --start-time $(date -v-1H +%s)000 \
  --filter-pattern "ERROR" \
  --limit 50 \
  --region us-east-1
```

### 4. Tail Logs (Live streaming)

```bash
# Stream logs in real-time
aws logs tail "/aws/lambda/Guides-guides-internal-list-guides" \
  --follow \
  --region us-east-1
```

## Common Queries

### Recent Errors
```
fields @timestamp, @message
| filter @message like /ERROR/ or @message like /Error/
| sort @timestamp desc
| limit 50
```

### Specific Request by ID
```
fields @timestamp, @message
| filter @message like /REQUEST_ID/
| sort @timestamp desc
```

### Cold Starts
```
fields @timestamp, @message
| filter @message like /INIT_START/
| sort @timestamp desc
| limit 20
```

### Duration/Performance
```
fields @timestamp, @message, @duration
| sort @duration desc
| limit 20
```

### Timeouts
```
fields @timestamp, @message
| filter @message like /Task timed out/
| sort @timestamp desc
| limit 20
```

## Workflow

When asked to read logs for a service:

1. **Quick Discovery**: List log groups with the stack name prefix:
   ```bash
   aws logs describe-log-groups \
     --log-group-name-prefix "/aws/lambda/{StackName}-" \
     --region us-east-1
   ```

2. **Match to Route Files**: Cross-reference discovered log groups with the route configurations to identify which handler each log group corresponds to

3. **Query Logs**: Use Logs Insights for complex queries or filter-log-events for quick checks

4. **Present Results**: Summarize findings, highlighting errors, patterns, or anomalies

## CRITICAL: Avoid Redundant Searches

- **NEVER** scan through files randomly looking for log groups
- **START** with `aws logs describe-log-groups` to see what exists
- **THEN** read route files only if you need to understand what each Lambda does
- The stack name is usually obvious from context or can be derived from the service name

## Region

- Default region is `us-east-1` unless specified otherwise
- Always include `--region us-east-1` in commands
- Check if the user mentions a specific environment (dev/staging/prod) which might have different regions

## Example Workflows

### User: "Show me recent errors in savvy-guides"

```bash
# 1. List all Guides log groups
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/lambda/Guides-" \
  --region us-east-1 \
  --query 'logGroups[].logGroupName' \
  --output text

# 2. Start a query across all groups (can specify multiple --log-group-names)
aws logs start-query \
  --log-group-names "/aws/lambda/Guides-guides-internal-list-guides" "/aws/lambda/Guides-guides-ios-get-guides" \
  --start-time $(date -v-1H +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 50' \
  --region us-east-1

# 3. Get results
aws logs get-query-results --query-id "QUERY_ID" --region us-east-1
```

### User: "What's happening in the list-guides endpoint?"

```bash
# Direct filter for recent activity
aws logs filter-log-events \
  --log-group-name "/aws/lambda/Guides-guides-internal-list-guides" \
  --start-time $(date -v-30M +%s)000 \
  --limit 100 \
  --region us-east-1
```

### User: "Tail the metadata service logs"

```bash
aws logs tail "/aws/lambda/Metadata-metadata-internal-get-brand" \
  --follow \
  --region us-east-1
```

## Time Calculations

For macOS:
- Last hour: `$(date -v-1H +%s)`
- Last 24 hours: `$(date -v-1d +%s)`
- Last 30 minutes: `$(date -v-30M +%s)`

For Linux:
- Last hour: `$(date -d '1 hour ago' +%s)`
- Last 24 hours: `$(date -d '1 day ago' +%s)`
- Last 30 minutes: `$(date -d '30 minutes ago' +%s)`

Note: `filter-log-events` requires milliseconds, so multiply by 1000 or append `000`.

## Key Principle

**This skill works identically for ALL Dfinitiv services** because they all:
- Use the same CDK patterns (SavvyStack, NestedApiStack, NestedEventStack)
- Store route configs in `lib/routes/`
- Follow the same CloudWatch log group naming convention
- Have consistent Lambda naming in their endpoint/event configurations
