# Destroy and Recreate Soak Test Deployment

> **Cost:** ~EUR 4/day. Always destroy when not in use.

---

## 1. Destroy Everything

```bash
cd /Users/erfolg/Documents/projects/iotdash/infra/soak-test
terraform destroy -auto-approve
```

This deletes: VM, NIC, NSG, public IP, VNet, subnet, ACR, resource group (all 9 resources).

---

## 2. Rebuild

```bash
terraform apply -auto-approve
```

Creates all resources from scratch (~90 seconds).

---

## 3. Get the New Public IP

```bash
# From terraform output
terraform output vm_public_ip

# Or from Azure CLI
az vm show -g rg-iotdash-soak-eastus -n vm-iotdash-soak -d --query publicIps -o tsv

# Or just the public IP resource
az network public-ip show -g rg-iotdash-soak-eastus -n pip-iotdash-soak --query ipAddress -o tsv
```

---

## 4. Wait for Cloud-Init (~5 min)

```bash
ssh -i ~/.ssh/iotdash-soak azureuser@<NEW_IP> 'cloud-init status --wait'
```

Check for errors:

```bash
ssh -i ~/.ssh/iotdash-soak azureuser@<NEW_IP> 'sudo tail -30 /var/log/cloud-init-output.log'
```

---

## 5. Fix Git Ownership

Cloud-init clones as root. Fix so CI/CD (azureuser) can use git:

```bash
ssh -i ~/.ssh/iotdash-soak azureuser@<NEW_IP> 'sudo chown -R azureuser:azureuser /opt/iotdash && git config --global --add safe.directory /opt/iotdash'
```

---

## 6. Verify Containers Are Running

```bash
ssh -i ~/.ssh/iotdash-soak azureuser@<NEW_IP> 'sudo docker ps'
```

All 7 containers should be up: emqx, influxdb, postgres, telegraf, backend, frontend, grafana.

---

## 7. Run Database Migrations and Seed

```bash
ssh -i ~/.ssh/iotdash-soak azureuser@<NEW_IP> 'sudo docker exec backend alembic upgrade head && sudo docker exec backend python -m app.seed'
```

---

## 8. Test Endpoints

```bash
curl -s -o /dev/null -w "%{http_code}" http://iotdash-soak.eastus.cloudapp.azure.com          # Frontend (port 80) → 200
curl -s -o /dev/null -w "%{http_code}" http://iotdash-soak.eastus.cloudapp.azure.com:5173     # Frontend (direct)  → 200
curl -s -o /dev/null -w "%{http_code}" http://iotdash-soak.eastus.cloudapp.azure.com:8000     # Backend             → 200
curl -s -o /dev/null -w "%{http_code}" http://iotdash-soak.eastus.cloudapp.azure.com:3000     # Grafana             → 200
```

---

## 9. Update GitHub Secret

Go to **github.com/svolodarskyi/iotdash → Settings → Secrets and variables → Actions**.

Update `SOAK_VM_HOST` to the new IP (DNS hostname doesn't change on rebuild, but the IP does).

---

## 10. Start Simulator (When Ready)

```bash
ssh -i ~/.ssh/iotdash-soak azureuser@<NEW_IP> 'sudo systemctl enable soak-simulator && sudo systemctl start soak-simulator'
```

Check status:

```bash
ssh -i ~/.ssh/iotdash-soak azureuser@<NEW_IP> 'sudo systemctl status soak-simulator'
ssh -i ~/.ssh/iotdash-soak azureuser@<NEW_IP> 'sudo journalctl -u soak-simulator -f'
```

Stop:

```bash
ssh -i ~/.ssh/iotdash-soak azureuser@<NEW_IP> 'sudo systemctl stop soak-simulator'
```

---

## Credentials

| Service | Username | Password |
|---------|----------|----------|
| SSH | `azureuser` | Key: `~/.ssh/iotdash-soak` |
| App (admin) | `admin@iotdash.com` | `admin123` |
| App (viewer) | `viewer@democorp.com` | `viewer123` |
| Grafana | `admin` | `admin` |

---

## Service URLs

**DNS hostname:** `iotdash-soak.eastus.cloudapp.azure.com` (or use the IP directly)

| Service | URL | NSG Port | Access |
|---------|-----|----------|--------|
| Frontend | `http://iotdash-soak.eastus.cloudapp.azure.com:5173` | 5173 | Public |
| Backend API | `http://iotdash-soak.eastus.cloudapp.azure.com:8000` | 8000 | Public |
| Grafana | `http://iotdash-soak.eastus.cloudapp.azure.com:3000` | 3000 | Public (anonymous access enabled*) |
| EMQX Dashboard | `http://iotdash-soak.eastus.cloudapp.azure.com:18083` | 18083 | Public |
| MQTT Broker | `iotdash-soak.eastus.cloudapp.azure.com:1883` | 1883 | Public |
| InfluxDB UI | `http://localhost:8086` (via SSH tunnel) | Not exposed | SSH tunnel only |
| PostgreSQL | `localhost:5432` (via SSH tunnel) | Not exposed | SSH tunnel only |

**\*Grafana note:** Anonymous access is currently enabled (`GF_AUTH_ANONYMOUS_ENABLED=true`) so that embedded dashboard iframes in the frontend work without extra authentication. This means anyone with the URL can view dashboards. After Sprint 12 (Grafana auth integration), Grafana will be proxied through nginx with service account tokens, anonymous access will be disabled, and port 3000 will be closed to public access (SSH tunnel only, like InfluxDB).

### Accessing InfluxDB and PostgreSQL

InfluxDB and PostgreSQL are not exposed to the internet (no NSG rules). Access them via SSH tunnel:

```bash
# InfluxDB — open http://localhost:8086 in browser after running this
ssh -i ~/.ssh/iotdash-soak -L 8086:localhost:8086 azureuser@iotdash-soak.eastus.cloudapp.azure.com

# PostgreSQL — connect with psql or any DB client to localhost:5432
ssh -i ~/.ssh/iotdash-soak -L 5432:localhost:5432 azureuser@iotdash-soak.eastus.cloudapp.azure.com
```

Multiple tunnels at once:

```bash
ssh -i ~/.ssh/iotdash-soak \
  -L 8086:localhost:8086 \
  -L 5432:localhost:5432 \
  azureuser@iotdash-soak.eastus.cloudapp.azure.com
```

### SSH Access

```bash
ssh -i ~/.ssh/iotdash-soak azureuser@iotdash-soak.eastus.cloudapp.azure.com
```

---

## Teardown

```bash
cd /Users/erfolg/Documents/projects/iotdash/infra/soak-test
terraform destroy -auto-approve
```

Also clean up the service principal when no longer needed:

```bash
az ad sp delete --id 6192e0fd-30b2-4c8d-b37d-095f8bb29e0a
```
