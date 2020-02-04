from peewee import *
from .userModel import User
import uuid

db = SqliteDatabase('MyTDatabase.db')


class BaseModel(Model):
    class Meta:
        database = db


class SpaceAWS(BaseModel):
    private_key = TextField()
    key_pair_id = CharField()
    security_group_id = CharField()
    gateway_id = CharField()
    uid = ForeignKeyField(model=User)
    id = UUIDField(unique=True, primary_key=True, default=str(uuid.uuid4()))
