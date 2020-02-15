from flask import Blueprint, request
import response as Response
import terraform as tf
import ansibleCon as ab
from app.config import URL_PREFIX
from shutil import copyfile
from .models.credentialsModel import AWSCreds, OpenstackCreds
from .models.userModel import Users
from .models.spaceModel import SpaceAWS
from passlib.hash import pbkdf2_sha256
import encryption
import os
import time

platform_crud = Blueprint('platform_crud', __name__, url_prefix=URL_PREFIX)


"""
Route to create a platform
Takes in
Platform name
Cloud Service
Space id
Password
User id
"""
@platform_crud.route('platform/create', methods=["Post"])
def createPlatform():
    data = request.json
    externalVolume = None
    print(data)
    if 'platformName' in data:
        platformName = data["platformName"]
    else:
        return Response.make_error_resp(msg="Platform Requires Name", code=400)

    if 'cloudService' in data:
        cloudService = data['cloudService']
    else:
        return Response.make_error_resp(msg="Cloud Service Choice is required", code=400)

    if 'uid' in data:
        uid = data['uid']
    else:
        return Response.make_error_resp(msg="User ID is required", code=400)

    try:
        user = Users.get(Users.uid == uid)
    except Users.DoesNotExist:
        return Response.make_error_resp(msg="No User Found")

    if 'password' in data:
        password = data['password']
    else:
        return Response.make_error_resp(msg="Password is required", code=400)

    if not pbkdf2_sha256.verify(password, user.password):
        return Response.make_error_resp(msg="Password is Incorrect", code=400)

    if 'sid' in data:
        sid = data['sid']
    else:
        return Response.make_error_resp(msg="Space ID is required", code=400)

    try:
        space = SpaceAWS.get((SpaceAWS.id == sid) & (SpaceAWS.uid == uid))
    except AWSCreds.DoesNotExist:
        return Response.make_error_resp(msg="Error Finding Creds", code=404)

    # Get the aws creds object
    try:
        creds = AWSCreds.get((AWSCreds.id == space.cid) & (AWSCreds.uid == uid))
    except AWSCreds.DoesNotExist:
        return Response.make_error_resp(msg="Error Finding Creds", code=404)

    # Decrypt the user data
    secretKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                         string=creds.secretKey)
    accessKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                         string=creds.accessKey)
    privateKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                         string=user.privateKey)

    safePlaformName = platformName.replace('/', '_')
    safePlaformName = safePlaformName.replace(' ', '_')

    platformPath = os.path.join(space.dir + "/platforms", safePlaformName)
    try:
        os.makedirs(platformPath)
    except FileExistsError as e:
        return Response.make_error_resp(msg="Platform Name already used", code=400)
    except Exception as e:
        return Response.make_error_resp(msg="Error Creating Platform Directory", code=400)

    validPlatforms = ["aws", "openstack"]
    if cloudService not in validPlatforms:
        return Response.make_error_resp(msg="invalid cloudService", code=400)
    tfPath = ""
    if cloudService == "aws":
        tfPath = "terraformScripts/createPlatform/aws"
        externalVolume = "/dev/nvme1n1"
        varPath = tf.generateAWSPlatformVars(space.keyPairId, space.securityGroupId, space.subnetId, secretKey, accessKey, safePlaformName, platformPath)
    elif cloudService == "openstack":
        tfPath = "terraformScripts/createPlatform/openstack"
        externalVolume = "/dev/vdb"

    ansiblePath = "ansiblePlaybooks/createPlatform"
    updateAnsiblePlaybook(cloudService, externalVolume, ansiblePath)

    requiredFiles = ["deploy.tf", "provider.tf"]

    for file in requiredFiles:
        copyfile(tfPath + "/" + file, platformPath + "/" + file)

    initResultCode = tf.init(platformPath)

    output, createResultCode = tf.create(platformPath)

    # Remove the vars file
    # os.remove(varPath)

    if createResultCode != 0:
        # Add destroy function here
        return Response.make_error_resp(msg="Error Creating Infrastructure", code=400)

    isUp = serverCheck(output["instance_ip_address"]["value"])

    if not isUp:
        return Response.make_error_resp(msg="Error Contacting Server")

    output, error = ab.configServer(output["instance_ip_address"]["value"], privateKey, ansiblePath)

    print(output)
    print(error)

    return Response.make_success_resp("Platform Created")


# ==============Helper Functions=============#

def serverCheck(floating_ip):
    counter = 0
    isUp = False
    while counter < 12:
        response = os.system("ping -c 1 " + floating_ip)

        if response == 0:
            time.sleep(10)
            isUp = True
            break
        else:
            time.sleep(10)
            counter += 1

    return isUp


def updateAnsiblePlaybook(cloudService, externalVolume, ansiblePath):
    # with is like your try .. finally block in this case
    with open(ansiblePath + "/installService.yml", 'r') as file:
        # read a list of lines into data
        data = file.readlines()

    # now change the 2nd line, note that you have to add a newline
    data[3] = "    cloudService: '" + cloudService + "'\n"
    data[4] = "    externalVol: '" + externalVolume + "'\n"

    # and write everything back
    with open(ansiblePath + "/installService.yml", 'w') as file:
        file.writelines(data)
