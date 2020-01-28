import subprocess


def configServer(floating_ip, ansiblePath):
    f = open(ansiblePath + "/inventory", "w+")
    f.write("[vms]\n" + floating_ip + "\n")
    f.close()
    executeCommand = "ansible-playbook -i inventory installService.yml -e 'ansible_python_interpreter=/usr/bin/python3'"
    process = subprocess.Popen(executeCommand.split(), stdout=subprocess.PIPE, cwd="./ansible")
    output, error = process.communicate()
    return output, error

