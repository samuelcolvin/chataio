import os
from aiohttp_prodtools.settings import BaseSettings


class Settings(BaseSettings):
    DB_NAME = 'chataio'
    DB_USER = 'postgres'
    DB_PASSWORD = None
    DB_HOST = 'localhost'
    DB_PORT = '5432'
    COOKIE_SECRET = 'paVv-Da51WqaDEqseFuepIKpfl8PifBT1xQmVgbpEQ8='

    @property
    def db_dsn(self):
        return os.getenv('DATABASE_URL', None) or super().db_dsn
