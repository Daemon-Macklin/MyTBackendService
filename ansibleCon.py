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

def updateAnsiblePlaybookVars(cloudService, externalVolume, database, rabbitTLS, monitoring, monitoringFreq, ansiblePath):

    monitoringFreq = "*/" + monitoringFreq

    with open(ansiblePath + "/installService.yml", 'r') as file:
        # read a list of lines into data
        data = file.readlines()

    # now change the 2nd line, note that you have to add a newline
    data[3] = "    cloudService: '" + cloudService + "'\n"
    data[4] = "    externalVol: '" + externalVolume + "'\n"
    data[5] = "    database: '" + database + "' \n"
    data[6] = "    rabbitmqTLS: '" + rabbitTLS + "' \n"
    data[7] = "    monitoring: '" + monitoring + "' \n"
    data[8] = "    monitoringFreq: '" + monitoringFreq + "' \n"

    # and write everything back
    with open(ansiblePath + "/installService.yml", 'w') as file:
        file.writelines(data)

def generateMyTConfig(rabbitUser, rabbitPass, rabbitTLS, database, ansiblePath):

    configPath = os.path.join(ansiblePath, "roles", "dmacklin.mytInstall", "templates", "config.ini")
    # Create config parser object
    conf = configparser.ConfigParser()

    if rabbitUser != "" and rabbitPass != "":
        setRabbitmqComposeData(rabbitUser, rabbitPass, database, ansiblePath)

    if rabbitTLS == "true":
        enableRabbitMQTLS(database, ansiblePath)

    # Generate config file data
    conf['rabbitmq'] = {
        'user': rabbitUser,
        'password': rabbitPass,
        'tlsEnabled': rabbitTLS
    }

    # Write data to file
    with open(configPath, 'w') as configfile:
        conf.write(configfile)

def setRabbitmqComposeData(rabbitUser, rabbitPass, database, ansiblePath):

    dcPath = os.path.join(ansiblePath, "roles", "dmacklin.mytInstall", "templates", "dockerComposeFiles", database + ".yml")

    with open(dcPath, 'r') as file:
        # read a list of lines into data
        data = file.readlines()

    data[11] = "    environment: \n"
    data[15] = "      - RABBITMQ_DEFAULT_USER=" + rabbitUser + "\n"
    data[16] = "      - RABBITMQ_DEFAULT_PASS=" + rabbitPass + "\n"


    # and write everything back
    with open(dcPath, 'w') as file:
        file.writelines(data)

def enableRabbitMQTLS(database, ansiblePath):

    dcPath = os.path.join(ansiblePath, "roles", "dmacklin.mytInstall", "templates", "dockerComposeFiles", database + ".yml")

    with open(dcPath, 'r') as file:
        # read a list of lines into data
        data = file.readlines()
    data[11] = "    environment: \n"
    data[12] = "      - RABBITMQ_SSL_CERTFILE=/cert_rabbitmq/cert.pem\n"
    data[13] = "      - RABBITMQ_SSL_KEYFILE=/cert_rabbitmq/key.pem\n"
    data[14] = "      - RABBITMQ_SSL_CACERTFILE=/cert_rabbitmq/cacert.pem\n"

    # and write everything back
    with open(dcPath, 'w') as file:
        file.writelines(data)


def generateRequirementsFile(packages, ansilbePath, roleName):

    string = ""
    for package in packages:
        string = string + package + "\n"

    path = os.path.join(ansilbePath, "roles", roleName, "templates", "requirements.txt")

    f = open(path, "w+")
    f.write(string)
    f.close()

def updateDBDumpVars(database, ansiblePath):

    ansiblePath = os.path.join(ansiblePath, "dbDump.yml")

    with open(ansiblePath, 'r') as file:
        # read a list of lines into data
        data = file.readlines()

    # Update Vars
    data[3] =  "    database: '" + database + "'\n"

    # and write everything back
    with open(ansiblePath, 'w') as file:
        file.writelines(data)