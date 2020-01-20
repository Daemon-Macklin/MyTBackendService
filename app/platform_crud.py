from flask import Blueprint
from app.config import URL_PREFIX

platform_crud = Blueprint('platform_crud', __name__, url_prefix=URL_PREFIX)


@platform_crud.route('platform/create', methods=["Post"])
def createPlatform():
    return "Created"