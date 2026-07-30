from __future__ import annotations

import argparse
import json
import sys

from core.cases import generate_cases
from core.config import load_config
from core.prompts import generate_prompts
from core.registry import available_plugins, create_plugin
from core.scoring import score_responses


def main() -> int:
    parser = argparse.ArgumentParser(description="PrimeAIExplorer v0.2 experiment runner.")
    sub = parser.add_subparsers(dest="command", required=True)

    for command in ("validate", "build-dataset", "generate-cases", "generate-prompts", "score"):
        p = sub.add_parser(command)
        p.add_argument("--config", required=True)
        if command == "build-dataset":
            p.add_argument("--overwrite", action="store_true")

    sub.add_parser("plugins")
    args = parser.parse_args()

    if args.command == "plugins":
        print("\n".join(available_plugins()))
        return 0

    config = load_config(args.config)
    plugin = create_plugin(config)

    if args.command == "validate":
        result = plugin.validate_source()
        print(json.dumps(result, indent=2))
        print("VALIDATION PASSED")
    elif args.command == "build-dataset":
        path = plugin.build_dataset(overwrite=args.overwrite)
        print(f"DATASET READY: {path}")
    elif args.command == "generate-cases":
        cases = generate_cases(config, plugin)
        print(f"CASES GENERATED: {len(cases):,}")
    elif args.command == "generate-prompts":
        count = generate_prompts(config, plugin)
        print(f"PROMPTS GENERATED: {count:,}")
    elif args.command == "score":
        path = score_responses(config, plugin)
        print(f"SCORES WRITTEN: {path}")
    else:
        parser.error(f"Unknown command: {args.command}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
