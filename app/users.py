from flask import Blueprint, request
from flask_jwt import JWT
from passlib.hash import pbkdf2_sha256
import response as Response
from app.config import URL_PREFIX
from .models.userModel import *
from .models.spaceModel import *

users = Blueprint('users', __name__, url_prefix=URL_PREFIX)


@users.route('users/create', methods=["Post"])
def createUser():
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
        password = pbkdf2_sha256.hash(data["password"])
    else:
        return Response.make_error_resp(msg="Password is required", code=400)

    db.connect()
    db.create_tables([User, SpaceAWS])

    newUser = User.create(userName=userName, email=email, password=password)

    try:
        newUser.save()
    except:
        return Response.make_error_resp(msg="Error creating user", code=400)
    finally:
        return Response.make_success_resp("User Created")


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
        print(user.password)
        print(password)
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
