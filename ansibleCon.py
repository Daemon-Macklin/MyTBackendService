import subprocess
from collections import namedtuple

import ansible as ab


def configServer(floatingIp, ansiblePath):
    # playbook_path = ansiblePath + "/installService.yml"
    inventory_path = ansiblePath + "/inventory"

    f = open(inventory_path, "w+")
    f.write("[vms]\n" + floatingIp + "\n")
    f.close()

    executeCommand = "ansible-playbook -i inventory installService.yml -e 'ansible_python_interpreter=/usr/bin/python3'"
    process = subprocess.Popen(executeCommand.split(), stdout=subprocess.PIPE, cwd=ansiblePath)
    output, error = process.communicate()
    return output, error
