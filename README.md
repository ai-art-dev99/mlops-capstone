# MLOps Capstone (End-to-End)

**Training → MLflow → Containerized FastAPI Serving → Helm + HPA → Prometheus/Grafana → Drift Checks → CI/CD**

[![CI/CD](https://img.shields.io/github/actions/workflow/status/ai-art-dev99/mlops-capstone/ci-cd.yml?branch=main)](https://github.com/ai-art-dev99/mlops-capstone/actions)
[![Container](https://img.shields.io/badge/container-GHCR-blue)](https://github.com/users/ai-art-dev99/packages/container/package/mlops-capstone)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)

> Cloud-agnostic project that demonstrates production-minded model deployment and ops. Works on any Kubernetes (kind/minikube/GKE/EKS/AKS); Terraform modules included for GKE Autopilot.

---

## ✨ What this shows
- **Model training** (Adult income) with **MLflow** metrics & artifacts  
- **Serving**: FastAPI (`/predict`, `/health`, `/metrics`) in a **Docker** image  
- **Kubernetes deploy** via **Helm** with **HPA** (autoscaling)  
- **Observability**: Prometheus metrics + Grafana dashboard JSON  
- **Data drift** check via a **CronJob** (simple categorical shift)  
- **CI/CD**: GitHub Actions → build & push to GHCR → deploy on release tag  
- **IaC**: Terraform to create a **GKE Autopilot** cluster and install workloads

---

## 🧭 Architecture

```
            +------------------+
            |   MLflow (UI)    |  <-- optional Helm chart
            +---------+--------+
                      ^
                      | metrics/artifacts
+---------+  train    |
| dataset | --------> |                         +------------------+
+----+----+           |                         |  Prometheus      |
     |                |                         +----+-------------+
     |                v                              ^
     |      +--------------------+                   | scrapes /metrics
     |      |  Train & Log (py)  |                   |
     |      +---------+----------+                   |
     |                | artifacts                    |
     |                v                              |
     |      +--------------------+                   |
     |      | Dockerized FastAPI |<------------------+
     |      +----+-----------+---+    Service        |
     |           |           |        +--------------v-----+
     |        /predict    /metrics    |  K8s (Helm + HPA)  |
     |                                 +-------------------+
```

---

## 🚀 Quickstart (Local)

```bash
# 1) Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) Train (sample or full OpenML dataset)
python model/train.py --dataset sample     # fast
# python model/train.py --dataset full     # downloads via OpenML

# 3) Save drift baseline
python monitoring/save_baseline.py

# 4) Run the API
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5) Try it
curl -X POST http://localhost:8000/predict   -H "content-type: application/json" -d @sample_payload.json

# 6) Metrics
curl http://localhost:8000/metrics
```

**Optional MLflow locally**
```bash
docker compose -f ops/docker-compose.mlflow.yml up -d
# UI: http://localhost:5000
```

**Docker**
```bash
docker build -t mlops-capstone:latest .
docker run --rm -p 8000:8000 mlops-capstone:latest
```

**k6 load test**
```bash
k6 run ops/loadtest/k6-smoke.js
```

---

## ☁️ Deploy to Kubernetes

Install the Prometheus/Grafana stack (optional but recommended):
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack   -n monitoring --create-namespace
```

Deploy the app:
```bash
helm upgrade --install capstone ./deploy/helm/app   -n mlops --create-namespace   --set image.repository=ghcr.io/ai-art-dev99/mlops-capstone   --set image.tag=latest
```

Enable Ingress (edit `deploy/helm/app/values.yaml`):
```yaml
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: domain.com
      paths:
        - path: /
          pathType: Prefix
```

---

## 🧱 Repo Layout

```
.
├── app/                     # FastAPI service
├── model/                   # Training + artifacts
├── monitoring/              # Drift job + baseline script
├── deploy/helm/app          # App Helm chart (ServiceMonitor + CronJob)
├── deploy/helm/mlflow       # MLflow Helm chart (optional)
├── infra/gke                # Terraform: GKE Autopilot cluster
├── infra/workloads          # Terraform: Helm releases (prom stack + app)
├── ops/dashboards           # Grafana dashboard JSON
├── ops/loadtest             # k6 scripts
├── .github/workflows        # CI/CD
├── sample_payload.json
└── requirements.txt
```

---

## 🔧 Configuration

**Environment variables (service)**
- `MODEL_PATH` (default `model/artifacts/model.pkl`)
- `ENCODER_PATH` (default `model/artifacts/encoder.pkl`)
- `REQUEST_LOG` (default `ops/data/live_requests.jsonl`)

**Helm values (common overrides)**
```bash
--set image.repository=ghcr.io/ai-art-dev99/mlops-capstone
--set image.tag=v0.1.0
--set autoscaling.maxReplicas=10
```

---

## 📈 Observability

- **Metrics:** Prometheus scrapes `/metrics` (request count & latency histograms).
- **Dashboard:** import `ops/dashboards/api-overview.json` into Grafana.
- **Drift:** a CronJob runs `monitoring/drift_job.py` nightly; adjust threshold via Helm values.

---

## 🔄 CI/CD

- **On push:** run tests, build & push image to GHCR.  
- **On GitHub Release:** deploy the Helm chart using the tagged image.

**Required repo secrets**
- `GITHUB_TOKEN` (automatically available for GHCR)
- `KUBE_CONFIG` (base64-encoded kubeconfig) if you want the pipeline to deploy

---

## 🛡️ Security & Prod Notes

- Non-root Docker user, health/readiness probes, small base image.  
- Use a private registry + image pull secrets for private clusters.  
- Add network policies & pod security standards in production.  
- Secrets: mount via cloud secret manager / sealed-secrets (not included here).

---

## 🧭 Roadmap

- [ ] Canary/shadow deploys (Argo Rollouts)  
- [ ] Slack alert for drift (webhook)  
- [ ] Feature store & model registry promotion gates  
- [ ] Load test thresholds enforced in CI

---

## 📜 License
Apache-2.0
