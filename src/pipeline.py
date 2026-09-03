"""Reproducible cleaning, data quality, and SQLite star-model load."""
from __future__ import annotations

import csv
import sqlite3
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data/raw/workforce_snapshot_sample.csv"
STAGE_PATH = ROOT / "data/staging/workforce_snapshot_clean.csv"
DB_PATH = ROOT / "data/workforce_lens.db"
REPORT_PATH = ROOT / "reports/data_quality_report.md"
SCHEMA_PATH = ROOT / "sql/analytics_model.sql"

REQUIRED_COLUMNS = {
    "snapshot_date", "worker_id", "org_id", "org_name", "location_id", "location_name",
    "job_family", "employment_status", "fte_fraction", "hire_date", "scheduled_hours",
    "productive_hours", "accepted_output_units", "labor_cost", "currency",
    "approved_position_count", "open_requisition_count", "scenario_id",
}
REQUIRED_VALUES = {
    "snapshot_date", "worker_id", "org_id", "org_name", "location_id", "location_name",
    "job_family", "employment_status", "fte_fraction", "hire_date", "scheduled_hours",
    "productive_hours", "accepted_output_units", "labor_cost_inr", "currency",
    "approved_position_count", "open_requisition_count", "scenario_id",
}
VALID_STATUS = {"ACTIVE", "LEAVE", "TERMINATED"}
VALID_TERMINATION = {"VOLUNTARY", "INVOLUNTARY", "OTHER"}
DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d")


class QualityError(ValueError):
    """Raised when an input cannot safely be published to the model."""


def _text(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def _identifier(value: str | None) -> str | None:
    value = _text(value)
    return value.upper() if value else None


def _date(value: str | None) -> str | None:
    value = _text(value)
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    raise QualityError(f"Invalid date: {value}")


def _number(value: str | None, field: str) -> Decimal:
    value = _text(value)
    if value is None:
        raise QualityError(f"Missing numeric value: {field}")
    try:
        return Decimal(value.replace("INR", "").replace("₹", "").replace(",", "").strip())
    except InvalidOperation as exc:
        raise QualityError(f"Invalid number for {field}: {value}") from exc


def clean_row(row: dict[str, str]) -> dict[str, object]:
    """Standardize one raw record according to the documented transformation ledger."""
    status = (_text(row.get("employment_status")) or "").upper()
    term_type = _text(row.get("termination_type"))
    cleaned = {
        "snapshot_date": _date(row.get("snapshot_date")), "worker_id": _identifier(row.get("worker_id")),
        "org_id": _identifier(row.get("org_id")), "org_name": (_text(row.get("org_name")) or "").title(),
        "location_id": _identifier(row.get("location_id")), "location_name": (_text(row.get("location_name")) or "").title(),
        "job_family": (_text(row.get("job_family")) or "").title(), "employment_status": status,
        "fte_fraction": _number(row.get("fte_fraction"), "fte_fraction"), "hire_date": _date(row.get("hire_date")),
        "termination_date": _date(row.get("termination_date")),
        "termination_type": term_type.upper() if term_type else None,
        "scheduled_hours": _number(row.get("scheduled_hours"), "scheduled_hours"),
        "productive_hours": _number(row.get("productive_hours"), "productive_hours"),
        "accepted_output_units": _number(row.get("accepted_output_units"), "accepted_output_units"),
        "labor_cost_inr": _number(row.get("labor_cost"), "labor_cost"),
        "currency": (_text(row.get("currency")) or "").upper(),
        "approved_position_count": int(_number(row.get("approved_position_count"), "approved_position_count")),
        "open_requisition_count": int(_number(row.get("open_requisition_count"), "open_requisition_count")),
        "scenario_id": _identifier(row.get("scenario_id")),
    }
    return cleaned


def validate(rows: list[dict[str, object]], source_columns: set[str], as_of: date | None = None) -> list[dict[str, object]]:
    """Run blocking contract, null, range, duplicate, category, and freshness checks."""
    failures: list[dict[str, object]] = []
    missing = sorted(REQUIRED_COLUMNS - source_columns)
    if missing:
        failures.append({"check": "required_columns", "threshold": "0 missing", "actual": ", ".join(missing), "status": "FAIL"})
        return failures
    failures.append({"check": "required_columns", "threshold": "0 missing", "actual": "0", "status": "PASS"})
    for column in REQUIRED_VALUES:
        nulls = sum(row.get(column) in (None, "") for row in rows)
        failures.append({"check": f"null_threshold:{column}", "threshold": "0 nulls", "actual": str(nulls), "status": "PASS" if nulls == 0 else "FAIL"})
    grain = [(r["snapshot_date"], r["worker_id"], r["scenario_id"]) for r in rows]
    duplicates = len(grain) - len(set(grain))
    failures.append({"check": "duplicate_grain", "threshold": "0 duplicates", "actual": str(duplicates), "status": "PASS" if duplicates == 0 else "FAIL"})
    invalid_ranges = sum(not (Decimal("0") <= r["fte_fraction"] <= Decimal("1") and r["scheduled_hours"] >= 0 and r["productive_hours"] >= 0 and r["productive_hours"] <= r["scheduled_hours"] and r["accepted_output_units"] >= 0 and r["labor_cost_inr"] >= 0 and r["open_requisition_count"] >= 0 and r["approved_position_count"] >= r["open_requisition_count"]) for r in rows)
    failures.append({"check": "invalid_ranges", "threshold": "0 rows", "actual": str(invalid_ranges), "status": "PASS" if invalid_ranges == 0 else "FAIL"})
    invalid_categories = sum(r["employment_status"] not in VALID_STATUS or (r["termination_type"] is not None and r["termination_type"] not in VALID_TERMINATION) or r["currency"] != "INR" for r in rows)
    failures.append({"check": "invalid_categories_or_currency", "threshold": "0 rows", "actual": str(invalid_categories), "status": "PASS" if invalid_categories == 0 else "FAIL"})
    snapshot_dates = [date.fromisoformat(str(r["snapshot_date"])) for r in rows if r.get("snapshot_date")]
    age = (as_of or date.today()) - max(snapshot_dates)
    failures.append({"check": "freshness", "threshold": "≤45 days", "actual": f"{age.days} days", "status": "PASS" if age.days <= 45 else "FAIL"})
    return failures


def write_stage(rows: list[dict[str, object]]) -> None:
    STAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with STAGE_PATH.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: str(value) if value is not None else "" for key, value in row.items()})


def load_model(rows: list[dict[str, object]]) -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_PATH.read_text())
        stage_columns = list(rows[0].keys())
        placeholders = ", ".join("?" for _ in stage_columns)
        connection.executemany(
            f"INSERT INTO stg_workforce_snapshot ({', '.join(stage_columns)}) VALUES ({placeholders})",
            [tuple(float(value) if isinstance(value, Decimal) else value for value in row.values()) for row in rows],
        )
        dates = sorted({str(r["snapshot_date"]) for r in rows})
        for value in dates:
            parsed = date.fromisoformat(value)
            connection.execute("INSERT INTO dim_date VALUES (?, ?, ?, ?, ?, ?)", (int(parsed.strftime("%Y%m%d")), value, parsed.year, parsed.month, parsed.strftime("%B"), (parsed.month - 1) // 3 + 1))
        dimensions = (("dim_organization", "organization_key", "org_id", "org_name"), ("dim_location", "location_key", "location_id", "location_name"), ("dim_job_family", "job_family_key", "job_family", "job_family"), ("dim_scenario", "scenario_key", "scenario_id", "scenario_id"))
        for table, key, business, label in dimensions:
            values = sorted({(str(r[business]), str(r[label])) for r in rows})
            for surrogate, (business_value, label_value) in enumerate(values, 1):
                if business == label:
                    connection.execute(f"INSERT INTO {table} ({key}, {business}) VALUES (?, ?)", (surrogate, business_value))
                else:
                    connection.execute(f"INSERT INTO {table} ({key}, {business}, {label}) VALUES (?, ?, ?)", (surrogate, business_value, label_value))
        keys = {name: {value: sk for sk, value in connection.execute(f"SELECT {key}, {business} FROM {table}")} for name, table, key, business in (("org", "dim_organization", "organization_key", "org_id"), ("location", "dim_location", "location_key", "location_id"), ("job", "dim_job_family", "job_family_key", "job_family"), ("scenario", "dim_scenario", "scenario_key", "scenario_id"))}
        for row in rows:
            connection.execute("""INSERT INTO fact_workforce_snapshot (
              snapshot_date_key, organization_key, location_key, job_family_key, scenario_key, worker_id,
              employment_status, fte_fraction, hire_date, termination_date, termination_type, scheduled_hours,
              productive_hours, accepted_output_units, labor_cost_inr, approved_position_count, open_requisition_count)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
              int(str(row["snapshot_date"]).replace("-", "")), keys["org"][str(row["org_id"])], keys["location"][str(row["location_id"])], keys["job"][str(row["job_family"])], keys["scenario"][str(row["scenario_id"])], row["worker_id"], row["employment_status"], float(row["fte_fraction"]), row["hire_date"], row["termination_date"], row["termination_type"], float(row["scheduled_hours"]), float(row["productive_hours"]), float(row["accepted_output_units"]), float(row["labor_cost_inr"]), row["approved_position_count"], row["open_requisition_count"]))
        connection.commit()
    finally:
        connection.close()


def db_integrity_check(expected_count: int) -> list[dict[str, object]]:
    connection = sqlite3.connect(DB_PATH)
    try:
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        stage_count = connection.execute("SELECT COUNT(*) FROM stg_workforce_snapshot").fetchone()[0]
        fact_count = connection.execute("SELECT COUNT(*) FROM fact_workforce_snapshot").fetchone()[0]
    finally:
        connection.close()
    return [
        {"check": "referential_integrity", "threshold": "0 FK violations", "actual": str(len(violations)), "status": "PASS" if not violations else "FAIL"},
        {"check": "database_stage_row_count", "threshold": f"{expected_count}", "actual": str(stage_count), "status": "PASS" if stage_count == expected_count else "FAIL"},
        {"check": "database_fact_row_count", "threshold": f"{expected_count}", "actual": str(fact_count), "status": "PASS" if fact_count == expected_count else "FAIL"},
    ]


def write_report(checks: list[dict[str, object]], raw_count: int, rows: list[dict[str, object]], raw_cost: Decimal) -> None:
    staged_cost = sum((r["labor_cost_inr"] for r in rows), Decimal("0"))
    checks.extend([
        {"check": "row_count_reconciliation", "threshold": "raw = staging", "actual": f"{raw_count} = {len(rows)}", "status": "PASS" if raw_count == len(rows) else "FAIL"},
        {"check": "labor_cost_reconciliation", "threshold": "raw = staging", "actual": f"INR {raw_cost} = INR {staged_cost}", "status": "PASS" if raw_cost == staged_cost else "FAIL"},
    ])
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Data Quality Report", "", "Generated by `python3 src/pipeline.py` from the synthetic workforce snapshot.", "", f"- Raw rows: **{raw_count}**", f"- Conformed rows: **{len(rows)}**", f"- Raw labor cost: **INR {raw_cost}**", f"- Conformed labor cost: **INR {staged_cost}**", "", "| Check | Threshold | Actual | Status |", "| --- | --- | --- | --- |"]
    lines.extend(f"| {item['check']} | {item['threshold']} | {item['actual']} | {item['status']} |" for item in checks)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(raw_path: Path = RAW_PATH, as_of: date | None = None) -> None:
    with raw_path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        source_columns = set(reader.fieldnames or [])
        raw_rows = list(reader)
    raw_cost = sum((_number(row.get("labor_cost"), "labor_cost") for row in raw_rows), Decimal("0"))
    rows = [clean_row(row) for row in raw_rows]
    checks = validate(rows, source_columns, as_of)
    failures = [item for item in checks if item["status"] == "FAIL"]
    if failures:
        raise QualityError("Data quality checks failed: " + "; ".join(str(item["check"]) for item in failures))
    write_stage(rows)
    load_model(rows)
    checks.extend(db_integrity_check(len(rows)))
    write_report(checks, len(raw_rows), rows, raw_cost)


if __name__ == "__main__":
    run()
    print(f"Loaded {DB_PATH} and generated {REPORT_PATH}")
