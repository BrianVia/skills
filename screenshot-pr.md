# Screenshot PR Skill

Take screenshots of the local dev frontend for PR documentation using Chrome DevTools MCP.

## Prerequisites

- Chrome DevTools MCP server must be configured
- Frontend dev server must be running (typically on port 5174)
- Test credentials are in `frontend/tests/helpers/auth.helper.ts`

## Default Configuration

- **Resolution**: 1920x1080
- **Dev Server Port**: 5174
- **Screenshot Path**: `/tmp/`

## Test Credentials

Located in `frontend/tests/helpers/auth.helper.ts`:
- **Super Admin**: `TEST_CREDENTIALS_SUPER_ADMIN_PEGASUS_1`
- **Admin**: `TEST_CREDENTIALS_ADMIN_PEGASUS_1`

## Workflow

When asked to take a screenshot for a PR:

### 1. Resize browser to standard resolution
```
Use mcp__chrome-devtools__resize_page with width: 1920, height: 1080
```

### 2. Navigate to the target page
```
Use mcp__chrome-devtools__navigate_page to go to http://localhost:5174/{route}
```

### 3. Check if login is required
```
Use mcp__chrome-devtools__take_snapshot to check current page state
If on /auth/login, proceed to login
```

### 4. Login with test credentials
```
Use mcp__chrome-devtools__fill_form to fill username and password fields
Use mcp__chrome-devtools__click on the login button
Wait for navigation to complete
```

### 5. Navigate to target page (if redirected after login)
```
Use mcp__chrome-devtools__navigate_page or click sidebar links
```

### 6. Wait for page to load
```
Use mcp__chrome-devtools__wait_for with relevant text
Or use mcp__chrome-devtools__take_snapshot to verify page state
```

### 7. Take screenshot
```
Use mcp__chrome-devtools__take_screenshot with:
- filePath: /tmp/{descriptive-name}.png
```

### 8. Attach to PR
```bash
# Add a comment to the PR with screenshot description
gh pr comment {PR_NUMBER} --body "## Screenshot

Description of what the screenshot shows...

![Screenshot](/tmp/screenshot.png)"
```

Note: GitHub CLI doesn't support direct image uploads. User can drag/drop the saved screenshot into the PR comment on GitHub.

## Example Usage

User: "Take a screenshot of the offers page for PR #288"

1. Resize to 1920x1080
2. Navigate to http://localhost:5174/offers/all
3. Login as super admin if prompted
4. Wait for "Publisher Offers" or relevant content
5. Take screenshot to /tmp/pr-288-offers.png
6. Add comment to PR #288 describing the screenshot
7. Inform user where screenshot is saved for manual upload

## Tips

- Always resize browser first to ensure consistent screenshots
- Use super admin credentials for full access to features
- Take snapshots to verify page state before screenshotting
- Use descriptive filenames including PR number
- Wait for dynamic content to load before capturing
