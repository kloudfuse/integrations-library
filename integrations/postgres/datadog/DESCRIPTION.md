## Setup

Collected by the Datadog agent. See [PostgreSQL Integration](https://docs.kloudfuse.com/platform/latest/integration/dd-agent/postgresql/).

Enable the `postgres` check on the pods to monitor with an Autodiscovery annotation such as `ad.datadoghq.com/<container>.check_names: '["postgres"]'`.
