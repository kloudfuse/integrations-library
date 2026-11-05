## Setup

Collected by the Datadog agent. See [Datadog integrations: Caching](https://docs.kloudfuse.com/platform/latest/reference/datadog/integrations/caching/).

Enable the `coredns` check on the pods to monitor with an Autodiscovery annotation such as `ad.datadoghq.com/<container>.check_names: '["coredns"]'`.
