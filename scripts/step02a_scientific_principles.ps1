# ============================================================
# PrimeAIExplorer v0.2
# Step 2A - Populate Scientific Principles
# ============================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = "C:\PrimeAIExplorer"
$ArchitectureDir = Join-Path $Root "architecture"
$OutputPath = Join-Path $ArchitectureDir "Scientific_Principles.md"

New-Item -ItemType Directory `
    -Path $ArchitectureDir `
    -Force | Out-Null

$ScientificPrinciples = @"
# PrimeAIExplorer Scientific Principles

Version: 0.2.0  
Status: Foundation  
Date: 2026-07-25

---

## 1. Mission

PrimeAIExplorer is a scientific observatory for studying how intelligent
systems learn, represent, compress, generalize, reason, and discover through
controlled and reproducible experiments.

PrimeAIExplorer does not exist merely to rank models.

Its primary objective is to understand observable AI behavior using disciplined
scientific methodology.

---

## 2. Foundational Statement

Artificial intelligence should not only be evaluated by benchmarks.

It should be studied through controlled, reproducible scientific experiments.

Benchmarks may report performance on fixed tasks.

Scientific experiments investigate how behavior changes when selected
conditions and variables change.

PrimeAIExplorer therefore emphasizes explanation, measurement,
reproducibility, and evidence preservation rather than leaderboard position
alone.

---

## 3. Guiding Principle

Make observations first.

Draw conclusions second.

Conclusions must emerge from preserved evidence rather than expectations,
preferences, or selective examples.

---

## 4. Principle 1 - Observe Before Theorizing

Scientific understanding begins with careful observation.

PrimeAIExplorer shall not begin with an assumption that a model is intelligent,
unintelligent, superior, inferior, capable, or incapable.

It shall first define observable behavior and collect evidence under controlled
conditions.

Theories may guide experiment design, but observations must be allowed to
challenge those theories.

---

## 5. Principle 2 - Measure Objectively

Whenever practical, PrimeAIExplorer shall use objective quantitative
measurements.

Examples include:

- exact-match accuracy
- numerical error
- prediction accuracy
- generalization accuracy
- consistency
- abstention rate
- response validity
- latency
- token usage
- compression ratio
- information efficiency

Subjective judgment may be used only when objective measurement is
insufficient.

Any subjective evaluation must use:

- an explicit rubric
- a documented scoring process
- preserved evaluator outputs
- human review where appropriate
- agreement analysis where multiple evaluators are used

---

## 6. Principle 3 - Use Controlled Experiments

Experiments should isolate variables whenever practical.

A controlled experiment must identify:

- independent variables
- dependent variables
- controlled variables
- nuisance variables
- experimental conditions
- comparison groups

Only the intended independent variable should change unless additional changes
are explicitly documented.

When perfect control is impossible, the limitations must be recorded.

---

## 7. Principle 4 - Preserve Reproducibility

Every experiment should be reproducible using the same:

- experiment specification
- dataset version
- prompt version
- model configuration
- execution protocol
- evaluation procedure
- statistical analysis
- software version

A reproducibility record should preserve:

- source-control commit
- Python version
- dependency versions
- operating system
- dataset checksums
- prompt hashes
- model identifier
- connector version
- execution parameters
- timestamps
- evaluator version
- statistics version

Reproducibility does not guarantee identical outputs from nondeterministic
systems, but it must preserve the conditions necessary for meaningful
replication.

---

## 8. Principle 5 - Use Canonical Representations

PrimeAIExplorer shall define canonical representations for:

- experiments
- hypotheses
- datasets
- prompts
- model subjects
- conditions
- runs
- observations
- evaluations
- metrics
- statistical summaries
- reports

Canonical representations reduce ambiguity and allow experiments to be
compared, validated, automated, and preserved over time.

Canonical identifiers shall be permanent and shall not be silently reused.

---

## 9. Principle 6 - Maintain Model Independence

The experimental framework shall remain independent of any specific AI model,
provider, or access method.

Models are scientific subjects.

They are not the architecture of the experiment itself.

The same experiment should be executable, where technically possible, against:

- deterministic local baselines
- open-weight local models
- hosted open models
- commercial API models
- future AI systems

Provider-specific adaptations must be documented and must not silently change
the scientific task.

---

## 10. Principle 7 - Preserve Evidence

Every completed model interaction shall be treated as a scientific observation.

Raw responses shall be preserved.

Failed requests, invalid responses, timeouts, retries, and refusals shall also
be preserved when they are part of the experimental record.

Derived artifacts shall reference their originating observations.

Examples of derived artifacts include:

- parsed responses
- normalized values
- metric scores
- statistical summaries
- tables
- figures
- reports

Raw evidence shall never be overwritten by interpretation.

---

## 11. Principle 8 - Define Evaluation Before Interpretation

Primary metrics and evaluation procedures should be defined before primary
results are interpreted.

This reduces the risk of selecting metrics only because they support a preferred
conclusion.

PrimeAIExplorer shall distinguish:

- primary metrics
- secondary metrics
- exploratory metrics
- confirmatory metrics
- post-hoc analyses

Changes to evaluation procedures must be versioned and documented.

---

## 12. Principle 9 - Distinguish Exploration from Confirmation

Exploratory experiments search for patterns, hypotheses, and unexpected
behavior.

Confirmatory experiments test predefined hypotheses under a locked protocol.

Both forms of research are valuable, but they must not be presented as though
they are the same.

An exploratory result may motivate a confirmatory experiment.

It does not automatically constitute confirmation.

---

## 13. Principle 10 - Make Hypotheses Falsifiable

A scientific hypothesis must permit evidence that could count against it.

For each hypothesis, PrimeAIExplorer should define:

- the expected relationship
- the null hypothesis
- the relevant variables
- the evaluation metric
- the comparison rule
- the conditions under which the hypothesis would not be supported

Experiments should not be designed only to produce confirming examples.

---

## 14. Principle 11 - Report Negative and Null Results

Scientific value does not depend on obtaining a positive result.

PrimeAIExplorer shall preserve and report:

- failed hypotheses
- null effects
- inconsistent results
- model failures
- non-monotonic behavior
- saturation
- regressions
- unexpected outcomes

Negative and null results improve scientific understanding and prevent
unnecessary repetition.

---

## 15. Principle 12 - Avoid Selective Reporting

PrimeAIExplorer shall not:

- report only favorable repetitions
- silently discard failed model responses
- omit inconvenient conditions
- change hypotheses after observing results without disclosure
- compare models using materially different tasks without disclosure
- remove outliers without documented justification
- present exploratory findings as confirmatory evidence

All planned conditions and repetitions should be accounted for.

---

## 16. Principle 13 - Interpret Behavioral Evidence Carefully

PrimeAIExplorer primarily observes external model behavior.

Behavioral observations may support statements such as:

- the model produced a correct answer
- performance changed with context size
- consistency increased
- latency changed
- a pattern generalized to hidden data

Behavioral observations do not, by themselves, prove claims about:

- internal representations
- consciousness
- understanding
- hidden reasoning processes
- training data contents
- causal mechanisms inside the model

Any inference beyond observed behavior must be identified as an inference.

---

## 17. Principle 14 - Practice Scientific Humility

Experimental results describe behavior observed under specific conditions.

They do not necessarily establish universal truths about intelligence.

Every report should identify:

- experimental scope
- tested models
- tested datasets
- tested conditions
- sample size
- known limitations
- uncertainty
- possible confounding factors
- replication status

Independent verification is encouraged.

---

## 18. Principle 15 - Separate Principles from Hypotheses

Scientific principles define how research is conducted.

Examples include:

- reproducibility
- transparency
- evidence preservation
- controlled experimentation

Scientific hypotheses are claims tested by experiments.

Examples include:

- increased useful context improves generalization
- compressed representations improve information efficiency
- abstraction emerges after a measurable threshold

Principles should remain stable.

Hypotheses are expected to evolve, be refined, or be disproven.

---

## 19. Principle 16 - Treat Paid Model Calls as Scientific Resources

Commercial model calls may have financial cost and may depend on changing
external services.

PrimeAIExplorer shall treat paid model access similarly to limited observatory
time.

Before a paid campaign begins:

1. The experiment specification should be reviewed.
2. The dataset should be validated.
3. Prompts should be finalized.
4. Evaluation should be tested.
5. Dry-run mode should pass.
6. Local or deterministic baselines should be executed.
7. Caching and observation preservation should be verified.

Every paid call should contribute to a defined scientific objective.

---

## 20. Principle 17 - Never Repeat Expensive Work Unnecessarily

PrimeAIExplorer should use deterministic cache keys based on relevant scientific
inputs.

A cache key may include:

- experiment version
- dataset checksum
- prompt hash
- model identifier
- connector version
- generation parameters

A reused observation must be marked as cached.

Cached results must remain linked to their original execution record.

Cache reuse improves cost control and reproducibility but must never be hidden.

---

## 21. Principle 18 - Build Infrastructure Before Large Campaigns

PrimeAIExplorer shall prioritize reliable scientific infrastructure before
large-scale model execution.

The preferred progression is:

1. Scientific principles
2. Canonical specifications
3. Reference implementation
4. Validation tests
5. Dry-run execution
6. Deterministic baseline
7. Local model pilot
8. Limited API pilot
9. Comparative campaign
10. Scientific publication

This sequence reduces wasted computation and strengthens the scientific value
of every observation.

---

## 22. Relationship to PrimeNet

PrimeNet provides deterministic mathematical universes.

PrimeAIExplorer provides controlled methodologies for studying intelligent
systems within those universes.

PrimeNet contributes:

- canonical mathematical observations
- exact ground truth
- deterministic datasets
- reproducible construction
- broad observational scale

PrimeAIExplorer contributes:

- canonical experiments
- model-independent execution
- preserved behavioral observations
- objective evaluation
- statistical comparison
- reproducible scientific reports

Together they establish a scientific ecosystem for observing both mathematical
structure and artificial intelligence.

---

## 23. Scientific Workflow

PrimeAIExplorer follows this progression:

Observe

Measure

Validate

Understand

Explain

Discover

Each stage depends on the integrity of the previous stage.

Discovery must not precede evidence.

---

## 24. Intelligence Spectrum

PrimeAIExplorer studies intelligence as a progression of observable
capabilities:

Observation

Memory

Compression

Pattern Discovery

Abstraction

Generalization

Reasoning

Scientific Discovery

Experiments may study one capability or a transition between capabilities.

The spectrum is not assumed to be perfectly linear.

Its purpose is to organize measurable scientific questions.

---

## 25. Experimental Universes

PrimeNet is the first experimental universe supported by PrimeAIExplorer.

Future experimental universes may include:

- symbolic algebra
- graph theory
- cellular automata
- formal logic
- physical simulations
- algorithmic environments

Each universe should provide:

- canonical observations
- deterministic or documented construction
- ground truth where possible
- versioned datasets
- measurable tasks
- reproducible provenance

The observatory architecture should remain independent of any one universe.

---

## 26. Core Scientific Commitments

PrimeAIExplorer commits to:

- observing before claiming
- measuring before ranking
- validating before publishing
- preserving raw evidence
- documenting limitations
- reporting negative results
- distinguishing inference from observation
- enabling independent reproduction
- allowing hypotheses to fail
- revising conclusions when evidence changes

---

## 27. Motto

Observe.

Measure.

Validate.

Understand.

---

## 28. Foundational Principle

Make observations first.

Draw conclusions second.

---

End of Document
"@

Set-Content `
    -Path $OutputPath `
    -Value $ScientificPrinciples `
    -Encoding UTF8

Write-Host ""
Write-Host "============================================================"
Write-Host " PrimeAIExplorer v0.2 - Step 2A"
Write-Host " Scientific Principles"
Write-Host "============================================================"
Write-Host ""

$Failed = $false

if (-not (Test-Path $OutputPath)) {
    Write-Host "[FAIL] Missing file: $OutputPath"
    $Failed = $true
}
else {
    $Item = Get-Item $OutputPath

    if ($Item.Length -le 0) {
        Write-Host "[FAIL] File is empty: $OutputPath"
        $Failed = $true
    }
    else {
        Write-Host "[PASS] $($Item.FullName)"
        Write-Host "       Size: $($Item.Length) bytes"
    }
}

$RequiredPhrases = @(
    "Artificial intelligence should not only be evaluated by benchmarks.",
    "Make observations first.",
    "Draw conclusions second.",
    "Observe Before Theorizing",
    "Preserve Reproducibility",
    "Maintain Model Independence",
    "Preserve Evidence",
    "Practice Scientific Humility",
    "Relationship to PrimeNet"
)

$Content = Get-Content $OutputPath -Raw

foreach ($Phrase in $RequiredPhrases) {
    if ($Content.Contains($Phrase)) {
        Write-Host "[PASS] Found: $Phrase"
    }
    else {
        Write-Host "[FAIL] Missing phrase: $Phrase"
        $Failed = $true
    }
}

$LineCount = (Get-Content $OutputPath).Count

Write-Host ""
Write-Host "Line count: $LineCount"

if ($LineCount -lt 200) {
    Write-Host "[WARN] Scientific principles document is shorter than expected"
}

if ($Failed) {
    Write-Host ""
    Write-Host "STEP 2A FAILED"
    exit 1
}

Write-Host ""
Write-Host "STEP 2A PASSED"