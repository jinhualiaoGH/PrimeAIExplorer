# PrimeAIExplorer v1.1.1 Maintenance Release

This package fixes two regressions introduced by v1.1.0:

1. Restores the legacy public function name:

```python
is_probable_prime_64
```

as an alias of:

```python
is_prime_64
```

2. Repairs the synthetic EXP-000002 test fixture so its requested target count
matches the number of left twin primes in the synthetic repository.

The installer also changes its behavior so any failed validation or test stops
the installation immediately. It will never print a successful installation
message after a failed test command.

## Installation

```powershell
cd C:\Downloads\PrimeAIExplorer_v1.1.1_Maintenance

Set-ExecutionPolicy `
    -Scope Process `
    -ExecutionPolicy Bypass

.\scripts\install_v1.1.1.ps1
```

## Expected result

```text
PrimeAIExplorer v1.1.1 validation passed.
...
Ran 81 or more tests
OK

PrimeAIExplorer v1.1.1 installed successfully.
```
