## Setup

1. Stream CloudWatch metrics to Kloudfuse through Kinesis Firehose: [AWS CloudWatch Metrics Integration](https://docs.kloudfuse.com/platform/latest/integration/aws/cloudwatch-metrics/).
2. Include the `AWS/EC2` namespace in the metric stream, or stream all namespaces.
3. EC2 publishes 5-minute metrics by default; 1-minute granularity needs detailed monitoring: see [CloudWatch Enablement Reference](https://docs.kloudfuse.com/platform/latest/reference/aws/cloudwatch/#ec2-detailed-monitoring).
