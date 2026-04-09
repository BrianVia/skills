---
name: babysit-pr
description: Monitor a PR until it's mergeable — fix CI failures, address review comments, push fixes, repeat. Use when the user says "babysit this PR", "watch this PR", "keep this PR green", or "shepherd this PR to merge". Runs a built-in poll loop.
argument-hint: "[PR number or URL] [--interval=3m] [--max-cycles=20]"
allowed-tools: Bash(git *), Bash(gh *), Bash(npm run *), Bash(bun run *), Bash(npx *), Bash(prettier *), Bash(sleep *), Bash(curl *), Read, Grep, Glob, Edit, Write, AskUserQuestion
---

# Babysit PR

You are a PR shepherd. Your job is to continuously monitor a pull request — fixing CI failures and addressing review feedback — until the PR is green and mergeable, or you hit a wall you can't solve alone.

## Phase 1: Identify the PR

1. Check `$ARGUMENTS` for a PR number or URL.
2. If no argument was provided, auto-detect from the current branch:
   ```bash
   gh pr view --json number,url,title,headRefName,state --jq '.'
   ```
3. If no PR exists for the current branch, tell the user and stop.

Extract and store:
- PR number
- Repository (owner/repo)
- Head branch name
- PR URL

Print: `Babysitting PR #<number>: <title> (<url>)`

## Phase 2: Parse Options

Defaults:
- **Poll interval**: 3 minutes (`--interval=3m`)
- **Max cycles**: 20 (`--max-cycles=20`)

Override from `$ARGUMENTS` if provided. The interval supports `s`, `m` suffixes (e.g., `30s`, `5m`).

## Phase 3: The Babysit Loop

Repeat until the PR is mergeable or max cycles is reached:

### Step 3.1: Fetch PR State

```bash
gh pr view <number> --json state,mergeable,mergeStateStatus,statusCheckRollup,reviews,comments,reviewRequests,isDraft
```

If the PR is already merged or closed, report and stop.
If the PR is in draft, report and stop — don't babysit drafts unless the user explicitly asked.

### Step 3.2: Check CI Status

```bash
gh pr checks <number> --json name,state,conclusion,description,detailsUrl
```

Categorize each check:
- **Passing**: `conclusion == "SUCCESS"` — nothing to do
- **Pending**: `state == "PENDING"` or `state == "IN_PROGRESS"` — wait for next cycle
- **Failing**: `conclusion == "FAILURE"` or `conclusion == "CANCELLED"` — needs action

If ALL checks are passing, skip to Step 3.3.

If any checks are **failing**:

1. **Read the failure details.** For each failing check:
   ```bash
   gh run view <run-id> --log-failed 2>/dev/null | tail -100
   ```
   If that doesn't work (not a GitHub Actions run), check the `detailsUrl` for clues or read the `description` field.

2. **Diagnose the failure.** Common categories:
   - **Lint/format errors**: Fix them locally, commit, push
   - **Type errors**: Read the relevant files, fix the types, commit, push
   - **Test failures**: Read the failing test + the code under test, fix the root cause, commit, push
   - **Build errors**: Read the error output, fix the issue, commit, push
   - **Flaky/infra failures**: Re-run the check:
     ```bash
     gh run rerun <run-id> --failed
     ```
   - **Unknown/unfixable**: Report to user with full context and ask for help

3. **After fixing**, commit with a descriptive message and push:
   ```bash
   git add <specific-files>
   git commit -m "fix: <what was fixed and why>"
   git push
   ```

4. **Do NOT stack fixes blindly.** After pushing a fix, move to the next cycle and wait for CI to re-run. Don't try to fix multiple unrelated failures in one pass without seeing the new CI results.

### Step 3.3: Check Review Comments

Fetch all review comments and PR comments:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --jq '.[] | {id, user: .user.login, body, path, line: .original_line, created_at, in_reply_to_id}'
gh api repos/{owner}/{repo}/issues/{number}/comments --jq '.[] | {id, user: .user.login, body, created_at}'
gh pr view <number> --json reviews --jq '.reviews[] | {author: .author.login, state, body}'
```

**Ignore:**
- Your own comments (bot comments from the current session)
- Comments you've already addressed in a previous cycle (track by comment ID)
- Review states of `APPROVED` with no body — that's just an approval, not feedback

**For each unaddressed review comment or requested change:**

1. **Read the comment carefully.** Understand what the reviewer is asking.
2. **Read the relevant code** — the file and line range the comment refers to.
3. **Decide: address it or push back.**

   - **Address it**: If the feedback is valid — a real bug, a meaningful improvement, or a reasonable request — make the fix. Then reply to the comment on the PR confirming what you changed:
     ```bash
     gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies -f body="Fixed — <brief explanation of what you did>"
     ```

   - **Push back**: If the feedback is wrong, unnecessary, or conflicts with the established approach, reply to the comment explaining why you're not making the change. Be respectful but direct. Tag the reviewer:
     ```bash
     gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies -f body="@{reviewer} <explanation of why this doesn't need to change>"
     ```

4. **After addressing all comments**, commit fixes and push:
   ```bash
   git add <specific-files>
   git commit -m "fix: address review feedback — <summary>"
   git push
   ```

### Step 3.4: Check Merge Readiness

After handling CI and reviews, assess overall state:

```bash
gh pr view <number> --json mergeStateStatus,reviewDecision,statusCheckRollup
```

- `mergeStateStatus == "CLEAN"` and `reviewDecision == "APPROVED"` → **PR is mergeable.** Report success and stop.
- `mergeStateStatus == "BLOCKED"` — check why (missing approvals, branch protection rules, merge conflicts, etc.)
- Merge conflicts: attempt to resolve:
  ```bash
  git fetch origin main
  git merge origin/main
  ```
  If conflicts arise, read the conflicting files, resolve them sensibly, commit the merge, and push. If the conflicts are too complex or ambiguous, ask the user.

### Step 3.5: Status Report

At the end of each cycle, print a concise status:

```
--- Cycle <N>/<max> ---
CI: <passing/failing/pending> (<details if failing>)
Reviews: <N unaddressed comments / all addressed / no comments>
Merge status: <clean/blocked/conflicts>
Next check in <interval>...
```

### Step 3.6: Sleep

```bash
sleep <interval-in-seconds>
```

Then loop back to Step 3.1.

## Phase 4: Exit Conditions

Stop the loop when ANY of these are true:

1. **PR is mergeable** (CI green + approved + no merge conflicts) → Report success. Do NOT auto-merge — just tell the user it's ready.
2. **PR is merged or closed** → Report and stop.
3. **Max cycles reached** → Report current state and what's still blocking.
4. **Stuck on an unfixable problem** → After 2 failed attempts at the same issue, stop and ask the user for help. Don't spin.
5. **User interrupts** → Stop gracefully.

When exiting, always print a final summary:

```
--- Babysit Complete ---
PR: #<number> (<url>)
Status: <mergeable/blocked/gave-up>
Cycles: <N>
Fixes applied: <list of commits pushed>
Open items: <anything still unresolved>
```

## Hard Rules

- NEVER auto-merge the PR. Your job is to get it to a mergeable state, not to merge it.
- NEVER force-push. Always regular `git push`.
- NEVER dismiss reviews or bypass branch protection.
- NEVER ignore review comments silently — either address them or reply explaining why not.
- NEVER push more than 3 fix commits in a single cycle without re-checking CI. Small, verifiable steps.
- ALWAYS track which comments you've already handled to avoid duplicate work.
- ALWAYS use descriptive commit messages — "fix CI" is not acceptable. Say what you fixed and why.
- ALWAYS ask the user if you're unsure whether to address feedback or push back on it.
- If the same CI check fails 3 times with the same error after your fixes, STOP and escalate to the user.
