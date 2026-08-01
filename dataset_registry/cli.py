"""CLI for Phase D1 dataset management."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .builder import build_manifest
from .io import load_manifest, write_manifest
from .models import DatasetSplit, ProvenanceRecord
from .registry import DatasetRegistry
from .validation import validate_manifest, verify_artifacts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PrimeAIExplorer dataset registry."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_command = subparsers.add_parser("build-manifest")
    build_command.add_argument("dataset_directory")
    build_command.add_argument("--name", required=True)
    build_command.add_argument("--version", required=True)
    build_command.add_argument("--description", default="")
    build_command.add_argument("--sequence-type", required=True)
    build_command.add_argument("--generated-by", required=True)
    build_command.add_argument("--generated-at-utc", required=True)
    build_command.add_argument("--source-type", required=True)
    build_command.add_argument("--source-reference", required=True)
    build_command.add_argument("--artifact", action="append", required=True)
    build_command.add_argument("--output", required=True)

    register_command = subparsers.add_parser("register")
    register_command.add_argument("dataset_directory")
    register_command.add_argument("manifest")
    register_command.add_argument("--registry-root", required=True)

    verify_command = subparsers.add_parser("verify")
    verify_command.add_argument("dataset_directory")
    verify_command.add_argument("manifest")

    list_command = subparsers.add_parser("list")
    list_command.add_argument("--registry-root", required=True)

    return parser


def main() -> int:
    arguments = build_parser().parse_args()

    if arguments.command == "build-manifest":
        provenance = ProvenanceRecord(
            source_type=arguments.source_type,
            source_reference=arguments.source_reference,
            generated_by=arguments.generated_by,
            generated_at_utc=arguments.generated_at_utc,
        )
        manifest = build_manifest(
            arguments.dataset_directory,
            name=arguments.name,
            version=arguments.version,
            description=arguments.description,
            sequence_type=arguments.sequence_type,
            provenance=provenance,
            artifact_paths=arguments.artifact,
        )
        write_manifest(arguments.output, manifest)
        print(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))
        return 0

    if arguments.command == "register":
        manifest = load_manifest(arguments.manifest)
        destination = DatasetRegistry(
            arguments.registry_root
        ).register(
            arguments.dataset_directory,
            manifest,
        )
        print(
            json.dumps(
                {
                    "dataset_id": manifest.dataset_id,
                    "directory": str(destination.resolve()),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if arguments.command == "verify":
        manifest = load_manifest(arguments.manifest)
        manifest_errors = validate_manifest(manifest)
        artifact_results = verify_artifacts(
            arguments.dataset_directory,
            manifest,
        )
        success = (
            not manifest_errors
            and all(
                item["exists"]
                and item["size_match"]
                and item["sha256_match"]
                for item in artifact_results
            )
        )
        print(
            json.dumps(
                {
                    "success": success,
                    "manifest_errors": manifest_errors,
                    "artifacts": artifact_results,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if success else 1

    registry = DatasetRegistry(arguments.registry_root)
    print(
        json.dumps(
            [item.to_dict() for item in registry.list()],
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
