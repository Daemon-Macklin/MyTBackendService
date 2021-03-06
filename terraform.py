from python_terraform import Terraform
import os
from random import choice
from string import ascii_lowercase

# Function to initialize terraform directory
def init(pathtoPlatform):

    terra = Terraform(pathtoPlatform)
    return terra.init()

# Function to run create infrastructure scripts
def create(pathToInf):

    # Initalize a terraform object
    # Make the working directory the openstack directory
    terra = Terraform(pathToInf)

    # Apply the IAC in the openstack directory and skip the planning Stage
    return_code, stdout, stderr = terra.apply(skip_plan=True)

    # Get the outputs from the apply
    outputs = terra.output()
    print(stderr)
    print(stdout)
    print(outputs)
    # Return the outputs
    return outputs, return_code

def destroy(pathToInf):

    terra = Terraform(pathToInf)

    return_code, stdout, stderr = terra.destroy()

    return return_code

# Function to generate variables file for aws spaces
def generateAWSSpaceVars(secretKey, accessKey, publicKey, availability_zone, spaceName, spacePath):

    string = 'variable "aws_secret_key"{\n  default = "' + secretKey + '"\n }\n\n\
    variable "aws_access_key" { \n  default = "' +accessKey +'"\n}\n\n\
    variable "public_key" { \n  default = "' + publicKey + '"\n}\n\n\
    variable "availability_zone" { \n  default = "' + availability_zone + '"\n}\n\n\
    variable "space_name" { \n default = "' + spaceName + '" \n } \n'

    path = spacePath + "/variables.tf"

    f = open(path, "w")
    f.write(string)
    f.close()

    return path

# Function to generate variables file for aws platforms
def generateAWSPlatformVars(keyPairId, securityGroupId, subnetId, secretKey, accessKey, dbsize, platformName, platformPath):
    string = 'variable "key_pair_id"{\n  default = "' + keyPairId + '"\n }\n\n\
    variable "aws_secret_key"{\n  default = "' + secretKey + '"\n }\n\n\
    variable "aws_access_key" { \n  default = "' + accessKey + '"\n}\n\n\
    variable "security_group_id" { \n  default = "' +securityGroupId +'"\n}\n\n\
    variable "subnet_id" { \n  default = "' + subnetId + '"\n}\n\n\
    variable "db_size" { \n  default = "' + str(dbsize) + '"\n}\n\n\
    variable "platform_name" { \n default = "' + platformName + '" \n } \n'

    path = platformPath + "/variables.tf"

    f = open(path, "w")
    f.write(string)
    f.close()

    return path

def generateOSPlatformVars(osUsername, osPassword, tenantName, authUrl, availabilityZone, flavorName, imageName, platformName, ipPool, securityGroup, intNetwork, publicKey, dbsize, platformPath):

    string = 'variable "openstack_user_name"{\n  default = "' + osUsername + '"\n }\n\n\
    variable "openstack_password"{\n  default = "' + osPassword + '"\n }\n\n\
    variable "openstack_tenant_name" { \n  default = "' + tenantName + '"\n}\n\n\
    variable "openstack_auth_url" { \n  default = "' +authUrl +'"\n}\n\n\
    variable "availability_zone" { \n default = "'+ availabilityZone + '"\n}\n\n\
    variable "ip_pool" { \n default = "' + ipPool + '"\n}\n\n\
    variable "security_group" { \n default = "' + securityGroup + '"\n}\n\n\
    variable "flavor_name" { \n default = "' + flavorName + '"\n}\n\n\
    variable "image_name" { \n default = "' + imageName + '"\n}\n\n\
    variable "internal_network" { \n default = "' + intNetwork + '"\n}\n\n\
    variable "public_key" { \n default = "' + publicKey + '"\n}\n\n\
    variable "db_size" { \n  default = "' + str(dbsize) + '"\n}\n\n\
    variable "platform_name" { \n default = "' + platformName + '" \n }\n'

    path = platformPath + "/variables.tf"

    f = open(path, "w")
    f.write(string)
    f.close()

    return path

def generateGCPPlatformVars(publicKey, account, platformName, platform, zone, dbsize, platformPath):


    keyPath = os.path.join(platformPath, "id_rsa.pub")
    f = open(keyPath, "w+")
    f.write(publicKey)
    f.close()

    accountPath = os.path.join(platformPath, "account.json")
    f = open(accountPath, "w+")
    f.write(account)
    f.close()

    string =  'variable "ssh_pub_file" { \n  default ="./id_rsa.pub" \n}\n\n\
    variable "platform" { \n  default = "' +platform +'"\n}\n\n\
    variable "zone" { \n  default = "' + zone + '"\n}\n\n\
    variable "db_size" { \n  default = "' + str(dbsize) + '"\n}\n\n\
    variable "platform_name" { \n default = "' + platformName + '" \n } \n'

    varPath = platformPath + "/variables.tf"
    f = open(varPath, "w")
    f.write(string)
    f.close()

    return varPath, accountPath, keyPath

def genComponentID():
    return ''.join(choice(ascii_lowercase) for i in range(12))