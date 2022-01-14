provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = "hux-example"
  location = "West Europe"
}
