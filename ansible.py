import subprocess


def configServer(floatingIp, ansiblePath):
    f = open(ansiblePath + "/inventory", "w+")
    f.write("[vms]\n" + floatingIp + "\n")
    f.close()
    executeCommand = "ansible-playbook -i inventory installService.yml -e 'ansible_python_interpreter=/usr/bin/python3'"
    process = subprocess.Popen(executeCommand.split(), stdout=subprocess.PIPE, cwd=ansiblePath)
    output, error = process.communicate()
    return output, error

# Follow this tutorial
# https://www.edureka.co/community/35975/is-it-possible-to-run-an-ansible-playbook-in-python-script