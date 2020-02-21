from flask import Blueprint, request
import response as Response
import terraform as tf
import ansibleCon as ab
from app.config import URL_PREFIX
from shutil import copyfile
from .models.credentialsModel import AWSCreds, OpenstackCreds
from .models.userModel import Users
from .models.spaceModel import SpaceAWS
from .models.platformModel import Platforms
from passlib.hash import pbkdf2_sha256
import encryption
import os
import time
import uuid
import shutil
from flask_jwt_extended import jwt_required


platform_crud = Blueprint('platform_crud', __name__, url_prefix=URL_PREFIX)

"""
Route to create a platform
Takes in
Platform name
Cloud Service
Space id
Password
User id
rabbitmq username
rabbitmq password
database
"""
@platform_crud.route('platform/create', methods=["Post"])
@jwt_required
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

    if "rabbitUser" in data:
        rabbitUser = data['rabbitUser']
    else:
        rabbitUser = ""

    if "rabbitPass" in data:
        rabbitPass = data['rabbitPass']
    else:
        rabbitPass = ""

    if "database" in data:
        validDbs = ["influxdb", "mongodb"]
        database = data['database']
        if database not in validDbs:
            return Response.make_error_resp(msg="Invalid database", code=400)
    else:
        return Response.make_error_resp(msg="Database is required", code=400)

    try:
        space = SpaceAWS.get((SpaceAWS.id == sid) & (SpaceAWS.uid == uid))
    except SpaceAWS.DoesNotExist:
        return Response.make_error_resp(msg="Error Finding Space", code=404)

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

    platformPath = os.path.join(space.dir, "platforms", safePlaformName)
    try:
        os.makedirs(platformPath)
    except FileExistsError as e:
        return Response.make_error_resp(msg="Platform Name already used", code=400)
    except:
        return Response.make_error_resp(msg="Error Creating Platform Directory", code=400)

    validPlatforms = ["aws", "openstack"]
    if cloudService not in validPlatforms:
        return Response.make_error_resp(msg="invalid cloudService", code=400)
    tfPath = ""
    if cloudService == "aws":
        tfPath = "terraformScripts/createPlatform/aws"
        externalVolume = "/dev/nvme1n1"
        varPath = tf.generateAWSPlatformVars(space.keyPairId, space.securityGroupId, space.subnetId, secretKey,
                                             accessKey, safePlaformName, platformPath)
    elif cloudService == "openstack":
        tfPath = "terraformScripts/createPlatform/openstack"
        externalVolume = "/dev/vdb"

    createAnsibleFiles = "ansiblePlaybooks/createPlatform"
    ansiblePath = os.path.join(platformPath, "ansible")

    shutil.copytree(createAnsibleFiles, ansiblePath)

    ab.updateAnsiblePlaybookVars(cloudService, externalVolume, database, ansiblePath)

    ab.generateMyTConfig(rabbitUser, rabbitPass, database, ansiblePath)

    requiredFiles = ["deploy.tf", "provider.tf"]

    for file in requiredFiles:
        copyfile(tfPath + "/" + file, platformPath + "/" + file)

    initResultCode = tf.init(platformPath)

    output, createResultCode = tf.create(platformPath)

    # Remove the vars file
    os.remove(varPath)

    if createResultCode != 0:
        # Add destroy function here
        return Response.make_error_resp(msg="Error Creating Infrastructure", code=400)

    isUp = serverCheck(output["instance_ip_address"]["value"])

    if not isUp:
        return Response.make_error_resp(msg="Error Contacting Server")

    output, error = ab.configServer(output["instance_ip_address"]["value"], privateKey, ansiblePath)

    print(output)
    print(error)

    newPlatform = Platforms.create(dir=platformPath, name=platformName, uid=user.uid, sid=space.id,
                                   cloudService=cloudService, ipAddress=output["instance_ip_address"]["value"],
                                   id=str(uuid.uuid4()))

    try:
        platform = Platforms.get(Platforms.id == newPlatform.id)
    except Platforms.DoesNotExist:
        return Response.make_error_resp(msg="Platform Not Found", code=400)

    res = {
        "id": platform.id,
        "name": platform.name
    }
    return Response.make_json_response(res)


"""
Route that will delete a platform
Takes in
User id
password
platform id
"""
@platform_crud.route('/platform/remove/<id>', methods=['Post'])
@jwt_required
def removePlatform(id):
    try:
        platform = Platforms.get(Platforms.id == id)
    except Platforms.DoesNotExist:
        return Response.make_error_resp(msg="Platform Not Found", code=400)

    data = request.json

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

    path = ""
    if platform.cloudService == "aws":

        space = SpaceAWS.get((SpaceAWS.id == platform.sid) & (SpaceAWS.uid == uid))
        creds = AWSCreds.get(AWSCreds.id == space.cid)

        secretKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                             string=creds.secretKey)
        accessKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                             string=creds.accessKey)

        tf.generateAWSPlatformVars("", "", "", secretKey, accessKey,
                                             "", platform.dir)

        path = platform.dir
        resultCode = tf.destroy(platform.dir)

        if resultCode != 0:
            return Response.make_error_resp(msg="Error deleting platform")

        platform.delete_instance()

    if path != "":
        shutil.rmtree(path)
        return Response.make_success_resp(msg="Platform Has been removed")


@platform_crud.route('/platforms/get/<uid>', methods=['get'])
@jwt_required
def getPlatforms(uid):

    try:
        user = Users.get(Users.uid == uid)
    except Users.DoesNotExist:
        return Response.make_error_resp(msg="No User Found")
    except:
        return Response.make_error_resp(msg="Error reading database", code=500)

    response = []
    platformQuery = Platforms.select(Platforms.name, Platforms.id, Platforms.cloudService, Platforms.ipAddress).where(Platforms.uid == user.uid)
    for platform in platformQuery:
        plat = {
            "name": platform.name,
            "id" : platform.id,
            "ip" : platform.ipAddress,
            "cloudService" : platform.cloudService
        }
        response.append(plat)

    res = {
        "platforms": response
    }
    return Response.make_json_response(res)


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
