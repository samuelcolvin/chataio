from pathlib import Path

import asyncpg
from aiohttp import web

from .settings import Settings
from .views import index, websocket

THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent


async def startup(app: web.Application):
    app['pg'] = await asyncpg.create_pool(dsn=app['settings'].db_dsn)


async def cleanup(app: web.Application):
    await app['pg'].close()


def setup_routes(app):
    app.router.add_get('/', index, name='index')
    app.router.add_get('/ws', websocket, name='websocket')
    app.router.add_static(app['static_root_url'], path=BASE_DIR / 'static')


def create_app(loop=None):
    app = web.Application()
    settings = Settings()
    app.update(
        settings=settings,
        static_root_url='/static',
    )

    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)

    setup_routes(app)
    return app
