# Sequence Plugin Framework v1.2

## Purpose

The v1.2 framework separates mathematical sequence behavior from experiment
orchestration. Core execution code can work with any plugin that implements
`SequencePlugin`.

## Required plugin metadata

```python
plugin_id: str
plugin_version: str
display_name: str
supported_representations: tuple[str, ...]
```

## Required methods

```python
validate_source(...)
build_dataset(...)
load_values(...)
```

The base class provides default implementations for:

```python
validate_dataset(...)
generate_cases(...)
render_prompt(...)
evaluate_prediction(...)
```

A plugin may override any default when its mathematical contract requires it.

## Index contract

`endpoint` is the zero-based target index. For an endpoint `e` and observation
window `w`, the observed absolute values are:

```text
values[e-w : e]
```

and the target is:

```text
values[e]
```

This makes the target unavailable to the public observation by construction.

## Representations

### absolute

The observation is the sequence values themselves. The target is the next
absolute value.

### gaps

The observation is the consecutive differences inside the absolute window.
The target is:

```text
next_absolute_value - last_observed_absolute_value
```

### combined

The observation contains the absolute values followed by their internal gaps.
The target remains the next absolute value.

## Compatibility

`sequence_plugins.builtin.left_twin.LeftTwinSequencePlugin` is an adapter over
the stable `plugins.left_twin` implementation from v1.1.1. No mathematical
definition, source rule, target count, or EXP-000002 scoring rule is changed.

## Adding a plugin

1. Create a subclass of `SequencePlugin`.
2. Give it a globally unique `plugin_id`.
3. Implement source validation, dataset building, and value loading.
4. Add structural validation where meaningful.
5. Register the module and class in both registry files.
6. Add unit tests.
7. Run the full regression suite.
