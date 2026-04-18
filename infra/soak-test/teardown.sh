#!/usr/bin/env bash
# Teardown soak test infrastructure
# WARNING: This destroys all resources — VM, disk, network, resource group
#
# Cost reminder: the soak test VM costs ~EUR 4/day (~EUR 110-130/month).
# Run this when you're done testing!

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== IoTDash Soak Test Teardown ==="
echo ""
echo "This will DESTROY all soak test resources:"
echo "  - VM (vm-iotdash-soak)"
echo "  - Disk, NIC, NSG, Public IP"
echo "  - VNet and Subnet"
echo "  - Resource Group (rg-iotdash-soak)"
echo ""
read -rp "Are you sure? (type 'yes' to confirm): " confirm

if [[ "$confirm" != "yes" ]]; then
  echo "Aborted."
  exit 1
fi

cd "$SCRIPT_DIR"
terraform destroy -auto-approve

echo ""
echo "Teardown complete. All soak test resources have been destroyed."
