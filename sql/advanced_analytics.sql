-- Governed, aggregate-only decision-support outputs.
-- These tables deliberately contain no worker-level record or recommendation.

CREATE TABLE IF NOT EXISTS analytics_capacity_scenario (
  capacity_scenario_key INTEGER PRIMARY KEY,
  model_version TEXT NOT NULL,
  input_snapshot_date TEXT NOT NULL,
  organization_key INTEGER NOT NULL REFERENCES dim_organization(organization_key),
  job_family_key INTEGER NOT NULL REFERENCES dim_job_family(job_family_key),
  scenario_name TEXT NOT NULL,
  planned_hiring_fte REAL NOT NULL,
  expected_attrition_rate REAL NOT NULL,
  additional_absence_rate REAL NOT NULL,
  required_productive_hours REAL NOT NULL,
  available_productive_hours REAL NOT NULL,
  capacity_gap_hours REAL NOT NULL,
  incremental_labor_cost_inr REAL NOT NULL,
  generated_at TEXT NOT NULL,
  UNIQUE(model_version, input_snapshot_date, organization_key, job_family_key, scenario_name)
);

CREATE TABLE IF NOT EXISTS analytics_attrition_absence_drivers (
  driver_assessment_key INTEGER PRIMARY KEY,
  model_version TEXT NOT NULL,
  input_snapshot_date TEXT NOT NULL,
  organization_key INTEGER NOT NULL REFERENCES dim_organization(organization_key),
  job_family_key INTEGER NOT NULL REFERENCES dim_job_family(job_family_key),
  active_headcount INTEGER NOT NULL,
  voluntary_exit_rate REAL NOT NULL,
  absence_proxy_rate REAL NOT NULL,
  vacancy_rate REAL NOT NULL,
  new_hire_fte_share REAL NOT NULL,
  attrition_contribution REAL NOT NULL,
  absence_contribution REAL NOT NULL,
  vacancy_contribution REAL NOT NULL,
  new_hire_contribution REAL NOT NULL,
  priority_score REAL NOT NULL,
  priority_band TEXT NOT NULL,
  interpretation TEXT NOT NULL,
  generated_at TEXT NOT NULL,
  UNIQUE(model_version, input_snapshot_date, organization_key, job_family_key)
);

CREATE VIEW IF NOT EXISTS vw_capacity_scenario_summary AS
SELECT a.model_version, a.input_snapshot_date, o.org_id, o.org_name, j.job_family,
       a.scenario_name, a.planned_hiring_fte, a.expected_attrition_rate,
       a.additional_absence_rate, a.required_productive_hours, a.available_productive_hours,
       a.capacity_gap_hours, a.incremental_labor_cost_inr
FROM analytics_capacity_scenario a
JOIN dim_organization o ON o.organization_key = a.organization_key
JOIN dim_job_family j ON j.job_family_key = a.job_family_key;

CREATE VIEW IF NOT EXISTS vw_attrition_absence_driver_priorities AS
SELECT d.model_version, d.input_snapshot_date, o.org_id, o.org_name, j.job_family,
       d.active_headcount, d.voluntary_exit_rate, d.absence_proxy_rate, d.vacancy_rate,
       d.new_hire_fte_share, d.attrition_contribution, d.absence_contribution,
       d.vacancy_contribution, d.new_hire_contribution, d.priority_score,
       d.priority_band, d.interpretation
FROM analytics_attrition_absence_drivers d
JOIN dim_organization o ON o.organization_key = d.organization_key
JOIN dim_job_family j ON j.job_family_key = d.job_family_key;
