from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io import load_json
from .models import SchedulerSpecification
from .scheduler import DependencyScheduler


def _scheduler(args: argparse.Namespace) -> DependencyScheduler:
    specification = SchedulerSpecification.from_dict(load_json(Path(args.specification)))
    return DependencyScheduler(specification, Path(args.state))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PrimeAIExplorer Phase E2 dependency scheduler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("plan", "run", "status", "reset-failed"):
        child = subparsers.add_parser(command)
        child.add_argument("specification")
        child.add_argument("--state", required=True)
        if command == "run":
            child.add_argument("--max-stages", type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    scheduler = _scheduler(args)
    if args.command == "plan":
        result = {
            "pipeline_name": scheduler.specification.name,
            "max_parallel": scheduler.specification.max_parallel,
            "topological_order": scheduler.topological_order(),
            "stages": [stage.to_dict() for stage in scheduler.specification.stages],
        }
    elif args.command == "run":
        result = scheduler.run(max_stages=args.max_stages)
    elif args.command == "status":
        result = scheduler.summary()
    else:
        result = scheduler.reset_failed()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
