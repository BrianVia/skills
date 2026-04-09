---
name: create-pr
description: Create a pull request with a problem-driven description. Use this skill whenever the user asks to create a PR, open a PR, submit changes for review, or says "let's PR this". Ensures PR descriptions communicate the WHY, not just the WHAT.
argument-hint: "[ticket-id]"
allowed-tools: Bash(git *), Bash(gh *), Bash(prettier *), Bash(npm run lint*), Bash(npm run check*), Bash(r2upload *), Bash(npx playwright screenshot *), Bash(sleep *), AskUserQuestion
---

# Create Pull Request

You are creating a pull request. The #1 failure mode of AI-generated PRs is describing WHAT changed without explaining WHY. Your job is to produce a PR that any engineer can read and understand the problem, the intent, and the approach — without reading the code.

## Phase 1: Gather Context

Run these in parallel to understand the current state:

- `git status`
- `git branch --show-current`
- `git fetch origin`
- `git log --oneline origin/main..HEAD`
- `git diff origin/main...HEAD --stat`
- `git diff origin/main...HEAD` (full diff)

Also extract any Linear ticket references (patterns like ABC-123, DFN-123) from:
- The `$ARGUMENTS` passed to this skill
- Branch name
- Commit messages

If a ticket ID is found, fetch the ticket details using Linear MCP to get the problem context.

## Phase 2: Determine the Problem Statement

This is the most critical step. You MUST identify the **problem** or **motivation** behind these changes. Not what files changed — WHY they changed.

### Sources to check (in priority order):

1. **Linear ticket** — If a ticket ID was found, the ticket description IS the problem statement. Use it.
2. **Conversation context** — Did the user explain what they were trying to do earlier in this session? What bug were they fixing? What feature were they building? What was the trigger?
3. **Branch name** — Does it hint at the intent? (e.g., `fix/race-condition-offer-sync`, `feat/brand-deletion-cdc`)
4. **Commit messages** — Do they collectively tell a story about the problem?
5. **The diff itself** — As a last resort, infer the problem from the code changes. This is the weakest signal.

### If the problem is unclear: ASK.

If after checking all sources you cannot confidently articulate the problem in 1-2 sentences, you MUST use AskUserQuestion:

"I can see what changed, but I want to make sure the PR description captures WHY. What problem does this solve? What triggered this work?"

Do NOT proceed with a vague description. Do NOT fabricate a problem statement. Ask.

**Examples of GOOD problem statements:**
- "Users were seeing duplicate offers when multiple sync operations ran concurrently because we had no distributed locking."
- "The brand deletion CDC handler was silently dropping events when the payload exceeded 64KB, causing orphaned offers to persist."
- "Customer onboarding required manual intervention to set up feature flags. This automates the process."

**Examples of BAD problem statements (the kind AI loves to write — DO NOT do this):**
- "This PR updates the offer sync handler and adds error handling." (WHAT, not WHY)
- "Refactored the CDC event processing pipeline for improved reliability." (Buzzwords, no problem)
- "Added new endpoint for brand management." (So what? What problem does it solve?)

## Phase 3: Pre-flight Checks

Before creating the PR, run the project's quality gates in parallel:

```bash
prettier --write $(git diff --name-only origin/main...HEAD | grep -E '\.(ts|tsx|js|jsx|json)$' | tr '\n' ' ')
npm run lint 2>&1 | tail -20
npm run check 2>&1 | tail -20
```

If lint or type checks fail, attempt to fix. If you can't fix them, inform the user before proceeding.

Stage and commit any formatting changes separately:
```bash
git add -p  # Only formatted files
git commit -m "style: format files"
```

## Phase 4: Construct the PR

### Title
- Under 70 characters
- Communicate intent, not mechanics
- Use conventional prefix when the repo uses them (feat:, fix:, refactor:, etc.)
- Good: "Fix race condition in concurrent offer sync"
- Bad: "Update offer-sync.ts and add lock mechanism"

### Description

Use this exact structure:

```markdown
## Problem

{1-3 sentences explaining the problem or motivation. This is the MOST IMPORTANT section.
What was broken? What was missing? What customer need triggered this?}

## Solution

{Brief explanation of the approach. Focus on key decisions and trade-offs, not a file-by-file changelog.}

## Changes

{Bullet points of NOTABLE changes only — what helps a reviewer understand the PR.
Skip obvious things like "updated imports" or "added types".}

## Testing

{How was this tested? What should a reviewer verify?
- Specific test commands if applicable
- Manual testing steps if applicable
- Edge cases considered}

## Screenshots

{If frontend changes were detected and screenshots captured in Phase 4.5, include them here.
Otherwise, omit this section entirely.}

## Links

{Include if applicable:
- Fixes DFN-XXX (use closing keyword for Linear auto-close)
- Depends on: #XX
- Related: #XX}

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### Linear Integration

If a Linear ticket ID was found, include it with a closing keyword in the description body:
- `Fixes DFN-123` — this auto-closes the issue when the PR merges

## Phase 4.5: Screenshots (Frontend/UI Projects)

If the diff contains frontend files (`.tsx`, `.jsx`, `.css`, `.svelte`, `.vue`, `.html`, or Tailwind changes), capture screenshots of the UI changes and include them in the PR.

### How to capture and host screenshots:

1. **Take a screenshot** of the relevant page using Playwright MCP or browser tools. Save to a known path (Playwright MCP saves to the working directory by default — use the `filename` param to control the name, e.g. `pr-screenshot.png`). The dev server is most likely already running — check with `curl -s -o /dev/null -w "%{http_code}" http://localhost:5173` (or whatever port the project uses) before attempting to start one.
2. **Upload to R2 CDN** using the `r2upload` CLI (uploads to `upload.flatmeadow.com`, files served from `media.brianvia.com`):
   ```bash
   r2upload /path/to/screenshot.png -d pr-screenshots
   ```
   This returns a `https://media.brianvia.com/pr-screenshots/<uuid>.png` URL on stdout.
3. **Verify the URL works** before including it: `curl -s -o /dev/null -w "%{http_code}" <url>` should return 200.
4. **Include the returned URL** in the PR body under a `## Screenshots` section.

### Screenshot section format:

```markdown
## Screenshots

| Before | After |
|--------|-------|
| N/A (new feature) | ![Screenshot](https://media.brianvia.com/pr-screenshots/uuid.png) |
```

If you can only capture the current state (not before/after), use a simpler format:

```markdown
## Screenshots

![Screenshot](https://media.brianvia.com/pr-screenshots/uuid.png)
```

### When to skip screenshots:
- Changes are purely logic/backend with no visual impact
- The project has no runnable frontend (e.g., pure API, CLI tool, library)
- The dev server fails to start — note this in the PR instead of blocking

## Phase 5: Create the PR

1. Verify not on main — create branch if needed
2. Push with upstream tracking: `git push -u origin $(git branch --show-current)`
3. Create PR with gh:

```bash
gh pr create --title "..." --body "$(cat <<'EOF'
...
EOF
)"
```

## Phase 6: Post-creation

After creating the PR:
1. Output the PR URL
2. If this is a **Dfinitiv repository** (org: `dfinitiv`, or repo names like `savvy-*`, `mojo-*`, etc.), proceed to Phase 7.
3. Otherwise, skip to Phase 8.

## Phase 7: Watch for Automated Review Feedback (Dfinitiv repos only)

Dfinitiv repositories have automated code review bots/agents that post feedback on PRs. After creating the PR:

1. **Wait for feedback to arrive:**
   ```bash
   sleep 300  # 5 minutes — gives review bots time to analyze the PR
   ```

2. **Fetch the review feedback:**
   ```bash
   gh pr view --json reviews,comments --jq '.reviews[], .comments[]'
   gh api repos/{owner}/{repo}/pulls/{pr_number}/comments
   ```

3. **Triage the feedback using your best judgement:**
   - **Address** feedback that identifies real bugs, security issues, or meaningful improvements
   - **Skip** feedback that is stylistic noise, overly pedantic, or conflicts with the established patterns in the codebase
   - If you're **unsure** whether feedback is worth addressing, use `AskUserQuestion` to ask the user: "The review bot flagged [X]. This seems [your assessment]. Should I address it or skip it?"

4. **If changes are needed:**
   - Make the fixes
   - Run pre-flight checks again (Phase 3)
   - Commit and push: `git push`
   - Optionally loop back to step 1 if the changes were significant enough to trigger another round of bot feedback (use judgement — one loop max)

5. **Report back** with a summary of what feedback was received and what you did about it.

## Phase 8: Hand Off to Babysit

Unless the user explicitly said not to babysit (e.g., "just create the PR", "no babysit", "skip babysit"), invoke the `/babysit-pr` skill with the PR number to begin monitoring CI and review comments.

Before handing off, tell the user:
> "PR created. Starting babysit-pr to monitor CI and reviews — I'll fix what I can and flag anything I need your help on. Say 'stop' anytime to end monitoring."

If the user opted out, just print the PR URL and you're done.

## Hard Rules

- NEVER create a PR with a description that only lists what files changed
- NEVER skip the problem statement — it is the entire point of this skill
- NEVER push to main directly
- NEVER proceed without a problem statement — ask instead
- ALWAYS run formatter on changed files before creating the PR
- ALWAYS include the Problem section, even for "obvious" changes
- ALWAYS use HEREDOC for the gh pr create --body to preserve formatting
