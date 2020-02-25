from peewee import *
from .userModel import Users
from .credentialsModel import AWSCreds
import uuid

db = SqliteDatabase('MyTDatabase.db')


class BaseModel(Model):
    class Meta:
        database = db


class Platforms(BaseModel):
    dir = CharField()
    name = CharField()
    uid = ForeignKeyField(model=Users)
    sid = CharField()
    cloudService = CharField()
    ipAddress = CharField()
    packageList = BlobField()
    id = UUIDField(unique=True, primary_key=True)