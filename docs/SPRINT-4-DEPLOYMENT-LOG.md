# Sprint 4 — Soak Test Deployment Log

> **Date:** 2026-04-17
> **Region:** eastus
> **VM:** Standard_D2as_v6 (2 vCPU, 8 GB RAM, AMD, no credit throttling)

---

## Step-by-Step Actions Taken

### 1. Verified Azure CLI Authentication

```
az account show
```

- Subscription: `0826a74f-0247-4a9f-8f05-4e7dbc56c888` (main)
- Tenant: `12b141e0-ebb1-4e7c-934f-afa1f63e2419`
- Authenticated via personal identity

### 2. Created Service Principal for Terraform

```
az ad sp create-for-rbac --name sp-iotdash-soak --role Contributor \
  --scopes /subscriptions/0826a74f-0247-4a9f-8f05-4e7dbc56c888
```

- **App ID:** `6192e0fd-30b2-4c8d-b37d-095f8bb29e0a`
- **Display Name:** `sp-iotdash-soak`
- **Tenant:** `12b141e0-ebb1-4e7c-934f-afa1f63e2419`
- Role: Contributor on the entire subscription

### 3. Generated SSH Keypair

```
ssh-keygen -t rsa -b 4096 -f ~/.ssh/iotdash-soak -N "" -C "iotdash-soak-test"
```

- Azure requires RSA keys (ed25519 not supported)
- Private key: `~/.ssh/iotdash-soak`
- Public key: `~/.ssh/iotdash-soak.pub`

### 4. Detected Public IP for NSG Rules

```
curl -4 ifconfig.me → 137.186.245.80
```

All NSG inbound rules are restricted to `137.186.245.80/32`.

### 5. Wrote Terraform Configuration

Files created in `infra/soak-test/`:

| File | Purpose |
|------|---------|
| `main.tf` | Provider, resource group, VNet, subnet, ACR |
| `vm.tf` | VM, NIC, NSG (8 rules), public IP (with DNS label), cloud-init |
| `variables.tf` | 15 configurable inputs |
| `outputs.tf` | VM IP, FQDN, SSH command, service URLs, ACR credentials |
| `cloud-init.yaml` | Automated VM setup (Docker, repo clone, stack start, simulator, cron) |
| `terraform.tfvars` | Real values (gitignored) |
| `terraform.tfvars.example` | Template for others |
| `teardown.sh` | `terraform destroy` with confirmation |

### 6. Terraform Init

```
terraform init
```

- Provider: `hashicorp/azurerm v3.117.1`

### 7. First Apply Attempt — westeurope (FAILED)

```
terraform apply -auto-approve  # location = "westeurope"
```

- **Error:** `standardDSv5Family` quota = 0 in westeurope
- 7 of 9 resources created, VM failed

### 8. Switched to eastus — Still DSv5 (FAILED)

```
terraform apply -auto-approve  # location = "eastus", vm_size = "Standard_D2s_v5"
```

- **Error:** `standardDSv5Family` quota = 0 in eastus too
- DSv5 has zero quota across the entire subscription

### 9. Found Available VM Family

```
az vm list-usage --location eastus -o table | grep -v " 0$"
```

- `Dav6 Family` has 10 vCPU quota available
- Selected `Standard_D2as_v6` (2 vCPU, 8 GB, AMD — equivalent performance to D2s_v5)

### 10. Destroyed westeurope Partial Resources

```
terraform destroy -auto-approve  # rg-iotdash-soak in westeurope
```

- 5 resources destroyed (NIC, public IP, subnet, VNet, resource group)
- ACR and NSG were already destroyed in the eastus retry cycle
- Cleared stale tfstate

### 11. Final Apply — eastus with D2as_v6 (SUCCESS)

```
terraform apply -auto-approve
# location = "eastus"
# resource_group_name = "rg-iotdash-soak-eastus"
# vm_size = "Standard_D2as_v6"
```

- **9 resources created in ~90 seconds**
- VM public IP: `13.82.138.72`

---

## Azure Resources Created

| # | Resource Type | Name | Details |
|---|--------------|------|---------|
| 1 | Resource Group | `rg-iotdash-soak-eastus` | eastus |
| 2 | Virtual Network | `vnet-iotdash-soak` | 10.0.0.0/16 |
| 3 | Subnet | `snet-iotdash-soak` | 10.0.1.0/24 |
| 4 | Network Security Group | `nsg-iotdash-soak` | 8 inbound rules (see below) |
| 5 | Public IP | `pip-iotdash-soak` | Dynamic, Basic SKU → `13.82.138.72`, DNS: `iotdash-soak.eastus.cloudapp.azure.com` |
| 6 | Network Interface | `nic-iotdash-soak` | + NSG association |
| 7 | NIC-NSG Association | — | Links NIC to NSG |
| 8 | Container Registry | `criotdashsoak` | Basic SKU, admin enabled, `criotdashsoak.azurecr.io` |
| 9 | Linux VM | `vm-iotdash-soak` | Standard_D2as_v6, Ubuntu 24.04, 128 GB Premium SSD |

### NSG Inbound Rules

| Priority | Name | Port | Source |
|----------|------|------|--------|
| 100 | SSH | 22 | 137.186.245.80/32 |
| 110 | SSH-GitHubActions | 22 | * (any — key-auth only) |
| 150 | HTTP | 80 | * |
| 200 | MQTT | 1883 | 137.186.245.80/32 |
| 300 | Backend | 8000 | 137.186.245.80/32 |
| 400 | Frontend | 5173 | 137.186.245.80/32 |
| 500 | Grafana | 3000 | 137.186.245.80/32 |
| 600 | EMQX Dashboard | 18083 | 137.186.245.80/32 |

**Note:** SSH is open to all IPs (priority 110) because GitHub Actions runner IPs are unpredictable. The VM uses SSH key authentication only (no password), so this is safe.

### Service Principal Created

| Field | Value |
|-------|-------|
| Name | `sp-iotdash-soak` |
| App ID | `6192e0fd-30b2-4c8d-b37d-095f8bb29e0a` |
| Tenant | `12b141e0-ebb1-4e7c-934f-afa1f63e2419` |
| Role | Contributor |
| Scope | Subscription `0826a74f-...` |

---

## VM Access

**DNS hostname:** `iotdash-soak.eastus.cloudapp.azure.com`

```bash
ssh -i ~/.ssh/iotdash-soak azureuser@iotdash-soak.eastus.cloudapp.azure.com
```

### Service URLs (once cloud-init completes)

| Service | URL | Access |
|---------|-----|--------|
| Frontend (clean URL) | http://iotdash-soak.eastus.cloudapp.azure.com | Public (port 80 → nginx on 5173) |
| Frontend (direct) | http://iotdash-soak.eastus.cloudapp.azure.com:5173 | Public |
| Backend API (via proxy) | http://iotdash-soak.eastus.cloudapp.azure.com/api/ | Public (nginx proxies to backend:8000) |
| Backend API (direct) | http://iotdash-soak.eastus.cloudapp.azure.com:8000 | Restricted to allowed IP |
| Grafana | http://iotdash-soak.eastus.cloudapp.azure.com:3000 | Restricted (anonymous access enabled for iframes) |
| EMQX Dashboard | http://iotdash-soak.eastus.cloudapp.azure.com:18083 | Restricted to allowed IP |
| InfluxDB | http://localhost:8086 (via SSH tunnel) | SSH tunnel only |
| PostgreSQL | localhost:5432 (via SSH tunnel) | SSH tunnel only |

---

## What Cloud-Init Does on First Boot (~5 min)

1. Installs Docker, docker-compose plugin, git, python3, jq
2. Configures Docker log rotation (50 MB max, 3 files)
3. Logs into ACR (`criotdashsoak.azurecr.io`)
4. Clones `github.com/svolodarskyi/iotdash` (main branch)
5. Runs `docker compose -f docker-compose.yml -f docker-compose.soak.yml up -d --build`
6. Creates Python venv, installs `aiomqtt`
7. Creates systemd service `soak-simulator` (1000 devices @ 5s, starts after 60s delay)
8. Sets up cron: `soak_monitor.sh` every 5 min, `soak_alerter.sh` every 15 min
9. Sets InfluxDB retention to 14 days (after 90s delay for services to start)

### Check cloud-init progress

```bash
ssh -i ~/.ssh/iotdash-soak azureuser@iotdash-soak.eastus.cloudapp.azure.com 'sudo tail -f /var/log/cloud-init-output.log'
```

---

## Next Steps Required

### 1. Wait for Cloud-Init to Complete (~5 min)

```bash
ssh -i ~/.ssh/iotdash-soak azureuser@iotdash-soak.eastus.cloudapp.azure.com 'cloud-init status --wait'
```

### 2. Verify Stack is Running

```bash
ssh -i ~/.ssh/iotdash-soak azureuser@iotdash-soak.eastus.cloudapp.azure.com 'sudo docker compose -f /opt/iotdash/docker-compose.yml -f /opt/iotdash/docker-compose.soak.yml ps'
```

### 3. Push Code to GitHub

The VM clones from `github.com/svolodarskyi/iotdash` main branch. All the soak test files need to be committed and pushed before the VM can use them. Until then, cloud-init will clone whatever is currently on main.

```bash
cd /Users/erfolg/Documents/projects/iotdash
git add -A
git commit -m "sprint 4: soak test IaC, CI/CD, simulator, monitoring"
git push origin main
```

### 4. Delete Old westeurope Resource Group

The old `rg-iotdash-soak` in westeurope was partially cleaned up via Terraform, but you said you'd delete it manually:

```bash
az group delete -n rg-iotdash-soak --yes --no-wait
```

### 5. Set GitHub Repository Secrets

Go to **github.com/svolodarskyi/iotdash → Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|-------------|-------|
| `SOAK_VM_HOST` | `iotdash-soak.eastus.cloudapp.azure.com` (or the IP: `13.82.138.72`) |
| `SOAK_VM_SSH_KEY` | Contents of `~/.ssh/iotdash-soak` (the private key — run `cat ~/.ssh/iotdash-soak` and paste) |
| `ACR_LOGIN_SERVER` | `criotdashsoak.azurecr.io` |
| `ACR_USERNAME` | `criotdashsoak` |
| `ACR_PASSWORD` | `6IlI3vhptrgfquYkzWu2cIrdua3vkfOInR1TMbvJcbTdiTLmOi1QJQQJ99CDACYeBjFEqg7NAAACAZCRHQTx` |

### 6. Test CI/CD Pipeline

After setting secrets, go to **Actions → "Soak Test — Build & Deploy" → Run workflow** (manual trigger).

### 7. Build and Push Images to ACR (First Time)

Until CI/CD runs, the VM builds images locally from source. To pre-push images:

```bash
# Login to ACR locally
az acr login --name criotdashsoak

# Build and push
docker build -f backend/Dockerfile.prod -t criotdashsoak.azurecr.io/iotdash-backend:latest ./backend
docker push criotdashsoak.azurecr.io/iotdash-backend:latest

docker build -f frontend/Dockerfile.prod -t criotdashsoak.azurecr.io/iotdash-frontend:latest ./frontend
docker push criotdashsoak.azurecr.io/iotdash-frontend:latest
```

### 8. Monitor the Soak Test

- Check metrics CSV: `ssh ... 'cat /opt/iotdash/soak-metrics.csv'`
- Check simulator: `ssh ... 'sudo journalctl -u soak-simulator -f'`
- Check alerts: `ssh ... 'cat /opt/iotdash/soak-alerter.log'`
- Download metrics weekly via GitHub Actions: "Soak Test — Collect Metrics"

### 9. Teardown When Done

```bash
cd infra/soak-test && bash teardown.sh
# or
terraform destroy -auto-approve
```

**Cost reminder: ~EUR 4/day. Destroy when testing is complete!**

---

## Files Changed / Created in This Sprint

| File | Action |
|------|--------|
| `infra/soak-test/main.tf` | Created |
| `infra/soak-test/vm.tf` | Created |
| `infra/soak-test/variables.tf` | Created |
| `infra/soak-test/outputs.tf` | Created |
| `infra/soak-test/cloud-init.yaml` | Created |
| `infra/soak-test/terraform.tfvars` | Created (gitignored) |
| `infra/soak-test/terraform.tfvars.example` | Created |
| `infra/soak-test/teardown.sh` | Created |
| `infra/soak-test/companies.yml` | Created |
| `docker-compose.soak.yml` | Created |
| `telegraf.soak.conf` | Created |
| `backend/Dockerfile.prod` | Created |
| `frontend/Dockerfile.prod` | Created |
| `tools/soak_simulator.py` | Created |
| `tools/soak_monitor.sh` | Created |
| `tools/soak_alerter.sh` | Created |
| `.github/workflows/soak-deploy.yml` | Created |
| `.github/workflows/soak-collect.yml` | Created |
| `.gitignore` | Updated (added Terraform + SSH key patterns) |
| `docs/planning/CHEAPEST-SOAK-TEST.md` | Updated (added 1000-device section) |
| `docs/planning/TECH-LEAD-PLAYBOOK.md` | Updated (Sprint 4 rewritten) |
| `docs/SPRINT-4-DECISIONS.md` | Created |
| `docs/SPRINT-4-FEATURES.md` | Created |
| `docs/SPRINT-4-MANUAL-QA.md` | Created |
| `docs/SPRINT-4-DEPLOYMENT-LOG.md` | Created (this file) |
