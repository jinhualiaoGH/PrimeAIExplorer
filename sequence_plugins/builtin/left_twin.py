from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from plugins.left_twin import LeftTwinPlugin as LegacyLeftTwinPlugin
from sequence_plugins.base import (
    DatasetMetadata,
    SequencePlugin,
    sha256_file,
)


class LeftTwinSequencePlugin(SequencePlugin):
    """Adapter over the verified v1.1.1 LeftTwinPlugin class API."""

    plugin_id = "left_twin"
    plugin_version = "1.2.2"
    display_name = "Left Twin Primes"
    supported_representations = ("absolute", "gaps", "combined")

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self._config = dict(config) if config is not None else None

    def configure(
        self,
        config: Mapping[str, Any],
    ) -> "LeftTwinSequencePlugin":
        self._config = dict(config)
        return self

    def _legacy(
        self,
        options: Mapping[str, Any] | None = None,
    ) -> LegacyLeftTwinPlugin:
        config = dict(options) if options is not None else self._config
        if config is None:
            raise ValueError(
                "LeftTwinSequencePlugin requires the complete EXP-000002 "
                "configuration. Pass config to the constructor, call "
                "configure(config), or supply options=config."
            )
        return LegacyLeftTwinPlugin(config)

    def validate_source(
        self,
        source: Path,
        *,
        required_count: int | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = dict(self._legacy(options).validate_source())
        if required_count is not None:
            result["required_count"] = int(required_count)
            result["sufficient"] = (
                int(result["left_twin_count"]) >= int(required_count)
            )
        result["adapter_plugin_id"] = self.plugin_id
        result["adapter_plugin_version"] = self.plugin_version
        return result

    def build_dataset(
        self,
        source: Path,
        destination: Path,
        *,
        count: int,
        options: Mapping[str, Any] | None = None,
    ) -> DatasetMetadata:
        legacy = self._legacy(options)
        configured_count = int(legacy.config["sequence"]["target_count"])
        configured_destination = legacy._dataset_path()

        if count != configured_count:
            raise ValueError(
                f"Requested count {count:,} does not match configured "
                f"EXP-000002 target_count {configured_count:,}."
            )
        if destination.resolve() != configured_destination.resolve():
            raise ValueError(
                "Left Twin dataset destination is controlled by the verified "
                f"EXP-000002 configuration: {configured_destination}"
            )

        built = legacy.build_dataset(overwrite=False)
        validation = legacy.validate_dataset(built)
        return DatasetMetadata(
            plugin_id=self.plugin_id,
            plugin_version=self.plugin_version,
            count=int(validation["count"]),
            dtype=str(validation["dtype"]),
            representation="absolute",
            source=str(source),
            sha256=sha256_file(built),
            minimum=int(validation["first_value"]),
            maximum=int(validation["held_out_target_value"]),
        )

    def load_values(
        self,
        dataset: Path,
        *,
        mmap_mode: str | None = "r",
    ) -> Sequence[int]:
        legacy = self._legacy()
        configured = legacy._dataset_path()
        if dataset.resolve() != configured.resolve():
            raise ValueError(
                "Left Twin dataset path must match the EXP-000002 "
                f"configuration: {configured}"
            )
        return legacy.load_dataset()

    def validate_dataset(
        self,
        dataset: Path,
        *,
        representation: str = "absolute",
    ) -> dict[str, Any]:
        self.validate_representation(representation)
        result = dict(self._legacy().validate_dataset(dataset))
        result.update(
            {
                "plugin_id": self.plugin_id,
                "plugin_version": self.plugin_version,
                "representation": representation,
            }
        )
        return result

    def generate_cases_from_legacy_windows(
        self,
        *,
        endpoints_1_based: Sequence[int],
        window_size: int,
        representation: str,
    ) -> list[dict[str, Any]]:
        legacy = self._legacy()
        return [
            {
                "endpoint_index_1_based": endpoint,
                "window": legacy.make_window(
                    endpoint,
                    window_size,
                    representation,
                ),
            }
            for endpoint in endpoints_1_based
        ]

    def is_structurally_valid(self, value: int) -> bool:
        from plugins.left_twin import is_prime_64

        return is_prime_64(value) and is_prime_64(value + 2)
