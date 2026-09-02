# Workforce Lens

Workforce Lens is a business analytics foundation for capacity, attrition, and productivity planning. It helps HR, operations, and finance make consistent workforce decisions using governed metrics and shared planning assumptions.

## Project charter

See [requirements](docs/requirements.md), [KPI catalog](docs/kpi_catalog.md), [data dictionary](docs/data_dictionary.md), and [assumptions](docs/assumptions.md).

## Architecture

```text
HRIS / ATS / Timekeeping / Finance / Operations
                    │
                    ▼
             data/raw (immutable extracts)
                    │
                    ▼
          data/staging (validated, conformed)
                    │
                    ▼
       SQL models and governed KPI calculations
                    │
          ┌─────────┼──────────┐
          ▼         ▼          ▼
      Power BI    Excel      Reports
```

## Repository layout

| Path | Purpose |
| --- | --- |
| `data/raw` | Access-controlled source extracts; never hand-edit. |
| `data/staging` | Validated, conformed intermediate data. |
| `sql` / `src` | Transformations and reusable analytics code. |
| `notebooks` / `tests` | Exploration and automated quality checks. |
| `powerbi` / `excel` / `reports` | Consumer-facing planning artifacts. |

## Screenshot placeholders

<!-- Add approved dashboard screenshots here. Do not include employee-level or sensitive data. -->

| Capacity planning | Attrition risk | Productivity trends |
| --- | --- | --- |
| `![Capacity dashboard](reports/screenshots/capacity-planning.png)` | `![Attrition dashboard](reports/screenshots/attrition-risk.png)` | `![Productivity dashboard](reports/screenshots/productivity-trends.png)` |

## Working agreement

Metrics and dimensions must follow the catalog and dictionary. Raw HR data remains restricted; reporting outputs must meet the privacy rules in the requirements. Run tests before publishing an update.

## Publish workflow

This repository configures a local post-commit hook that attempts `git push` after each commit once a GitHub remote exists. It is intentionally best-effort: a failed push leaves the commit local and visible for retry with `git push`.
