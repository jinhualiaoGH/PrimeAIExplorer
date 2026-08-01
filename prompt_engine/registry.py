from __future__ import annotations

from dataclasses import dataclass, field

from kernel.exceptions import ValidationError
from prompt_engine.models import PromptTemplateSpec


@dataclass
class PromptTemplateRegistry:
    _templates: dict[str, PromptTemplateSpec] = field(default_factory=dict)

    def register(self, template: PromptTemplateSpec) -> None:
        if template.template_id in self._templates:
            raise ValidationError(
                f"prompt template is already registered: {template.template_id}"
            )
        self._templates[template.template_id] = template

    def resolve(self, template_id: str) -> PromptTemplateSpec:
        try:
            return self._templates[template_id]
        except KeyError as exc:
            raise ValidationError(
                f"unknown prompt template: {template_id!r}"
            ) from exc

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._templates))
