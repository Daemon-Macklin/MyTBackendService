from flask import Blueprint, request
import response as Response
import terraform as tf
from app.config import URL_PREFIX
from shutil import copyfile
import os
import time
from .models.userModel import Users
from .models.spaceModel import *
from .models.credentialsModel import *
from .models.platformModel import Platforms
from passlib.hash import pbkdf2_sha256
import encryption
import uuid
import shutil
from flask_jwt_extended import jwt_required


spaces = Blueprint('spaces', __name__, url_prefix=URL_PREFIX)

"""
Route to create a new space
Takes in:
User id
creds id
user password
space name
Returns:
id
availability_zone
keypair id
subnet id
security group id
"""
@spaces.route('spaces/create/aws', methods=["Post"])
@jwt_required
def createAWSSpace():

    data = request.json

    # Verify required fields
    if 'uid' in data:
        uid = data['uid']
    else:
        return Response.make_error_resp(msg="User id is required", code=400)

    if 'cid' in data:
        cid = data['cid']
    else:
        return Response.make_error_resp(msg="Credential id is required", code=400)

    if 'password' in data:
        password = data['password']
    else:
        return Response.make_error_resp(msg="Password  is required", code=400)

    #if 'cloudService' in data:
    #    validPlatforms = ["aws", "openstack"]
    #    cloudService = data['cloudService']
    #    if cloudService not in validPlatforms:
    #        return Response.make_error_resp(msg="invalid cloudService", code=400)
    #else:
    #    return Response.make_error_resp(msg="Cloud Service Choice is required", code=400)

    if 'spaceName' in data:
        spaceName = data['spaceName'] + tf.genComponentID()
    else:
        return Response.make_error_resp(msg="Name of space required", code=400)

    if 'availability_zone' in data:
        availability_zone = data["availability_zone"]
    else:
        return Response.make_error_resp(msg="Availability Zone is required", code=400)

    # Get rid of unsafe characters in the name
    safeSpaceName = spaceName.replace('/', '_')
    safeSpaceName = safeSpaceName.replace(' ', '_')

    # Create a safe path
    spacePath = os.path.join("spaces", safeSpaceName)

    # Get the users data
    try:
        user = Users.get(Users.uid == uid)
    except Users.DoesNotExist:
        return Response.make_error_resp(msg="User does not exist", code=404)

    # Create a new directory for the space
    try:
        os.makedirs(spacePath)
    except FileExistsError as e:
        print(e)
        return Response.make_error_resp(msg="Space Name already used", code=400)
    except Exception as e:
        print(e)
        return Response.make_error_resp(msg="Error Creating Space Directory", code=400)


    # Verify the users password
    if pbkdf2_sha256.verify(password, user.password):

        tfPath = "terraformScripts/createSpace/aws"
        requiredFiles = ["deploy.tf", "provider.tf"]

        # Get the files from the source code directory
        for file in requiredFiles:
            copyfile(tfPath + "/" + file, spacePath + "/" + file)

        # Get the aws creds object
        try:
            creds = AWSCreds.get((AWSCreds.id == cid) & (AWSCreds.uid == uid))
        except AWSCreds.DoesNotExist:
            return Response.make_error_resp(msg="Error Finding Creds", code=404)

        # Decrypt the user data
        secretKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=creds.secretKey)
        accessKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=creds.accessKey)
        publicKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=user.publicKey)

        # Generate the variables file
        varPath = tf.generateAWSSpaceVars(secretKey, accessKey, publicKey, availability_zone, safeSpaceName, spacePath)

        # Init the terraform directory
        initResultCode = tf.init(spacePath)

        print(initResultCode)

        # Run the terrafom script
        output, createResultCode = tf.create(spacePath)

        # Check the result code for errors
        if createResultCode != 0:
            # Add destroy function here
            print("Removing Inf")
            tf.destroy(spacePath)
            shutil.rmtree(spacePath)
            return Response.make_error_resp(msg="Error Creating Infrastructure", code=400)

        # Remove the vars file
        os.remove(varPath)

        # Get data from the terraform outputs
        keyPairId = output["key_pair"]["value"]
        securityGroupId = output["security_group"]["value"]
        subnetId = output["subnet"]["value"]

        # Create the space object
        newSpace = SpaceAWS.create(dir=spacePath, keyPairId=keyPairId, securityGroupId=securityGroupId,
                                   name=safeSpaceName, subnetId=subnetId, uid=uid, availabilityZone=availability_zone,
                                   cid=cid, id=str(uuid.uuid4()))

        # Get the new space object
        try:
            newSpace = SpaceAWS.get(SpaceAWS.id == newSpace.id)
        except AWSCreds.DoesNotExist as e:
            return Response.make_error_resp(msg="Error Finding Creds", code=404)

        # Return the space data
        res = {
            "id" : newSpace.id,
            "name" : newSpace.name
        }
        return Response.make_json_response(res)

    else:
        return Response.make_error_resp(msg="Password is incorrect")

"""
Takes in:
name
tenant network
availability zone
ip pool
intenral network
creds id
security Group
uid 
password
"""
@spaces.route('spaces/create/os', methods=["Post"])
@jwt_required
def createOSSpace():

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

    if "cid" in data:
        cid = data["cid"]
    else:
        return Response.make_error_resp(msg="Creds id is required", code=400)

    if "tenantName" in data:
        tenantName = data["tenantName"]
    else:
        return Response.make_error_resp(msg="Tenant Name is required", code=400)

    if "availabilityZone" in data:
        availabilityZone = data["availabilityZone"]
    else:
        return Response.make_error_resp(msg="Availability Zone is required", code=400)

    if "ipPool" in data:
        ipPool = data["ipPool"]
    else:
        return Response.make_error_resp(msg="Ip Pool is required", code=400)

    if "securityGroup" in data:
        securityGroup = data["securityGroup"]
    else:
        return Response.make_error_resp(msg="Security Group is required", code=400)

    if "intNetwork" in data:
        intNetwork = data["intNetwork"]
    else:
        return Response.make_error_resp(msg="intNetwork is required", code=400)

    if "name" in data:
        name = data["name"]
    else:
        return Response.make_error_resp(msg="Name is required", code=400)

    if pbkdf2_sha256.verify(password, user.password):

        # Get the aws creds object
        try:
            creds = OSCreds.get((OSCreds.id == cid) & (OSCreds.uid == uid))
        except OSCreds.DoesNotExist:
            return Response.make_error_resp(msg="Error Finding Creds", code=404)

        newSpace = SpaceOS.create(name=name, tenantName=tenantName, availabilityZone=availabilityZone, ipPool=ipPool, securityGroup=securityGroup, intNetwork=intNetwork, uid=uid, cid=cid, id=str(uuid.uuid4()))

        # Get the new space object
        try:
            newSpace = SpaceOS.get(SpaceOS.id == newSpace.id)
        except AWSCreds.DoesNotExist as e:
            return Response.make_error_resp(msg="Error Finding new Space", code=404)

        # Return the space data
        res = {
            "id" : newSpace.id,
            "name" : newSpace.name
        }
        return Response.make_json_response(res)

    else:
        return Response.make_error_resp(msg="Password is incorrect")


"""
Route that will delete a platform
Takes in
User id
password
space id
"""
@spaces.route('/space/remove/aws/<id>', methods=['Post'])
@jwt_required
def removeAWSSpace(id):

    try:
        space = SpaceAWS.get(SpaceAWS.id == id)
    except SpaceAWS.DoesNotExist:
        return Response.make_error_resp(msg="Space Not Found", code=400)

    platforms = Platforms.select().where(Platforms.sid == space.id)
    if len(platforms) != 0:
        return Response.make_error_resp(msg="Please remove all platforms in this space before removing space")

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

    creds = AWSCreds.get(AWSCreds.id == space.cid)

    secretKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                         string=creds.secretKey)
    accessKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey,
                                         string=creds.accessKey)

    tf.generateAWSSpaceVars(secretKey, accessKey, "", "", "", space.dir)

    path = space.dir
    resultCode = tf.destroy(space.dir)

    if resultCode != 0:
        return Response.make_error_resp(msg="Error deleting platform")

    space.delete_instance()

    if path != "":
        shutil.rmtree(path)
        return Response.make_success_resp(msg="Space Has been removed")


@spaces.route('/space/remove/os/<id>', methods=['Post'])
@jwt_required
def removeOSSpace(id):

    try:
        space = SpaceOS.get(SpaceOS.id == id)
    except SpaceOS.DoesNotExist:
        return Response.make_error_resp(msg="Space Not Found", code=400)

    platforms = Platforms.select().where(Platforms.sid == space.id)
    if len(platforms) != 0:
        return Response.make_error_resp(msg="Please remove all platforms in this space before removing space")

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

    if pbkdf2_sha256.verify(password, user.password):
        space.delete_instance()
        return Response.make_success_resp("Space Removed")

    else:
        return Response.make_error_resp(msg="Password is Incorrect", code=400)


@spaces.route('/spaces/get/<uid>', methods=['Get'])
@jwt_required
def getSpaces(uid):
    try:
        user = Users.get(Users.uid == uid)
    except Users.DoesNotExist:
        return Response.make_error_resp(msg="No User Found")
    except:
        return Response.make_error_resp(msg="Error reading database", code=500)

    response = []
    awsQuery = SpaceAWS.select(SpaceAWS.name, SpaceAWS.id).where(SpaceAWS.uid == user.uid)
    for space in awsQuery:
        awsSpace = {
            "name": space.name,
            "id": space.id,
            "type": "AWS"
        }
        response.append(awsSpace)

    osQuery = SpaceOS.select(SpaceOS.name, SpaceOS.id).where(SpaceOS.uid == user.uid)
    for space in osQuery:
        osSpace = {
            "name": space.name,
            "id": space.id,
            "type": "Openstack"
        }
        response.append(osSpace)

    res = {
        "spaces": response
    }
    return Response.make_json_response(res)
