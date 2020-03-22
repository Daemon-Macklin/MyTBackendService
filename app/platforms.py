from flask import Blueprint, request, send_file
import requests
import response as Response
import terraform as tf
import ansibleCon as ab
from app.config import URL_PREFIX
from shutil import copyfile
from .models.credentialsModel import *
from .models.userModel import Users
from .models.spaceModel import *
from .models.platformModel import Platforms
from passlib.hash import pbkdf2_sha256
import encryption
import os
import time
import uuid
import shutil
from flask_jwt_extended import jwt_required
import datetime
import subprocess


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
rabbitmq tls
database
database size
data processing script
list of packages
monitoring
monitoring freq
image name
flavor name
zone
cid
"""
@platform_crud.route('platform/create', methods=["Post"])
@jwt_required
def createPlatform():
    data = dict(request.form)

    if 'script' in request.files:
        script = request.files['script']
    else:
        script = None

    externalVolume = None

    if 'platformName' in data:
        platformName = data["platformName"] + tf.genComponentID()
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
        sid = ""

    if "rabbitUser" in data:
        rabbitUser = data['rabbitUser']
    else:
        rabbitUser = ""

    if "rabbitPass" in data:
        rabbitPass = data['rabbitPass']
    else:
        rabbitPass = ""

    if "rabbitTLS" in data:
        # Get string version of rabbitTLS flag as ansible is looking for a string
        rabbitTLS = data['rabbitTLS']
    else:
        rabbitTLS = "false"

    if "database" in data:
        validDbs = ["influxdb", "mongodb", "mysqldb", "timescaledb"]
        database = data['database']
        if database not in validDbs:
            return Response.make_error_resp(msg="Invalid database", code=400)
    else:
        return Response.make_error_resp(msg="Database is required", code=400)

    if "dbsize" in data:
        dbsize = int(data["dbsize"])
        if dbsize % 10 != 0 or dbsize > 100:
            return Response.make_error_resp(msg="Database Size is invalid")
    else:
       return Response.make_error_resp(msg="Database Size is required", code=400)

    if 'packages' in data:
        packages = data['packages'].replace(" ", "").split(",")
    else:
        packages = []

    if 'monitoring' in data:
        monitoring = data["monitoring"]
        if monitoring == "true":
            monitoringFreq = data["monitoringFreq"]
        else:
            monitoringFreq = "30"
    else:
        monitoring = "false"
        monitoringFreq = "30"

    if len(packages) != 0:
        issue = checkPackages(packages)
        if issue != "":
            return Response.make_error_resp(msg=issue + " Package not valid", code=400)

    packages = packages + ["pika==1.1.0", "influxdb", "pymongo"]

    safePlatformName = platformName.replace('/', '_')
    safePlatformName = safePlatformName.replace(' ', '_')

    cid = ""
    space = ""
    # ------------Terraform Setup------------#
    validPlatforms = ["aws", "openstack", "gcp"]
    if cloudService not in validPlatforms:
        return Response.make_error_resp(msg="invalid cloudService", code=400)

    # Define Terraform Variables
    tfPath = ""
    platformPath = ""
    if cloudService == "aws":
        tfPath = "terraformScripts/createPlatform/aws"
        externalVolume = "/dev/nvme1n1"
        try:
            space = SpaceAWS.get((SpaceAWS.id == sid) & (SpaceAWS.uid == uid))
        except SpaceAWS.DoesNotExist:
            return Response.make_error_resp(msg="Error Finding Space", code=400)
        platformPath = os.path.join(space.dir, "platforms", safePlatformName)

    elif cloudService == "openstack":
        tfPath = "terraformScripts/createPlatform/openstack"
        externalVolume = "/dev/vdb"
        if 'flavorName' in data:
            flavorName = data['flavorName']
        else:
            return Response.make_error_resp(msg="Flavor Name Required for Openstack")

        if 'imageName' in data:
            imageName = data['imageName']
        else:
            return Response.make_error_resp(msg="Image Name Required for Openstack")

        try:
            space = SpaceOS.get((SpaceOS.id == sid) & (SpaceOS.uid == uid))
        except SpaceOS.DoesNotExist:
            return Response.make_error_resp(msg="Error Finding Space", code=400)
        platformPath = os.path.join("openstack", "platforms", safePlatformName)

    elif cloudService == "gcp":
        tfPath = "terraformScripts/createPlatform/gcp"
        externalVolume = "/dev/sdb"
        if 'zone' in data:
            zone = data['zone']
        else:
            return Response.make_error_resp(msg="Zone Required for GCP")

        if 'cid' in data:
            cid = data['cid']
        else:
            return Response.make_error_resp(msg="Credentials Required for GCP")

        try:
            creds = GCPCreds.get((GCPCreds.id == cid) & (GCPCreds.uid == uid))
        except SpaceOS.DoesNotExist:
            return Response.make_error_resp(msg="Error Finding Credentials", code=400)
        platformPath = os.path.join("gcp", "platforms", safePlatformName)

    try:
        shutil.copytree(tfPath, platformPath)
    except FileExistsError as e:
        return Response.make_error_resp(msg="Platform Name already used", code=400)

    if cloudService == "aws":
        print(dbsize)
        varPath = awsGenVars(user, password, space, dbsize, safePlatformName, platformPath)
        if varPath == "Error Finding Creds":
            return Response.make_error_resp(msg="Error Finding Creds", code=400)

    elif cloudService == "openstack":
        print(dbsize)
        varPath = osGenVars(user, password, space, flavorName, imageName, dbsize, safePlatformName, platformPath)
        if varPath == "Error Finding Creds":
            return Response.make_error_resp(msg="Error Finding Creds", code=400)

    elif cloudService == "gcp":
        print(dbsize)
        varPath, accountPath, keyPath = gcpGenVars(user, password, creds, zone, dbsize, safePlatformName, platformPath)

    #------------Ansible Setup------------#
    createAnsibleFiles = "ansiblePlaybooks/createPlatform"
    ansiblePath = os.path.join(platformPath, "ansible", "createPlatform")

    shutil.copytree(createAnsibleFiles, ansiblePath)

    if script:
        script.save(os.path.join(ansiblePath, "roles", "dmacklin.mytInstall", "templates", "dataProcessing.py"))

    ab.updateAnsiblePlaybookVars(cloudService, externalVolume, database, rabbitTLS, monitoring, monitoringFreq, ansiblePath)

    ab.generateMyTConfig(rabbitUser, rabbitPass, rabbitTLS, database, ansiblePath)

    ab.generateRequirementsFile(packages, ansiblePath, "dmacklin.mytInstall")

    # ------------Terraform Create------------#
    initResultCode = tf.init(platformPath)

    output, createResultCode = tf.create(platformPath)

    print(createResultCode)
    if createResultCode != 0:
        # Add destroy function here
        print("Removing Inf")
        tf.destroy(platformPath)
        shutil.rmtree(platformPath)
        return Response.make_error_resp(msg="Error Creating Infrastructure", code=400)

    # Remove the vars file
    os.remove(varPath)

    if cloudService == "gcp":
        os.remove(accountPath)
        os.remove(keyPath)

    isUp = serverCheck(output["instance_ip_address"]["value"])

    if not isUp:
        return Response.make_error_resp(msg="Error Contacting Server")

    # ------------Ansible Create------------#
    privateKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                          string=user.privateKey)

    aboutput, aberror = ab.runPlaybook(output["instance_ip_address"]["value"], privateKey, ansiblePath, "installService")

    print(aboutput)
    print(aberror)

    # ------------Save Platform------------#
    newPlatform = Platforms.create(dir=platformPath, name=safePlatformName, uid=user.uid, sid=sid, cid=cid,
                                   cloudService=cloudService, ipAddress=output["instance_ip_address"]["value"],
                                   packageList=data['packages'], database=database, dbsize=dbsize, id=str(uuid.uuid4()))

    try:
        platform = Platforms.get(Platforms.id == newPlatform.id)
    except Platforms.DoesNotExist:
        return Response.make_error_resp(msg="Platform Not Found", code=400)

    # ------------Return Data------------#
    if rabbitTLS == "true":
        filename = "cert_rabbitmq.zip"
        dumpPath = os.path.join(ansiblePath, filename)
        try:
            return send_file(dumpPath, attachment_filename=filename, as_attachment=True, mimetype="application/zip")
        except Exception as e:
            print(e)
            return Response.make_error_resp("Error Getting Certs", code=400)
    else:
        res = {
            "id": platform.id,
            "name": platform.name
        }
        return Response.make_data_resp(res)


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

        tf.generateAWSPlatformVars("", "", "", secretKey, accessKey, 0,
                                             "", platform.dir)

    elif platform.cloudService == "openstack":

        space = SpaceOS.get((SpaceOS.id == platform.sid) & (SpaceOS.uid == uid))
        creds = OSCreds.get(OSCreds.id == space.cid)

        osUsername = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                              string=creds.username)
        osPassword = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                              string=creds.password)
        authUrl = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                           string=creds.authUrl)

        tf.generateOSPlatformVars(osUsername, osPassword, space.tenantName, authUrl, space.availabilityZone, "", "", "", space.ipPool,
                                         space.securityGroup, space.intNetwork, "", "", platform.dir)

    elif platform.cloudService == "gcp":
        creds = GCPCreds.get(GCPCreds.id == platform.cid)

        gcpGenVars(user, password, creds, "", "", platform.name, platform.dir)

    path = platform.dir
    resultCode = tf.destroy(platform.dir)

    if resultCode != 0:
        return Response.make_error_resp(msg="Error deleting platform")

    platform.delete_instance()

    if path != "":
        shutil.rmtree(path)
        return Response.make_success_resp(msg="Platform Has been removed")


@platform_crud.route('/platforms/get/<uid>', methods=['Get'])
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


"""
Endpoint to update the data processing script in a platform
takes in:
uid
password
script
platform id
list of packages
"""
@platform_crud.route('/platforms/update/processing/<id>', methods=['Post'])
@jwt_required
def updateDataProcessing(id):

    try:
        platform = Platforms.get(Platforms.id == id)
    except Platforms.DoesNotExist:
        return Response.make_error_resp(msg="Platform Not Found", code=400)

    data = dict(request.form)

    if 'script' in request.files:
        script = request.files['script']
    else:
        return Response.make_error_resp(msg="Script not in request", code=400)

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

    if 'packages' in data:
        packages = data['packages'].replace(" ", "").split(",")
    else:
        packages = []

    if len(packages) != 0:
        issue = checkPackages(packages)
        if issue != "":
            return Response.make_error_resp(msg=issue + " Package not valid", code=400)

    exsistingPackages = platform.packageList.split(",")
    packages = exsistingPackages + packages + ["pika==1.1.0", "influxdb", "pymongo"]


    if not pbkdf2_sha256.verify(password, user.password):
        return Response.make_error_resp(msg="Password is Incorrect", code=400)

    privateKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                          string=user.privateKey)

    updateAnsibleFiles = "ansiblePlaybooks/updateProcessing"

    ansiblePath = os.path.join(platform.dir, "ansible", "updatePlatform")

    if os.path.exists(ansiblePath):
        shutil.rmtree(ansiblePath)

    shutil.copytree(updateAnsibleFiles, ansiblePath)

    script.save(os.path.join(ansiblePath, "roles", "dmacklin.updateProcessing", "templates", "dataProcessing.py"))

    ab.generateRequirementsFile(packages, ansiblePath, "dmacklin.updateProcessing")

    output, error = ab.runPlaybook(platform.ipAddress, privateKey, ansiblePath, "updateProcessing")

    print(output)
    print(error)

    return Response.make_success_resp(msg="Script updated")

"""
Endpoint to update the data processing script in a platform
takes in:
uid
password
platform id
"""
@platform_crud.route('/platforms/database/dump/<id>', methods=['Post'])
@jwt_required
def databaseDump(id):

    data = request.json
    try:
        platform = Platforms.get(Platforms.id == id)
    except Platforms.DoesNotExist:
        return Response.make_error_resp(msg="Platform Not Found", code=400)

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

    database = platform.database
    privateKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                          string=user.privateKey)

    dumpAnsibleFiles = "ansiblePlaybooks/dataBaseDump"

    ansiblePath = os.path.join(platform.dir, "ansible", "dataBaseDump")

    if os.path.exists(ansiblePath):
        shutil.rmtree(ansiblePath)

    shutil.copytree(dumpAnsibleFiles, ansiblePath)

    ab.updateDBDumpVars(database, ansiblePath)

    output, error = ab.runPlaybook(platform.ipAddress, privateKey, ansiblePath, "dbDump")

    print(output)
    print(error)

    filename = ""
    dumpPath = ""
    if database == "influxdb":
        filename = "influxdump.zip"
        dumpPath = os.path.join(ansiblePath, filename)
    elif database == "mongodb":
        filename =  "mongodump.zip"
        dumpPath = os.path.join(ansiblePath, filename)

    try:
        return send_file(dumpPath,attachment_filename=filename, as_attachment=True, mimetype="application/zip")
    except Exception as e:
        print(e)
        return Response.make_error_resp("Error Getting Dump", code=400)

@platform_crud.route('/platforms/dataProcessingFile', methods=['Get'])
@jwt_required
def dataProcessingFile():
    path = "app/downloads/dataProcessing.py"

    try:
        return send_file(path, attachment_filename="dataProcessing.py", as_attachment=True)
    except Exception as e:
        print(e)
        return Response.make_error_resp("Error Getting File", code=400)

#==============Helper Functions==============#

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

def checkPackages(packages):

    for package in packages:
        response = requests.get("https://pypi.python.org/pypi/{}/json".format(package))
        if response.status_code != 200:
            return package

    return ""

def awsGenVars(user, password, space, dbsize, safePlatformName, platformPath):
    print(dbsize)

    # Get the aws creds object
    try:
        creds = AWSCreds.get((AWSCreds.id == space.cid) & (AWSCreds.uid == user.uid))
    except AWSCreds.DoesNotExist:
        return "Error Finding Creds"

    # Decrypt the user data
    secretKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                         string=creds.secretKey)
    accessKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                         string=creds.accessKey)

    return tf.generateAWSPlatformVars(space.keyPairId, space.securityGroupId, space.subnetId, secretKey,
                                         accessKey, dbsize, safePlatformName, platformPath)


def osGenVars(user, password, space, flavorName, imageName, dbsize, safePlatformName, platformPath):
    print(dbsize)

    try:
        creds = OSCreds.get((OSCreds.id == space.cid) & (OSCreds.uid == user.uid))
    except OSCreds.DoesNotExist:
        return "Error Finding Creds"

    osUsername = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=creds.username)
    osPassword = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=creds.password)
    authUrl = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=creds.authUrl)
    publicKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,string=user.publicKey)

    return tf.generateOSPlatformVars(osUsername, osPassword, space.tenantName, authUrl, space.availabilityZone,
                                     flavorName, imageName, safePlatformName, space.ipPool, space.securityGroup,
                                     space.intNetwork, publicKey, dbsize, platformPath)


def gcpGenVars(user, password, creds, zone, dbsize, platformName, platformPath):
    print(dbsize)

    publicKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,string=user.publicKey)
    account = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,string=creds.account)

    return tf.generateGCPPlatformVars(publicKey, account, platformName, creds.platform, zone, dbsize, platformPath)


