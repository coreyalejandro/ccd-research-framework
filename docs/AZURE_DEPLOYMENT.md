# CCD Research Framework — Azure Deployment Guide

## Prerequisites

- Azure CLI installed (`az --version`)
- Docker installed
- Azure Container Registry (ACR) or Docker Hub access

## Option 1: Azure Container Instances (ACI) — Quickstart

### Step 1: Build and push image

```bash
docker build -t ccd-research-framework .

# Tag for ACR
az acr login --name <your-acr-name>
docker tag ccd-research-framework <your-acr-name>.azurecr.io/ccd-research-framework:latest
docker push <your-acr-name>.azurecr.io/ccd-research-framework:latest
```

### Step 2: Deploy to ACI

```bash
az container create \
  --resource-group ccd-rg \
  --name ccd-research-framework \
  --image <your-acr-name>.azurecr.io/ccd-research-framework:latest \
  --cpu 2 --memory 4 \
  --registry-login-server <your-acr-name>.azurecr.io \
  --registry-username <acr-username> \
  --registry-password <acr-password> \
  --environment-variables ANTHROPIC_API_KEY=<key> \
  --ports 8000
```

### Step 3: Verify

```bash
az container show --resource-group ccd-rg --name ccd-research-framework --query instanceView.state
```

---

## Option 2: Azure Kubernetes Service (AKS) — Production

### Deployment manifest (k8s/deployment.yaml)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ccd-research-framework
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ccd-research-framework
  template:
    metadata:
      labels:
        app: ccd-research-framework
    spec:
      containers:
      - name: ccd
        image: <your-acr>.azurecr.io/ccd-research-framework:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: ccd-secrets
              key: anthropic-api-key
```

### Deploy

```bash
kubectl apply -f k8s/deployment.yaml
kubectl rollout status deployment/ccd-research-framework
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Optional | Claude verification fallback |
| `OPENAI_API_KEY` | Optional | OpenAI cross-model testing |
| `CCD_DETECTION_THRESHOLD` | Optional | Default 0.7 |
| `CCD_LOG_LEVEL` | Optional | DEBUG/INFO/WARNING |

---

## Monitoring

Use Azure Monitor + Application Insights for:
- Detection latency (target <100ms per SLA)
- False positive rate per model
- Rollout health per model tier

---

## Troubleshooting

**Container fails health check**: Verify `python -m pytest tests/ -q` passes inside the image.

**High memory usage**: Corpus generation for large batches is memory-intensive.
Set `--memory 4` minimum for ACI.

**Timeout on first run**: Corpus caching cold start can take 10–15s. Increase
ACI startup timeout with `--restart-policy OnFailure`.
