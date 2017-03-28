from aiohttp_prodtools.settings import BaseSettings, Required


class Settings(BaseSettings):
    DB_NAME = 'chataio'
    DB_USER = 'postgres'
    DB_PASSWORD = Required(str)
    DB_HOST = 'localhost'
    DB_PORT = '5432'
    COOKIE_SECRET = Required(str)
