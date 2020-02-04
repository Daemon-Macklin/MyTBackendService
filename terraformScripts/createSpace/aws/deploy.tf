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
  key_name   = "myt-key"
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDgCHDE7WffkghdAIeoCazVgIctTdsOM+yKHCgek/IbUUveWGPlPgMsxLGGvWrXe/nLDsNVEXvIPZNvsKFLtXnP24DBXws8zi1XgJCzsd4CxFgoRr0DVnHlvKCatezKiqo1FB35Bn5fxy7414w96rrCsesbXbivPu3dd9O/vAC4LxjXoNE4wChWDfxMPCUVhbLtskvTQP683UdGlEhLdDJbQtrfgAeaWFg0nWs6xxsxkFEbTIlrP6562XqBxg3AbCeEALzGG7W3s0LS2+5QO6QC6WUZQsolrh85ktnzs2CYKPThk8Bv8qoUqWQ1VEkuKn61TPAWB3lnfuk6ymzNWD+T dmacklin@DESKTOP-KNU45C3"
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
