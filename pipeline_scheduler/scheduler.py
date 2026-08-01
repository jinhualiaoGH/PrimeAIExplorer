from __future__ import annotations

import subprocess
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from .io import load_json, write_json_atomic
from .models import ScheduledStage, SchedulerSpecification


class SchedulerError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class StageExecution:
    stage_name: str
    return_code: int
    stdout: str
    stderr: str


Executor = Callable[[ScheduledStage], StageExecution]


class DependencyScheduler:
    def __init__(self, specification: SchedulerSpecification, state_path: Path):
        self.specification = specification
        self.state_path = state_path
        self._stage_by_name = {stage.name: stage for stage in specification.stages}
        self._validate_graph()

    def _validate_graph(self) -> None:
        if len(self._stage_by_name) != len(self.specification.stages):
            raise SchedulerError("duplicate stage names are not allowed")
        names = set(self._stage_by_name)
        for stage in self.specification.stages:
            missing = sorted(set(stage.depends_on) - names)
            if missing:
                raise SchedulerError(f"stage {stage.name!r} has missing dependencies: {missing}")
            if stage.name in stage.depends_on:
                raise SchedulerError(f"stage {stage.name!r} cannot depend on itself")
        self.topological_order()

    def topological_order(self) -> list[str]:
        indegree = {name: 0 for name in self._stage_by_name}
        children: dict[str, list[str]] = {name: [] for name in self._stage_by_name}
        for stage in self.specification.stages:
            indegree[stage.name] = len(stage.depends_on)
            for dependency in stage.depends_on:
                children[dependency].append(stage.name)
        ready = deque(sorted(name for name, value in indegree.items() if value == 0))
        result: list[str] = []
        while ready:
            current = ready.popleft()
            result.append(current)
            for child in sorted(children[current]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
        if len(result) != len(self._stage_by_name):
            raise SchedulerError("dependency cycle detected")
        return result

    def _new_state(self) -> dict:
        return {
            "schema_version": "1.0",
            "pipeline_name": self.specification.name,
            "created_at_utc": utc_now(),
            "updated_at_utc": utc_now(),
            "status": "pending",
            "stages": {
                stage.name: {
                    "status": "pending",
                    "attempts": 0,
                    "return_code": None,
                    "started_at_utc": None,
                    "completed_at_utc": None,
                    "stdout": "",
                    "stderr": "",
                }
                for stage in self.specification.stages
            },
        }

    def load_state(self) -> dict:
        return load_json(self.state_path) if self.state_path.exists() else self._new_state()

    def save_state(self, state: dict) -> None:
        state["updated_at_utc"] = utc_now()
        write_json_atomic(self.state_path, state)

    def reset_failed(self) -> dict:
        state = self.load_state()
        reset_count = 0
        for record in state["stages"].values():
            if record["status"] in {"failed", "blocked"}:
                record.update(
                    status="pending",
                    return_code=None,
                    started_at_utc=None,
                    completed_at_utc=None,
                    stdout="",
                    stderr="",
                )
                reset_count += 1
        state["status"] = "pending"
        self.save_state(state)
        return {"reset_count": reset_count, "state_path": str(self.state_path)}

    def ready_stage_names(self, state: dict) -> list[str]:
        ready: list[str] = []
        for name in self.topological_order():
            record = state["stages"][name]
            if record["status"] != "pending":
                continue
            stage = self._stage_by_name[name]
            dependency_records = [state["stages"][item] for item in stage.depends_on]
            if any(item["status"] in {"failed", "blocked"} for item in dependency_records):
                record["status"] = "blocked"
                continue
            if all(item["status"] in {"completed", "skipped"} for item in dependency_records):
                ready.append(name)
        return ready

    def run(self, executor: Executor | None = None, max_stages: int | None = None) -> dict:
        executor = executor or subprocess_executor
        state = self.load_state()
        state["status"] = "running"
        self.save_state(state)
        executed = 0
        while True:
            ready = self.ready_stage_names(state)
            if not ready:
                break
            for name in ready[: self.specification.max_parallel]:
                if max_stages is not None and executed >= max_stages:
                    state["status"] = "paused"
                    self.save_state(state)
                    return self.summary(state)
                stage = self._stage_by_name[name]
                record = state["stages"][name]
                record["status"] = "running"
                record["attempts"] += 1
                record["started_at_utc"] = utc_now()
                self.save_state(state)
                result = executor(stage)
                record["return_code"] = result.return_code
                record["stdout"] = result.stdout
                record["stderr"] = result.stderr
                record["completed_at_utc"] = utc_now()
                record["status"] = "completed" if result.return_code == 0 else "failed"
                executed += 1
                self.save_state(state)
                if result.return_code != 0 and not stage.continue_on_failure:
                    self.ready_stage_names(state)
                    state["status"] = "failed"
                    self.save_state(state)
                    return self.summary(state)
        statuses = {item["status"] for item in state["stages"].values()}
        if statuses <= {"completed", "skipped"}:
            state["status"] = "completed"
        elif "failed" in statuses or "blocked" in statuses:
            state["status"] = "failed"
        else:
            state["status"] = "paused"
        self.save_state(state)
        return self.summary(state)

    def summary(self, state: dict | None = None) -> dict:
        state = state or self.load_state()
        counts: dict[str, int] = {}
        for item in state["stages"].values():
            counts[item["status"]] = counts.get(item["status"], 0) + 1
        return {
            "pipeline_name": state["pipeline_name"],
            "status": state["status"],
            "stage_count": len(state["stages"]),
            "counts": dict(sorted(counts.items())),
            "state_path": str(self.state_path),
            "topological_order": self.topological_order(),
        }


def subprocess_executor(stage: ScheduledStage) -> StageExecution:
    completed = subprocess.run(
        list(stage.command),
        check=False,
        capture_output=True,
        text=True,
    )
    return StageExecution(
        stage_name=stage.name,
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
