import pulumi
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs

# Deploy kube-prometheus-stack via Helm
prometheus_stack = Release(
    "kube-prometheus-stack",
    ReleaseArgs(
        chart="kube-prometheus-stack",
        namespace="monitoring",
        create_namespace=True,
        repository_opts=RepositoryOptsArgs(
            repo="https://prometheus-community.github.io/helm-charts",
        ),
        values={
            "grafana": {
                "adminPassword": "admin123",
                "service": {
                    "type": "NodePort",
                    "nodePort": 30300,
                },
            },
            "prometheus": {
                "prometheusSpec": {
                    "podMonitorSelectorNilUsesHelmValues": False,
                    "serviceMonitorSelectorNilUsesHelmValues": False,
                },
            },
        },
    ),
)

pulumi.export("grafana_url", "http://$(minikube ip):30300")
pulumi.export("grafana_user", "admin")
pulumi.export("grafana_password", "admin123")