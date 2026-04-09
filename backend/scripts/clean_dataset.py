from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

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


def _normalize_json_str(value: str) -> str:
    if value == "":
        return value
    try:
        obj = json.loads(value)
        if isinstance(obj, list):
            normalized = []
            seen = set()
            for item in obj:
                if isinstance(item, str):
                    item = " ".join(item.split()).strip()
                key = json.dumps(item, sort_keys=True) if not isinstance(item, str) else item.lower()
                if key not in seen:
                    normalized.append(item)
                    seen.add(key)
            obj = normalized
        return json.dumps(obj, ensure_ascii=True)
    except Exception:
        return value


def _normalize_row(table: str, row: dict[str, str]) -> dict[str, str]:
    out = {k: (v if v is not None else "") for k, v in row.items()}
    for key, val in list(out.items()):
        if isinstance(val, str):
            out[key] = " ".join(val.split()).strip()

    if table == "jobs":
        if out.get("current_stage"):
            out["current_stage"] = out["current_stage"].lower()
    if table == "recommendations":
        if out.get("decision"):
            out["decision"] = out["decision"].lower()
    for json_col in {
        "requirements",
        "preferred_qualifications",
        "workflow_state",
        "strengths",
        "gaps",
        "missing_skills",
        "overqualification",
        "interviewers",
        "key_observations",
        "concerns",
        "risk_factors",
    }:
        if json_col in out:
            out[json_col] = _normalize_json_str(out[json_col])
    return out


def _dedupe_rows(table: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    keys = TABLE_SPECS[table]["upsert_keys"]
    if not keys:
        return rows
    latest_by_key: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        k = tuple((row.get(col) or "").strip() for col in keys)
        latest_by_key[k] = row
    return list(latest_by_key.values())


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})


def _zip_folder(folder: Path) -> Path:
    zip_path = folder.with_suffix(".zip")
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
        for p in sorted(folder.rglob("*")):
            if p.is_file():
                zf.write(p, arcname=p.relative_to(folder))
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean and normalize exported dataset.")
    parser.add_argument("--input", required=True, help="Dataset zip or folder path.")
    parser.add_argument(
        "--output-dir",
        default="backend/data/exports",
        help="Output directory for cleaned dataset folder/zip.",
    )
    parser.add_argument(
        "--no-dedupe",
        action="store_true",
        help="Normalize only; keep every row (no upsert-key deduplication).",
    )
    args = parser.parse_args()

    root, tmp = _resolve_input(Path(args.input))
    try:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_dir = Path(args.output_dir) / f"prohr_dataset_cleaned_{ts}"
        out_dir.mkdir(parents=True, exist_ok=True)

        for table, spec in TABLE_SPECS.items():
            src = root / f"{table}.csv"
            rows = load_csv_rows(src)
            normalized = [_normalize_row(table, row) for row in rows]
            final_rows = normalized if args.no_dedupe else _dedupe_rows(table, normalized)
            _write_csv(out_dir / f"{table}.csv", spec["columns"], final_rows)
            suffix = " (no-dedupe)" if args.no_dedupe else ""
            print(f"[clean] {table}: in={len(rows)} out={len(final_rows)}{suffix}")

        wf = root / "workflow_states.jsonl"
        if wf.exists():
            (out_dir / "workflow_states.jsonl").write_text(
                wf.read_text(encoding="utf-8"), encoding="utf-8"
            )
        zip_path = _zip_folder(out_dir)
        print(f"[clean] folder={out_dir}")
        print(f"[clean] zip={zip_path}")
    finally:
        if tmp is not None:
            tmp.cleanup()


if __name__ == "__main__":
    main()
