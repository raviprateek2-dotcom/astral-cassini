from __future__ import annotations

import argparse
import csv
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from dataset_common import (
    ALLOWED_DECISIONS,
    ALLOWED_JOB_STAGES,
    DATETIME_COLUMNS,
    FLOAT_COLUMNS,
    INT_COLUMNS,
    JSON_COLUMNS,
    TABLE_SPECS,
    ValidationResult,
    load_csv_rows,
    parse_bool,
    parse_datetime,
    parse_json,
)


def _resolve_input(input_path: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if input_path.is_dir():
        return input_path, None
    if input_path.suffix.lower() == ".zip":
        tmp = tempfile.TemporaryDirectory()
        with ZipFile(input_path, "r") as zf:
            zf.extractall(tmp.name)
        return Path(tmp.name), tmp
    raise ValueError("Input must be a directory or .zip file")


def _validate_rows(table: str, rows: list[dict[str, str]], result: ValidationResult) -> None:
    spec = TABLE_SPECS[table]
    required = spec["upsert_keys"]
    json_cols = JSON_COLUMNS.get(table, set())
    int_cols = INT_COLUMNS.get(table, set())
    float_cols = FLOAT_COLUMNS.get(table, set())
    dt_cols = DATETIME_COLUMNS.get(table, set())

    for i, row in enumerate(rows, start=2):
        for key in required:
            if (row.get(key) or "").strip() == "":
                result.errors.append(f"{table}.csv:{i} missing required upsert key '{key}'")

        for col in json_cols:
            val = row.get(col, "")
            if val != "":
                try:
                    parse_json(val)
                except Exception as exc:
                    result.errors.append(f"{table}.csv:{i} invalid JSON in '{col}': {exc}")

        for col in int_cols:
            val = row.get(col, "")
            if val != "":
                try:
                    int(val)
                except Exception:
                    result.errors.append(f"{table}.csv:{i} invalid int in '{col}'")

        for col in float_cols:
            val = row.get(col, "")
            if val != "":
                try:
                    float(val)
                except Exception:
                    result.errors.append(f"{table}.csv:{i} invalid float in '{col}'")

        bool_cols = {"is_active", "outreach_completed", "offer_sent"}
        for col in bool_cols:
            if col in row and row[col] != "":
                try:
                    parse_bool(row[col])
                except Exception:
                    result.errors.append(f"{table}.csv:{i} invalid bool in '{col}'")

        for col in dt_cols:
            val = row.get(col, "")
            if val != "":
                try:
                    parse_datetime(val)
                except Exception as exc:
                    result.errors.append(f"{table}.csv:{i} invalid datetime in '{col}': {exc}")

        if table == "jobs":
            stage = (row.get("current_stage") or "").strip()
            if stage and stage not in ALLOWED_JOB_STAGES:
                result.errors.append(f"{table}.csv:{i} invalid current_stage '{stage}'")
        if table == "recommendations":
            decision = (row.get("decision") or "").strip()
            if decision and decision not in ALLOWED_DECISIONS:
                result.errors.append(f"{table}.csv:{i} invalid decision '{decision}'")


def validate_dataset(input_path: Path) -> ValidationResult:
    root, tmp = _resolve_input(input_path)
    result = ValidationResult(errors=[], warnings=[], rows_by_table={})
    try:
        for table, spec in TABLE_SPECS.items():
            csv_path = root / f"{table}.csv"
            if not csv_path.exists():
                result.errors.append(f"Missing required file: {table}.csv")
                continue
            with csv_path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
            expected = spec["columns"]
            if headers != expected:
                result.errors.append(
                    f"{table}.csv header mismatch. expected={expected} got={headers}"
                )
                continue
            rows = load_csv_rows(csv_path)
            result.rows_by_table[table] = len(rows)
            _validate_rows(table, rows, result)

        wf = root / "workflow_states.jsonl"
        if wf.exists():
            result.rows_by_table["workflow_states"] = sum(1 for _ in wf.open("r", encoding="utf-8"))
        else:
            result.warnings.append("workflow_states.jsonl missing (optional but recommended)")
        return result
    finally:
        if tmp is not None:
            tmp.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate editable PRO HR dataset bundle.")
    parser.add_argument("--input", required=True, help="Path to dataset zip or extracted folder.")
    args = parser.parse_args()

    result = validate_dataset(Path(args.input))
    for table, count in sorted(result.rows_by_table.items()):
        print(f"[rows] {table}: {count}")
    for warning in result.warnings:
        print(f"[warning] {warning}")
    if result.errors:
        for err in result.errors:
            print(f"[error] {err}")
        raise SystemExit(1)
    print("[ok] Dataset validation passed.")


if __name__ == "__main__":
    main()
