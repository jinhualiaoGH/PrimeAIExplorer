from __future__ import annotations

import argparse
import csv
import importlib
import json
from pathlib import Path


REQUIRED_COLUMNS = (
    "connector_id",
    "title",
    "short_name",
    "version",
    "status",
    "connector_type",
    "implementation_module",
    "cost_class",
    "external_access",
    "created_date",
    "modified_date",
)

ALLOWED_STATUS = {"Active", "Planned", "Disabled", "Retired"}
ALLOWED_COST_CLASS = {"free", "paid", "local"}
ALLOWED_EXTERNAL = {"true", "false"}


def fail(message: str) -> None:
    raise SystemExit(f"[FAIL] {message}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the PrimeAIExplorer connector registry."
    )
    parser.add_argument(
        "--root",
        default="C:/PrimeAIExplorer",
        help="PrimeAIExplorer project root.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    csv_path = root / "connectors" / "connector_registry.csv"
    json_path = root / "connectors" / "connector_registry.json"

    if not csv_path.exists():
        fail(f"Missing CSV registry: {csv_path}")
    if not json_path.exists():
        fail(f"Missing JSON registry: {json_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            fail(
                "Unexpected CSV columns.\n"
                f"Expected: {REQUIRED_COLUMNS}\n"
                f"Found:    {tuple(reader.fieldnames or ())}"
            )
        rows = list(reader)

    if not rows:
        fail("CSV registry contains no records.")

    identifiers: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        connector_id = row["connector_id"].strip()
        if not connector_id:
            fail(f"Row {row_number}: missing connector_id.")
        if connector_id in identifiers:
            fail(f"Duplicate connector_id: {connector_id}")
        identifiers.add(connector_id)

        if row["status"] not in ALLOWED_STATUS:
            fail(f"{connector_id}: invalid status {row['status']!r}")
        if row["cost_class"] not in ALLOWED_COST_CLASS:
            fail(f"{connector_id}: invalid cost_class {row['cost_class']!r}")
        if row["external_access"].lower() not in ALLOWED_EXTERNAL:
            fail(
                f"{connector_id}: invalid external_access "
                f"{row['external_access']!r}"
            )

        if row["status"] == "Active":
            module_name = row["implementation_module"].strip()
            if not module_name:
                fail(f"{connector_id}: active connector has no implementation_module.")
            try:
                importlib.import_module(module_name)
            except Exception as exc:
                fail(
                    f"{connector_id}: cannot import {module_name!r}: {exc}"
                )

    with json_path.open("r", encoding="utf-8") as stream:
        registry_object = json.load(stream)

    json_rows = registry_object.get("connectors")
    if not isinstance(json_rows, list):
        fail("JSON registry has no connectors array.")

    csv_ids = [row["connector_id"] for row in rows]
    json_ids = [row.get("connector_id") for row in json_rows]
    if csv_ids != json_ids:
        fail(
            "CSV and JSON registry identifiers differ.\n"
            f"CSV:  {csv_ids}\n"
            f"JSON: {json_ids}"
        )

    active = [row for row in rows if row["status"] == "Active"]
    if not active:
        fail("Registry has no active connector.")

    mock = next(
        (row for row in rows if row["connector_id"] == "CONNECTOR-000001"),
        None,
    )
    if mock is None:
        fail("CONNECTOR-000001 is missing.")
    if mock["status"] != "Active":
        fail("CONNECTOR-000001 must be Active.")
    if mock["cost_class"] != "free":
        fail("CONNECTOR-000001 must be free.")
    if mock["external_access"].lower() != "false":
        fail("CONNECTOR-000001 must have external_access=false.")

    print("PrimeAIExplorer Connector Registry Validator")
    print("=" * 72)
    print(f"[PASS] CSV registry       {csv_path}")
    print(f"[PASS] JSON registry      {json_path}")
    print(f"[PASS] Records            {len(rows)}")
    print(f"[PASS] Active connectors  {len(active)}")
    print(f"[PASS] Free mock           CONNECTOR-000001")
    print("=" * 72)
    print("Connector registry validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
