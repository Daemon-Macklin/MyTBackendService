resource "openstack_networking_floatingip_v2" "myip" {
  pool = var.ip_pool
}

resource "openstack_compute_keypair_v2" "myKeyPair" {
  name       = "${var.platform_name}-key"
  public_key = var.public_key
}

resource "openstack_compute_instance_v2" "virtualMachine" {
  name = var.platform_name
  image_name = var.image_name
  availability_zone = var.availability_zone
  flavor_name = var.flavor_name
  key_pair = openstack_compute_keypair_v2.myKeyPair.name
  security_groups = [var.security_group]
  network {
    name = var.internal_network
    }
}
resource "openstack_compute_floatingip_associate_v2" "myip" {
  floating_ip = openstack_networking_floatingip_v2.myip.address
  instance_id = openstack_compute_instance_v2.virtualMachine.id
  fixed_ip    = openstack_compute_instance_v2.virtualMachine.network[0].fixed_ip_v4
}

resource "openstack_blockstorage_volume_v2" "virtualMachineVolume" {
  name        = "${var.platform_name}-storage"
  description = ""
  size        = var.db_size
  availability_zone =  var.availability_zone
}

resource "openstack_compute_volume_attach_v2" "va_1" {
  instance_id = openstack_compute_instance_v2.virtualMachine.id
  volume_id   = openstack_blockstorage_volume_v2.virtualMachineVolume.id
}

output "instance_ip_address" {
  value = openstack_networking_floatingip_v2.myip.address
}