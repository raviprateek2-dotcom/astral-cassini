from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from dataset_common import (
    BOOL_COLUMNS,
    DATETIME_COLUMNS,
    FLOAT_COLUMNS,
    INT_COLUMNS,
    JSON_COLUMNS,
    TABLE_SPECS,
    load_csv_rows,
    parse_bool,
    parse_datetime,
    parse_json,
)
from validate_dataset import validate_dataset

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.db_models import (  # noqa: E402
    AuditEvent,
    CandidateScore,
    Interview,
    Job,
    Offer,
    Outreach,
    Recommendation,
    User,
)

MODEL_BY_TABLE = {
    "users": User,
    "jobs": Job,
    "candidate_scores": CandidateScore,
    "interviews": Interview,
    "recommendations": Recommendation,
    "audit_events": AuditEvent,
    "outreach": Outreach,
    "offers": Offer,
}


def _resolve_input(input_path: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if input_path.is_dir():
        return input_path, None
    if input_path.suffix.lower() == ".zip":
        tmp = tempfile.TemporaryDirectory()
        with ZipFile(input_path, "r") as zf:
            zf.extractall(tmp.name)
        return Path(tmp.name), tmp
    raise ValueError("Input must be a directory or .zip file")


def _coerce_value(table: str, column: str, raw: str):
    if raw == "":
        return None
    if column in JSON_COLUMNS.get(table, set()):
        return parse_json(raw)
    if column in BOOL_COLUMNS.get(table, set()):
        return parse_bool(raw)
    if column in INT_COLUMNS.get(table, set()):
        return int(raw)
    if column in FLOAT_COLUMNS.get(table, set()):
        return float(raw)
    if column in DATETIME_COLUMNS.get(table, set()):
        return parse_datetime(raw)
    return raw


def _upsert_table(db, root: Path, table: str, dry_run: bool) -> tuple[int, int]:
    model = MODEL_BY_TABLE[table]
    spec = TABLE_SPECS[table]
    columns = spec["columns"]
    keys = spec["upsert_keys"]
    rows = load_csv_rows(root / f"{table}.csv")
    created = 0
    updated = 0
    for row in rows:
        key_filter = {k: _coerce_value(table, k, row.get(k, "")) for k in keys}
        existing = db.query(model).filter_by(**key_filter).first()
        payload = {c: _coerce_value(table, c, row.get(c, "")) for c in columns}
        if existing:
            for col, val in payload.items():
                setattr(existing, col, val)
            updated += 1
        else:
            db.add(model(**payload))
            created += 1
    if not dry_run:
        db.commit()
    else:
        db.rollback()
    return created, updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Import editable PRO HR dataset bundle.")
    parser.add_argument("--input", required=True, help="Path to dataset zip or extracted folder.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually write changes. Default is dry-run.",
    )
    parser.add_argument(
        "--tables",
        default="all",
        help="Comma-separated subset of tables to import, or 'all'.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    validation = validate_dataset(input_path)
    if not validation.ok:
        print("[error] Dataset failed validation. Fix errors before import.")
        for err in validation.errors:
            print(f"  - {err}")
        raise SystemExit(1)

    root, tmp = _resolve_input(input_path)
    try:
        selected_tables = (
            list(TABLE_SPECS.keys())
            if args.tables == "all"
            else [t.strip() for t in args.tables.split(",") if t.strip()]
        )
        db = SessionLocal()
        try:
            for table in selected_tables:
                if table not in TABLE_SPECS:
                    raise ValueError(f"Unknown table '{table}'")
                created, updated = _upsert_table(db, root, table, dry_run=not args.apply)
                mode = "apply" if args.apply else "dry-run"
                print(f"[{mode}] {table}: created={created} updated={updated}")
        finally:
            db.close()
    finally:
        if tmp is not None:
            tmp.cleanup()


if __name__ == "__main__":
    main()
