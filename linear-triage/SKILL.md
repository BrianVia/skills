---
name: linear-triage
description: Analyze a Linear ticket and generate an implementation plan. Use when the user mentions "triage", "analyze ticket", "implementation plan for [ticket ID]", or provides a Linear ticket identifier like "ABC-123" or "DFN-456" and wants analysis.
---

# Linear Triage Skill

Analyze Linear tickets against the Dfinitiv codebase and generate detailed implementation plans.

## When to Use

- User asks to "triage" or "analyze" a Linear ticket
- User provides a ticket ID (e.g., "DFN-123", "ABC-456") and wants an implementation plan
- User says something like "what would it take to implement [ticket]?"

## How to Execute

Run the linear-triage CLI from its directory:

```bash
cd /Users/via/Development/Dfinitiv/linear-triage && bun run triage --ticket "<TICKET_ID>" --context "<OPTIONAL_CONTEXT>"
```

### Parameters

- `--ticket` (required): The Linear ticket identifier (e.g., "DFN-123")
- `--context` (optional): Additional context or thoughts from the developer to guide the analysis

### Examples

```bash
# Basic analysis
cd /Users/via/Development/Dfinitiv/linear-triage && bun run triage --ticket "DFN-123"

# With developer context
cd /Users/via/Development/Dfinitiv/linear-triage && bun run triage --ticket "DFN-123" --context "Focus on the API layer, I think the validation logic needs updating"
```

## What It Does

1. Fetches the ticket details from Linear API
2. Syncs all configured Dfinitiv repositories (if needed)
3. Analyzes the codebase using Claude to determine:
   - Which repositories are involved
   - Which files need to be modified
   - Complexity rating (low/medium/high)
   - Estimated hours
   - Dependencies and blockers
   - Step-by-step implementation plan
4. Saves a markdown plan to `~/dev/triage-workspace/plans/`
5. Outputs a summary

## Output

The skill generates a markdown file at:
```
~/dev/triage-workspace/plans/{TICKET-ID}.md
```

And prints a summary including:
- Complexity rating
- Estimated hours
- Repositories involved
- Number of files to modify
- Any dependencies/blockers

## Requirements

- `LINEAR_API_KEY` environment variable must be set
- Bun runtime installed
- Access to Dfinitiv GitHub repositories

## Workflow

When the user asks to triage a ticket:

1. Extract the ticket ID from their message
2. Ask if they have any additional context to provide (optional)
3. Run the triage command
4. Report the results and where the plan was saved
