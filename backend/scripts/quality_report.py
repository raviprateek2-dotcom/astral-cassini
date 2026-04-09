from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from dataset_common import TABLE_SPECS, load_csv_rows


def _resolve_input(input_path: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if input_path.is_dir():
        return input_path, None
    if input_path.suffix.lower() == ".zip":
        tmp = tempfile.TemporaryDirectory()
        with ZipFile(input_path, "r") as zf:
            zf.extractall(tmp.name)
        return Path(tmp.name), tmp
    raise ValueError("Input must be a directory or .zip file")


def _safe_parse_json(value: str):
    if value == "":
        return None
    try:
        return json.loads(value)
    except Exception:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate data quality report for exported dataset.")
    parser.add_argument("--input", required=True, help="Path to dataset zip or extracted folder.")
    args = parser.parse_args()

    root, tmp = _resolve_input(Path(args.input))
    try:
        totals = {"rows": 0, "missing_cells": 0, "invalid_json": 0}
        print("=== DATA QUALITY REPORT ===")
        for table, spec in TABLE_SPECS.items():
            rows = load_csv_rows(root / f"{table}.csv")
            cols = spec["columns"]
            row_count = len(rows)
            if row_count == 0:
                print(f"[{table}] rows=0 missing_pct=0.00 invalid_json=0")
                continue
            missing_cells = 0
            invalid_json = 0
            for row in rows:
                for col in cols:
                    val = row.get(col, "")
                    if val == "":
                        missing_cells += 1
                    if col in {"requirements", "preferred_qualifications", "workflow_state", "strengths", "gaps",
                               "missing_skills", "overqualification", "interviewers", "key_observations",
                               "concerns", "risk_factors"} and val != "":
                        if _safe_parse_json(val) is None:
                            invalid_json += 1
            total_cells = row_count * len(cols)
            missing_pct = (missing_cells / total_cells) * 100 if total_cells else 0.0
            print(
                f"[{table}] rows={row_count} missing_pct={missing_pct:.2f} "
                f"missing_cells={missing_cells} invalid_json={invalid_json}"
            )
            totals["rows"] += row_count
            totals["missing_cells"] += missing_cells
            totals["invalid_json"] += invalid_json
        print("---")
        print(
            f"[total] rows={totals['rows']} missing_cells={totals['missing_cells']} "
            f"invalid_json={totals['invalid_json']}"
        )
    finally:
        if tmp is not None:
            tmp.cleanup()


if __name__ == "__main__":
    main()
