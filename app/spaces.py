from flask import Blueprint, request
import response as Response
import terraform as tf
from app.config import URL_PREFIX
from shutil import copyfile
import os
import time
from .models.userModel import User
from .models.spaceModel import SpaceAWS

spaces = Blueprint('spaces', __name__, url_prefix=URL_PREFIX)

"""
Route to create a new space
Takes in:
User id
creds id
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
        return Response.make_error_resp(msg="Credential id is required")

    user = User.get(User.uid == uid)
    print(user)
    return "Whoops this function is not complete"
