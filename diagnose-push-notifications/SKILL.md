---
name: diagnose-push-notifications
description: Diagnose why a user isn't receiving push notifications. Use when someone reports missing push notifications, notification delivery failures, or asks to investigate push notification issues for a specific user. Expects user identifiers (userId, memberId, deviceId, or notificationToken) and optionally an environment number.
---

# Push Notification Diagnostic Skill

You are an expert at diagnosing push notification delivery failures in the Dfinitiv mojo-users architecture. This skill walks through a systematic investigation to determine why a specific user isn't receiving push notifications.

## Architecture Overview

Push notifications flow through this pipeline:

```
iOS/Android App registers device token
    -> Token written to DynamoDB: USER#{userId} / NOTIFICATION
    -> CDC triggers notification-inserted or notification-modified Lambda
    -> Lambda creates SNS Platform Endpoint (APNS or FCM)
    -> Lambda subscribes endpoint to broadcast topic + cohort topics
    -> Endpoint ARN and subscription ARNs stored back to DynamoDB
```

**Notification delivery paths:**
- **Targeted** (by userId/memberId/identityId): Look up endpoint ARN from NOTIFICATION record -> SNS PublishCommand to endpoint
- **Cohort**: Publish to cohort's SNS topic -> SNS fans out to all subscribed endpoints
- **Broadcast**: Publish to broadcast SNS topic -> SNS fans out to all subscribed endpoints

**Key DynamoDB records:**
- `USER#{userId} / META` — User profile, identityId, memberId
- `USER#{userId} / NOTIFICATION` — apnsToken, fcmToken, apnsEndpointArn, fcmEndpointArn, broadcast subscription ARNs
- `USER#{userId} / COHORT#{cohortId}` — Cohort membership with apnsSubscriptionArn, fcmSubscriptionArn
- `COHORT#{cohortId} / META` — Cohort metadata with snsTopicArn
- `NOTIFICATION#{taskId} / APNS` — Notification task record with results

## Input

The user will provide some combination of:
- **userId** (UUID)
- **memberId** (e.g., AB123456)
- **deviceId** (UUID)
- **notificationToken** (hex string)
- **Environment** — referenced by number or name. Use this table:

| # | Profile | Customer | Environment |
|---|---|---|---|
| 10 | pegasus-9-read-only | Pegasus | Production |
| 13 | demo-1-read-only | Demo | Development |
| 14 | demo-3-read-only | Demo | Test |
| 15 | demo-9-read-only | Demo | Production |
| 16 | pegasus-1-read-only | Pegasus | Development |
| 17 | pegasus-3-read-only | Pegasus | Test |
| 18 | pegasus-5-read-only | Pegasus | Stage |

If no environment is specified, ask. Authenticate with: `echo "<number>" | sso`

## Diagnostic Procedure

### Step 1: Authenticate and Find the Table

```bash
echo "<env_number>" | sso
```

Then find the mojo-users table:
```bash
aws dynamodb list-tables --query "TableNames[?contains(@, 'users') || contains(@, 'Users')]" --output text --region us-east-1
```

### Step 2: Look Up the User

If you have a **userId**, query directly:
```bash
aws dynamodb get-item --table-name "$TABLE" \
  --key '{"pk": {"S": "USER#<userId>"}, "sk": {"S": "META"}}' \
  --region us-east-1
```

If you only have a **memberId**, find the userId first via GSI:
```bash
aws dynamodb query --table-name "$TABLE" \
  --index-name gsi2 \
  --key-condition-expression "gsi2pk = :pk AND gsi2sk = :sk" \
  --expression-attribute-values '{":pk": {"S": "MEMBER"}, ":sk": {"S": "<memberId>"}}' \
  --region us-east-1
```

Record the userId, identityId, and memberId from META for later steps.

### Step 3: Check the NOTIFICATION Record

```bash
aws dynamodb get-item --table-name "$TABLE" \
  --key '{"pk": {"S": "USER#<userId>"}, "sk": {"S": "NOTIFICATION"}}' \
  --region us-east-1
```

**What to check:**
- Does `apnsToken` / `fcmToken` exist?
- Does `apnsEndpointArn` / `fcmEndpointArn` exist?
- When was it last `updatedAt`?

**If endpoint ARNs are missing:** The token registration flow failed. Check CloudWatch logs for `notification-inserted` or `notification-modified` Lambda.

### Step 4: Validate SNS Endpoints

For each endpoint ARN found in Step 3, verify it exists and is enabled in SNS:

```bash
aws sns get-endpoint-attributes \
  --endpoint-arn "<endpointArn>" \
  --region us-east-1
```

**What to check:**
- Does the endpoint exist? (NotFound = deleted/stale)
- Is `Enabled` = `true`? (false = APNS/FCM reported delivery failure)
- Does `Token` match the token in DynamoDB?
- Does `CustomUserData` contain the correct userId?

**Common findings:**
- **Endpoint doesn't exist**: Token rotated but new endpoint wasn't created. Check `notification-modified` Lambda logs.
- **Enabled = false**: APNS/FCM reported delivery failure. User may have uninstalled the app or disabled notifications.
- **Token mismatch**: Endpoint was created with a different token. May have been taken over by another user.
- **Wrong userId in CustomUserData**: Endpoint was taken over by another user's device.

### Step 5: Diagnose Based on Notification Type

#### For Targeted Notifications (userId/memberId)

Check if there's a recent notification task:
```bash
aws dynamodb get-item --table-name "$TABLE" \
  --key '{"pk": {"S": "NOTIFICATION#<taskId>"}, "sk": {"S": "APNS"}}' \
  --region us-east-1
```

**What to check in the task record:**
- `status` — COMPLETED, FAILED, PROCESSING?
- `results` — Did individual targets succeed or fail?
- `successCount` / `failureCount`
- If `success: true` with a `messageId` but user didn't receive: the issue is downstream of SNS (APNS/FCM delivery or device-side)

**Targeted flow reads from NOTIFICATION record**, so if the endpoint ARN there is valid and enabled, SNS accepted the message. The issue is then Apple/Google-side.

#### For Cohort Notifications

1. **Find the cohort META record:**
```bash
aws dynamodb get-item --table-name "$TABLE" \
  --key '{"pk": {"S": "COHORT#<cohortId>"}, "sk": {"S": "META"}}' \
  --region us-east-1
```
Note the `snsTopicArn`.

2. **Check the user's cohort membership:**
```bash
aws dynamodb get-item --table-name "$TABLE" \
  --key '{"pk": {"S": "USER#<userId>"}, "sk": {"S": "COHORT#<cohortId>"}}' \
  --region us-east-1
```
Note `apnsSubscriptionArn` and `fcmSubscriptionArn`.

3. **List all subscriptions on the cohort topic:**
```bash
aws sns list-subscriptions-by-topic \
  --topic-arn "<snsTopicArn>" \
  --region us-east-1
```

4. **CRITICAL CHECK — Verify the subscription points to the correct endpoint:**

The user's `apnsSubscriptionArn` from their COHORT record maps to one of the subscriptions on the topic. Find that subscription and check which `Endpoint` it points to. **This endpoint must match the user's current `apnsEndpointArn` from their NOTIFICATION record.**

If they don't match, that's the bug. The subscription is pointing to a stale/deleted endpoint.

```bash
# Check which endpoint the subscription points to
aws sns get-endpoint-attributes \
  --endpoint-arn "<endpoint from subscription>" \
  --region us-east-1
```

**Known bug (fixed in PR #796):** When a user's push token rotates, cohort topic subscriptions were not updated to point to the new SNS endpoint. The old subscription remains pointing to a deleted endpoint, causing cohort notifications to silently fail for that user.

#### For Broadcast Notifications

Check `apnsBroadcastSubscriptionArn` / `fcmBroadcastSubscriptionArn` on the NOTIFICATION record, then verify the subscription exists on the broadcast topic.

### Step 6: Check All Endpoints on a Topic (Delivery Audit)

To see exactly how many users received a cohort/broadcast notification, audit every endpoint on the topic:

```bash
aws sns list-subscriptions-by-topic --topic-arn "<topicArn>" --region us-east-1 \
  --query 'Subscriptions[].Endpoint' --output text | tr '\t' '\n' | while read endpoint; do
  result=$(aws sns get-endpoint-attributes --endpoint-arn "$endpoint" --region us-east-1 2>&1)
  if echo "$result" | grep -q "NotFound\|does not exist"; then
    echo "DEAD    $endpoint"
  else
    enabled=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['Attributes']['Enabled'])" 2>/dev/null)
    user_data=$(echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin)['Attributes'].get('CustomUserData','{}'); print(json.loads(d).get('userId','unknown'))" 2>/dev/null)
    echo "${enabled:-?}     $user_data    $endpoint"
  fi
done
```

This shows: alive/dead status, enabled flag, owning userId, and endpoint ARN for every subscription.

### Step 7: Check CloudWatch Logs (if needed)

Relevant log groups follow the pattern `/aws/lambda/Users-mojo-users-events-*`:

| Lambda | Log Group | When to Check |
|---|---|---|
| Token registered (new) | `Users-mojo-users-events-notification-inserted` | Token first written |
| Token changed | `Users-mojo-users-events-notification-modified` | Token rotation |
| Targeted send | `Users-mojo-users-events-process-push-notification-targeted` | Targeted push |
| Cohort send | `Users-mojo-users-events-process-push-notification-cohort` | Cohort push |
| Broadcast send | `Users-mojo-users-events-process-push-notification-broadcast` | Broadcast push |
| Delivery failure | `Users-notifications` / `Users-fcm-notifications` | SNS reports failure |

Use CloudWatch Logs Insights:
```bash
aws logs start-query \
  --log-group-names "<log-group>" \
  --start-time $(date -v-1H +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /<userId or taskId>/ | sort @timestamp desc | limit 50' \
  --region us-east-1

# Then poll for results:
aws logs get-query-results --query-id "<queryId>" --region us-east-1
```

## Common Root Causes

### 1. Stale Cohort Subscription (Most Common)
**Symptom:** User gets targeted and broadcast pushes but NOT cohort pushes.
**Cause:** Token rotated, new SNS endpoint created, but cohort subscription still points to old/deleted endpoint.
**Fix:** PR #796 in mojo-users fixes this going forward. For existing users, cohort subscriptions need to be manually re-created or the user needs to trigger another token change.

### 2. Endpoint Doesn't Exist
**Symptom:** `apnsEndpointArn` in DynamoDB but SNS returns NotFound.
**Cause:** Endpoint was deleted (delivery failure cleanup, or manual deletion) but DynamoDB wasn't updated.
**Fix:** User needs to re-register (reinstall app or force token refresh).

### 3. Endpoint Disabled
**Symptom:** Endpoint exists but `Enabled: false`.
**Cause:** APNS/FCM reported persistent delivery failure (app uninstalled, notifications disabled in OS settings).
**Fix:** User must re-enable notifications in device settings and re-open the app to trigger token refresh.

### 4. SNS Reports Success but Device Doesn't Receive
**Symptom:** Task shows `success: true` with messageId, but notification doesn't appear.
**Cause:** APNS accepted the message but didn't deliver. Could be: Focus mode, DND, app in foreground, stale APNS token (Apple drops silently), or APNS certificate issue.
**Fix:** Check iOS Settings > Notifications > [App]. Check if Focus mode is on. Check if app was in foreground when push was sent.

### 5. Wrong User Owns the Endpoint
**Symptom:** Endpoint exists and is enabled, but `CustomUserData` shows a different userId.
**Cause:** Another user registered with the same device token (e.g., signed into a different account on the same device). The endpoint was "taken over."
**Fix:** The previous user's endpoint reference should have been cleared. If not, this is a bug in the takeover logic in `processTokenChange`.

## Output Format

After completing the investigation, summarize findings in this format:

```
## Push Notification Diagnostic: [User Name / ID]
**Environment:** [env name]
**Date:** [date]

### User Details
- userId: ...
- memberId: ...
- identityId: ...

### Notification Infrastructure Status
| Component | Status | Details |
|---|---|---|
| APNS Token | OK/Missing | ... |
| APNS Endpoint | OK/Dead/Disabled | ARN: ... |
| FCM Token | OK/Missing | ... |
| FCM Endpoint | OK/Dead/Disabled | ARN: ... |
| Broadcast Sub (APNS) | OK/Missing | ... |
| Broadcast Sub (FCM) | OK/Missing | ... |

### Cohort Memberships
| Cohort | APNS Sub | Points to Correct Endpoint? | FCM Sub | Points to Correct Endpoint? |
|---|---|---|---|---|

### Root Cause
[Clear explanation of why notifications aren't being delivered]

### Recommended Fix
[Specific steps to resolve the issue]
```
