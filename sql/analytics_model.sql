PRAGMA foreign_keys = ON;

-- Conformed landing table. Grain: one source worker, snapshot date, and scenario.
CREATE TABLE stg_workforce_snapshot (
  snapshot_date TEXT NOT NULL,
  worker_id TEXT NOT NULL,
  org_id TEXT NOT NULL,
  org_name TEXT NOT NULL,
  location_id TEXT NOT NULL,
  location_name TEXT NOT NULL,
  job_family TEXT NOT NULL,
  employment_status TEXT NOT NULL,
  fte_fraction REAL NOT NULL,
  hire_date TEXT NOT NULL,
  termination_date TEXT,
  termination_type TEXT,
  scheduled_hours REAL NOT NULL,
  productive_hours REAL NOT NULL,
  accepted_output_units REAL NOT NULL,
  labor_cost_inr REAL NOT NULL,
  currency TEXT NOT NULL,
  approved_position_count INTEGER NOT NULL,
  open_requisition_count INTEGER NOT NULL,
  scenario_id TEXT NOT NULL,
  UNIQUE(snapshot_date, worker_id, scenario_id)
);

CREATE TABLE dim_date (
  date_key INTEGER PRIMARY KEY,
  calendar_date TEXT NOT NULL UNIQUE,
  year INTEGER NOT NULL,
  month INTEGER NOT NULL,
  month_name TEXT NOT NULL,
  quarter INTEGER NOT NULL
);

CREATE TABLE dim_organization (
  organization_key INTEGER PRIMARY KEY,
  org_id TEXT NOT NULL UNIQUE,
  org_name TEXT NOT NULL
);

CREATE TABLE dim_location (
  location_key INTEGER PRIMARY KEY,
  location_id TEXT NOT NULL UNIQUE,
  location_name TEXT NOT NULL
);

CREATE TABLE dim_job_family (
  job_family_key INTEGER PRIMARY KEY,
  job_family TEXT NOT NULL UNIQUE
);

CREATE TABLE dim_scenario (
  scenario_key INTEGER PRIMARY KEY,
  scenario_id TEXT NOT NULL UNIQUE
);

-- Grain: one worker business key on one workforce snapshot date and scenario.
CREATE TABLE fact_workforce_snapshot (
  workforce_snapshot_key INTEGER PRIMARY KEY,
  snapshot_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
  organization_key INTEGER NOT NULL REFERENCES dim_organization(organization_key),
  location_key INTEGER NOT NULL REFERENCES dim_location(location_key),
  job_family_key INTEGER NOT NULL REFERENCES dim_job_family(job_family_key),
  scenario_key INTEGER NOT NULL REFERENCES dim_scenario(scenario_key),
  worker_id TEXT NOT NULL,
  employment_status TEXT NOT NULL,
  fte_fraction REAL NOT NULL,
  hire_date TEXT NOT NULL,
  termination_date TEXT,
  termination_type TEXT,
  scheduled_hours REAL NOT NULL,
  productive_hours REAL NOT NULL,
  accepted_output_units REAL NOT NULL,
  labor_cost_inr REAL NOT NULL,
  approved_position_count INTEGER NOT NULL,
  open_requisition_count INTEGER NOT NULL,
  UNIQUE(snapshot_date_key, worker_id, scenario_key)
);
