---
name: tailscale-expose
description: Expose local dev servers publicly via Tailscale Funnel. Use when the user asks to "expose", "share publicly", "make accessible", or "tunnel" a local port or dev server to the internet.
---

# Tailscale Funnel - Expose Local Servers

Expose a local development server publicly via Tailscale Funnel.

## Instructions

1. Check current funnel status:
```bash
tailscale funnel status
```

2. Determine the port to expose:
   - Use the port the user specified, OR
   - Auto-detect running dev servers:
   ```bash
   lsof -i -P -n | grep LISTEN | grep -E ':(5173|3000|8080|4321|5000)\s'
   ```
   - Default to 5173 (Vite) if nothing found

3. Start the funnel:
```bash
tailscale funnel <port>
```

4. Show the user the public URL from the output.

5. Remind them how to stop: `tailscale funnel off`

## Common Ports Reference
- 5173 - Vite
- 3000 - Next.js, Create React App, Express
- 8080 - Generic dev servers
- 4321 - Astro
- 5000 - Flask

## Troubleshooting
If funnel fails with an ACL error, the user needs to enable Funnel in their Tailscale admin console under Access Controls.
