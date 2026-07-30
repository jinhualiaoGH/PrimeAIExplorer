# PrimeAIExplorer v0.3.0 Release Notes

## Interactive Workspace

v0.3.0 introduces a single interactive research cockpit that unifies the v0.2.6 workflow.

### New command

- `workspace`

### Workspace actions

- Progress overview and per-window completion
- Next unfinished prompt
- Open `current_response.json`
- Dry-run validation
- Atomic response commit with backup
- Automatic analysis refresh
- Response history
- Open HTML report
- Clean exit

### Automation

- `--commands` runs comma-separated workspace actions non-interactively.
- `--no-auto-refresh` disables automatic analysis after commit.

### Validation

- 18 unit tests pass.
- Workspace commit and analysis refresh are covered by regression tests.
- Existing v0.2.6 commands remain available.
