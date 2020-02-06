from peewee import *
import uuid

db = SqliteDatabase('MyTDatabase.db')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    userName = CharField(unique=True)
    password = CharField()
    passSalt = BlobField()
    email = CharField(unique=True)
    resKey = BlobField()
    keySalt = BlobField()
    uid = UUIDField(unique=True, primary_key=True)
