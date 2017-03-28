import base64

from aiohttp import web

import aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import asyncpg

from .settings import Settings
from .views import index, websocket


async def startup(app: web.Application):
    app['pg'] = await asyncpg.create_pool(dsn=app['settings'].db_dsn)


async def cleanup(app: web.Application):
    await app['pg'].close()


def setup_routes(app):
    app.router.add_get('/', index, name='index')
    app.router.add_get('/ws', websocket, name='websocket')


def create_app(loop):
    app = web.Application()
    settings = Settings()
    app.update(
        settings=settings
    )

    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)

    secret_key = base64.urlsafe_b64decode(settings.COOKIE_SECRET)
    aiohttp_session.setup(app, EncryptedCookieStorage(secret_key))

    setup_routes(app)
    return app
