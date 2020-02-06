from flask import Blueprint, request
from flask_jwt import JWT
from passlib.hash import pbkdf2_sha256
import response as Response
import encryption as encryption
from app.config import URL_PREFIX
from .models.userModel import *
from .models.spaceModel import *
from .models.credentialsModel import *
import os

users = Blueprint('users', __name__, url_prefix=URL_PREFIX)


@users.route('users/create', methods=["Post"])
def createUser():
    db.connect()
    db.create_tables([User, SpaceAWS, AWSCreds, OpenstackCreds])

    data = request.json
    print(data)

    if 'userName' in data:
        userName = data["userName"]
    else:
        return Response.make_error_resp(msg="Username is required", code=400)

    if 'email' in data:
        email = data["email"]
    else:
        return Response.make_error_resp(msg="Email is required", code=400)

    if 'password' in data:
        passSalt = os.urandom(16)
        password = pbkdf2_sha256.hash(data["password"], salt=passSalt)
        keySalt = os.urandom(16)
        resKey = encryption.generateResKey(password, keySalt)
    else:
        return Response.make_error_resp(msg="Password is required", code=400)

    try:
        User.create(userName=userName, email=email, password=password, passSalt=passSalt,
                    resKey=resKey, keySalt=keySalt, uid=str(uuid.uuid4()))

    except IntegrityError as e:
        print(e)
        return Response.make_error_resp(msg="Email or Username already in use", code=400)

    except OperationalError as e:
        print(e)
        return Response.make_error_resp(msg="Error creating user")

    user = User.get(User.email == email)
    print(user)
    if user is None:
        return Response.make_error_resp("Error Finding user")
    res = {
        'userName': user.userName,
        'email': user.email,
        'uid': user.uid,
    }
    return Response.make_json_response(res)


@users.route('users/login', methods=['Get'])
def login():
    data = request.json

    if 'email' in data:
        email = data["email"]
    else:
        return Response.make_error_resp(msg="Email is required", code=400)

    if 'password' in data:
        password = data["password"]
    else:
        return Response.make_error_resp(msg="Password is required", code=400)

    try:
        user = User.get(User.email == email)
    except:
        return Response.make_error_resp(msg="No User with that email", code=400)
    finally:
        if pbkdf2_sha256.verify(password, user.password):
            res = {
                'success': True,
                'username': user.userName,
                'email': user.email,
                'uid': user.uid,
            }
            return Response.make_json_response(res)
        else:
            return Response.make_error_resp(msg="Password Incorrect", code=400)

