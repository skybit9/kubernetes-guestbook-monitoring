# Kubernetes Guestbook with Prometheus + Grafana Monitoring

Extends the official [Pulumi Python Guestbook](https://github.com/pulumi/examples/tree/master/kubernetes-py-guestbook) with full observability using `kube-prometheus-stack`.

---

## Architecture

```
Pulumi (Python)
├── guestbook.py        → Redis Leader, Redis Replica, Frontend (PHP)
└── monitoring.py       → Prometheus + Grafana via Helm (kube-prometheus-stack)
                          + ServiceMonitor for frontend scraping
```

```
                    ┌─────────────────────────────────────┐
                    │          Minikube Cluster            │
                    │                                      │
                    │  [Frontend PHP]     NodePort 30080   │
                    │  [Redis Leader]     port 6379        │
                    │  [Redis Replica]    port 6379        │
                    │                                      │
                    │  [Prometheus]       port 9090        │
                    │  [Grafana]          NodePort 30300   │
                    │  [kube-state-metrics]                │
                    │  [node-exporter]                     │
                    └─────────────────────────────────────┘
```

---

## Prerequisites

> **Note:** Written for **macOS**. Commands use Homebrew and macOS-specific tooling.

| Tool | Install |
|------|---------|
| Docker Desktop | https://docker.com |
| Minikube | `brew install minikube` |
| kubectl | `brew install kubectl` |
| Pulumi | `brew install pulumi` |
| Python 3.14 | `brew install python@3.14` |

> **Docker Desktop requirement:** Allocate at least **8GB RAM**.
> Docker Desktop → Settings → Resources → Memory → 8GB → Apply & Restart.

---

## Deploy the Application

### 1. Start Minikube

```bash
minikube start --cpus=4 --memory=8192 --driver=docker
```

Verify:

```bash
kubectl get nodes
# STATUS = Ready
```

### 2. Clone and Setup Project

```bash
git clone https://github.com/skybit9/kubernetes-guestbook-monitoring
cd kubernetes-guestbook-monitoring

pulumi login --local

python3 -m venv venv
source venv/bin/activate

pip install pulumi pulumi-kubernetes
```

### 3. Configure and Deploy

```bash
pulumi config set isMinikube true
PULUMI_CONFIG_PASSPHRASE="" pulumi up --yes
```

Expected output:

```
+ 9 resources created
Duration: ~90s
```

### 4. Access the Applications

> **CRITICAL — Read this before running anything below:**
>
> - Each service requires its **own dedicated terminal tab** that must stay open.
> - **Closing a terminal tab kills the tunnel — the service becomes immediately unreachable.**
> - Ports are assigned dynamically on every run. Always use the `http://127.0.0.1:<PORT>` URL printed in the terminal. Never use the `192.168.x.x` URL.
> - Service names contain a **random suffix generated at deploy time** and change on every fresh deploy. The commands below use `kubectl` to look up the correct name automatically — copy and run them exactly as written. Do not hardcode or guess the service name.

**Terminal 1 — Guestbook frontend (keep open):**
```bash
minikube service frontend
```

**Terminal 2 — Grafana (keep open or Grafana is unreachable):**
```bash
minikube service $(kubectl get svc -n monitoring -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}') -n monitoring
```

**Terminal 3 — Prometheus (keep open or Prometheus is unreachable):**
```bash
minikube service $(kubectl get svc -n monitoring -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].metadata.name}') -n monitoring --url
```

After running each command, copy the `http://127.0.0.1:<PORT>` URL from the terminal output and open it in your browser.

---

## Grafana Access Details

| Field | Value |
|-------|-------|
| URL | `http://127.0.0.1:<PORT>` (from Terminal 2 above) |
| Username | `admin` |
| Password | `admin123` |

### View Guestbook Dashboard (Stretch Goal)

The custom **Guestbook Application** dashboard is provisioned automatically via Helm and displays live metrics for all 3 pods.

1. Login to Grafana
2. Left menu → **Dashboards**
3. Open **Guestbook Application**
4. Dashboard panels:
   - **CPU Usage by Pod** — CPU consumption rate per pod (frontend, redis-leader, redis-replica)
   - **Memory Usage by Pod** — working set memory in MiB per pod
   - **Pod Restart Count** — restart count with green (healthy) / yellow (5+ restarts) threshold

### View Built-in Kubernetes Dashboard

1. Left menu → **Dashboards**
2. Open **Kubernetes / Compute Resources / Namespace (Pods)**
3. Set `namespace = default`
4. All 3 guestbook pods visible: `frontend`, `redis-leader`, `redis-replica`

---

## Verify Prometheus is Scraping Metrics

### Method 1: Prometheus Targets UI

1. Open Prometheus (Terminal 3)
2. Click **Status → Target Health**
3. Confirm all targets show `UP`
4. `serviceMonitor/monitoring/frontend-monitor/0` visible in list

### Method 2: kubectl

```bash
kubectl get servicemonitor -n monitoring
# Expected: frontend-monitor listed
```

### Method 3: Query Prometheus directly

In Prometheus UI → **Query** tab:

```promql
kube_pod_info{namespace="default"}
```

Returns rows for `frontend`, `redis-leader`, `redis-replica`.

```promql
container_cpu_usage_seconds_total{pod=~"frontend.*|redis-leader.*|redis-replica.*"}
```

Returns CPU metrics for all 3 pods.

```promql
container_memory_working_set_bytes{namespace="default",pod=~"frontend.*|redis-leader.*|redis-replica.*"}
```

Returns memory metrics for all 3 pods.

---

## Known Limitations

**Frontend /metrics endpoint:** The PHP guestbook frontend does not expose a `/metrics` endpoint. Prometheus scrapes the pod but receives `HTTP 404`. Pod resource metrics (CPU, memory, restarts) are available via **cAdvisor** and **kube-state-metrics**, both bundled with `kube-prometheus-stack` — these power the Guestbook Application dashboard.

**Minikube cAdvisor label behaviour:** On Minikube, `container_cpu_usage_seconds_total` does not include a `namespace` label in cAdvisor metrics. The dashboard CPU query therefore filters by pod name regex instead of namespace. Memory uses `container_memory_working_set_bytes` (with namespace label) rather than `container_memory_rss`, which is not available per-namespace on Minikube.

---

## Project Structure

```
kubernetes-guestbook-monitoring/
├── __main__.py          # Entry point — imports guestbook and monitoring
├── guestbook.py         # Redis Leader, Redis Replica, Frontend deployments
├── monitoring.py        # Prometheus + Grafana Helm release + ServiceMonitor
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── requirements.txt
└── README.md
```

---

## Teardown

```bash
PULUMI_CONFIG_PASSPHRASE="" pulumi destroy --yes
minikube stop
```