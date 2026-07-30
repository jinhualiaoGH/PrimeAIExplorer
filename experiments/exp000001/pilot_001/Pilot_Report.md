# EXP-000001 Pilot Evaluation Report

Evaluator version: 1.0.0
Generated: 2026-07-26T03:26:31.773674Z

## Scientific Question

How does the visible prime-gap observation window affect prediction, confidence, and observable explanation strategy?

## Pilot Design

- One shared hidden prediction target
- Five observation windows: 4, 8, 16, 32, and 64
- One independent manual ChatGPT conversation per window
- Ground truth withheld during model collection
- No API call or automated model connector

## Objective Results

| Window | Prediction | Truth | Correct | Confidence | Absolute Error | Brier Score | Observable Strategy |
|---:|---:|---:|:---:|---:|---:|---:|---|
| 4 | 6 | 6 | Yes | 18 | 0 | 0.6724 | frequency_and_local_heuristic |
| 8 | 6 | 6 | Yes | 18 | 0 | 0.6724 | frequency_and_local_heuristic |
| 16 | 6 | 6 | Yes | 18 | 0 | 0.6724 | frequency_and_local_heuristic |
| 32 | 6 | 6 | Yes | 100 | 0 | 0.0000 | sequence_recognition_claim |
| 64 | 6 | 6 | Yes | 18 | 0 | 0.6724 | frequency_and_local_heuristic |

## Pilot Summary

- Correct predictions: 5/5
- Accuracy: 100.0%
- Mean absolute error: 0.000
- Mean reported confidence: 34.4
- Confidence range: 18â€“100
- Mean Brier score: 0.5379

## Observable Strategy Counts

- `frequency_and_local_heuristic`: 4
- `sequence_recognition_claim`: 1

## Interpretation Boundary

Strategy labels are rule-based descriptions of the written explanations. They do not reveal or verify the model's private internal reasoning.

Because this pilot contains one shared target and only five responses, it cannot establish a general memory-performance relationship. It validates the experimental workflow and identifies hypotheses for the larger study.

## Provenance

- Cases: `C:\PrimeAIExplorer\datasets\EXP-000001\cases.json`
- Responses: `C:\PrimeAIExplorer\experiments\exp000001\pilot_001\responses.json`
- Experiment: `EXP-000001`
- Evaluator: `1.0.0`

## Guiding Principle

Make observations first. Draw conclusions second.
