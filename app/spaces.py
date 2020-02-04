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
Private Key
"""
@spaces.route('spaces/create', methods=["Post"])
def createSpace():

    data = request.json

    if