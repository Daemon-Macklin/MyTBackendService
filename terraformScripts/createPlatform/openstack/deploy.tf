resource "openstack_networking_floatingip_v2" "myip" {
  pool = "ext-net"
}

resource "openstack_compute_instance_v2" "DMacklinMyTDemo" {
  name = "DMacklinMyTDemo"
  image_name = "ubuntu-1804-LTS"
  availability_zone = "nova"
  flavor_name = "ig.big.disk"
  key_pair = var.openstack_keypair
  security_groups = ["default", "ssh-open-world", "ICMP", "http", "3000 - Open to all", "RabbitMq - Open to all"]
  network {
    name = var.tenant_network
    }
}
resource "openstack_compute_floatingip_associate_v2" "myip" {
  floating_ip = openstack_networking_floatingip_v2.myip.address
  instance_id = openstack_compute_instance_v2.DMacklinMyTDemo.id
  fixed_ip    = openstack_compute_instance_v2.DMacklinMyTDemo.network[0].fixed_ip_v4
}

resource "openstack_blockstorage_volume_v2" "DMacklinMyTDemoVolume" {
  name        = "DMacklinMyTVolume"
  description = ""
  size        = 2
  availability_zone = "nova"
}

resource "openstack_compute_volume_attach_v2" "va_1" {
  instance_id = openstack_compute_instance_v2.DMacklinMyTDemo.id
  volume_id   = openstack_blockstorage_volume_v2.DMacklinMyTDemoVolume.id
}

output "instance_ip_address" {
  value = openstack_networking_floatingip_v2.myip.address
}