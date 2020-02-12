import subprocess

# Function to launch server configuration ansible playbook
def configServer(floatingIp, ansiblePath):
    # Get the path of the inventory file
    inventory_path = ansiblePath + "/inventory"

    # Open the inventory file and add the floating ip address
    f = open(inventory_path, "w+")
    f.write("[vms]\n" + floatingIp + "\n")
    f.close()

    # Run the ansible-playbook command
    executeCommand = "ansible-playbook -i inventory installService.yml -e 'ansible_python_interpreter=/usr/bin/python3'"
    process = subprocess.Popen(executeCommand.split(), stdout=subprocess.PIPE, cwd=ansiblePath)
    output, error = process.communicate()

    # Return the output and error
    return output, error
