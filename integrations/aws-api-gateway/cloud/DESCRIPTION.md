## Setup

1. Stream CloudWatch metrics to Kloudfuse through Kinesis Firehose: [AWS CloudWatch Metrics Integration](https://docs.kloudfuse.com/platform/latest/integration/aws/cloudwatch-metrics/).
2. Include the `AWS/ApiGateway` namespace in the metric stream, or stream all namespaces.
3. API Gateway publishes stage-level metrics by default; per-route metrics need detailed metrics: see [CloudWatch Enablement Reference](https://docs.kloudfuse.com/platform/latest/reference/aws/cloudwatch/#api-gateway-detailed-metrics).
