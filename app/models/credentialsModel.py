from peewee import *
from .userModel import Users
import uuid

db = SqliteDatabase('MyTDatabase.db')


class BaseModel(Model):
    class Meta:
        database = db


class AWSCreds(BaseModel):
    name = CharField()
    accessKey = CharField(max_length=20)
    secretKey = CharField(max_length=40)
    uid = ForeignKeyField(model=Users)
    id = UUIDField(unique=True, primary_key=True)


class OpenstackCreds(BaseModel):
    name = CharField()
    username = CharField()
    password = CharField()
    authUrl = CharField()
    uid = ForeignKeyField(model=Users)
    id = UUIDField(unique=True, primary_key=True)

class GCPCreds(BaseModel):
    name = CharField()
    account = BlobField()
    uid = ForeignKeyField(model=Users)
    id = UUIDField(unique=True, primary_key=True)
