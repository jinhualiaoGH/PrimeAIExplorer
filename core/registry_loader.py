"""Canonical registry loading and relationship validation."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable


class RegistryError(RuntimeError):
    """Raised when a canonical registry is missing or invalid."""


class RegistryLoader:
    """Load canonical CSV registries from one repository root."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def _load_csv(
        self,
        relative_path: str,
    ) -> list[dict[str, str]]:
        path = self.root / relative_path

        if not path.exists():
            raise RegistryError(
                f"Registry does not exist: {path}"
            )

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as stream:
            rows = list(csv.DictReader(stream))

        if not rows:
            raise RegistryError(
                f"Registry contains no records: {path}"
            )

        return rows

    @staticmethod
    def _index(
        rows: Iterable[dict[str, str]],
        key: str,
    ) -> dict[str, dict[str, str]]:
        index: dict[str, dict[str, str]] = {}

        for row in rows:
            identifier = row.get(key, "").strip()

            if not identifier:
                raise RegistryError(
                    f"Registry record is missing key: {key}"
                )

            if identifier in index:
                raise RegistryError(
                    f"Duplicate registry identifier: {identifier}"
                )

            index[identifier] = row

        return index

    def experiments(self) -> dict[str, dict[str, str]]:
        return self._index(
            self._load_csv(
                "experiments/experiment_registry.csv"
            ),
            "experiment_id",
        )

    def datasets(self) -> dict[str, dict[str, str]]:
        return self._index(
            self._load_csv(
                "datasets/dataset_registry.csv"
            ),
            "dataset_id",
        )

    def prompts(self) -> dict[str, dict[str, str]]:
        return self._index(
            self._load_csv(
                "prompts/prompt_registry.csv"
            ),
            "prompt_id",
        )

    def connectors(self) -> dict[str, dict[str, str]]:
        return self._index(
            self._load_csv(
                "connectors/connector_registry.csv"
            ),
            "connector_id",
        )

    def execution_profiles(
        self,
    ) -> dict[str, dict[str, str]]:
        return self._index(
            self._load_csv(
                "executions/run_registry.csv"
            ),
            "execution_profile_id",
        )

    def validate_selection(
        self,
        *,
        experiment_id: str,
        dataset_id: str,
        prompt_id: str,
        connector_id: str,
        execution_profile_id: str,
        free_mode: bool = True,
    ) -> dict[str, dict[str, str]]:
        experiments = self.experiments()
        datasets = self.datasets()
        prompts = self.prompts()
        connectors = self.connectors()
        profiles = self.execution_profiles()

        try:
            experiment = experiments[experiment_id]
            dataset = datasets[dataset_id]
            prompt = prompts[prompt_id]
            connector = connectors[connector_id]
            profile = profiles[execution_profile_id]
        except KeyError as error:
            raise RegistryError(
                f"Unknown registry identifier: {error.args[0]}"
            ) from error

        if prompt["experiment_id"] != experiment_id:
            raise RegistryError(
                "Prompt does not reference the selected experiment."
            )

        if prompt["dataset_id"] != dataset_id:
            raise RegistryError(
                "Prompt does not reference the selected dataset."
            )

        if profile["connector_id"] != connector_id:
            raise RegistryError(
                "Execution profile does not use the selected connector."
            )

        if connector["status"] != "Active":
            raise RegistryError(
                f"Connector is not active: {connector_id}"
            )

        if profile["status"] != "Active":
            raise RegistryError(
                f"Execution profile is not active: "
                f"{execution_profile_id}"
            )

        if free_mode:
            if connector["external_access"].lower() != "false":
                raise RegistryError(
                    "Free mode prohibits external-access connectors."
                )

            if connector["cost_class"].lower() != "free":
                raise RegistryError(
                    "Free mode prohibits non-free connectors."
                )

            if profile["external_access"].lower() != "false":
                raise RegistryError(
                    "Free mode prohibits external execution profiles."
                )

            if profile["cost_class"].lower() != "free":
                raise RegistryError(
                    "Free mode prohibits paid execution profiles."
                )

        return {
            "experiment": experiment,
            "dataset": dataset,
            "prompt": prompt,
            "connector": connector,
            "execution_profile": profile,
        }


__all__ = [
    "RegistryError",
    "RegistryLoader",
]
