from flask import Blueprint, request
from app.config import URL_PREFIX
import response as Response
from .models.credentialsModel import *
import peewee

credentials = Blueprint('credentials', __name__, url_prefix=URL_PREFIX)

"""
Route to create a new aws credentials
Takes in:
name
access key
secret key
User id
"""


@credentials.route('credentials/create/aws', methods=["Post"])
def createCredentials():
    data = request.json

    if 'name' in data:
        name = data['name']
    else:
        return Response.make_error_resp("Name is required ", code=400)

    if 'accessKey' in data:
        accessKey = data['accessKey']
    else:
        return Response.make_error_resp("Access Key is Required")

    if 'secretKey' in data:
        secretKey = data['secretKey']
    else:
        return Response.make_error_resp("Secret Key is Required")

    if 'uid' in data:
        uid = data['uid']
    else:
        return Response.make_error_resp("User id is Required")

    creds = None

    try:
        db.connect()
        newCredentials = AWSCreds(name=name, accessKey=accessKey, secretKey=secretKey, uid=uid)
        newCredentials.save(force_insert=True)
        creds = AWSCreds.get(AWSCreds.id == newCredentials.id)
    except Exception as e:
        print(e)
        return Response.make_error_resp("Error Creating Creds")
    finally:
        if creds is None:
            return Response.make_error_resp("Error Creating Creds")
        res = {
            'name': creds.name,
            'id': creds.id
        }
        return Response.make_json_response(res)
