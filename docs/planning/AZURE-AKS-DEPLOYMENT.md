# Azure AKS Deployment: Kubernetes with Helm Charts

## Motivation

AKS gives a single orchestration layer for all services — no split between VM and Container Apps. Helm charts make deployments reproducible and upgradeable. This is a good fit if the team already knows Kubernetes or plans to scale beyond a handful of devices.

| Advantage over Hybrid (VM + Container Apps) | Detail |
|---------------------------------------------|--------|
| **Single deployment target** | One `kubectl apply` or `helm upgrade` for everything |
| **Native TCP + HTTPS ingress** | NGINX Ingress Controller handles both HTTP and raw TCP (MQTT) |
| **Horizontal scaling** | HPA for Backend, EMQX clustering via Kubernetes operator |
| **Ecosystem** | Official Helm charts exist for EMQX, InfluxDB, Grafana, PostgreSQL |
| **Portable** | Same manifests work on any Kubernetes (local, AWS, GCP) |

---

## Architecture Overview

```
                        ┌──────────────────────────────────────────────┐
                        │           AKS Cluster (1 node pool)          │
                        │                                              │
                        │  ┌─────────────────────────────────────────┐ │
                        │  │        NGINX Ingress Controller         │ │
                        │  │  :443 HTTPS ──▶ Frontend, Backend,      │ │
  Clients ──HTTPS──────▶│  │                 Grafana                  │ │
  IoT Devices ─MQTTS───▶│  │  :8883 TCP ───▶ EMQX                   │ │
                        │  └──────────┬──────────────────────────────┘ │
                        │             │                                │
                        │  ┌──────────▼─────┐  ┌──────────────────┐   │
                        │  │     EMQX       │  │   Backend API    │   │
                        │  │  (StatefulSet) │  │   (Deployment)   │   │
                        │  │  1 replica     │  │   1-3 replicas   │   │
                        │  └───────┬────────┘  └───────┬──────────┘   │
                        │          │                    │              │
                        │  ┌───────▼────────┐          │              │
                        │  │   Telegraf     │          │              │
                        │  │  (Deployment) │          │              │
                        │  │  1 replica    │          │              │
                        │  └───────┬───────┘          │              │
                        │          │                   │              │
                        │  ┌───────▼───────────────────▼───────────┐  │
                        │  │            InfluxDB                   │  │
                        │  │         (StatefulSet, PVC)            │  │
                        │  └───────────────────▲───────────────────┘  │
                        │                      │                      │
                        │  ┌───────────────────┴───────────────────┐  │
                        │  │            Grafana                    │  │
                        │  │         (Deployment)                  │  │
                        │  └───────────────────────────────────────┘  │
                        │                                              │
                        │  ┌───────────────────────────────────────┐   │
                        │  │         Frontend (Deployment)         │   │
                        │  │         Nginx serving SPA             │   │
                        │  └───────────────────────────────────────┘   │
                        └──────────────────┬───────────────────────────┘
                                           │ Private Endpoint
                        ┌──────────────────▼───────────────────────────┐
                        │   Azure Database for PostgreSQL              │
                        │   (Flexible Server)                          │
                        └──────────────────────────────────────────────┘
```

---

## Minimal Setup — What You Need to Start

### 1. AKS Cluster

```bash
# Create resource group
az group create -n rg-iotdash-dev -l westeurope

# Create AKS cluster — minimal, single node
az aks create \
  -g rg-iotdash-dev \
  -n aks-iotdash-dev \
  --node-count 1 \
  --node-vm-size Standard_D2s_v5 \
  --enable-managed-identity \
  --generate-ssh-keys \
  --network-plugin azure \
  --attach-acr criotdash          # your Azure Container Registry

# Get credentials
az aks get-credentials -g rg-iotdash-dev -n aks-iotdash-dev
```

**Single node is enough for dev/staging.** For production, use 2-3 nodes with availability zones.

### 2. NGINX Ingress Controller (with TCP support)

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=/healthz \
  --set tcp.8883="default/emqx:8883"
```

The `--set tcp.8883` line tells NGINX Ingress to forward raw TCP on port 8883 to the EMQX service — this is how IoT devices reach the broker.

### 3. Deploy Services via Helm

#### Option A — Use existing community Helm charts

```bash
# EMQX
helm repo add emqx https://repos.emqx.io/charts
helm install emqx emqx/emqx \
  --set replicaCount=1 \
  --set persistence.enabled=true \
  --set persistence.size=2Gi \
  --values helm/emqx-values.yaml

# InfluxDB
helm repo add influxdata https://helm.influxdata.com/
helm install influxdb influxdata/influxdb2 \
  --set persistence.enabled=true \
  --set persistence.size=10Gi \
  --set adminUser.token=$(az keyvault secret show --vault-name kv-iotdash --name influx-token --query value -o tsv) \
  --values helm/influxdb-values.yaml

# Grafana
helm repo add grafana https://grafana.github.io/helm-charts
helm install grafana grafana/grafana \
  --set persistence.enabled=false \
  --set adminPassword=$(az keyvault secret show --vault-name kv-iotdash --name grafana-admin-pw --query value -o tsv) \
  --values helm/grafana-values.yaml
```

#### Option B — Custom umbrella chart (recommended for this project)

```
helm/iotdash/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── namespace.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── telegraf-deployment.yaml
│   ├── telegraf-configmap.yaml
│   ├── ingress.yaml
│   └── secrets.yaml           # ExternalSecret or sealed-secret refs
└── charts/                    # subcharts (dependencies)
    ├── emqx/
    ├── influxdb2/
    └── grafana/
```

```yaml
# Chart.yaml
apiVersion: v2
name: iotdash
version: 0.1.0
dependencies:
  - name: emqx
    version: "5.8.*"
    repository: https://repos.emqx.io/charts
  - name: influxdb2
    version: "2.*"
    repository: https://helm.influxdata.com/
  - name: grafana
    version: "8.*"
    repository: https://grafana.github.io/helm-charts
```

```bash
# One-command deploy
helm dependency update helm/iotdash
helm install iotdash helm/iotdash -f helm/iotdash/values-dev.yaml
```

---

## Minimal Kubernetes Manifests (no Helm, just to start)

If you want to skip Helm initially and just get things running:

### Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: iotdash
```

### Backend

```yaml
# k8s/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: iotdash
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: backend
          image: criotdash.azurecr.io/iotdash-backend:latest
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: iotdash-secrets
          env:
            - name: INFLUXDB_URL
              value: "http://influxdb:8086"
            - name: MQTT_BROKER_HOST
              value: "emqx"
            - name: MQTT_BROKER_PORT
              value: "1883"
            - name: GRAFANA_URL
              value: "http://grafana:3000"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: iotdash
spec:
  selector:
    app: backend
  ports:
    - port: 8000
      targetPort: 8000
```

### Frontend

```yaml
# k8s/frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: iotdash
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: frontend
          image: criotdash.azurecr.io/iotdash-frontend:latest
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: iotdash
spec:
  selector:
    app: frontend
  ports:
    - port: 80
      targetPort: 80
```

### Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: iotdash-ingress
  namespace: iotdash
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - app.iotdash.example.com
        - grafana.iotdash.example.com
      secretName: iotdash-tls
  rules:
    - host: app.iotdash.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
    - host: grafana.iotdash.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: grafana
                port:
                  number: 3000
```

### Apply everything

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/ -n iotdash
```

---

## Security Setup

### Network Layer

```
VNet: vnet-iotdash (10.0.0.0/16)
│
├── Subnet: snet-aks        (10.0.0.0/22)   ← AKS nodes (Azure CNI)
├── Subnet: snet-postgres   (10.0.4.0/24)   ← PostgreSQL Flexible Server
└── Subnet: snet-endpoints  (10.0.5.0/24)   ← Private Endpoints
```

**AKS to PostgreSQL:** Private endpoint in `snet-endpoints`, private DNS zone `privatelink.postgres.database.azure.com`. No public access on PostgreSQL.

**AKS to Internet:** Only via Load Balancer (ingress). Optionally lock egress with Azure Firewall or NSG.

### Kubernetes Network Policies

```yaml
# k8s/network-policies.yaml

# Default deny all ingress in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: iotdash
spec:
  podSelector: {}
  policyTypes:
    - Ingress

---
# Allow ingress-nginx → frontend, backend, grafana
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ingress-to-web
  namespace: iotdash
spec:
  podSelector:
    matchLabels:
      tier: web                  # label on frontend, backend, grafana pods
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
  policyTypes:
    - Ingress

---
# InfluxDB: only reachable from backend, grafana, telegraf
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-influxdb-access
  namespace: iotdash
spec:
  podSelector:
    matchLabels:
      app: influxdb
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: backend
        - podSelector:
            matchLabels:
              app: grafana
        - podSelector:
            matchLabels:
              app: telegraf
      ports:
        - port: 8086
  policyTypes:
    - Ingress

---
# EMQX: TCP from ingress (devices) + internal from telegraf and backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-emqx-access
  namespace: iotdash
spec:
  podSelector:
    matchLabels:
      app: emqx
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - port: 8883
    - from:
        - podSelector:
            matchLabels:
              app: telegraf
        - podSelector:
            matchLabels:
              app: backend
      ports:
        - port: 1883
  policyTypes:
    - Ingress
```

### Secret Management

**Option A — Azure Key Vault + CSI Driver (recommended):**

```bash
# Install CSI driver add-on
az aks enable-addons -g rg-iotdash-dev -n aks-iotdash-dev \
  --addons azure-keyvault-secrets-provider
```

```yaml
# k8s/secret-provider.yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: iotdash-kv
  namespace: iotdash
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "<managed-identity-client-id>"
    keyvaultName: kv-iotdash
    objects: |
      array:
        - |
          objectName: influx-token
          objectType: secret
        - |
          objectName: jwt-secret
          objectType: secret
        - |
          objectName: grafana-admin-pw
          objectType: secret
        - |
          objectName: postgres-password
          objectType: secret
    tenantId: "<tenant-id>"
  secretObjects:
    - secretName: iotdash-secrets
      type: Opaque
      data:
        - objectName: influx-token
          key: INFLUXDB_TOKEN
        - objectName: jwt-secret
          key: JWT_SECRET_KEY
        - objectName: grafana-admin-pw
          key: GRAFANA_ADMIN_PASSWORD
        - objectName: postgres-password
          key: DATABASE_PASSWORD
```

Pods mount the CSI volume and secrets appear as environment variables via `secretRef`.

**Option B — Sealed Secrets (simpler, GitOps-friendly):**

```bash
# Install sealed-secrets controller
helm install sealed-secrets sealed-secrets/sealed-secrets -n kube-system

# Encrypt secrets locally, commit encrypted version to git
kubeseal --format yaml < k8s/secrets-plain.yaml > k8s/secrets-sealed.yaml
```

### MQTT Security (EMQX on K8s)

Same layered approach as the hybrid doc — the EMQX Helm chart supports all of this via `values.yaml`:

```yaml
# helm/emqx-values.yaml
replicaCount: 1

emqxConfig:
  # TLS listener
  EMQX_LISTENERS__SSL__DEFAULT__BIND: "0.0.0.0:8883"
  EMQX_LISTENERS__SSL__DEFAULT__SSL_OPTIONS__CERTFILE: /etc/emqx/certs/tls.crt
  EMQX_LISTENERS__SSL__DEFAULT__SSL_OPTIONS__KEYFILE: /etc/emqx/certs/tls.key

  # Disable anonymous
  EMQX_ALLOW_ANONYMOUS: "false"

  # Rate limiting
  EMQX_LISTENERS__SSL__DEFAULT__MAX_CONN_RATE: "100/s"

  # Internal plain TCP (cluster only, not exposed via ingress)
  EMQX_LISTENERS__TCP__DEFAULT__BIND: "0.0.0.0:1883"

# Mount TLS cert from cert-manager or Key Vault
extraVolumes:
  - name: emqx-tls
    secret:
      secretName: emqx-tls-cert

extraVolumeMounts:
  - name: emqx-tls
    mountPath: /etc/emqx/certs
    readOnly: true
```

### TLS Certificates (cert-manager)

```bash
# Install cert-manager
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set crds.enabled=true
```

```yaml
# k8s/cluster-issuer.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@iotdash.example.com
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
      - http01:
          ingress:
            class: nginx
```

HTTPS certs for ingress are automatic. For the EMQX MQTTS cert, create a separate `Certificate` resource:

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: emqx-tls-cert
  namespace: iotdash
spec:
  secretName: emqx-tls-cert
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - mqtt.iotdash.example.com
```

### RBAC (Kubernetes)

```yaml
# Minimal: Backend pod needs no special K8s permissions.
# Only the CI/CD pipeline service principal needs cluster access.

# If using Workload Identity for Azure SDK calls:
apiVersion: v1
kind: ServiceAccount
metadata:
  name: backend-sa
  namespace: iotdash
  annotations:
    azure.workload.identity/client-id: "<managed-identity-client-id>"
```

---

## Cost Estimate (EUR/month, West Europe)

### Minimal Dev/Staging (1 node)

| Resource | SKU | Est. Cost |
|----------|-----|-----------|
| AKS cluster | Free tier (no SLA) | €0 |
| Node pool | 1x Standard_D2s_v5 (2 vCPU, 8 GB) | ~€70 |
| Managed Disks (InfluxDB PVC 10 GB + EMQX PVC 2 GB) | Premium SSD | ~€5 |
| Azure Container Registry | Basic | ~€5 |
| PostgreSQL Flexible Server | Burstable B1ms | ~€13 |
| Key Vault | Standard | ~€1 |
| Public IP (Load Balancer) | Standard | ~€4 |
| **Total** | | **~€98** |

### Production (3 nodes, HA)

| Resource | SKU | Est. Cost |
|----------|-----|-----------|
| AKS cluster | Standard tier (SLA) | ~€60 |
| Node pool | 3x Standard_D2s_v5 (across 3 AZs) | ~€210 |
| Managed Disks (PVCs with ZRS) | Premium SSD | ~€15 |
| Azure Container Registry | Standard | ~€17 |
| PostgreSQL Flexible Server | General Purpose D2s_v3, HA | ~€120 |
| Key Vault | Standard | ~€1 |
| Public IP + LB | Standard | ~€4 |
| Azure Monitor (Container Insights) | Log Analytics | ~€10-30 |
| **Total** | | **~€440-460** |

### Cost Comparison

| Setup | Dev/Staging | Production |
|-------|-------------|------------|
| **AKS (this doc)** | ~€98/mo | ~€440/mo |
| **Hybrid VM + Container Apps** | ~€120/mo | ~€200-250/mo |
| **All Container Apps** | ~€110/mo | ~€250-300/mo |

AKS is cheapest for dev (free control plane), but production HA with 3 nodes + paid tier is significantly more. The sweet spot is if you need Kubernetes features (operators, network policies, Helm ecosystem) or plan to grow beyond a few services.

---

## Comparison: When to Pick Which

| Factor | AKS | Hybrid (VM + CA) | All Container Apps |
|--------|-----|-------------------|--------------------|
| **Team knows K8s** | Best | Okay | Best |
| **Team is small / no K8s exp** | Overhead | Good | Best |
| **TCP ingress (MQTT)** | Native via Ingress | Native on VM | Awkward |
| **Scale to zero** | No (nodes run 24/7) | Partial (CA scales, VM doesn't) | Yes |
| **InfluxDB perf** | Good (local PVC) | Best (local disk) | Poor (Azure Files) |
| **Operational burden** | Medium (K8s management) | Medium (VM + CA) | Low |
| **Production HA cost** | High (~€440) | Medium (~€230) | Medium (~€280) |
| **Helm/GitOps** | Native | Partial | No |
| **Future scaling** | Best | Manual (add VMs) | Auto but limited |

---

## Getting Started Checklist

```
[ ] Create resource group and ACR
[ ] Build & push Docker images (backend, frontend) to ACR
[ ] Create AKS cluster (single node, free tier)
[ ] Install NGINX Ingress Controller with TCP passthrough for 8883
[ ] Install cert-manager + ClusterIssuer
[ ] Create Azure Key Vault, populate secrets
[ ] Deploy with either:
    [ ] Option A: raw manifests (k8s/*.yaml) for quick start
    [ ] Option B: umbrella Helm chart for repeatable deploys
[ ] Create PostgreSQL Flexible Server with private endpoint
[ ] Configure DNS records (app.*, mqtt.*, grafana.*)
[ ] Test: fake_device.py → mqtts://mqtt.iotdash.example.com:8883
[ ] Test: browser → https://app.iotdash.example.com
```
