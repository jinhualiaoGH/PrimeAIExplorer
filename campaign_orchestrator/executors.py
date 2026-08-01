"""Pluggable execution boundary for D4."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

from benchmark_campaign.models import CampaignWorkItem


@dataclass(frozen=True, slots=True)
class ExecutionOutcome:
    success: bool
    experiment_id: str | None = None
    catalog_record_id: str | None = None
    error_message: str | None = None
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.success and not self.experiment_id:
            raise ValueError(
                "successful outcomes require experiment_id."
            )
        if not self.success and not self.error_message:
            raise ValueError(
                "failed outcomes require error_message."
            )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        if self.metadata is not None:
            result["metadata"] = dict(self.metadata)
        return result


class WorkItemExecutor(Protocol):
    def execute(
        self,
        item: CampaignWorkItem,
    ) -> ExecutionOutcome:
        ...


class DemoExecutor:
    """Deterministic offline executor for validation and demonstrations."""

    def __init__(
        self,
        *,
        fail_ordinals: set[int] | None = None,
    ) -> None:
        self.fail_ordinals = set(fail_ordinals or set())

    def execute(
        self,
        item: CampaignWorkItem,
    ) -> ExecutionOutcome:
        if item.ordinal in self.fail_ordinals:
            return ExecutionOutcome(
                success=False,
                error_message=f"Controlled failure for ordinal {item.ordinal}.",
                metadata={"executor": "demo"},
            )

        return ExecutionOutcome(
            success=True,
            experiment_id=f"EXP-D4-{item.work_item_id[3:]}",
            catalog_record_id=f"XR-D4-{item.work_item_id[3:]}",
            metadata={
                "executor": "demo",
                "provider": item.provider,
                "model": item.model,
            },
        )


class CommandExecutor:
    """
    Execute an external command that reads a work-item JSON file and writes an
    outcome JSON file. The command template may use {input} and {output}.
    """

    def __init__(
        self,
        command_template: str,
        *,
        working_directory: str | Path | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.command_template = command_template
        self.working_directory = (
            Path(working_directory)
            if working_directory is not None
            else None
        )
        self.timeout_seconds = timeout_seconds

    def execute(
        self,
        item: CampaignWorkItem,
    ) -> ExecutionOutcome:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory(prefix="primeaiexplorer_d4_") as temporary:
            root = Path(temporary)
            input_path = root / "work_item.json"
            output_path = root / "outcome.json"

            input_path.write_text(
                json.dumps(
                    item.to_dict(),
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            command = self.command_template.format(
                input=str(input_path),
                output=str(output_path),
            )

            completed = subprocess.run(
                command,
                cwd=self.working_directory,
                shell=True,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )

            if completed.returncode != 0:
                return ExecutionOutcome(
                    success=False,
                    error_message=(
                        completed.stderr.strip()
                        or completed.stdout.strip()
                        or f"Command returned {completed.returncode}."
                    ),
                    metadata={
                        "returncode": completed.returncode,
                        "stdout": completed.stdout,
                        "stderr": completed.stderr,
                    },
                )

            if not output_path.exists():
                return ExecutionOutcome(
                    success=False,
                    error_message="Executor did not create outcome JSON.",
                    metadata={
                        "returncode": completed.returncode,
                        "stdout": completed.stdout,
                        "stderr": completed.stderr,
                    },
                )

            document = json.loads(
                output_path.read_text(encoding="utf-8-sig")
            )
            return ExecutionOutcome(
                success=bool(document["success"]),
                experiment_id=document.get("experiment_id"),
                catalog_record_id=document.get(
                    "catalog_record_id"
                ),
                error_message=document.get("error_message"),
                metadata=document.get("metadata"),
            )
