from peewee import *
from .userModel import User
import uuid

db = SqliteDatabase('MyTDatabase.db')


class BaseModel(Model):
    class Meta:
        database = db


class AWSCreds(BaseModel):
    name = CharField()
    accessKey = CharField(max_length=20)
    secretKey = CharField(max_length=40)
    uid = ForeignKeyField(model=User)
    id = UUIDField(unique=True, primary_key=True, default=str(uuid.uuid4()))


class OpenstackCreds(BaseModel):
    name = CharField()
    username: CharField()
    password: CharField()
    authUrl: CharField()
    key_pair: CharField()
    tenantName: CharField()
    uid = ForeignKeyField(model=User)
    id = UUIDField(unique=True, primary_key=True, default=str(uuid.uuid4()))
