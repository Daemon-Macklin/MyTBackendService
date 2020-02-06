from flask import Blueprint, request
from passlib.hash import pbkdf2_sha256
from app.config import URL_PREFIX
import response as Response
import encryption
from .models.credentialsModel import *

credentials = Blueprint('credentials', __name__, url_prefix=URL_PREFIX)

"""
Route to create a new aws credentials
Takes in:
name
access key
secret key
password
User id
"""
@credentials.route('credentials/create/aws', methods=["Post"])
def createCredentials():
    data = request.json

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

    user = User.get(User.uid == uid)
    if user is None:
        return Response.make_error_resp(msg="No User found", code=404)
    elif pbkdf2_sha256.verify(password, user.password):

        accessKey = encryption.encryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=accessKey)
        secretKey = encryption.encryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=secretKey)
        try:
            newCredentials = AWSCreds.create(name=name, accessKey=accessKey, secretKey=secretKey, uid=uid,
                                             id=str(uuid.uuid4()))
        except Exception as e:
            print(e)
            return Response.make_error_resp("Error Creating Creds")

        creds = AWSCreds.get(AWSCreds.id == newCredentials.id)
        if creds is None:
            return Response.make_error_resp("Error Creating Creds")
        res = {
            'name': creds.name,
            'id': creds.id
        }
        return Response.make_json_response(res)

    else:
        return Response.make_error_resp(msg="Password is not correct", code=400)
