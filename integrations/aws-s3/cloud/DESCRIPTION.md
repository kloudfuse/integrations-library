## Setup

1. Stream CloudWatch metrics to Kloudfuse through Kinesis Firehose: [AWS CloudWatch Metrics Integration](https://docs.kloudfuse.com/platform/latest/integration/aws/cloudwatch-metrics/).
2. Include the `AWS/S3` namespace in the metric stream, or stream all namespaces.
3. Request metrics (GET, PUT, DELETE counts and latency) must be enabled per bucket and are billed by AWS: see [CloudWatch Enablement Reference](https://docs.kloudfuse.com/platform/latest/reference/aws/cloudwatch/#s3-request-metrics).
