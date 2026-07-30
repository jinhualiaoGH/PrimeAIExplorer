"""Built-in sequence plugins.

Modules are intentionally not imported eagerly. Dynamic loading uses the
registry's module and class names, preventing one optional adapter from
blocking unrelated plugins.
"""

__all__ = [
    "integer_sequence",
    "left_twin",
    "prime_gap",
    "prime_square",
    "prime_value",
]
