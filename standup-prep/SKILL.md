---
name: standup-prep
description: Prepare daily standup summary by collecting git commits, open GitHub PRs, and Linear ticket activity from the last 24 hours. Use when preparing for standup, daily recap, or checking what was accomplished yesterday.
argument-hint: "[days=1] [--skip-linear] [--skip-gh]"
allowed-tools: Bash(python3 *), Bash(gh *), Bash(curl *), mcp__linear__list_issues, mcp__linear__get_issue, mcp__claude_ai_Linear__list_issues, mcp__claude_ai_Linear__get_issue
---

# Standup Prep

Prepare a standup-ready summary of Brian's work from the past day across three data sources.

## Step 1: Git Commits

Run the git-commits script to scan all Dfinitiv repos (including conductor-workspaces) for local commits:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/git-commits.py ~/Development/Dfinitiv --author "Brian Via" --days ${0:-1}
```

## Step 2: GitHub PRs

Use `gh search prs` to get PRs across all repos globally (no git directory required).

**All open PRs:**

```bash
gh search prs --author @me --state open --limit 30 --json repository,title,number,updatedAt,isDraft,url
```

**Recently closed/merged PRs** (updated in the last ${0:-1} day(s)):

```bash
gh search prs --author @me --state closed --sort updated --limit 15 --json repository,title,number,updatedAt,state
```

Filter the closed PRs to only those updated within the lookback window (${0:-1} day(s)).

## Step 3: Linear Ticket Activity

Use the Linear MCP tools to find Brian's recent activity. Do the following:

1. Call `list_issues` (via Linear MCP) with `assignee: "me"` and `updatedAt: "-P${0:-1}D"` to find issues updated in the lookback window. Look for status transitions (moved to In Progress, In Review, Done, etc.).

2. For any issues found, get the key details: identifier (e.g. STUDIO-325), title, current status, and what changed.

3. If Linear MCP is not available, fall back to running this curl command via Bash:

```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { viewer { assignedIssues(filter: { updatedAt: { gte: \"CUTOFF_DATE\" } }, first: 25, orderBy: updatedAt) { nodes { identifier title state { name } updatedAt priorityLabel labels { nodes { name } } history(first: 5, orderBy: createdAt) { nodes { fromState { name } toState { name } createdAt } } } } } }"
  }' | python3 -c "
import json, sys
data = json.load(sys.stdin)
issues = data.get('data', {}).get('viewer', {}).get('assignedIssues', {}).get('nodes', [])
for issue in issues:
    status = issue.get('state', {}).get('name', '?')
    transitions = []
    for h in issue.get('history', {}).get('nodes', []):
        fr = h.get('fromState', {})
        to = h.get('toState', {})
        if fr and to:
            transitions.append(f'{fr[\"name\"]} -> {to[\"name\"]}')
    trans_str = ', '.join(transitions) if transitions else 'updated'
    print(f'{issue[\"identifier\"]}: {issue[\"title\"]} [{status}] ({trans_str})')
if not issues:
    print('No issues updated recently')
"
```

Replace `CUTOFF_DATE` with the ISO 8601 datetime for ${0:-1} day(s) ago in UTC.

## Step 4: Reconcile and Synthesize

Before producing the summary, reconcile data across all three sources:

- **Commits ↔ PRs**: Match local commits to their PRs by branch name or commit message. Don't list both separately — group them.
- **PRs ↔ Linear**: Match PRs to Linear tickets by ticket ID in the branch name, PR title, or commit messages (patterns like STUDIO-XXX, PLAT-XXX, PUB-XXX).
- **Conductor worktrees**: Commits from `conductor/` prefixed repos are worktree checkouts of the same upstream repos. Deduplicate against the main repo entries if both appear.
- **Merged vs local**: If a PR shows as merged on GitHub but the local repo hasn't fetched, trust the GitHub data.

Then produce a clean standup summary:

### Standup — [Today's Date]

**What I did:**
- [One bullet per logical work item — a commit, its PR, and its Linear ticket for the SAME work belong together on one line]
- [But NEVER combine separate tickets or unrelated PRs onto a single line — each distinct work item gets its own bullet]
- [Include ticket identifiers where applicable, e.g. "STUDIO-324: Allow editing users in staging — PR #42 merged, Done"]

**In progress:**
- [One bullet per open PR or active ticket — never combine multiple on one line]

**Blockers / Notes:**
- [One bullet per item]
- [Leave empty if none]

Keep it concise — this is for a 60-second verbal update at the 9:30 standup. No fluff. Use ticket identifiers (STUDIO-XXX, PLAT-XXX, PUB-XXX) wherever possible. A commit + its PR + its ticket = one bullet. Two separate tickets = two bullets. Never stack unrelated items on one line.
