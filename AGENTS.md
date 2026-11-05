# AGENTS.md

Rules for AI agents and contributors editing this repo. The layout, file formats and
collector values are in [README.md](./README.md); read it first.

## Every change

- Edit only `integrations/` and `tags.json`. `dist/` is generated: never edit it by hand.
- Run `python3 scripts/validate.py --write` and commit the regenerated `dist/` in the same
  commit as the source change. CI fails on a stale `dist/`.
- Run `python3 -m unittest discover tests` if you touch `scripts/`.

## Alert rules

- Rules use Grafana's **provisioning-export** shape: `title`, `condition`, `data`,
  `noDataState`, `execErrState`, `for`, `annotations`, `labels` directly on the rule.
- A rule copied from Grafana's ruler API (nested under `grafana_alert`, snake_case
  `no_data_state` / `exec_err_state`) must be translated. Copying the snake_case keys
  across silently loses the no-data and error settings on import.
- One rule group per file in `alerts/`. Name the group, and the file, after the
  integration id (`aws-rds-cloud`), or the id plus a suffix (`aws-rds-cloud-storage`).

## Dashboards

- One Grafana dashboard per file in `dashboards/`, named after its title in kebab-case.
- Reference datasources by the fixed Kloudfuse UIDs already used in this repo
  (Prometheus `P09C4D52DEC9B98E6`); don't introduce new datasource UIDs.

## Collector and splitting

- Decide `otel` / `datadog` / `cloud` from the **metric names** in the queries, not from a
  folder or file name. Datadog-agent metrics look like `redis_stats_keyspace_hits` and
  carry `kube_cluster_name`; OTel metrics look like `k8s_pod_phase` or
  `system_cpu_utilization`.
- A cloud integration covers one metric namespace: every dashboard in `aws-rds/cloud`
  queries `aws_rds_*`. A new service gets a new folder, not a dashboard in a neighbor's.

## Tags

- Use the tags already in `tags.json`. Add a new one only when no existing tag fits, and
  keep them lowercase.

## This repo will be public

- No customer names, customer-specific dashboards, internal hostnames, tokens or
  webhook URLs. Scan before committing content copied from anywhere else.

## Verifying

Validation proves the format, not that the content works. Before calling an
integration done, upload its `dist/<id>.json` on a test cluster's Integrations page
(`/admin/integrations` → Upload package) and check that the dashboards render and the
alert rules evaluate.
