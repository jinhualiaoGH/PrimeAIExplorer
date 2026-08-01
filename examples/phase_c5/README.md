# Phase C5 Example

First generate a C4 analysis bundle:

```powershell
py -m metrics_engine.cli compare `
    --model model-a=.\examples\phase_c4\model_a_responses.jsonl `
    --model model-b=.\examples\phase_c4\model_b_responses.jsonl `
    --output .\analysis\phase_c4_demo
```

Then generate the C5 report:

```powershell
py -m report_engine.cli `
    .\analysis\phase_c4_demo `
    --output .\reports\phase_c5_demo `
    --experiment-label phase-c4-demo `
    --title "PrimeAIExplorer Phase C5 Demonstration"
```
