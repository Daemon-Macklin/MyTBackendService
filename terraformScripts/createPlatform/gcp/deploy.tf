resource "google_compute_instance" "default" {
  name         = var.platform_name
  machine_type = "n1-standard-2"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-1804-lts"
      size = 10
   	}
  }

  network_interface {
    network = "default"
    access_config {}
  }

  metadata = {
   ssh-keys = "ubuntu:${file(var.ssh_pub_file)}" 
 }
}

resource "google_compute_attached_disk" "default" {
  disk     = google_compute_disk.default.self_link
  instance = google_compute_instance.default.self_link
}


resource "google_compute_disk" "default" {
  name  = "${var.platform_name}-storage"
  size = 10
  zone = var.zone
}


resource "google_compute_firewall" "securitygroups" {
  name    = "${var.platform_name}-firewall"
  network = "default"

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["80", "22"]
  }

}
