from flask import Blueprint, request
from passlib.hash import pbkdf2_sha256
from app.config import URL_PREFIX
from flask_jwt_extended import jwt_required
import response as Response
import encryption
from .models.credentialsModel import *
from .models.spaceModel import *
from .models.platformModel import *
import uuid

credentials = Blueprint('credentials', __name__, url_prefix=URL_PREFIX)

"""
Route to create a new aws credentials
Takes in:
name
access key
secret key
password
User id

Returns:
Creds id
Creds name
"""
@credentials.route('credentials/create/aws', methods=["Post"])
@jwt_required
def createAWSCredentials():
    data = request.json

    # Check required fields
    if 'name' in data:
        name = data['name']
    else:
        return Response.make_error_resp("Name is required ", code=400)

    if 'password' in data:
        password = data["password"]
    else:
        return Response.make_error_resp(msg="Password is required", code=400)

    if 'uid' in data:
        uid = data['uid']
    else:
        return Response.make_error_resp("User id is Required")

    if 'accessKey' in data:
        accessKey = data['accessKey']
    else:
        return Response.make_error_resp("Access Key is Required")

    if 'secretKey' in data:
        secretKey = data['secretKey']
    else:
        return Response.make_error_resp("Secret Key is Required")

    # Get the user
    try:
        user = Users.get(Users.uid == uid)
    except Users.DoesNotExist:
        return Response.make_error_resp(msg="User does not exist", code=404)

    # Verify user password
    if pbkdf2_sha256.verify(password, user.password):

        # Encrypt the user data
        accessKey = encryption.encryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=accessKey)
        secretKey = encryption.encryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=secretKey)

        # Create the credentials object
        try:
            newCreds = AWSCreds.create(name=name, accessKey=accessKey, secretKey=secretKey, uid=uid,
                                             id=str(uuid.uuid4()))
        except Exception as e:
            print(e)
            return Response.make_error_resp("Error Creating Creds")

        # Check the creds are there
        try:
            creds = AWSCreds.get(AWSCreds.id == newCreds.id)
        except AWSCreds.DoesNotExist:
            return Response.make_error_resp(msg="Error Finding Creds", code=400)

        # Return the name and id of the creds
        res = {
            'name': creds.name,
            'id': creds.id
        }
        return Response.make_json_response(res)

    else:
        return Response.make_error_resp(msg="Password is not correct", code=400)


"""
Function to create Google Cloud Platform Credentials
Takes in:
account.json file
name
password
os username
os password
authURL
uid
"""
@credentials.route('credentials/create/os', methods=["Post"])
@jwt_required
def createOSCredentials():

    data = request.json
    # Check required fields
    if 'name' in data:
        name = data['name']
    else:
        return Response.make_error_resp("Name is required ", code=400)

    if 'password' in data:
        password = data["password"]
    else:
        return Response.make_error_resp(msg="Password is required", code=400)

    if 'uid' in data:
        uid = data['uid']
    else:
        return Response.make_error_resp("User id is Required")

    if 'osUsername' in data:
        osUsername = data["osUsername"]
    else:
        return Response.make_error_resp("Openstack Username is Required")

    if 'osPassword' in data:
        osPassword = data["osPassword"]
    else:
        return Response.make_error_resp("Openstack Password is Required")

    if 'authUrl' in data:
        authUrl = data["authUrl"]
    else:
        return Response.make_error_resp("authUrl is Required")

    # Get the user
    try:
        user = Users.get(Users.uid == uid)
    except Users.DoesNotExist:
        return Response.make_error_resp(msg="User does not exist", code=404)

    # Verify user password
    if pbkdf2_sha256.verify(password, user.password):

        # Encrypt Data
        osUsername = encryption.encryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=osUsername)
        osPassword = encryption.encryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=osPassword)
        authUrl = encryption.encryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=authUrl)

        # Create the credentials object
        try:
            newCreds = OpenstackCreds.create(name=name, username=osUsername, password=osPassword, authUrl=authUrl, uid=uid,
                                             id=str(uuid.uuid4()))
        except Exception as e:
            print(e)
            return Response.make_error_resp("Error Creating Creds")

        # Check the creds are there
        try:
            creds = OpenstackCreds.get(OpenstackCreds.id == newCreds.id)
        except OpenstackCreds.DoesNotExist:
            return Response.make_error_resp(msg="Error Finding Creds", code=400)

        # Return the name and id of the creds
        res = {
            'name': creds.name,
            'id': creds.id
        }
        return Response.make_json_response(res)

    else:
        return Response.make_error_resp(msg="Password is not correct", code=400)


"""
Function to create Google Cloud Platform Credentials
Takes in:
account.json file
platform
name
password
uid
"""
@credentials.route('credentials/create/gcp', methods=["Post"])
@jwt_required
def createGCPCredentials():
    data = dict(request.form)

    # Check required fields
    if 'account' in request.files:
        account = request.files['account'].read().decode("utf-8")
    else:
        return Response.make_error_resp("Account is required", code=400)

    if 'platform' in data:
        platform = data['platform']
    else:
        return Response.make_error_resp("Platform is required", code=400)

    if 'name' in data:
        name = data['name']
    else:
        return Response.make_error_resp("Name is required", code=400)

    if 'password' in data:
        password = data["password"]
    else:
        return Response.make_error_resp(msg="Password is required", code=400)

    if 'uid' in data:
        uid = data['uid']
    else:
        return Response.make_error_resp("User id is Required")

    try:
        user = Users.get(Users.uid == uid)
    except Users.DoesNotExist:
        return Response.make_error_resp(msg="No User Found")
    except Exception as e:
        return Response.make_error_resp(msg="Error reading database", code=500)

    if pbkdf2_sha256.verify(password, user.password):
        account = encryption.encryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=account)

        try:
            newCreds = GCPCreds.create(name=name, platform=platform, account=account,uid=uid,id=str(uuid.uuid4()))
        except Exception as e:
            print(e)
            return Response.make_error_resp(msg="Error Creating Credentials", code=400)

        # Check the creds are there
        try:
            creds = GCPCreds.get(GCPCreds.id == newCreds.id)
        except OpenstackCreds.DoesNotExist:
            return Response.make_error_resp(msg="Error Finding Creds", code=400)

        # Return the name and id of the creds
        res = {
            'name': creds.name,
            'id': creds.id
        }
        return Response.make_json_response(res)

    else:
        return Response.make_error_resp(msg="Password is not correct", code=400)

"""
Function to get all of the users credentials. 
"""
@credentials.route('credentials/get/<uid>', methods=["Get"])
@jwt_required
def getAllCreds(uid):

    try:
        user = Users.get(Users.uid == uid)
    except Users.DoesNotExist:
        return Response.make_error_resp(msg="No User Found")
    except:
        return Response.make_error_resp(msg="Error reading database", code=500)

    response = []
    awsQuery = AWSCreds.select(AWSCreds.name, AWSCreds.id).where(AWSCreds.uid == user.uid)
    for creds in awsQuery:
        cred = {
            "name": creds.name,
            "id" : creds.id,
            "type": "AWS"
        }
        response.append(cred)

    osQuery = OpenstackCreds.select(OpenstackCreds.name, OpenstackCreds.id).where(OpenstackCreds.uid == user.uid)
    for creds in osQuery:
        cred = {
            "name": creds.name,
            "id" : creds.id,
            "type": "Openstack"
        }
        response.append(cred)

    gcpQuery = GCPCreds.select(GCPCreds.name, GCPCreds.id).where(GCPCreds.uid == user.uid)
    for creds in gcpQuery:
        cred = {
            "name": creds.name,
            "id" : creds.id,
            "type": "GCP"
        }
        response.append(cred)

    res = {
        "creds": response
    }
    return Response.make_json_response(res)


@credentials.route('credentials/remove/<type>/<id>', methods=["DELETE"])
@jwt_required
def removeCreds(type, id):

    if type == "AWS":
        cred = AWSCreds.get(AWSCreds.id == id)
        spaces = SpaceAWS.select().where(SpaceAWS.cid == cred.id)
        if len(spaces) != 0:
            return Response.make_error_resp(msg="Please Delete Spaces using these credentials before deleting "
                                                "credentials", code=400)
        else:
            cred.delete_instance()
            return Response.make_success_resp("Credentials have been removed")

    if type == "Openstack":
        cred = OpenstackCreds.get(OpenstackCreds.id == id)
        spaces = SpaceOS.select().where(SpaceOS.cid == cred.id)
        if len(spaces) != 0:
            return Response.make_error_resp(msg="Please Delete Spaces using these credentials before deleting "
                                                "credentials", code=400)
        else:
            cred.delete_instance()
            return Response.make_success_resp("Credentials have been removed")

    if type == "GCP":
        cred = GCPCreds.get(GCPCreds.id == id)
        platforms = Platforms.select().where(Platforms.cid == cred.id)
        if len(platforms) != 0:
            return Response.make_error_resp(msg="Please Delete Platforms using these credentials before deleting "
                                                "credentials", code=400)
        else:
            cred.delete_instance()
            return Response.make_success_resp("Credentials have been removed")

    else:
        return Response.make_error_resp("Invalid Type", code=400)
