from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

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
from dataset_common import TABLE_SPECS, serialize_value  # noqa: E402

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


def _write_table_csv(export_dir: Path, table: str, rows: list[object]) -> Path:
    columns = TABLE_SPECS[table]["columns"]
    path = export_dir / f"{table}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: serialize_value(getattr(row, col, None)) for col in columns})
    return path


def _write_workflow_jsonl(export_dir: Path, jobs: list[Job]) -> Path:
    path = export_dir / "workflow_states.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for job in jobs:
            payload = {
                "job_id": job.job_id,
                "current_stage": job.current_stage,
                "workflow_state": job.workflow_state or {},
            }
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    return path


def _write_dataset_readme(export_dir: Path) -> Path:
    path = export_dir / "README_dataset.md"
    lines = [
        "# Editable PRO HR Dataset",
        "",
        "This bundle contains exported recruitment data in CSV and JSONL formats.",
        "",
        "## Files",
        "- users.csv",
        "- jobs.csv",
        "- candidate_scores.csv",
        "- interviews.csv",
        "- recommendations.csv",
        "- audit_events.csv",
        "- outreach.csv",
        "- offers.csv",
        "- workflow_states.jsonl (nested state snapshots)",
        "",
        "## Editing Rules",
        "- Keep CSV headers unchanged.",
        "- Preserve upsert key columns (see docs/DATASET_FORMAT.md).",
        "- Use ISO timestamps (e.g. 2026-04-09T21:00:00+00:00).",
        "- JSON columns must stay valid JSON strings.",
        "",
        "## Re-import",
        "1. Validate first:",
        "   python backend/scripts/validate_dataset.py --input <zip-or-folder>",
        "2. Dry run import:",
        "   python backend/scripts/import_dataset.py --input <zip-or-folder> --dry-run",
        "3. Apply import:",
        "   python backend/scripts/import_dataset.py --input <zip-or-folder> --apply",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_template_dir(export_dir: Path) -> Path:
    template_dir = export_dir / "editable_templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    for table, spec in TABLE_SPECS.items():
        path = template_dir / f"{table}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=spec["columns"])
            writer.writeheader()
    return template_dir


def _zip_export(export_dir: Path) -> Path:
    zip_path = export_dir.with_suffix(".zip")
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
        for file_path in sorted(export_dir.rglob("*")):
            if file_path.is_file():
                zf.write(file_path, arcname=file_path.relative_to(export_dir))
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export editable dataset bundle from PRO HR DB.")
    parser.add_argument(
        "--output-dir",
        default=str(BACKEND_ROOT / "data" / "exports"),
        help="Directory where export folder/zip will be generated.",
    )
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_dir = Path(args.output_dir)
    export_dir = base_dir / f"prohr_dataset_{ts}"
    export_dir.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        for table, model in MODEL_BY_TABLE.items():
            rows = db.query(model).all()
            _write_table_csv(export_dir, table, rows)
            print(f"[export] {table}.csv rows={len(rows)}")
        jobs = db.query(Job).all()
        _write_workflow_jsonl(export_dir, jobs)
    finally:
        db.close()

    _write_dataset_readme(export_dir)
    _write_template_dir(export_dir)
    zip_path = _zip_export(export_dir)
    print(f"[export] folder={export_dir}")
    print(f"[export] zip={zip_path}")


if __name__ == "__main__":
    main()
