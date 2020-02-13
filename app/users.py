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

"""
Route to create new users
Takes in:
Username
email
password

Returns:
username
email
password
"""
@users.route('users/create', methods=["Post"])
def createUser():

    # Create the database tables if they don't already exist.
    db.connect()
    db.create_tables([User, SpaceAWS, AWSCreds, OpenstackCreds])

    data = request.json

    # Verify data
    if 'userName' in data:
        userName = data["userName"]
    else:
        return Response.make_error_resp(msg="Username is required", code=400)

    if 'email' in data:
        email = data["email"]
    else:
        return Response.make_error_resp(msg="Email is required", code=400)

    if 'password' in data:

        # Generate two random salts for the password and the key
        passSalt = os.urandom(16)
        keySalt = os.urandom(16)

        # Hash the password and generate the encryption key
        password = pbkdf2_sha256.hash(data["password"], salt=passSalt)
        resKey = encryption.generateResKey(data["password"], keySalt)
    else:
        return Response.make_error_resp(msg="Password is required", code=400)

    # Generate the user ssh key
    privateKey, publicKey = encryption.generateSSHKey()

    # Encrypt the user ssh key
    privateKey = encryption.encryptString(password=data['password'], salt=keySalt, resKey=resKey, string=privateKey)
    publicKey = encryption.encryptString(password=data['password'], salt=keySalt, resKey=resKey, string=publicKey)

    # Create the user
    try:
        User.create(userName=userName, email=email, password=password, passSalt=passSalt,
                    resKey=resKey, keySalt=keySalt, privateKey=privateKey, publicKey=publicKey, uid=str(uuid.uuid4()))

    except IntegrityError as e:
        print(e)
        return Response.make_error_resp(msg="Email or Username already in use", code=400)

    except OperationalError as e:
        print(e)
        return Response.make_error_resp(msg="Error creating user")

    try:
        user = User.get(User.email == email)
    except User.DoesNotExist:
        return Response.make_error_resp("Error Finding user")

    res = {
        'userName': user.userName,
        'email': user.email,
        'uid': user.uid,
    }
    return Response.make_json_response(res)

"""
Function to login a user

Takes in
email
password

Returns:
Username
Email
Uid
"""
@users.route('users/login', methods=['Get'])
def login():
    data = request.json

    # Verify data
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
    except User.DoesNotExist:
        return Response.make_error_resp(msg="No User Found")
    except:
        return Response.make_error_resp(msg="Error reading database", code=500)

    # Verify password
    if pbkdf2_sha256.verify(password, user.password):

        # Return data
        res = {
            'success': True,
            'username': user.userName,
            'email': user.email,
            'uid': user.uid,
        }
        return Response.make_json_response(res)
    else:
        return Response.make_error_resp(msg="Password Incorrect", code=400)

"""
Route to update user data
Takes in:
uid
password
new username
new password

Returns
Updated user object
"""
@users.route('users/update', methods=['Post'])
def updateUser():

    data = request.json

    # Verify data
    if 'uid' in data:
        uid = data["uid"]
    else:
        return Response.make_error_resp(msg="UID is required", code=400)

    try:
        user = User.get(User.uid == uid)
    except User.DoesNotExist:
        return Response.make_error_resp(msg="No User Found")
    except:
        return Response.make_error_resp(msg="Error reading database", code=500)

    if 'password' in data:
        password = data["password"]
    else:
        return Response.make_error_resp(msg="Password is required", code=400)

    # Verify password
    if pbkdf2_sha256.verify(password, user.password):

        if data["newPassword"] is not None:
            pass
        if data["newUserName"] is not None:
            user.userName = data["newUserName"]
            user.save()
        # Return data
        res = {
            'success': True,
            'username': user.userName,
            'email': user.email,
            'uid': user.uid,
        }
        return Response.make_json_response(res)
    else:
        return Response.make_error_resp(msg="Password Incorrect", code=400)