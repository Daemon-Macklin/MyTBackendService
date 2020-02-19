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
def createCredentials():
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
            "type": "aws"
        }
        response.append(cred)

    res = {
        "creds": response
    }
    return Response.make_json_response(res)


@credentials.route('credentials/remove/<type>/<id>', methods=["DELETE"])
@jwt_required
def removeCreds(type, id):

    if type == "aws":
        cred = AWSCreds.get(AWSCreds.id == id)
        spaces = SpaceAWS.select().where(SpaceAWS.cid == cred.id)
        if len(spaces) != 0:
            return Response.make_error_resp(msg="Please Delete Spaces using these credentials before deleting "
                                                "credentials", code=400)
        else:
            cred.delete_instance()
            return Response.make_success_resp("Credentials have been removed")
