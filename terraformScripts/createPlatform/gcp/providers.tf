
provider "google" {
  credentials = file("account.json")
  project     = var.platform
  region      = var.zone
}
