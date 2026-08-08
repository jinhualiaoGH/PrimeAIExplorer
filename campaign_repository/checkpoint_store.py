from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from kernel.exceptions import ValidationError
from .checkpoint_contracts import CampaignCheckpoint


def _canonical_json_bytes(value) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


class CampaignCheckpointStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.checkpoints_root = self.root / "checkpoints"
        self.latest_root = self.root / "latest"

    def initialize(self) -> None:
        self.checkpoints_root.mkdir(parents=True, exist_ok=True)
        self.latest_root.mkdir(parents=True, exist_ok=True)

    def checkpoint_path(self, checkpoint: CampaignCheckpoint) -> Path:
        return (
            self.checkpoints_root
            / checkpoint.campaign_id
            / checkpoint.experiment_id
            / f"{checkpoint.checkpoint_sequence:012d}-{checkpoint.checkpoint_sha256}.json"
        )

    def latest_pointer_path(self, *, campaign_id: str, experiment_id: str) -> Path:
        return self.latest_root / campaign_id / f"{experiment_id}.json"

    def write(self, checkpoint: CampaignCheckpoint, *, publish_latest: bool = True) -> str:
        if not isinstance(checkpoint, CampaignCheckpoint):
            raise ValidationError("checkpoint must be CampaignCheckpoint.")
        self.initialize()
        path = self.checkpoint_path(checkpoint)
        self._write_immutable(path, _canonical_json_bytes(checkpoint.to_dict()))

        if publish_latest:
            pointer = {
                "schema_version": "i3.0",
                "campaign_id": checkpoint.campaign_id,
                "experiment_id": checkpoint.experiment_id,
                "checkpoint_id": checkpoint.checkpoint_id,
                "checkpoint_sequence": checkpoint.checkpoint_sequence,
                "checkpoint_sha256": checkpoint.checkpoint_sha256,
                "checkpoint_path": str(path.relative_to(self.root)).replace("\\", "/"),
            }
            self._write_replaceable(
                self.latest_pointer_path(
                    campaign_id=checkpoint.campaign_id,
                    experiment_id=checkpoint.experiment_id,
                ),
                _canonical_json_bytes(pointer),
            )
        return str(path.relative_to(self.root)).replace("\\", "/")

    def read(self, path: str | Path) -> dict:
        path = Path(path)
        if not path.is_absolute():
            path = self.root / path
        if not path.is_file():
            raise FileNotFoundError(path)
        return json.loads(path.read_text(encoding="utf-8"))

    def read_latest(self, *, campaign_id: str, experiment_id: str) -> dict:
        pointer_path = self.latest_pointer_path(
            campaign_id=campaign_id,
            experiment_id=experiment_id,
        )
        if not pointer_path.is_file():
            raise FileNotFoundError(pointer_path)
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        checkpoint_path = self.root / pointer["checkpoint_path"]
        if not checkpoint_path.is_file():
            raise FileNotFoundError(checkpoint_path)
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("checkpoint_sha256") != pointer.get("checkpoint_sha256"):
            raise ValidationError("latest pointer/checkpoint SHA-256 mismatch.")
        return checkpoint

    def list_checkpoint_files(self, *, campaign_id: str, experiment_id: str) -> tuple[Path, ...]:
        root = self.checkpoints_root / campaign_id / experiment_id
        if not root.is_dir():
            return ()
        return tuple(sorted(root.glob("*.json")))

    @staticmethod
    def _write_immutable(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() == data:
                return
            raise ValidationError(
                f"immutable checkpoint path already exists with different content: {path}"
            )
        fd, temp_name = tempfile.mkstemp(
            prefix=path.name + ".",
            suffix=".tmp",
            dir=str(path.parent),
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    @staticmethod
    def _write_replaceable(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=path.name + ".",
            suffix=".tmp",
            dir=str(path.parent),
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
