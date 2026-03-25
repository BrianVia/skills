---
name: slack
description: Send Slack messages via SlackPipes. Use when the user asks to "send to Slack", "notify on Slack", "post to #channel", or when scripts need Slack notifications.
---

# Slack Messaging - SlackPipes

Send messages to any Slack channel using SlackPipes (slackpipes.com) - one webhook URL that routes to any channel.

## Quick Usage

**IMPORTANT: Always use direct curl for sending messages.** The `~/scripts/slack` bash wrapper has a bug — it silently swallows API errors (pipes to /dev/null, only checks curl exit code) and breaks JSON when messages contain special characters (backticks, quotes, newlines). Use curl directly instead.

**Direct curl (preferred method):**
```bash
curl -X POST \
  https://api.slackpipes.com/webhook/upABXZgJpaCM/general \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello!"}'
```

Replace `general` in the URL path with the target channel name.

**TypeScript/JavaScript:**
```typescript
import { slack, notify } from '~/scripts/slack-notifier';

// Simple message to any channel
await slack.send('general', 'Hello!');
await slack.send('alerts', 'Deployment complete');

// With Block Kit formatting
await slack.send('engineering', {
  text: 'Build passed',
  username: 'CI Bot',
  icon_emoji: ':white_check_mark:',
  blocks: [
    { type: 'header', text: { type: 'plain_text', text: 'Build Status' } },
    { type: 'section', text: { type: 'mrkdwn', text: '*Result:* Passed' } }
  ]
});

// Pre-built notification templates
await notify.ipChange(oldIP, newIP);
await notify.dnsUpdate('example.com', oldIP, newIP);
await notify.error('backup script', 'disk full', 'alerts');
```

**Bash wrapper (unreliable — see note above):**
```bash
~/scripts/slack "Hello world"                    # → #general
~/scripts/slack -c alerts "Server down!"         # → #alerts
echo "Backup done" | ~/scripts/slack -c ops      # pipe support
```

## Channel Routing

SlackPipes supports three routing methods (all equivalent):

```bash
# 1. URL path (preferred)
POST /webhook/{key}/{channel}

# 2. Header
POST /webhook/{key}
X-SlackPipes-Channel: alerts

# 3. Body field
POST /webhook/{key}
{"text": "...", "channel": "alerts"}
```

## Environment Variables

Optional - the key is embedded in scripts but can be overridden:

```bash
export SLACKPIPES_KEY="upABXZgJpaCM"  # Override webhook key
```

## TypeScript API Reference

```typescript
// Main send function
send(
  channel: string,              // Channel name (with or without #)
  message: string | SlackMessage,
  options?: { key?: string }    // Override SlackPipes key
): Promise<boolean>

// Pre-built templates
notify.ipChange(oldIP: string | null, newIP: string, hostname?: string): Promise<boolean>
notify.dnsUpdate(domain: string, oldIP: string | null, newIP: string): Promise<boolean>
notify.error(context: string, error: string, channel?: string): Promise<boolean>

// SlackMessage interface
interface SlackMessage {
  text: string;
  username?: string;
  icon_emoji?: string;
  blocks?: any[];      // Slack Block Kit
  attachments?: any[];
}
```

## Available Channels

Choose the most appropriate channel for the message content. If none fit, suggest creating a new one — but always pick from this list:

- `bookmarks` - Saved links and references
- `general` - General announcements
- `deluge-logs` - Deluge/torrent logging
- `deployments` - Deployment notifications
- `errors` - Error alerts
- `ideas` - Ideas and brainstorming
- `issues-triage` - Issue triage and tracking
- `random` - Off-topic / misc
- `twitter-explorations` - Twitter/X research
- `standup` - Standup updates

## Files

- `/home/via/scripts/slack` - Bash CLI wrapper
- `/home/via/scripts/slack-notifier.ts` - TypeScript module

## Service

- **SlackPipes**: https://slackpipes.com
- One webhook URL routes to any channel
- Built-in rate limiting and retry logic
- Request logging (content never stored)
