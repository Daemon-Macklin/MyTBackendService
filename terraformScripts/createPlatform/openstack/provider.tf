provider "openstack" {
user_name = var.openstack_user_name
tenant_name = var.openstack_tenant_name
password  = var.openstack_password
auth_url  = var.openstack_auth_url
} 
