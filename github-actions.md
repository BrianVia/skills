# GitHub Actions Skill

Check and monitor GitHub Actions workflow runs using the `gh` CLI.

## Common Commands

### List recent runs
```bash
gh run list --limit 10
```

### Watch a run in progress (live tail)
```bash
gh run watch
```

### View details of a specific run
```bash
gh run view <run-id>
```

### View full logs of a run
```bash
gh run view <run-id> --log
```

### View failed logs only
```bash
gh run view <run-id> --log-failed
```

### Re-run a failed workflow
```bash
gh run rerun <run-id>
```

### Re-run only failed jobs
```bash
gh run rerun <run-id> --failed
```

### Cancel a run in progress
```bash
gh run cancel <run-id>
```

### List workflows
```bash
gh workflow list
```

### Manually trigger a workflow
```bash
gh workflow run <workflow-name>
```

## Usage

When the user asks about GitHub Actions status, run failures, or deployment progress:

1. Use `gh run list` to see recent runs and their status
2. Use `gh run watch` to live-tail an in-progress run
3. Use `gh run view <id> --log-failed` to diagnose failures
4. Offer to re-run failed workflows with `gh run rerun`
