## Setup

Collected by the Datadog agent. See [Datadog integrations: Message Queues & Streaming](https://docs.kloudfuse.com/platform/latest/reference/datadog/integrations/message-queues/).

Enable the `kafka` and `kafka_consumer` checks on the pods to monitor with an Autodiscovery annotation such as `ad.datadoghq.com/<container>.check_names: '["kafka", "kafka_consumer"]'`.

The broker check reads JMX, so the agent needs JMX access to the brokers.
