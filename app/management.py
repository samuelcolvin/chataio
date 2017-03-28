import asyncio
import asyncpg

from .settings import Settings
from .models import INIT

DROP_CONNECTIONS = """\
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = $1 AND pid <> pg_backend_pid();
"""


async def _prepare_database(delete_existing: bool) -> bool:
    """
    (Re)create a fresh database and run migrations.

    :param delete_existing: whether or not to drop an existing database if it exists
    :return: whether or not a database has been (re)created
    """
    settings_no_db = Settings(DB_NAME=None)
    settings = Settings()

    conn = await asyncpg.connect(dsn=settings_no_db.db_dsn)
    try:
        already_exists = await conn.fetchval('SELECT EXISTS (SELECT datname FROM pg_catalog.pg_database WHERE '
                                             'datname=$1)', settings.DB_NAME)
        if already_exists:
            if not delete_existing:
                print('database "{}" already exists, skipping'.format(settings.DB_NAME))
                return False
            else:
                await conn.execute(DROP_CONNECTIONS, settings.DB_NAME)
                print('dropping database "{}" as it already exists...'.format(settings.DB_NAME))
                await conn.execute('DROP DATABASE {}'.format(settings.DB_NAME))
        else:
            print('database "{}" does not yet exist'.format(settings.DB_NAME))
        print('creating database "{}"...'.format(settings.DB_NAME))
        await conn.execute('CREATE DATABASE {}'.format(settings.DB_NAME))
    finally:
        await conn.close()

    conn = await asyncpg.connect(dsn=settings.db_dsn)
    try:
        print('creating tables from model definition...')
        await conn.execute(INIT)
    finally:
        await conn.close()


def prepare_database(delete_existing: bool):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_prepare_database(delete_existing))
