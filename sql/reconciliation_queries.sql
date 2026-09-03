-- Run after `python3 src/pipeline.py` to prove curated reporting totals reconcile.
SELECT * FROM vw_reconciliation_source_to_reporting;

-- Reconciliation must return zero rows before release.
SELECT * FROM vw_reconciliation_source_to_reporting WHERE reconciliation_status <> 'PASS';

-- Reusable KPI, trend, cohort, and exception queries for report consumers.
SELECT * FROM vw_workforce_kpis ORDER BY period_date, org_id, job_family;
SELECT * FROM vw_kpi_period_trends ORDER BY org_id, job_family, period_date;
SELECT * FROM vw_hiring_cohorts ORDER BY hire_cohort_month, org_id, job_family;
SELECT * FROM vw_productivity_exceptions ORDER BY period_date, org_id, job_family, worker_id;
