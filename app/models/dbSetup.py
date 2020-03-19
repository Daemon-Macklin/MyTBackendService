from .userModel import *
from .spaceModel import *
from .credentialsModel import *
from .platformModel import *


def init():
    # Create the database tables if they don't already exist.
    db.connect()
    db.create_tables([Users, SpaceAWS, SpaceOS, AWSCreds, OSCreds, GCPCreds, Platforms])