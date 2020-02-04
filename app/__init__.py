from .platforms import platform_crud
from .users import users
from .spaces import spaces
from .credentials import credentials

EXPORT_BLUEPRINTS = [platform_crud, users, spaces, credentials]

