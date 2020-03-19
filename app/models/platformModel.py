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
    cloudService = CharField()
    ipAddress = CharField()
    packageList = TextField()
    database = TextField()
    dbsize = IntegerField(null=True)
    sid = CharField()
    cid = CharField()
    uid = ForeignKeyField(model=Users)
    id = UUIDField(unique=True, primary_key=True)