from peewee import *
import uuid

db = SqliteDatabase('MyTDatabase.db')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    email = CharField(unique=True)
    uid = UUIDField(unique=True, primary_key=True, default=str(uuid.uuid4()))