resource "aws_vpc" "my_vpc" {
  cidr_block = "172.16.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name = "${var.space_name}-VPC"
  }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.my_vpc.id

  tags = {
    Name = "${var.space_name}-GW"
  }
}


resource "aws_subnet" "my_subnet" {
  vpc_id = aws_vpc.my_vpc.id
  cidr_block = "172.16.10.0/24"
  availability_zone = var.availability_zone
  map_public_ip_on_launch = true
  tags = {
    Name = "${var.space_name}-Subnet"
  }
}

resource "aws_route" "route" {
  route_table_id = aws_vpc.my_vpc.default_route_table_id
  destination_cidr_block    = "0.0.0.0/0"
  gateway_id = aws_internet_gateway.gw.id
}

resource "aws_security_group" "MyT-SG" {
  name        = "${var.space_name}-SG"
  description = "Allow inbound traffic on required MyT ports"
  vpc_id      = aws_vpc.my_vpc.id

  ingress {
    from_port = 3000
    protocol = "tcp"
    to_port = 3000
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 5672
    protocol = "tcp"
    to_port = 5672
    cidr_blocks = ["0.0.0.0/0"]
  }

    ingress {
    from_port = 5671
    protocol = "tcp"
    to_port = 5671
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 22
    protocol = "tcp"
    to_port = 22
    cidr_blocks = ["0.0.0.0/0"]
  }

    ingress {
    from_port = 8
    to_port = 0
    protocol = "icmp"
    cidr_blocks = ["0.0.0.0/0"]
  }


    egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
    egress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    ipv6_cidr_blocks     = ["::/0"]
  }
}

resource "aws_key_pair" "MyT-Key" {
  key_name   = "${var.space_name}-key"
  public_key = var.public_key
}

output "key_pair" {
  value = aws_key_pair.MyT-Key.id
}

output "security_group" {
  value = aws_security_group.MyT-SG.id
}

output "subnet" {
  value = aws_subnet.my_subnet.id
}
