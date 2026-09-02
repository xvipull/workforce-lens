# Project Charter: Workforce Capacity, Attrition & Productivity Planning

## Purpose and business problem

Leaders currently reconcile headcount, vacancies, attendance, exits, and output in separate spreadsheets. Definitions differ by function and reporting is retrospective, making it difficult to identify capacity gaps, assess attrition exposure, or fund the right hiring and productivity actions. Workforce Lens provides a governed planning layer at approved organizational and time levels.

## Stakeholder personas

| Persona | Needs | Primary actions |
| --- | --- | --- |
| HR Business Partner (HRBP) | Equitable workforce visibility and retention signals | Review workforce movement, flag hotspots, support interventions. |
| Operations Manager | Reliable staffing-to-demand view | Compare required versus available capacity; prioritize hiring, schedules, and process improvements. |
| Finance Planning | Auditable cost and scenario inputs | Forecast labor expense, validate plan-versus-actual, and assess funding trade-offs. |

## Decisions supported

- Where should hiring requisitions, redeployment, overtime, or contingent labor close a capacity gap?
- Which approved population or location shows material voluntary-attrition exposure requiring a retention plan?
- Does a productivity change reflect staffing, demand, mix, quality, or a measurement issue?
- What is the headcount, FTE, labor-cost, and output impact of baseline, hiring, and attrition scenarios?

## Scope

**In scope:** monthly and weekly workforce snapshots; approved organization/location/job-family aggregations; hires, exits, vacancies, FTE, capacity, labor cost, demand/output, productivity, and scenario planning; Power BI and Excel-ready semantic outputs; data-quality controls and metric documentation.

**Out of scope:** automated employment decisions, individual performance ranking, disciplinary action, compensation recommendations, candidate screening, real-time workforce scheduling, and prediction scores at individual employee level.

## Data ownership and cadence

| Domain | System-of-record owner | Planned refresh |
| --- | --- | --- |
| Worker, organization, job, hire/exit | HRIS / People Operations | Weekly; month-end certified |
| Requisitions and vacancies | Talent Acquisition | Weekly |
| Hours, attendance, overtime | Timekeeping / Payroll | Weekly; month-end certified |
| Labor cost and plan | Finance Planning | Monthly, with monthly forecast cycle |
| Demand, output, quality | Operations Analytics | Weekly |

## Security and privacy

Apply least privilege and role-based access. Keep employee identifiers only in restricted raw/staging zones; dashboards use approved aggregated views and minimum group-size suppression (default: fewer than 10 people). Do not expose protected characteristics, free-text HR notes, health/leave details, compensation detail, or individual attrition predictions. Encrypt data in transit and at rest, retain according to HR/legal policy, and log access to restricted data. HR and Legal/Privacy must approve any new sensitive field or external sharing.

## Assumptions and risks

The operating assumptions are maintained in [assumptions.md](assumptions.md). Key risks include late or inconsistent source extracts, organization hierarchy changes, denominator misuse, productivity measures that ignore work mix or quality, inappropriate inference from aggregate patterns, and access-control misconfiguration. Mitigations include certified close dates, effective-dated mappings, reconciliation tests, metric caveats, human review, and quarterly access reviews.

## Measurable acceptance criteria

1. HRIS month-end active headcount and FTE reconcile to the certified HR report within ±0.5% by organization and month.
2. Finance labor cost reconciles to the approved monthly finance total within ±1.0%, with exceptions documented.
3. KPI outputs include the catalog definition, owner, period, and last-refresh timestamp; all required fields are populated for 100% of published KPIs.
4. Weekly data is available by 12:00 local time on the second business day after source delivery; month-end certified outputs are available by the fifth business day.
5. Capacity gap, voluntary attrition, and productivity views support approved organization/location/job-family filters and suppress groups below the privacy threshold.
6. Automated quality tests cover uniqueness, referential integrity, valid date ranges, and null thresholds; release blocks on critical test failure.
7. HRBP, Operations, and Finance each complete an acceptance walkthrough using two agreed planning scenarios and sign off on metric interpretation.
