from __future__ import annotations

from importlib import import_module
from pathlib import Path

from .base import SequencePlugin
from .registry import PluginRecord, load_csv, load_json


class PluginRegistry:
    def __init__(self, records: list[PluginRecord]) -> None:
        self._records = {record.plugin_id: record for record in records}

    @classmethod
    def from_path(cls, path: Path) -> "PluginRegistry":
        suffix = path.suffix.casefold()
        if suffix == ".csv":
            records = load_csv(path)
        elif suffix == ".json":
            records = load_json(path)
        else:
            raise ValueError(
                f"Unsupported plugin registry extension: {path.suffix}"
            )
        return cls(records)

    def identifiers(self, *, active_only: bool = False) -> tuple[str, ...]:
        records = self._records.values()
        if active_only:
            records = (record for record in records if record.active)
        return tuple(sorted(record.plugin_id for record in records))

    def get(self, plugin_id: str) -> PluginRecord:
        try:
            return self._records[plugin_id]
        except KeyError as exc:
            raise KeyError(f"Unknown sequence plugin: {plugin_id}") from exc

    def create(
        self,
        plugin_id: str,
        *,
        allow_inactive: bool = False,
    ) -> SequencePlugin:
        record = self.get(plugin_id)
        if not record.active and not allow_inactive:
            raise ValueError(
                f"Sequence plugin {plugin_id} is not active "
                f"(status={record.status})."
            )

        module = import_module(record.module)
        plugin_type = getattr(module, record.class_name)
        plugin = plugin_type()

        if not isinstance(plugin, SequencePlugin):
            raise TypeError(
                f"{record.module}.{record.class_name} does not implement "
                "SequencePlugin."
            )
        if plugin.plugin_id != record.plugin_id:
            raise ValueError(
                f"Registry ID {record.plugin_id!r} does not match plugin ID "
                f"{plugin.plugin_id!r}."
            )
        return plugin


def load_plugin(
    plugin_id: str,
    registry_path: Path,
    *,
    allow_inactive: bool = False,
) -> SequencePlugin:
    return PluginRegistry.from_path(registry_path).create(
        plugin_id,
        allow_inactive=allow_inactive,
    )
