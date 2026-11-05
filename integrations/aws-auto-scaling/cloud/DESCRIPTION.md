## Setup

1. Stream CloudWatch metrics to Kloudfuse through Kinesis Firehose: [AWS CloudWatch Metrics Integration](https://docs.kloudfuse.com/platform/latest/integration/aws/cloudwatch-metrics/).
2. Include the `AWS/AutoScaling` namespace in the metric stream, or stream all namespaces.
3. Group-level metrics (instance counts, scaling activity) must be enabled per Auto Scaling group: see [CloudWatch Enablement Reference](https://docs.kloudfuse.com/platform/latest/reference/aws/cloudwatch/#autoscaling).
