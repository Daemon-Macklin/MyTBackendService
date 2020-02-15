from peewee import *
from .userModel import Users
from .credentialsModel import AWSCreds
import uuid

db = SqliteDatabase('MyTDatabase.db')


class BaseModel(Model):
    class Meta:
        database = db


class PlatformModel(BaseModel):
    dir = CharField()
    uid = ForeignKeyField(model=User)
    sid = ForeignKeyField()
    cloudService = CharField()
    ipAddress = CharField()
    id = UUIDField(unique=True, primary_key=True)