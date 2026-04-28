# Kubernetes Guestbook with Prometheus + Grafana Monitoring

Extends the official [Pulumi Python Guestbook](https://github.com/pulumi/examples/tree/master/kubernetes-py-guestbook) with full observability using `kube-prometheus-stack`.

---

## Architecture

```
Pulumi (Python)
├── guestbook.py        → Redis Leader, Redis Replica, Frontend (PHP)
└── monitoring.py       → Prometheus + Grafana via Helm (kube-prometheus-stack)
```

```
                    ┌─────────────────────────────┐
                    │        Minikube Cluster       │
                    │                               │
                    │  [Frontend PHP]  port 30080   │
                    │  [Redis Leader]  port 6379    │
                    │  [Redis Replica] port 6379    │
                    │                               │
                    │  [Prometheus]    port 9090    │
                    │  [Grafana]       port 30300   │
                    └─────────────────────────────┘
```

---

## Prerequisites

> **Note:** This guide is written for **macOS**. Commands use Homebrew and macOS-specific tooling. Steps will differ on Windows or Linux.

| Tool | Install |
|------|---------|
| Docker Desktop | https://docker.com |
| Minikube | `brew install minikube` |
| kubectl | `brew install kubectl` |
| Pulumi | `brew install pulumi` |
| Python 3.14 | `brew install python@3.14` |

---

## Deploy the Application

### 1. Start Minikube

```bash
minikube start --cpus=4 --memory=8192 --driver=docker
```

> **Requirement:** Docker Desktop must have at least **8GB RAM** allocated. Go to Docker Desktop → Settings → Resources → Memory → set to 8GB or higher → Apply & Restart.

Verify:
```bash
kubectl get nodes
# Should show 1 node, STATUS = Ready
```

### 2. Clone and Setup Project

```bash
git clone <your-repo-url>
cd guestbook-monitoring

pulumi login --local

python3 -m venv venv
source venv/bin/activate

pip install pulumi pulumi-kubernetes
```

### 3. Configure and Deploy

```bash
pulumi config set isMinikube true
pulumi up
```

Type `yes` when prompted. Deployment takes ~2-3 minutes.

Expected output:
```
+ 8 resources created
Duration: ~80s
```

### 4. Access the Applications

Each service requires its own terminal tab. Keep all tabs open while using the apps.

**Terminal Tab 1 — Guestbook:**
```bash
minikube service frontend
# Opens browser at http://127.0.0.1:<PORT>
```

**Terminal Tab 2 — Grafana:**
```bash
minikube service kube-prometheus-stack-305d0c41-grafana -n monitoring
# Opens browser at http://127.0.0.1:<PORT>
```

**Terminal Tab 3 — Prometheus:**
```bash
minikube service kube-prometheus-stack-305d-prometheus -n monitoring
# Opens browser at http://127.0.0.1:<PORT>
```

> Note: Ports are dynamically assigned each time. Always use the `127.0.0.1` URL, not the `192.168.x.x` URL shown.

---

## Grafana Access Details

| Field | Value |
|-------|-------|
| URL | `http://127.0.0.1:<PORT>` (from terminal output above) |
| Username | `admin` |
| Password | `admin123` |

### View Guestbook Metrics in Grafana

1. Login to Grafana
2. Left menu → **Dashboards**
3. Open **Kubernetes / Compute Resources / Namespace (Pods)**
4. Set `namespace` = `default`
5. All 3 guestbook pods are visible: `frontend`, `redis-leader`, `redis-replica`

---

## Verify Prometheus is Scraping Metrics

### Method 1: Prometheus Targets UI

1. Open Prometheus (Terminal Tab 3)
2. Click **Status → Target Health**
3. Confirm all targets show `UP` state
4. `serviceMonitor/monitoring/frontend-monitor/0` will be visible

### Method 2: kubectl

```bash
kubectl get servicemonitor -n monitoring
```

Expected output includes `frontend-monitor`.

### Method 3: Query Prometheus directly

In Prometheus UI → **Query** tab, run:
```
kube_pod_info{namespace="default"}
```

Should return rows for `frontend`, `redis-leader`, `redis-replica`.

---

## Known Limitation

The PHP guestbook frontend does not expose a `/metrics` endpoint. Prometheus reaches the pod but receives `HTTP 404`. Pod resource metrics (CPU, memory, restarts) are available via `kube-state-metrics` which is bundled with `kube-prometheus-stack`.

---

## Project Structure

```
guestbook-monitoring/
├── __main__.py          # Entry point — imports guestbook and monitoring
├── guestbook.py         # Redis Leader, Redis Replica, Frontend deployments
├── monitoring.py        # Prometheus + Grafana Helm release
├── Pulumi.yaml
├── Pulumi.dev.yaml
└── requirements.txt
```

---

## Teardown

```bash
pulumi destroy
minikube stop
```
