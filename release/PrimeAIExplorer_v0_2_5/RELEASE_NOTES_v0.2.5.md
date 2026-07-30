# PrimeAIExplorer v0.2.5 Release Notes

## Collection Assistant

v0.2.5 introduces an atomic collection workflow for preallocated partial-pilot ledgers. The new `collect` command validates one response, protects the existing ledger with a timestamped backup, fills the next pending entry, and reports collection progress.

Operational files such as `current_response.json` and `pilot_manifest.json` are ignored by response discovery.
