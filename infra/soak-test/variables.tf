variable "location" {
  description = "Azure region for soak test resources"
  type        = string
  default     = "westeurope"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-iotdash-soak"
}

variable "vm_size" {
  description = "Azure VM size (D2s_v5 = 2 vCPU, 8 GB, no credit throttling)"
  type        = string
  default     = "Standard_D2s_v5"
}

variable "os_disk_size_gb" {
  description = "OS disk size in GB"
  type        = number
  default     = 128
}

variable "admin_username" {
  description = "SSH admin username for the VM"
  type        = string
  default     = "azureuser"
}

variable "admin_ssh_public_key" {
  description = "SSH public key for VM access"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH into the VM (your IP/32)"
  type        = string
}

variable "acr_name" {
  description = "Azure Container Registry name (globally unique, alphanumeric only)"
  type        = string
  default     = "criotdashsoak"
}

variable "github_repo" {
  description = "GitHub repository URL to clone on the VM"
  type        = string
  default     = "https://github.com/svolodarskyi/iotdash.git"
}

variable "github_branch" {
  description = "Git branch to checkout on the VM"
  type        = string
  default     = "main"
}

variable "device_count" {
  description = "Number of simulated devices for the soak test"
  type        = number
  default     = 1000
}

variable "publish_interval" {
  description = "Publish interval in seconds for simulated devices"
  type        = number
  default     = 5
}

variable "github_actions_cidrs" {
  description = "GitHub Actions runner IP ranges for SSH access"
  type        = list(string)
  default     = ["4.152.0.0/14", "13.64.0.0/11", "20.0.0.0/9", "40.64.0.0/10", "52.0.0.0/8", "104.208.0.0/13"]
}

variable "dns_label" {
  description = "DNS label for the public IP (<label>.<region>.cloudapp.azure.com)"
  type        = string
  default     = "iotdash-soak"
}

variable "alert_webhook_url" {
  description = "Webhook URL for soak test alerts (Slack, ntfy.sh, etc.). Leave empty to disable."
  type        = string
  default     = ""
}
