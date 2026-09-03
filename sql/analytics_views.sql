-- SQLite KPI, exception, cohort, trend, and reconciliation layer.
-- Apply after sql/analytics_model.sql. All report views use curated fact data.

CREATE VIEW vw_workforce_kpis AS
WITH base AS (
  SELECT d.calendar_date AS period_date, o.org_id, o.org_name, l.location_id, l.location_name,
         j.job_family, s.scenario_id, f.worker_id, f.employment_status, f.fte_fraction,
         f.scheduled_hours, f.productive_hours, f.accepted_output_units, f.labor_cost_inr,
         f.approved_position_count, f.open_requisition_count, f.termination_type
  FROM fact_workforce_snapshot f
  JOIN dim_date d ON d.date_key = f.snapshot_date_key
  JOIN dim_organization o ON o.organization_key = f.organization_key
  JOIN dim_location l ON l.location_key = f.location_key
  JOIN dim_job_family j ON j.job_family_key = f.job_family_key
  JOIN dim_scenario s ON s.scenario_key = f.scenario_key
)
SELECT period_date, org_id, org_name, location_id, location_name, job_family, scenario_id,
       COUNT(DISTINCT CASE WHEN employment_status = 'ACTIVE' THEN worker_id END) AS active_headcount,
       ROUND(SUM(CASE WHEN employment_status = 'ACTIVE' THEN fte_fraction ELSE 0 END), 2) AS active_fte,
       SUM(CASE WHEN termination_type = 'VOLUNTARY' THEN 1 ELSE 0 END) AS voluntary_exits,
       ROUND(1.0 * SUM(CASE WHEN termination_type = 'VOLUNTARY' THEN 1 ELSE 0 END) /
             NULLIF(COUNT(DISTINCT CASE WHEN employment_status = 'ACTIVE' THEN worker_id END), 0), 4) AS voluntary_attrition_rate,
       SUM(scheduled_hours) AS scheduled_hours,
       SUM(productive_hours) AS productive_hours,
       SUM(scheduled_hours) - SUM(productive_hours) AS capacity_shortfall_hours,
       ROUND(1.0 * SUM(accepted_output_units) / NULLIF(SUM(productive_hours), 0), 2) AS productivity_per_hour,
       ROUND(1.0 * SUM(labor_cost_inr) / NULLIF(SUM(CASE WHEN employment_status = 'ACTIVE' THEN fte_fraction ELSE 0 END), 0), 2) AS labor_cost_per_active_fte,
       MAX(approved_position_count) AS approved_positions,
       MAX(open_requisition_count) AS open_requisitions,
       ROUND(1.0 * MAX(open_requisition_count) / NULLIF(MAX(approved_position_count), 0), 4) AS vacancy_rate
FROM base
GROUP BY period_date, org_id, org_name, location_id, location_name, job_family, scenario_id;

CREATE VIEW vw_kpi_period_trends AS
WITH monthly AS (
  SELECT period_date, org_id, job_family, scenario_id,
         SUM(active_headcount) AS active_headcount,
         SUM(active_fte) AS active_fte,
         SUM(productive_hours) AS productive_hours,
         SUM(capacity_shortfall_hours) AS capacity_shortfall_hours,
         ROUND(1.0 * SUM(productivity_per_hour * productive_hours) / NULLIF(SUM(productive_hours), 0), 2) AS productivity_per_hour
  FROM vw_workforce_kpis
  GROUP BY period_date, org_id, job_family, scenario_id
)
SELECT *,
       active_headcount - LAG(active_headcount) OVER (PARTITION BY org_id, job_family, scenario_id ORDER BY period_date) AS headcount_change_pop,
       ROUND(1.0 * (productivity_per_hour - LAG(productivity_per_hour) OVER (PARTITION BY org_id, job_family, scenario_id ORDER BY period_date)) /
         NULLIF(LAG(productivity_per_hour) OVER (PARTITION BY org_id, job_family, scenario_id ORDER BY period_date), 0), 4) AS productivity_change_pct_pop
FROM monthly;

CREATE VIEW vw_hiring_cohorts AS
WITH worker_history AS (
  SELECT f.worker_id, o.org_id, j.job_family, d.calendar_date AS snapshot_date, f.hire_date,
         f.employment_status, f.fte_fraction,
         MIN(d.calendar_date) OVER (PARTITION BY f.worker_id, o.org_id, j.job_family) AS first_observed_date
  FROM fact_workforce_snapshot f
  JOIN dim_date d ON d.date_key = f.snapshot_date_key
  JOIN dim_organization o ON o.organization_key = f.organization_key
  JOIN dim_job_family j ON j.job_family_key = f.job_family_key
)
SELECT substr(hire_date, 1, 7) || '-01' AS hire_cohort_month, org_id, job_family,
       COUNT(DISTINCT worker_id) AS workers_observed,
       ROUND(SUM(CASE WHEN employment_status = 'ACTIVE' THEN fte_fraction ELSE 0 END), 2) AS active_fte,
       ROUND(AVG(julianday(snapshot_date) - julianday(hire_date)), 1) AS average_tenure_days
FROM worker_history
GROUP BY hire_cohort_month, org_id, job_family;

CREATE VIEW vw_productivity_exceptions AS
WITH worker_productivity AS (
  SELECT d.calendar_date AS period_date, o.org_id, j.job_family, f.worker_id,
         1.0 * f.accepted_output_units / NULLIF(f.productive_hours, 0) AS productivity_per_hour
  FROM fact_workforce_snapshot f
  JOIN dim_date d ON d.date_key = f.snapshot_date_key
  JOIN dim_organization o ON o.organization_key = f.organization_key
  JOIN dim_job_family j ON j.job_family_key = f.job_family_key
  WHERE f.productive_hours > 0
), baseline AS (
  SELECT period_date, org_id, job_family, AVG(productivity_per_hour) AS mean_productivity,
         AVG(productivity_per_hour * productivity_per_hour) - AVG(productivity_per_hour) * AVG(productivity_per_hour) AS variance
  FROM worker_productivity
  GROUP BY period_date, org_id, job_family
)
SELECT w.period_date, w.org_id, w.job_family, w.worker_id, ROUND(w.productivity_per_hour, 2) AS productivity_per_hour,
       ROUND(b.mean_productivity, 2) AS segment_mean,
       ROUND(b.variance, 4) AS segment_variance,
       'REVIEW: productivity outside segment variance boundary' AS exception_reason
FROM worker_productivity w
JOIN baseline b USING (period_date, org_id, job_family)
WHERE b.variance > 0
  AND ABS(w.productivity_per_hour - b.mean_productivity) > 2 * sqrt(b.variance);

-- Source in this layer is the validated clean landing table; reporting is the curated fact.
CREATE VIEW vw_reconciliation_source_to_reporting AS
WITH source_totals AS (
  SELECT snapshot_date AS period_date, scenario_id, COUNT(*) AS source_rows,
         SUM(fte_fraction) AS source_fte, SUM(productive_hours) AS source_productive_hours,
         SUM(accepted_output_units) AS source_output_units, SUM(labor_cost_inr) AS source_labor_cost
  FROM stg_workforce_snapshot GROUP BY snapshot_date, scenario_id
), reporting_totals AS (
  SELECT d.calendar_date AS period_date, s.scenario_id, COUNT(*) AS reporting_rows,
         SUM(f.fte_fraction) AS reporting_fte, SUM(f.productive_hours) AS reporting_productive_hours,
         SUM(f.accepted_output_units) AS reporting_output_units, SUM(f.labor_cost_inr) AS reporting_labor_cost
  FROM fact_workforce_snapshot f JOIN dim_date d ON d.date_key = f.snapshot_date_key
  JOIN dim_scenario s ON s.scenario_key = f.scenario_key
  GROUP BY d.calendar_date, s.scenario_id
)
SELECT src.period_date, src.scenario_id, src.source_rows, rpt.reporting_rows,
       src.source_fte, rpt.reporting_fte, src.source_productive_hours, rpt.reporting_productive_hours,
       src.source_output_units, rpt.reporting_output_units, src.source_labor_cost, rpt.reporting_labor_cost,
       CASE WHEN src.source_rows = rpt.reporting_rows
              AND ABS(src.source_fte - rpt.reporting_fte) <= 0.01
              AND ABS(src.source_productive_hours - rpt.reporting_productive_hours) <= 0.01
              AND ABS(src.source_output_units - rpt.reporting_output_units) <= 0.01
              AND ABS(src.source_labor_cost - rpt.reporting_labor_cost) <= 0.01
            THEN 'PASS' ELSE 'FAIL' END AS reconciliation_status,
       '0.01 absolute tolerance for numeric measures; exact row counts' AS documented_tolerance
FROM source_totals src JOIN reporting_totals rpt USING (period_date, scenario_id);
