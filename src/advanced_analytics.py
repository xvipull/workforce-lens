"""Aggregate capacity scenarios and transparent attrition/absence driver prioritization.

This is decision support only: it produces segment-level planning prompts, not
individual predictions, rankings, or automated HR decisions.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from pipeline import DB_PATH, ROOT

MODEL_VERSION = "capacity-driver-v1.0"
SQL_PATH = ROOT / "sql/advanced_analytics.sql"
SCENARIOS = {
    "BASELINE": {"planned_hiring_fte": 0.0, "expected_attrition_rate": 0.0, "additional_absence_rate": 0.0},
    "HIRING_ACCELERATED": {"planned_hiring_fte": 2.0, "expected_attrition_rate": 0.0, "additional_absence_rate": 0.0},
    "ATTRITION_PRESSURE": {"planned_hiring_fte": 0.0, "expected_attrition_rate": 0.10, "additional_absence_rate": 0.0},
    "ABSENCE_PRESSURE": {"planned_hiring_fte": 0.0, "expected_attrition_rate": 0.0, "additional_absence_rate": 0.10},
}


def band(score: float) -> str:
    return "FOCUS" if score >= 66 else "REVIEW" if score >= 33 else "MONITOR"


def contribution(value: float, benchmark: float, weight: float) -> float:
    """Capped, transparent weighted contribution for an aggregate segment."""
    return round(min(max(value, 0.0) / benchmark, 1.0) * weight, 2)


def run() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError("Run `python3 src/pipeline.py` before advanced analytics.")
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SQL_PATH.read_text())
        connection.execute("DELETE FROM analytics_capacity_scenario")
        connection.execute("DELETE FROM analytics_attrition_absence_drivers")
        segments = connection.execute("""
            SELECT d.calendar_date, f.organization_key, f.job_family_key,
              SUM(CASE WHEN f.employment_status = 'ACTIVE' THEN 1 ELSE 0 END) AS active_headcount,
              SUM(CASE WHEN f.employment_status = 'ACTIVE' THEN f.fte_fraction ELSE 0 END) AS active_fte,
              SUM(CASE WHEN f.termination_type = 'VOLUNTARY' THEN 1 ELSE 0 END) AS voluntary_exits,
              SUM(f.scheduled_hours) AS scheduled_hours, SUM(f.productive_hours) AS productive_hours,
              SUM(f.labor_cost_inr) AS labor_cost,
              MAX(f.approved_position_count) AS approved_positions, MAX(f.open_requisition_count) AS open_requisitions,
              SUM(CASE WHEN f.employment_status = 'ACTIVE' AND julianday(d.calendar_date) - julianday(f.hire_date) <= 180 THEN f.fte_fraction ELSE 0 END) AS new_hire_fte
            FROM fact_workforce_snapshot f
            JOIN dim_date d ON d.date_key = f.snapshot_date_key
            GROUP BY d.calendar_date, f.organization_key, f.job_family_key
        """).fetchall()
        for (period, org_key, job_key, active_headcount, active_fte, exits, scheduled, productive, cost, approved, openings, new_hire_fte) in segments:
            productive_per_fte = productive / active_fte if active_fte else 0.0
            cost_per_fte = cost / active_fte if active_fte else 0.0
            for name, assumptions in SCENARIOS.items():
                available = (active_fte + assumptions["planned_hiring_fte"]) * (1 - assumptions["expected_attrition_rate"]) * productive_per_fte * (1 - assumptions["additional_absence_rate"])
                connection.execute("""INSERT INTO analytics_capacity_scenario (
                    model_version, input_snapshot_date, organization_key, job_family_key, scenario_name,
                    planned_hiring_fte, expected_attrition_rate, additional_absence_rate,
                    required_productive_hours, available_productive_hours, capacity_gap_hours,
                    incremental_labor_cost_inr, generated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    MODEL_VERSION, period, org_key, job_key, name, assumptions["planned_hiring_fte"],
                    assumptions["expected_attrition_rate"], assumptions["additional_absence_rate"],
                    scheduled, round(available, 2), round(scheduled - available, 2),
                    round(assumptions["planned_hiring_fte"] * cost_per_fte, 2), generated_at,
                ))
            voluntary_rate = exits / active_headcount if active_headcount else 0.0
            absence_proxy = (scheduled - productive) / scheduled if scheduled else 0.0
            vacancy_rate = openings / approved if approved else 0.0
            new_hire_share = new_hire_fte / active_fte if active_fte else 0.0
            attrition_points = contribution(voluntary_rate, .10, 35)
            absence_points = contribution(absence_proxy, .15, 25)
            vacancy_points = contribution(vacancy_rate, .15, 20)
            new_hire_points = contribution(new_hire_share, .20, 20)
            score = round(attrition_points + absence_points + vacancy_points + new_hire_points, 2)
            interpretation = (f"Segment-level planning prompt: voluntary exits contribute {attrition_points}, "
                              f"availability loss proxy contributes {absence_points}, vacancies contribute {vacancy_points}, "
                              f"and recent-hire concentration contributes {new_hire_points}. Human review required.")
            connection.execute("""INSERT INTO analytics_attrition_absence_drivers (
                model_version, input_snapshot_date, organization_key, job_family_key, active_headcount,
                voluntary_exit_rate, absence_proxy_rate, vacancy_rate, new_hire_fte_share,
                attrition_contribution, absence_contribution, vacancy_contribution, new_hire_contribution,
                priority_score, priority_band, interpretation, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                MODEL_VERSION, period, org_key, job_key, active_headcount, round(voluntary_rate, 4),
                round(absence_proxy, 4), round(vacancy_rate, 4), round(new_hire_share, 4), attrition_points,
                absence_points, vacancy_points, new_hire_points, score, band(score), interpretation, generated_at,
            ))


if __name__ == "__main__":
    run()
    print(f"Persisted governed decision-support outputs in {DB_PATH}")
