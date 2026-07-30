# PrimeAIExplorer v0.3.1

Interactive Workspace usability maintenance release.

## Improvements

- Accepts `4`, `4)`, `4.`, `(4)`, `[4]`, and similar menu input.
- Accepts case-insensitive command names and aliases.
- Uses `Selection (1-9 or command):` as the interactive prompt.
- Avoids redrawing the full workspace header after read-only actions.
- Redraws status after commit and analysis refresh.
- Adds optional arrow-key history through `prompt-toolkit`.
- Falls back cleanly to built-in input when the optional dependency is absent.
- Adds regression tests for numeric punctuation and command-name normalization.
