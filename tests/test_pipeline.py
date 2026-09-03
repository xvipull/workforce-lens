import csv
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pipeline  # noqa: E402


class PipelineTests(unittest.TestCase):
    def test_clean_row_standardizes_keys_dates_currency_and_categories(self):
        row = {"snapshot_date": "08/31/2026", "worker_id": " w-1 ", "org_id": " ops ", "org_name": "north ops", "location_id": " blr ", "location_name": "bengaluru", "job_family": "operations", "employment_status": "active", "fte_fraction": "1", "hire_date": "2024/01/01", "termination_date": "", "termination_type": "", "scheduled_hours": "160", "productive_hours": "150", "accepted_output_units": "25", "labor_cost": "INR 1,200", "currency": "inr", "approved_position_count": "2", "open_requisition_count": "1", "scenario_id": "baseline"}
        cleaned = pipeline.clean_row(row)
        self.assertEqual(cleaned["snapshot_date"], "2026-08-31")
        self.assertEqual(cleaned["worker_id"], "W-1")
        self.assertEqual(cleaned["labor_cost_inr"], pipeline.Decimal("1200"))
        self.assertEqual(cleaned["employment_status"], "ACTIVE")

    def test_validate_rejects_duplicate_grain_and_invalid_range(self):
        base = pipeline.clean_row({"snapshot_date": "2026-08-31", "worker_id": "w-1", "org_id": "ops", "org_name": "ops", "location_id": "blr", "location_name": "blr", "job_family": "ops", "employment_status": "active", "fte_fraction": "1", "hire_date": "2024-01-01", "termination_date": "", "termination_type": "", "scheduled_hours": "10", "productive_hours": "9", "accepted_output_units": "1", "labor_cost": "10", "currency": "inr", "approved_position_count": "1", "open_requisition_count": "0", "scenario_id": "baseline"})
        broken = dict(base, productive_hours=pipeline.Decimal("11"))
        checks = pipeline.validate([base, broken], pipeline.REQUIRED_COLUMNS, date(2026, 9, 3))
        self.assertIn("FAIL", [item["status"] for item in checks if item["check"] in {"duplicate_grain", "invalid_ranges"}])

    def test_validate_rejects_missing_required_column(self):
        checks = pipeline.validate([], {"worker_id"}, date(2026, 9, 3))
        self.assertEqual(checks[0]["check"], "required_columns")
        self.assertEqual(checks[0]["status"], "FAIL")

    def test_sample_pipeline_creates_model_and_report(self):
        pipeline.run(as_of=date(2026, 9, 3))
        self.assertTrue(pipeline.DB_PATH.exists())
        self.assertIn("referential_integrity", pipeline.REPORT_PATH.read_text())


if __name__ == "__main__":
    unittest.main()
