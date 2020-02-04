resource "aws_instance" "web" {
  ami = "ami-02df9ea15c1778c9c"
  instance_type = "t3a.small"
  key_name = var.key_pair_id
  security_groups = [var.security_group_id]
  subnet_id = var.subnet_id

  tags = {
    Name = "MyTPlatform"
  }
}

resource "aws_ebs_volume" "db-volume" {
  availability_zone = "eu-west-1a"
  size              = 10
  tags = {
    Name = "MyT-DB storage"
  }
}

resource "aws_volume_attachment" "ebs_att" {
  device_name = "/dev/sdh"
  volume_id   = aws_ebs_volume.db-volume.id
  instance_id = aws_instance.web.id
}

output "instance_ip_address" {
  value = aws_instance.web.public_ip
}

output "volume_device_name" {
  value = aws_volume_attachment.ebs_att.device_name
}