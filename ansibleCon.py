import subprocess
import os

# Function to launch server configuration ansible playbook
def configServer(floatingIp, privateKey, ansiblePath):
    # Get the path of the inventory file
    inventoryPath = ansiblePath + "/inventory"
    keyPath = ansiblePath + "/id_rsa"

    # Open the inventory file and add the floating ip address
    f = open(inventoryPath, "w+")
    f.write("[vms]\n" + floatingIp + "\n")
    f.close()

    # Open the private key file and add the private key
    f = open(keyPath, "w+")
    f.write(privateKey)
    f.close()

    os.chmod(keyPath, 0o600)

    # Run the ansible-playbook command
    executeCommand = "ansible-playbook -i inventory installService.yml -e 'ansible_python_interpreter=/usr/bin/python3'"
    process = subprocess.Popen(executeCommand.split(), stdout=subprocess.PIPE, cwd=ansiblePath)
    output, error = process.communicate()

    # Delete the key
    os.remove(keyPath)

    # Return the output and error
    return output, error
