from flask import Blueprint, request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity, get_raw_jwt
from passlib.hash import pbkdf2_sha256
import response as Response
import encryption as encryption
from app.config import URL_PREFIX
from .models.userModel import *
from .models.spaceModel import *
from .models.credentialsModel import *
from .models.platformModel import *
import os
import uuid

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
    db.create_tables([Users, SpaceAWS, AWSCreds, OpenstackCreds, Platforms])

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
        Users.create(userName=userName, email=email, password=password, passSalt=passSalt,
                    resKey=resKey, keySalt=keySalt, privateKey=privateKey, publicKey=publicKey, uid=str(uuid.uuid4()))

    except IntegrityError as e:
        print(e)
        return Response.make_error_resp(msg="Email or Username already in use", code=400)

    except OperationalError as e:
        print(e)
        return Response.make_error_resp(msg="Error creating user")

    try:
        user = Users.get(Users.email == email)
    except Users.DoesNotExist:
        return Response.make_error_resp("Error Finding user")

    # Generate User tokens
    access_token = create_access_token(identity=user.userName)
    refresh_token = create_refresh_token(identity=user.userName)
    res = {
        'success' : True,
        'username': user.userName,
        'email': user.email,
        'uid': user.uid,
        'access_token': access_token,
        'refresh_token': refresh_token
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
@users.route('users/login', methods=['Post'])
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
        user = Users.get(Users.email == email)
    except Users.DoesNotExist:
        return Response.make_error_resp(msg="No User Found")
    except:
        return Response.make_error_resp(msg="Error reading database", code=500)

    # Verify password
    if pbkdf2_sha256.verify(password, user.password):

        # Generate User tokens
        access_token = create_access_token(identity=user.userName)
        refresh_token = create_refresh_token(identity=user.userName)

        # Return data
        res = {
            'success': True,
            'username': user.userName,
            'email': user.email,
            'uid': user.uid,
            'access_token': access_token,
            'refresh_token': refresh_token
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
        user = Users.get(Users.uid == uid)
    except Users.DoesNotExist:
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

"""
Endpoint to remove a user

takes in:
uid
password
"""
@jwt_required
@users.route("/users/remove/<uid>", methods=["Post"])
def removeUser(uid):

    data = request.json

    try:
        user = Users.get(Users.uid == uid)
    except Users.DoesNotExist:
        return Response.make_error_resp(msg="No User Found")
    except:
        return Response.make_error_resp(msg="Error reading database", code=500)

    platforms = Platforms.select().where(Platforms.uid == user.uid)
    awsSpaces = SpaceAWS.select().where(SpaceAWS.uid == user.uid)

    if len(platforms) != 0 or len(awsSpaces) !=0:
        return Response.make_error_resp(msg="Please remove all spaces and platforms before deleting account")

    if 'password' in data:
        password = data["password"]
    else:
        return Response.make_error_resp(msg="Password is required", code=400)

    # Verify password
    if pbkdf2_sha256.verify(password, user.password):

        AWSCreds.delete().where(AWSCreds.uid == user.uid)
        OpenstackCreds.delete().where(OpenstackCreds.uid == user.uid)

        user.delete_instance()
        return Response.make_success_resp("User has been removed")

"""
Route to get the users ssh keys
takes in
uid
password
Returns
public key
private key
"""
@users.route('/users/sshKey/<uid>', methods=["Post"])
@jwt_required
def getSshKey(uid):
    data = request.json

    try:
        user = Users.get(Users.uid == uid)
    except Users.DoesNotExist:
        return Response.make_error_resp(msg="No User Found")
    except:
        return Response.make_error_resp(msg="Error reading database", code=500)

    if 'password' in data:
        password = data["password"]
    else:
        return Response.make_error_resp(msg="Password is required", code=400)

    # Verify password
    if not pbkdf2_sha256.verify(password, user.password):
        return Response.make_error_resp(msg="Password is not correct", code=400)

    # Encrypt the user ssh key
    privateKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=user.privateKey)
    publicKey = encryption.decryptString(password=password, salt=user.keySalt, resKey=user.resKey, string=user.publicKey)

    res = {
        "publicKey": publicKey,
        "privateKey": privateKey
    }

    return Response.make_json_response(res)

"""
Function to refresh a token
"""
@users.route('/refresh', methods=['Get'])
@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    res = {
        'access_token': create_access_token(identity=current_user)
    }
    Response.make_json_response(res)

