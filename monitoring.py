import json
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs
from pulumi_kubernetes.apiextensions import CustomResource

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
                "dashboardProviders": {
                    "dashboardproviders.yaml": {
                        "apiVersion": 1,
                        "providers": [{
                            "name": "default",
                            "orgId": 1,
                            "folder": "",
                            "type": "file",
                            "disableDeletion": False,
                            "allowUiUpdates": True,
                            "options": {"path": "/var/lib/grafana/dashboards/default"},
                        }],
                    }
                },
                "dashboards": {
                    "default": {
                        "guestbook-app": {
                            "json": json.dumps({
                                "title": "Guestbook Application",
                                "uid": "guestbook-app-001",
                                "schemaVersion": 36,
                                "refresh": "30s",
                                "templating": {
                                    "list": [{
                                        "name": "datasource",
                                        "type": "datasource",
                                        "pluginId": "prometheus",
                                        "label": "Data Source",
                                        "hide": 0,
                                        "refresh": 1,
                                        "current": {"text": "Prometheus", "value": "prometheus"},
                                    }]
                                },
                                "panels": [
                                    {
                                        "id": 1,
                                        "title": "CPU Usage by Pod",
                                        "type": "timeseries",
                                        "gridPos": {"x": 0, "y": 0, "w": 24, "h": 8},
                                        "datasource": {"type": "prometheus", "uid": "${datasource}"},
                                        "targets": [{
                                            "refId": "A",
                                            "datasource": {"type": "prometheus", "uid": "${datasource}"},
                                            "legendFormat": "{{ pod }}",
                                            "expr": "sum(rate(container_cpu_usage_seconds_total{pod=~\"frontend.*|redis-leader.*|redis-replica.*\"}[2m])) by (pod)",
                                        }],
                                        "fieldConfig": {"defaults": {"unit": "percentunit"}},
                                    },
                                    {
                                        "id": 2,
                                        "title": "Memory Usage by Pod",
                                        "type": "timeseries",
                                        "gridPos": {"x": 0, "y": 8, "w": 24, "h": 8},
                                        "datasource": {"type": "prometheus", "uid": "${datasource}"},
                                        "targets": [{
                                            "refId": "A",
                                            "datasource": {"type": "prometheus", "uid": "${datasource}"},
                                            "legendFormat": "{{ pod }}",
                                            "expr": "container_memory_working_set_bytes{namespace=\"default\",pod=~\"frontend.*|redis-leader.*|redis-replica.*\"}",
                                        }],
                                        "fieldConfig": {"defaults": {"unit": "bytes"}},
                                    },
                                    {
                                        "id": 3,
                                        "title": "Pod Restart Count",
                                        "type": "stat",
                                        "gridPos": {"x": 0, "y": 16, "w": 24, "h": 4},
                                        "datasource": {"type": "prometheus", "uid": "${datasource}"},
                                        "targets": [{
                                            "refId": "A",
                                            "datasource": {"type": "prometheus", "uid": "${datasource}"},
                                            "legendFormat": "{{ pod }}",
                                            "expr": "kube_pod_container_status_restarts_total{namespace=\"default\",pod=~\"frontend.*|redis-leader.*|redis-replica.*\"}",
                                        }],
                                        "fieldConfig": {
                                            "defaults": {
                                                "unit": "short",
                                                "thresholds": {
                                                    "mode": "absolute",
                                                    "steps": [
                                                        {"color": "green", "value": None},
                                                        {"color": "yellow", "value": 5},
                                                    ],
                                                },
                                            }
                                        },
                                        "options": {"colorMode": "background"},
                                    },
                                ],
                            })
                        }
                    }
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

# ServiceMonitor for guestbook frontend
# Note: PHP frontend does not expose /metrics — Prometheus will reach the pod
# but receive HTTP 404. Pod resource metrics (CPU, memory, restarts) are
# available via cAdvisor and kube-state-metrics bundled with kube-prometheus-stack.
frontend_monitor = CustomResource(
    "frontend-service-monitor",
    api_version="monitoring.coreos.com/v1",
    kind="ServiceMonitor",
    metadata={
        "name": "frontend-monitor",
        "namespace": "monitoring",
        "labels": {"release": "kube-prometheus-stack"},
    },
    spec={
        "namespaceSelector": {"matchNames": ["default"]},
        "selector": {"matchLabels": {"app": "frontend"}},
        "endpoints": [{"port": "http", "path": "/metrics", "interval": "30s"}],
    },
    opts=pulumi.ResourceOptions(depends_on=[prometheus_stack]),
)

pulumi.export("grafana_url", "http://$(minikube ip):30300")
pulumi.export("grafana_user", "admin")
pulumi.export("grafana_password", "admin123")
pulumi.export("grafana_dashboard", "Dashboards > default > Guestbook Application")