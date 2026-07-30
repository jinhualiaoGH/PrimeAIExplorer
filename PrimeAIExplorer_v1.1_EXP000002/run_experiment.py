from __future__ import annotations

import argparse
import json

from core.baselines import generate_baseline_responses
from core.cases import generate_cases
from core.config import load_config
from core.prompts import generate_prompts
from core.registry import available_plugins, create_plugin
from core.run_summary import summarize_scores
from core.scoring import score_responses


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PrimeAIExplorer v1.1 experiment runner."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    config_commands = (
        "validate-source",
        "build-dataset",
        "validate-dataset",
        "generate-cases",
        "generate-prompts",
        "generate-baselines",
        "score",
        "summarize",
        "pipeline",
    )
    for command in config_commands:
        command_parser = sub.add_parser(command)
        command_parser.add_argument("--config", required=True)
        if command in {"build-dataset", "pipeline"}:
            command_parser.add_argument("--overwrite", action="store_true")
        if command == "pipeline":
            command_parser.add_argument(
                "--skip-build",
                action="store_true",
                help="Use an existing validated dataset.",
            )

    sub.add_parser("plugins")
    args = parser.parse_args()

    if args.command == "plugins":
        print("\n".join(available_plugins()))
        return 0

    config = load_config(args.config)
    plugin = create_plugin(config)

    if args.command == "validate-source":
        print(json.dumps(plugin.validate_source(), indent=2))
        print("SOURCE VALIDATION PASSED")
    elif args.command == "build-dataset":
        print(f"DATASET READY: {plugin.build_dataset(overwrite=args.overwrite)}")
    elif args.command == "validate-dataset":
        validator = getattr(plugin, "validate_dataset", None)
        if validator is None:
            raise RuntimeError(
                f"Plugin {plugin.plugin_name} has no validate_dataset method."
            )
        print(json.dumps(validator(), indent=2))
        print("DATASET VALIDATION PASSED")
    elif args.command == "generate-cases":
        print(f"CASES GENERATED: {len(generate_cases(config, plugin)):,}")
    elif args.command == "generate-prompts":
        print(f"PROMPTS GENERATED: {generate_prompts(config, plugin):,}")
    elif args.command == "generate-baselines":
        print(json.dumps(generate_baseline_responses(config, plugin), indent=2))
        print("BASELINE RESPONSES GENERATED")
    elif args.command == "score":
        print(f"SCORES WRITTEN: {score_responses(config, plugin)}")
    elif args.command == "summarize":
        print(f"SUMMARY WRITTEN: {summarize_scores(config)}")
    elif args.command == "pipeline":
        print(json.dumps(plugin.validate_source(), indent=2))
        if not args.skip_build:
            print(f"DATASET READY: {plugin.build_dataset(overwrite=args.overwrite)}")
        validator = getattr(plugin, "validate_dataset")
        print(json.dumps(validator(), indent=2))
        print(f"CASES GENERATED: {len(generate_cases(config, plugin)):,}")
        print(f"PROMPTS GENERATED: {generate_prompts(config, plugin):,}")
        print(json.dumps(generate_baseline_responses(config, plugin), indent=2))
        print(f"SCORES WRITTEN: {score_responses(config, plugin)}")
        print(f"SUMMARY WRITTEN: {summarize_scores(config)}")
        print("EXP-000002 PIPELINE PASSED")
    else:
        parser.error(f"Unknown command: {args.command}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
