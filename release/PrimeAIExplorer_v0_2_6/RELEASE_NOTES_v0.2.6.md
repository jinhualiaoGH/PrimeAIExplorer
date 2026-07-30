# PrimeAIExplorer v0.2.6 Release Notes

## Collection workflow

v0.2.6 adds four workflow improvements while preserving the validated v0.2.5 ledger format and atomic commit behavior.

- New `progress` command with a text progress bar and per-window completion.
- New `history` command with optional `--limit`.
- New `resume` command that prints the next prompt and working-file path; `--open-editor` is supported on Windows.
- New `collect --refresh-analysis` option with `--analysis-output`, `--experiment-id`, `--pilot-id`, and `--bins`.
- Fifteen regression and unit tests cover dataset loading, partial ledgers, collection, metrics, progress, history, and resume.
