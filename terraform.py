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

def generateAWSVars(secretKey, accessKey, publicKey, spaceName, spacePath):

    string = 'variable "aws_secret_key"{\n  default = "' + secretKey + '"\n }\n\n\
    variable "aws_access_key" { \n  default = "' +accessKey +'"\n}\n\n\
    variable "public_key" { \n  default = "' + publicKey + '"\n}\n\n\
    variable "space_name" { \n default = "' + spaceName + '" \n } \n'

    path = spacePath + "/variables.tf"

    f = open(path, "w")
    f.write(string)
    f.close()

    return path
