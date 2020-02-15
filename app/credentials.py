from flask import Blueprint, request
from passlib.hash import pbkdf2_sha256
from app.config import URL_PREFIX
import response as Response
import encryption
from .models.credentialsModel import *
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
    except User.DoesNotExist:
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
