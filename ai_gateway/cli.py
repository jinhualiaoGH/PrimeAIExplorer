from __future__ import annotations

import argparse
import json

from .audit import JsonlAuditSink
from .config import load_gateway_configuration
from .gateway import AIGateway
from .models import GatewayRequest


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="PrimeAIExplorer universal AI gateway."
    )
    value.add_argument("--config", required=True)
    commands = value.add_subparsers(dest="command", required=True)

    commands.add_parser("routes")
    health = commands.add_parser("health")
    health.add_argument("--live", action="store_true")

    invoke = commands.add_parser("invoke")
    invoke.add_argument("--route", required=True)
    invoke.add_argument("--prompt", required=True)
    invoke.add_argument("--system-prompt")
    invoke.add_argument("--temperature", type=float, default=0.0)
    invoke.add_argument("--max-output-tokens", type=int)
    invoke.add_argument("--seed", type=int)
    invoke.add_argument("--json-mode", action="store_true")
    invoke.add_argument(
        "--metadata-json",
        default="{}",
        help="JSON object passed as request metadata.",
    )

    return value


def main() -> int:
    arguments = parser().parse_args()
    routes, retry_policy, options = load_gateway_configuration(
        arguments.config
    )
    audit_sink = (
        JsonlAuditSink(str(options["audit_path"]))
        if options.get("audit_path")
        else None
    )
    gateway = AIGateway(
        routes=routes,
        retry_policy=retry_policy,
        requests_per_second=(
            float(options["requests_per_second"])
            if options.get("requests_per_second") is not None
            else None
        ),
        audit_sink=audit_sink,
    )

    if arguments.command == "routes":
        result = [
            {
                "alias": item.alias,
                "provider": item.provider,
                "model": item.model,
            }
            for item in routes.list_routes()
        ]
    elif arguments.command == "health":
        result = gateway.health(live=arguments.live)
    else:
        metadata = json.loads(arguments.metadata_json)

        if not isinstance(metadata, dict):
            raise ValueError(
                "--metadata-json must contain a JSON object."
            )

        result = gateway.invoke(
            GatewayRequest(
                route=arguments.route,
                prompt=arguments.prompt,
                system_prompt=arguments.system_prompt,
                temperature=arguments.temperature,
                max_output_tokens=arguments.max_output_tokens,
                seed=arguments.seed,
                json_mode=arguments.json_mode,
                metadata=metadata,
            )
        ).to_dict()

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
