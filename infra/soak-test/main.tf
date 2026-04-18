terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "soak" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    environment = "soak-test"
    project     = "iotdash"
    purpose     = "performance-testing"
  }
}

resource "azurerm_virtual_network" "soak" {
  name                = "vnet-iotdash-soak"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.soak.location
  resource_group_name = azurerm_resource_group.soak.name
}

resource "azurerm_subnet" "soak" {
  name                 = "snet-iotdash-soak"
  resource_group_name  = azurerm_resource_group.soak.name
  virtual_network_name = azurerm_virtual_network.soak.name
  address_prefixes     = ["10.0.1.0/24"]
}
