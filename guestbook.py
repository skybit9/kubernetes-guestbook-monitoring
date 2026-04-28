import pulumi
from pulumi_kubernetes.apps.v1 import Deployment
from pulumi_kubernetes.core.v1 import Service

config = pulumi.Config()
is_minikube = config.get_bool("isMinikube") or True

# Redis Leader
redis_leader_labels = {"app": "redis-leader"}

redis_leader_deployment = Deployment(
    "redis-leader",
    spec={
        "selector": {"match_labels": redis_leader_labels},
        "replicas": 1,
        "template": {
            "metadata": {"labels": redis_leader_labels},
            "spec": {
                "containers": [{
                    "name": "redis-leader",
                    "image": "redis",
                    "resources": {"requests": {"cpu": "100m", "memory": "100Mi"}},
                    "ports": [{"container_port": 6379}],
                }]
            },
        },
    },
)

redis_leader_service = Service(
    "redis-leader",
    metadata={"name": "redis-leader", "labels": redis_leader_labels},
    spec={
        "ports": [{"port": 6379, "target_port": 6379}],
        "selector": redis_leader_labels,
    },
)

# Redis Replica
redis_replica_labels = {"app": "redis-replica"}

redis_replica_deployment = Deployment(
    "redis-replica",
    spec={
        "selector": {"match_labels": redis_replica_labels},
        "replicas": 1,
        "template": {
            "metadata": {"labels": redis_replica_labels},
            "spec": {
                "containers": [{
                    "name": "redis-replica",
                    "image": "pulumi/guestbook-redis-replica",
                    "resources": {"requests": {"cpu": "100m", "memory": "100Mi"}},
                    "env": [{"name": "GET_HOSTS_FROM", "value": "dns"}],
                    "ports": [{"container_port": 6379}],
                }]
            },
        },
    },
)

redis_replica_service = Service(
    "redis-replica",
    metadata={"name": "redis-replica", "labels": redis_replica_labels},
    spec={
        "ports": [{"port": 6379, "target_port": 6379}],
        "selector": redis_replica_labels,
    },
)

# Frontend
frontend_labels = {"app": "frontend"}

frontend_deployment = Deployment(
    "frontend",
    spec={
        "selector": {"match_labels": frontend_labels},
        "replicas": 1,
        "template": {
            "metadata": {
                "labels": frontend_labels,
                "annotations": {
                    "prometheus.io/scrape": "true",
                    "prometheus.io/port": "80",
                },
            },
            "spec": {
                "containers": [{
                    "name": "php-redis",
                    "image": "pulumi/guestbook-php-redis",
                    "resources": {"requests": {"cpu": "100m", "memory": "100Mi"}},
                    "env": [{"name": "GET_HOSTS_FROM", "value": "dns"}],
                    "ports": [{"container_port": 80}],
                }]
            },
        },
    },
)

frontend_service = Service(
    "frontend",
    metadata={
        "name": "frontend",
        "labels": frontend_labels,
        "annotations": {
            "prometheus.io/scrape": "true",
            "prometheus.io/port": "80",
        },
    },
    spec={
        "type": "NodePort",
        "ports": [{"port": 80, "target_port": 80, "node_port": 30080}],
        "selector": frontend_labels,
    },
)

frontend_ip = frontend_service.spec.apply(
    lambda spec: spec.cluster_ip or ""
)

pulumi.export("frontend_url", "http://$(minikube ip):30080")