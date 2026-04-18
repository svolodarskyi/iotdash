resource "azurerm_public_ip" "soak" {
  name                = "pip-iotdash-soak"
  location            = azurerm_resource_group.soak.location
  resource_group_name = azurerm_resource_group.soak.name
  allocation_method   = "Dynamic"
  sku                 = "Basic"
}

resource "azurerm_network_security_group" "soak" {
  name                = "nsg-iotdash-soak"
  location            = azurerm_resource_group.soak.location
  resource_group_name = azurerm_resource_group.soak.name

  security_rule {
    name                       = "SSH"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = var.allowed_ssh_cidr
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "MQTT"
    priority                   = 200
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "1883"
    source_address_prefix      = var.allowed_ssh_cidr
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "Backend"
    priority                   = 300
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "8000"
    source_address_prefix      = var.allowed_ssh_cidr
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "Frontend"
    priority                   = 400
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5173"
    source_address_prefix      = var.allowed_ssh_cidr
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "Grafana"
    priority                   = 500
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3000"
    source_address_prefix      = var.allowed_ssh_cidr
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "EMQX-Dashboard"
    priority                   = 600
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "18083"
    source_address_prefix      = var.allowed_ssh_cidr
    destination_address_prefix = "*"
  }
}

resource "azurerm_network_interface" "soak" {
  name                = "nic-iotdash-soak"
  location            = azurerm_resource_group.soak.location
  resource_group_name = azurerm_resource_group.soak.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.soak.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.soak.id
  }
}

resource "azurerm_network_interface_security_group_association" "soak" {
  network_interface_id      = azurerm_network_interface.soak.id
  network_security_group_id = azurerm_network_security_group.soak.id
}

resource "azurerm_linux_virtual_machine" "soak" {
  name                  = "vm-iotdash-soak"
  location              = azurerm_resource_group.soak.location
  resource_group_name   = azurerm_resource_group.soak.name
  size                  = var.vm_size
  admin_username        = var.admin_username
  network_interface_ids = [azurerm_network_interface.soak.id]

  custom_data = base64encode(templatefile("${path.module}/cloud-init.yaml", {
    github_repo       = var.github_repo
    github_branch     = var.github_branch
    device_count      = var.device_count
    publish_interval  = var.publish_interval
    alert_webhook_url = var.alert_webhook_url
    acr_login_server  = azurerm_container_registry.soak.login_server
    acr_username      = azurerm_container_registry.soak.admin_username
    acr_password      = azurerm_container_registry.soak.admin_password
  }))

  admin_ssh_key {
    username   = var.admin_username
    public_key = var.admin_ssh_public_key
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
    disk_size_gb         = var.os_disk_size_gb
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "ubuntu-24_04-lts"
    sku       = "server"
    version   = "latest"
  }

  tags = {
    environment = "soak-test"
    project     = "iotdash"
  }
}
