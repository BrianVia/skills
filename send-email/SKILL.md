---
name: send-email
description: Send emails from the server via Resend API. Use when the user asks to "send an email", "email me", "notify via email", or when scripts need email alerts.
---

# Send Email - Resend API

Send emails from this server using the Resend API.

## Quick Usage

**CLI (from bash):**
```bash
~/scripts/email -t "recipient@example.com" -s "Subject" "Email body here"
```

**Python (import in scripts):**
```python
import sys
sys.path.insert(0, '/home/via/scripts')
from email_sender import send_email, send_email_simple

# Simple - returns True/False
send_email_simple("recipient@example.com", "Subject", "Body text")

# Full - returns dict with success, id, error
result = send_email(
    to="recipient@example.com",
    subject="Subject",
    body="Plain text body",
    html="<h1>HTML body</h1>"  # optional
)
```

## CLI Options

```bash
~/scripts/email -t TO -s SUBJECT [options] [body]

Required:
  -t, --to         Recipient email (can repeat for multiple)
  -s, --subject    Email subject line

Optional:
  --from-email     Sender email (default: RESEND_FROM_EMAIL env var)
  --from-name      Sender name (default: RESEND_FROM_NAME env var)
  --html           HTML content (body becomes plain text fallback)
  --reply-to       Reply-to address
  --cc, --bcc      CC/BCC recipients (can repeat)
  -f, --file       Read body from file
  -v, --verbose    Show details
  --dry-run        Preview without sending
```

## Examples

```bash
# Simple alert
~/scripts/email -t "user@example.com" -s "Server Alert" "Disk space low"

# From stdin (great for cron/scripts)
echo "Backup completed at $(date)" | ~/scripts/email -t "admin@example.com" -s "Backup Status"

# With HTML formatting
~/scripts/email -t "user@example.com" -s "Report" \
  --html "<h1>Daily Report</h1><p>All systems operational.</p>" \
  "Daily Report: All systems operational."

# Multiple recipients
~/scripts/email -t "a@example.com" -t "b@example.com" -s "Team Update" "Message"

# Read from file
~/scripts/email -t "user@example.com" -s "Log Report" -f /var/log/summary.txt
```

## Environment Variables

These must be set (in ~/.bashrc or ~/.environment_variables):

```bash
export RESEND_API_KEY="re_xxxxxxxxxxxx"        # Required - from resend.com
export RESEND_FROM_EMAIL="alerts@domain.com"   # Optional - verified domain
export RESEND_FROM_NAME="Server"               # Optional - sender display name
```

## Python Function Reference

```python
send_email(
    to: str | list,           # Recipient(s) - required
    subject: str,             # Subject line - required
    body: str,                # Plain text body - required
    html: str = None,         # HTML body - optional
    from_email: str = None,   # Override env var
    from_name: str = None,    # Override env var
    reply_to: str = None,
    cc: str | list = None,
    bcc: str | list = None,
    api_key: str = None       # Override env var
) -> dict  # {"success": bool, "id": str, "error": str}
```

## Troubleshooting

- **"No API key provided"**: Set RESEND_API_KEY environment variable
- **403 error**: API key invalid or domain not verified in Resend dashboard
- **"from" address rejected**: Use `onboarding@resend.dev` for testing, or verify your domain at resend.com

## Files

- `/home/via/scripts/email-sender.py` - Main Python module
- `/home/via/scripts/email` - Bash wrapper for CLI usage
