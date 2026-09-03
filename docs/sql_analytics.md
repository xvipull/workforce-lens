# SQL Analytics Layer

`sql/analytics_views.sql` is loaded automatically after the conformed stage and star model. All KPI views operate from `fact_workforce_snapshot`; the only exception is the explicitly labelled staging-side of the reconciliation view.

| View | Purpose |
| --- | --- |
| `vw_workforce_kpis` | Reusable headcount, FTE, voluntary attrition, capacity shortfall, productivity, labor-cost/FTE, and vacancy measures at period × organization × location × job family × scenario grain. |
| `vw_kpi_period_trends` | Uses `LAG` window functions for period-over-period headcount and productivity change. A single-period source correctly returns null prior-period deltas. |
| `vw_hiring_cohorts` | Segments observed workers by hire month, organization, and job family; reports observed workers, active FTE, and tenure. |
| `vw_productivity_exceptions` | Flags nonzero-variance segments where productivity is more than two standard deviations from the segment mean. This is a review queue, never an employment-action recommendation. |
| `vw_reconciliation_source_to_reporting` | Compares the validated `stg_workforce_snapshot` source landing totals to curated fact totals. Row count must match exactly; FTE, productive hours, output, and INR labor cost each permit at most 0.01 absolute difference. |

Run `sqlite3 data/workforce_lens.db < sql/reconciliation_queries.sql` after `python3 src/pipeline.py`. Release is blocked if the second reconciliation query returns any row.

## EDA

Run `make eda` after the pipeline. The Pandas/NumPy/Matplotlib script examines post-cleaning missingness, IQR outlier candidates, distribution, correlation, and aggregate operational drivers. It saves four purpose-specific PNGs to `reports/figures`; no employee identifiers appear in the figures.
