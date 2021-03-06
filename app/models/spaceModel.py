from peewee import *
from .userModel import Users
from .credentialsModel import *
import uuid

db = SqliteDatabase('MyTDatabase.db')


class BaseModel(Model):
    class Meta:
        database = db


class SpaceAWS(BaseModel):
    dir = CharField()
    keyPairId = CharField()
    securityGroupId = CharField()
    subnetId = CharField()
    name = CharField()
    availabilityZone = CharField()
    uid = ForeignKeyField(model=Users)
    cid = ForeignKeyField(model=AWSCreds)
    id = UUIDField(unique=True, primary_key=True)

class SpaceOS(BaseModel):
    name = CharField()
    tenantName = CharField()
    availabilityZone = CharField()
    ipPool = CharField()
    intNetwork = CharField()
    securityGroup = CharField()
    uid = ForeignKeyField(model=Users)
    cid = ForeignKeyField(model=OSCreds)
    id = UUIDField(unique=True, primary_key=True)
