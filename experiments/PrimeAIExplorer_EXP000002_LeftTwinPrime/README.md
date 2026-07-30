# PrimeAIExplorer EXP-000002
## Left Twin Prime Continuation

This experiment evaluates whether AI models can predict the next left twin prime from a finite observation window.

A left twin prime is a prime `q` such that `q + 2` is also prime.

Examples:

```text
3, 5, 11, 17, 29, 41, 59, 71, 101, ...
```

The experiment supports three prompt representations:

1. `absolute` — recent left twin primes only.
2. `gaps` — recent gaps between consecutive left twin primes.
3. `combined` — current left twin prime plus recent left-twin-prime gaps.

## Canonical target

For an endpoint index `i`, the model predicts:

```text
ltp(i + 1)
```

where `ltp(i)` is the `i`-th left twin prime.

## PrimeNet source contract

The dataset generator assumes numerically aligned PrimeNet partitions:

```text
prime partition: primes_START_END.npy
gap partition:   corresponding .npy file containing one outgoing gap per stored prime
```

The gap repository uses the left-owned full-mode rule:

```text
gap[j] = prime_after(prime[j]) - prime[j]
```

Therefore:

```text
gap[j] == 2
```

identifies a left twin prime at `prime[j]`.

## Quick start

Edit:

```text
config/experiment_config.json
```

Then run:

```powershell
cd C:\PrimeAIExplorer

py .\experiments\exp000002_left_twin_prime\src\validate_sources.py `
    --config .\experiments\exp000002_left_twin_prime\config\experiment_config.json

py .\experiments\exp000002_left_twin_prime\src\generate_ltp_dataset.py `
    --config .\experiments\exp000002_left_twin_prime\config\experiment_config.json

py .\experiments\exp000002_left_twin_prime\src\validate_ltp_dataset.py `
    --config .\experiments\exp000002_left_twin_prime\config\experiment_config.json

py .\experiments\exp000002_left_twin_prime\src\generate_cases.py `
    --config .\experiments\exp000002_left_twin_prime\config\experiment_config.json

py .\experiments\exp000002_left_twin_prime\src\generate_prompts.py `
    --config .\experiments\exp000002_left_twin_prime\config\experiment_config.json
```

After collecting model responses:

```powershell
py .\experiments\exp000002_left_twin_prime\src\score_responses.py `
    --config .\experiments\exp000002_left_twin_prime\config\experiment_config.json
```

## Response format

Each model must return JSON only:

```json
{
  "prediction": 123456789,
  "confidence": 50,
  "explanation": "Brief explanation."
}
```

For the `combined` representation, the model still returns the predicted next left twin prime in `prediction`.

## Leakage control

Do not give models:

- the hidden target,
- the source index of the target when testing pattern-only continuation,
- answer-key files,
- deterministic primality tools unless running a separate tool-enabled condition.

Use many randomly sampled endpoints, not only index `100000000`.
