output "vm_public_ip" {
  description = "Public IP address of the soak test VM"
  value       = azurerm_linux_virtual_machine.soak.public_ip_address
}

output "ssh_command" {
  description = "SSH command to connect to the soak test VM"
  value       = "ssh ${var.admin_username}@${azurerm_linux_virtual_machine.soak.public_ip_address}"
}

output "grafana_url" {
  description = "Grafana dashboard URL"
  value       = "http://${azurerm_linux_virtual_machine.soak.public_ip_address}:3000"
}

output "emqx_dashboard_url" {
  description = "EMQX dashboard URL"
  value       = "http://${azurerm_linux_virtual_machine.soak.public_ip_address}:18083"
}

output "backend_url" {
  description = "Backend API URL"
  value       = "http://${azurerm_linux_virtual_machine.soak.public_ip_address}:8000"
}

output "resource_group" {
  description = "Resource group name (for teardown)"
  value       = azurerm_resource_group.soak.name
}
