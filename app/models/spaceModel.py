from peewee import *
from .userModel import User
from .credentialsModel import AWSCreds
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
    uid = ForeignKeyField(model=User)
    cid = ForeignKeyField(model=AWSCreds)
    id = UUIDField(unique=True, primary_key=True, default=str(uuid.uuid4()))
