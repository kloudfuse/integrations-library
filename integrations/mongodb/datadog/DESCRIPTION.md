## Setup

Collected by the Datadog agent. See [MongoDB Integration](https://docs.kloudfuse.com/platform/latest/integration/dd-agent/mongodb/).

Enable the `mongo` check on the pods to monitor with an Autodiscovery annotation such as `ad.datadoghq.com/<container>.check_names: '["mongo"]'`.
