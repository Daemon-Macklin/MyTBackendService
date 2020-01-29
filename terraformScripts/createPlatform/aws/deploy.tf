resource "aws_vpc" "my_vpc" {
  cidr_block = "172.16.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name = "MyTVPC"
  }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.my_vpc.id

  tags = {
    Name = "main"
  }
}


resource "aws_subnet" "my_subnet" {
  vpc_id = aws_vpc.my_vpc.id
  cidr_block = "172.16.10.0/24"
  availability_zone = "eu-west-1a"
  map_public_ip_on_launch = true
  tags = {
    Name = "MyTSubnet"
  }
}

resource "aws_route" "route" {
  route_table_id = aws_vpc.my_vpc.default_route_table_id
  destination_cidr_block    = "0.0.0.0/0"
  gateway_id = aws_internet_gateway.gw.id
}

resource "aws_security_group" "MyT-SG" {
  name        = "MyT-SG"
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
    from_port = 22
    protocol = "tcp"
    to_port = 22
    cidr_blocks = ["0.0.0.0/0"]
  }
ingress {
  protocol = "icmp"
  from_port = 8
  to_port = 0
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
  key_name   = "myt-key"
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC1czloJeXHAt65uC2n1eWiuzgREygy/C8nGIRYvStElsOa0Hunjw4HMCPz4BEdkO9p2nEkO16QmZbOks6P1eC3LtdbQgBYiy4+s+k/Sg4NlXosN1eI7gTM9CP88iDSVh+gZPracJYfq8EB4eHZBZRQD/EZkuVohrq8TxDuJppNp2xLT7wqkEviooRoxz270cJLQ1ozO89GX437Bkr1+VbzuL9p8l+Bay2FXXStCrvMLq9a8A3bC7oZ6f3zyHyzmFSY7U9yuD+YdMBXhQ0TXNGflB/d2RfJWAfDwgiejuHBJ0M63+kQW7IsoKVrhV9d0JOpZDM5Caek+8ngh/BBn7V/ dmacklin@dmacklin-KPL-W0X"
}

resource "aws_instance" "web" {
  ami = "ami-02df9ea15c1778c9c"
  instance_type = "t3a.small"
  key_name = aws_key_pair.MyT-Key.id
  security_groups = [aws_security_group.MyT-SG.id]
  subnet_id = aws_subnet.my_subnet.id
  depends_on = ["aws_internet_gateway.gw"]

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