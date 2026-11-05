## Setup

1. Follow [GCP Metrics Integration](https://docs.kloudfuse.com/platform/latest/integration/kloudfuse/gcp-metrics/).
2. Add `kubernetes.io/`, `prometheus.googleapis.com` and `compute.googleapis.com` to `typePrefixes`.
3. The API server and scheduler panels read GKE control plane metrics (`prometheus.googleapis.com`), which must be enabled on the cluster.
