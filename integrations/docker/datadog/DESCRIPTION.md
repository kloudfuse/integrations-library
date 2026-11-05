## Setup

Collected by the Datadog agent. See [Docker with the Datadog Agent](https://docs.kloudfuse.com/platform/latest/integration/dd-agent/docker/).

Enable the `docker` check on the pods to monitor with an Autodiscovery annotation such as `ad.datadoghq.com/<container>.check_names: '["docker"]'`.
