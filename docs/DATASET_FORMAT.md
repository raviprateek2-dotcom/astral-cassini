# Dataset Format

This project supports an editable dataset bundle for analysis, cleanup, and re-import.

## Export

From repo root:

```powershell
python backend/scripts/export_dataset.py
```

Output:

- Folder: `backend/data/exports/prohr_dataset_YYYYMMDD_HHMMSS/`
- Zip: `backend/data/exports/prohr_dataset_YYYYMMDD_HHMMSS.zip`

Bundle files:

- `users.csv`
- `jobs.csv`
- `candidate_scores.csv`
- `interviews.csv`
- `recommendations.csv`
- `audit_events.csv`
- `outreach.csv`
- `offers.csv`
- `workflow_states.jsonl`
- `editable_templates/*.csv`

## Edit Rules

- Keep CSV headers exactly as exported.
- Do not remove upsert key columns.
- Keep JSON fields as valid JSON strings.
- Keep timestamps in ISO format.

## Validate

```powershell
python backend/scripts/validate_dataset.py --input backend/data/exports/prohr_dataset_YYYYMMDD_HHMMSS.zip
```

## Quality Report

```powershell
python backend/scripts/quality_report.py --input backend/data/exports/prohr_dataset_YYYYMMDD_HHMMSS.zip
```

## Clean / Normalize

```powershell
python backend/scripts/clean_dataset.py --input backend/data/exports/prohr_dataset_YYYYMMDD_HHMMSS.zip
```

This generates a new cleaned bundle:

- `backend/data/exports/prohr_dataset_cleaned_YYYYMMDD_HHMMSS/`
- `backend/data/exports/prohr_dataset_cleaned_YYYYMMDD_HHMMSS.zip`

Preserve all rows (normalize whitespace and JSON only; no deduplication by upsert keys):

```powershell
python backend/scripts/clean_dataset.py --input backend/data/exports/prohr_dataset_YYYYMMDD_HHMMSS.zip --no-dedupe
```

## Import (safe first)

Dry run:

```powershell
python backend/scripts/import_dataset.py --input backend/data/exports/prohr_dataset_YYYYMMDD_HHMMSS.zip
```

Apply:

```powershell
python backend/scripts/import_dataset.py --input backend/data/exports/prohr_dataset_YYYYMMDD_HHMMSS.zip --apply
```

Subset example:

```powershell
python backend/scripts/import_dataset.py --input backend/data/exports/prohr_dataset_YYYYMMDD_HHMMSS.zip --tables jobs,candidate_scores --apply
```

## Upsert Keys

- `users`: `email`
- `jobs`: `job_id`
- `candidate_scores`: `job_id,candidate_id`
- `interviews`: `job_id,candidate_id,scheduled_time`
- `recommendations`: `job_id,candidate_id`
- `audit_events`: `job_id,timestamp,action`
- `outreach`: `job_id,candidate_id`
- `offers`: `job_id,candidate_id`
