from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from model_providers import ModelRequest, default_registry

from .engine import InvocationEngine, load_provider_configuration


def _print(value) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))


def command_run(args: argparse.Namespace) -> int:
    config = load_provider_configuration(args.config)
    summary = InvocationEngine(config).run(
        args.input,
        args.output,
        manifest_path=args.manifest,
        resume=not args.no_resume,
        force=args.force,
        stop_on_error=args.stop_on_error,
    )
    _print(summary.to_dict())
    return 1 if summary.failed_count else 0


def command_providers(_: argparse.Namespace) -> int:
    registry = default_registry()
    _print({"providers": list(registry.names())})
    return 0


def command_health(args: argparse.Namespace) -> int:
    config = load_provider_configuration(args.config)
    provider_name = config["provider"]
    required_environment = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }.get(provider_name)
    result = {
        "provider": provider_name,
        "model": config["model"],
        "configuration_valid": True,
        "credential_environment": required_environment,
        "credential_present": bool(os.getenv(required_environment)) if required_environment else None,
        "live_probe": bool(args.live),
    }
    if args.live:
        provider = default_registry().create(provider_name, **config.get("options", {}))
        response = provider.generate(
            ModelRequest(
                prompt=args.prompt,
                model=config["model"],
                system_prompt=config.get("system_prompt"),
                temperature=0.0,
                max_output_tokens=args.max_output_tokens,
                json_mode=False,
                metadata={"health_check": True},
            )
        )
        result.update(
            live_success=True,
            latency_seconds=response.latency_seconds,
            request_id=response.request_id,
            finish_reason=response.finish_reason,
        )
    _print(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PrimeAIExplorer Phase E3 model invocation engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Invoke a configured model provider for JSONL cases")
    run.add_argument("--config", required=True)
    run.add_argument("--input", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--manifest")
    run.add_argument("--no-resume", action="store_true")
    run.add_argument("--force", action="store_true")
    run.add_argument("--stop-on-error", action="store_true")
    run.set_defaults(func=command_run)

    providers = subparsers.add_parser("providers", help="List registered provider adapters")
    providers.set_defaults(func=command_providers)

    health = subparsers.add_parser("health", help="Validate provider configuration and optional live connectivity")
    health.add_argument("--config", required=True)
    health.add_argument("--live", action="store_true")
    health.add_argument("--prompt", default="Reply with OK.")
    health.add_argument("--max-output-tokens", type=int, default=16)
    health.set_defaults(func=command_health)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
