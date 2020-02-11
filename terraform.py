from python_terraform import Terraform


def init(pathtoPlatform):

    terra = Terraform(pathtoPlatform)
    return_code = terra.init()

def create(pathToInf):

    # Initalize a terraform object
    # Make the working directory the openstack directory
    terra = Terraform(pathToInf)

    # Apply the IAC in the openstack directory and skip the planning Stage
    return_code, stdout, stderr = terra.apply(skip_plan=True)

    # Get the outputs from the apply
    outputs = terra.output()

    # Return the outputs
    return outputs, return_code

def generateAWSSpaceVars(secretKey, accessKey, publicKey, spaceName, spacePath):

    string = 'variable "aws_secret_key"{\n  default = "' + secretKey + '"\n }\n\n\
    variable "aws_access_key" { \n  default = "' +accessKey +'"\n}\n\n\
    variable "public_key" { \n  default = "' + publicKey + '"\n}\n\n\
    variable "space_name" { \n default = "' + spaceName + '" \n } \n'

    path = spacePath + "/variables.tf"

    f = open(path, "w")
    f.write(string)
    f.close()

    return path

def generateAWSPlatformVars(keyPairId, securityGroupId, subnetId, spaceName):

    string = 'variable "key_pair_id"{\n  default = "' + keyPairId + '"\n }\n\n\
    variable "security_group_id" { \n  default = "' +securityGroupId +'"\n}\n\n\
    variable "subnet_id" { \n  default = "' + subnetId + '"\n}\n\n\
    variable "space_name" { \n default = "' + spaceName + '" \n } \n'

    path = spacePath + "/variables.tf"

    f = open(path, "w")
    f.write(string)
    f.close()

    return path