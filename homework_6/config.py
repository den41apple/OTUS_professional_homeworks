"""
Конфигурация переменных
"""
from dotenv import load_dotenv
from envparse import Env

load_dotenv()
env = Env()

SECRET_KEY = env.str("SECRET_KEY", default="django-insecure--+zi3j8y2vs-3^=0$yn=3s+*jr=*lceov#0r$w$oqgab!*j8lt")
DEBUG = env.bool("DEBUG", default=True)

PG_HOST = env.str("PG_HOST", default="localhost")
PG_PORT = env.int("PG_PORT", default=5432)
PG_USER = env.str("PG_USER", default="user")
PG_PASSWORD = env.str("PG_PASSWORD", default="password")
PG_DB_NAME = env.str("PG_DB_NAME", default="hasker")
