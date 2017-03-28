import asyncio
import asyncpg

from .settings import Settings
from .models import INIT


async def _prepare_database(delete_existing: bool, create_db: bool) -> bool:
    """
    (Re)create a fresh database and run migrations.

    :param delete_existing: whether or not to drop an existing database if it exists
    :return: whether or not a database has been (re)created
    """
    settings_no_db = Settings(DB_NAME=None)
    settings = Settings()
    if not delete_existing and not create_db:
        raise RuntimeError('calling _prepare_database with delete_existing = False and create_db = False is dangerous')

    if create_db:
        conn = await asyncpg.connect(dsn=settings_no_db.db_dsn)
        try:
            db_exists = await conn.fetchval('SELECT EXISTS (SELECT datname FROM pg_catalog.pg_database WHERE '
                                            'datname=$1)', settings.DB_NAME)
            if db_exists:
                if not delete_existing:
                    print('database "{}" already exists, skipping'.format(settings.DB_NAME))
                    return False
                else:
                    print('database "{}"already exists...'.format(settings.DB_NAME))
            else:
                print('database "{}" does not yet exist'.format(settings.DB_NAME))
                print('creating database "{}"...'.format(settings.DB_NAME))
                await conn.execute('CREATE DATABASE {}'.format(settings.DB_NAME))
        finally:
            await conn.close()

    conn = await asyncpg.connect(dsn=settings.db_dsn)
    try:
        print('dropping and recreating scheme...')
        await conn.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')
        print('creating tables from model definition...')
        await conn.execute(INIT)
    finally:
        await conn.close()


def prepare_database(delete_existing: bool, create_db=True):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_prepare_database(delete_existing, create_db))
