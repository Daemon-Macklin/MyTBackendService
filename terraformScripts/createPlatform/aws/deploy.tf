data "aws_ami" "ubuntu" {
  most_recent = true
  owners = ["063491364108"]
}

resource "aws_vpc" "my_vpc" {
  cidr_block = "172.16.0.0/16"

  tags = {
    Name = "MyTVPC"
  }
}

resource "aws_security_group" "MyT-SG" {
  name        = "MyT-SG"
  description = "Allow inbound traffic on required MyT ports"
  vpc_id      = aws_vpc.my_vpc.id

  ingress {
    from_port = 3000
    protocol = "tcp"
    to_port = 3000
  }

  ingress {
    from_port = 5672
    protocol = "tcp"
    to_port = 5672
  }
}

resource "aws_key_pair" "MyT-Key" {
  key_name   = "myt-key"
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC1czloJeXHAt65uC2n1eWiuzgREygy/C8nGIRYvStElsOa0Hunjw4HMCPz4BEdkO9p2nEkO16QmZbOks6P1eC3LtdbQgBYiy4+s+k/Sg4NlXosN1eI7gTM9CP88iDSVh+gZPracJYfq8EB4eHZBZRQD/EZkuVohrq8TxDuJppNp2xLT7wqkEviooRoxz270cJLQ1ozO89GX437Bkr1+VbzuL9p8l+Bay2FXXStCrvMLq9a8A3bC7oZ6f3zyHyzmFSY7U9yuD+YdMBXhQ0TXNGflB/d2RfJWAfDwgiejuHBJ0M63+kQW7IsoKVrhV9d0JOpZDM5Caek+8ngh/BBn7V/ dmacklin@dmacklin-KPL-W0X"
}


resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3a.small"
  key_name = aws_key_pair.MyT-Key.id
  security_groups = [aws_security_group.MyT-SG.id]
  associate_public_ip_address = true

  ebs_block_device {
    device_name = "/dev/xvdb"
    volume_type = "gp2"
    volume_size = 10
  }

  tags = {
    Name = "MyTPlatform"
  }
}