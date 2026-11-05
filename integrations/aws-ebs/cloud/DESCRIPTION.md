## Setup

1. Stream CloudWatch metrics to Kloudfuse through Kinesis Firehose: [AWS CloudWatch Metrics Integration](https://docs.kloudfuse.com/platform/latest/integration/aws/cloudwatch-metrics/).
2. Include the `AWS/EBS` namespace in the metric stream, or stream all namespaces.
3. Volume-level metrics appear only for volumes attached to a running instance: see [CloudWatch Enablement Reference](https://docs.kloudfuse.com/platform/latest/reference/aws/cloudwatch/#ebs-metrics).
