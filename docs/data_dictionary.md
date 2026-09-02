# Data Dictionary

| Field | Type | Description | Source owner | Classification |
| --- | --- | --- | --- | --- |
| `snapshot_date` | date | As-of date of workforce snapshot | People Operations | Internal |
| `worker_id` | string | Pseudonymous worker identifier; restricted zone only | People Operations | Restricted personal data |
| `org_id` | string | Effective-dated organization identifier | People Operations | Internal |
| `location_id` | string | Approved work location identifier | People Operations | Internal |
| `job_family` | string | Standardized job family | People Operations | Internal |
| `employment_status` | string | Active, leave, terminated, etc. | People Operations | Restricted personal data |
| `fte_fraction` | decimal | Contracted FTE fraction | People Operations | Restricted personal data |
| `hire_date` | date | Worker start date | People Operations | Restricted personal data |
| `termination_date` | date | Worker end date, if applicable | People Operations | Restricted personal data |
| `termination_type` | string | Voluntary/involuntary/other standardized exit type | HRBP | Restricted personal data |
| `approved_position_count` | integer | Budgeted approved positions | Finance Planning | Confidential |
| `open_requisition_count` | integer | Open approved requisitions | Talent Acquisition | Confidential |
| `scheduled_hours` | decimal | Planned paid/scheduled hours | Timekeeping | Restricted personal data |
| `productive_hours` | decimal | Approved productive-hours measure | Operations Analytics | Confidential |
| `accepted_output_units` | decimal | Output passing stated quality rule | Operations Analytics | Confidential |
| `labor_cost` | decimal | Approved labor cost in reporting currency | Finance Planning | Confidential |
| `scenario_id` | string | Named planning scenario | Finance Planning | Internal |
| `refresh_timestamp` | timestamp | Source ingestion completion timestamp | Data Engineering | Internal |

No protected characteristics, health information, free-text notes, home addresses, bank data, or individual performance assessments are part of this model.
