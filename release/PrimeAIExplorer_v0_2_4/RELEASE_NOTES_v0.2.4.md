# PrimeAIExplorer v0.2.4 Release Notes

## Pilot Manager

v0.2.4 understands preallocated pilot ledgers. An entry with `response: null` is a valid pending case, not malformed data. Completed responses alone contribute to accuracy, Brier score, ECE, entropy, and explanation metrics.

New commands:

- `pilot-status`: ledger totals, completion percentage, and next case.
- `next-case`: prints the next unfinished prompt.

Reports now distinguish pilot completion from full-dataset coverage.
