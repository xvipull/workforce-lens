# Advanced Decision-Support Analytics

## Purpose and safeguards

The capacity scenarios and attrition/absence driver output support HRBP, Operations, and Finance planning conversations. They are aggregate outputs at **snapshot date × organization × job family** grain. They must never be used to make, recommend, or automate hiring, termination, performance, compensation, scheduling, or other employment decisions about an individual.

No employee identifiers, protected characteristics, individual predictions, or individual rankings are persisted in these analytical outputs. Use the results as a prompt to inspect data quality, workload, hiring plans, and manager context; HRBP remains accountable for any action.

## Capacity scenarios

`analytics_capacity_scenario` persists four versioned scenarios per aggregate segment. Required productive hours use scheduled hours as a planning-demand proxy. Available productive hours equal active FTE plus planned hiring FTE, multiplied by observed productive hours per active FTE and applicable attrition/absence assumptions.

| Scenario | Planned hiring FTE | Expected attrition | Additional absence | Decision use |
| --- | ---: | ---: | ---: | --- |
| `BASELINE` | 0 | 0% | 0% | Reference using observed productivity. |
| `HIRING_ACCELERATED` | 2 | 0% | 0% | Illustrates capacity and monthly labor-cost effect of two additional FTE. |
| `ATTRITION_PRESSURE` | 0 | 10% | 0% | Sensitivity to an illustrative aggregate attrition shock. |
| `ABSENCE_PRESSURE` | 0 | 0% | 10% | Sensitivity to an illustrative additional availability reduction. |

## Interpretable attrition/absence driver priority

`analytics_attrition_absence_drivers` is a transparent heuristic, not a predictive risk model. Its 0–100 score is the sum of capped, inspectable contributions: voluntary exits (35 points at 10%), scheduled-to-productive-hours availability loss proxy (25 points at 15%), vacancy rate (20 points at 15%), and recent-hire FTE share (20 points at 20%). Bands are `MONITOR` below 33, `REVIEW` from 33–65.99, and `FOCUS` from 66 upward.

The availability-loss measure is explicitly a proxy: it cannot distinguish absence from work mix, training, data defects, downtime, or quality work. The synthetic source is a single snapshot with a small population, so it cannot establish causation, forecast attrition, or support statistically stable comparisons. Recalibrate thresholds only after HR, Operations, Finance, and Privacy approval using enough historical aggregate data.

## Governed access and operation

Run `make advanced` after `make pipeline`. SQL consumers use `vw_capacity_scenario_summary` and `vw_attrition_absence_driver_priorities`, not the worker-level fact. Model version, timestamp, scenario assumptions, and contribution fields provide traceability. Outputs should continue to observe the repository privacy threshold before dashboard publication.
