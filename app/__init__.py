from .platforms import platform_crud
from .users import users
from .spaces import spaces

EXPORT_BLUEPRINTS = [platform_crud, users, spaces]

