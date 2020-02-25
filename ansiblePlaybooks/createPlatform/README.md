# Ansible

Ansible will allow the user to point to the ip address of a virtual machine and then automatically setup the machine and install the required components.

```bash
ansible-playbook -i inventory installService.yml  -e 'ansible_python_interpreter=/usr/bin/python3'
```
