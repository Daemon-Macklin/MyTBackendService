import subprocess
import configparser
import os

# Function to launch server configuration ansible playbook
def runPlaybook(floatingIp, privateKey, ansiblePath, playbooknName):
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
    executeCommand = "ansible-playbook -i inventory " + playbooknName + ".yml  -e 'ansible_python_interpreter=/usr/bin/python3'"
    print(executeCommand)
    process = subprocess.Popen(executeCommand.split(), stdout=subprocess.PIPE, cwd=ansiblePath)
    output, error = process.communicate()

    # Delete the key
    os.remove(keyPath)

    # Return the output and error
    return "", ""

def updateAnsiblePlaybookVars(cloudService, externalVolume, database, ansiblePath):
    # with is like your try .. finally block in this case
    with open(ansiblePath + "/installService.yml", 'r') as file:
        # read a list of lines into data
        data = file.readlines()

    # now change the 2nd line, note that you have to add a newline
    data[3] = "    cloudService: '" + cloudService + "'\n"
    data[4] = "    externalVol: '" + externalVolume + "'\n"
    data[5] = "    database: '" + database + "' \n"

    # and write everything back
    with open(ansiblePath + "/installService.yml", 'w') as file:
        file.writelines(data)

def generateMyTConfig(rabbitUser, rabbitPass, database, ansiblePath):

    configPath = os.path.join(ansiblePath, "roles", "dmacklin.mytInstall", "templates", "config.ini")
    # Create config parser object
    conf = configparser.ConfigParser()

    if rabbitUser != "" and rabbitPass != "":
        setRabbitmqComposeData(rabbitUser, rabbitPass, database, ansiblePath)

    # Generate config file data
    conf['rabbitmq'] = {
        'user': rabbitUser,
        'password': rabbitPass
    }

    # Write data to file
    with open(configPath, 'w') as configfile:
        conf.write(configfile)

def setRabbitmqComposeData(rabbitUser, rabbitPass, database, ansiblePath):

    dcPath = os.path.join(ansiblePath, "roles", "dmacklin.mytInstall", "templates", "dockerComposeFiles", database + ".yml")

    with open(dcPath, 'r') as file:
        # read a list of lines into data
        data = file.readlines()

    data[19] = "    environment: \n"
    data[20] = "      - RABBITMQ_DEFAULT_USER=" + rabbitUser + "\n"
    data[21] = "      - RABBITMQ_DEFAULT_PASS=" + rabbitPass + "\n"

    # and write everything back
    with open(dcPath, 'w') as file:
        file.writelines(data)


def generateRequirementsFile(list, ansilbePath):

    string = ""
    for package in list:
        string = string + package + "\n"

    path = os.path.join(ansilbePath, "roles", "dmacklin.mytInstall", "templates", "requirements.txt")

    f = open(path, "w+")
    f.write(string)
    f.close()