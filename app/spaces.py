from flask import Blueprint, request
import response as Response
import terraform as tf
from app.config import URL_PREFIX
from shutil import copyfile
import os
import time
from .models.userModel import User
from .models.spaceModel import SpaceAWS
from .models.credentialsModel import AWSCreds
from passlib.hash import pbkdf2_sha256
import encryption

spaces = Blueprint('spaces', __name__, url_prefix=URL_PREFIX)

"""
Route to create a new space
Takes in:
User id
creds id
user password
cloud service
platform name
"""
@spaces.route('spaces/create', methods=["Post"])
def createSpace():
    data = request.json

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

    if 'cloudService' in data:
        validPlatforms = ["aws", "openstack"]
        cloudService = data['cloudService']
        if cloudService not in validPlatforms:
            return Response.make_error_resp(msg="invalid cloudService", code=400)
    else:
        return Response.make_error_resp(msg="Cloud Service Choice is required", code=400)

    if 'spaceName' in data:
        spaceName = data['spaceName']
    else:
        return Response.make_error_resp(msg="Name of space required", code=400)

    safeSpaceName = spaceName.replace('/', '_')
    safeSpaceName = safeSpaceName.replace(' ', '_')

    spacePath = os.path.join("spaces", safeSpaceName)

    try:
        os.makedirs(spacePath)
    except FileExistsError as e:
        print(e)
        return Response.make_error_resp(msg="Space Name already used", code=400)
    except Exception as e:
        print(e)
        return Response.make_error_resp(msg="Error Creating Space Directory", code=400)


    user = User.get(User.uid == uid)
    if pbkdf2_sha256.verify(password, user.password):

        tfPath = "terraformScripts/createSpace/aws"
        requiredFiles = ["deploy.tf", "provider.tf"]

        for file in requiredFiles:
            copyfile(tfPath + "/" + file, spacePath + "/" + file)

        if cloudService == 'aws':

            try:
                creds = AWSCreds.get((AWSCreds.id == cid) & (AWSCreds.uid == uid))
            except AWSCreds.DoesNotExist:
                return Response.make_error_resp(msg="Error Finding Creds", code=400)

            secretKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=creds.secretKey)
            accessKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=creds.accessKey)
            publicKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=user.publicKey)
            varPath = tf.generateAWSSpaceVars(secretKey, accessKey, publicKey, safeSpaceName, spacePath)


        elif cloudService == 'openstack':
            return Response.make_success_resp("Spaces are not required for openstack")

        initResultCode = tf.init(spacePath)

        output, createResultCode = tf.create(spacePath)

        if createResultCode != 0:
            # Add destroy function here
            return Response.make_error_resp(msg="Error Creating Infrastructure", code=400)

        keyPairId = output["key_pair"]["value"]
        securityGroupId = output["security_group"]["value"]
        subnetId = output["subnet"]["value"]

        newSpace = SpaceAWS.create(dir=spacePath, keyPairId=keyPairId, securityGroupId=securityGroupId, subnetId=subnetId, uid=uid, cid=cid)
        try:
            newSpace = SpaceAWS.get(SpaceAWS.id == newSpace.id)
        except AWSCreds.DoesNotExist as e:
            print(e)
            return Response.make_error_resp(msg="Error Finding Creds", code=400)

        res = {
            "id" : newSpace.id,
            "keyPair" : newSpace.keyPairId,
            "SG" : newSpace.securityGroupId,
            "subnet" : newSpace.subnetId
        }
        return Response.make_json_response(res)

    else:
        return Response.make_error_resp(msg="Password is incorrect")