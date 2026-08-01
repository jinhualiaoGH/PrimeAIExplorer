# Phase E1 Demonstration

```powershell
py .\examples\phase_e1\build_demo_spec.py
py -m end_to_end_pipeline.cli validate .\examples\phase_e1\pipeline_specification.json
py -m end_to_end_pipeline.cli run .\examples\phase_e1\pipeline_specification.json
```

The demonstration creates deterministic offline response records, analyzes them
with C4, and renders the C5 scientific report through one E1 pipeline command.
Run the command again to verify hash-based resume and idempotence.
