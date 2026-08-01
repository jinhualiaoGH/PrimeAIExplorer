from __future__ import annotations

import argparse
import json
from pathlib import Path

from .builder import build_bundle
from .verification import verify_bundle


def _json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and verify immutable PrimeAIExplorer reproducibility bundles."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Build a reproducibility bundle.")
    build.add_argument("--project-root", type=Path, default=Path("."))
    build.add_argument("--output-root", type=Path, required=True)
    build.add_argument("--bundle-name", required=True)
    build.add_argument("--source", type=Path, action="append", required=True)
    build.add_argument("--reproduce-command", nargs="*", default=[])
    build.add_argument("--metadata-json", type=Path)
    build.add_argument("--no-archive", action="store_true")
    build.add_argument("--overwrite", action="store_true")

    verify = subparsers.add_parser("verify", help="Verify a reproducibility bundle.")
    verify.add_argument("bundle_root", type=Path)

    inspect = subparsers.add_parser("inspect", help="Show the bundle manifest.")
    inspect.add_argument("bundle_root", type=Path)

    return parser


def main() -> int:
    args = _build_parser().parse_args()

    if args.command == "build":
        metadata: dict[str, object] = {}
        if args.metadata_json:
            metadata = json.loads(args.metadata_json.read_text(encoding="utf-8"))

        result = build_bundle(
            project_root=args.project_root,
            output_root=args.output_root,
            bundle_name=args.bundle_name,
            sources=args.source,
            command=args.reproduce_command,
            metadata=metadata,
            create_archive=not args.no_archive,
            overwrite=args.overwrite,
        )
        _json(result.to_dict())
        return 0

    if args.command == "verify":
        result = verify_bundle(args.bundle_root)
        _json(result)
        return 0 if result["success"] else 1

    if args.command == "inspect":
        manifest = json.loads((args.bundle_root / "manifest.json").read_text(encoding="utf-8"))
        _json(manifest)
        return 0

    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
