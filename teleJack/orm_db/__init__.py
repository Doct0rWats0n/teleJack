from .base_control import Controller
from .data import *

BASE_PATH = 'teleJack/orm_db/db/user_base.sqlite'  # Путь до игровой базы данных
global_init(BASE_PATH)
base = Controller()
