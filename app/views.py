import asyncio
import json
import logging
from functools import partial

from aiohttp import WSMsgType
from aiohttp.web import Response, WebSocketResponse

logger = logging.getLogger('chataio')
hdlr = logging.StreamHandler()
hdlr.setLevel(logging.INFO)
logger.setLevel(logging.INFO)
logger.addHandler(hdlr)


BASE_PAGE = """\
<title>{title}</title>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="{styles_css_url}" rel="stylesheet">
</head>
<body data-ws-url="{ws_url}">
<main>
  <h1>{title}</h1>
  <div id="status">Initialising...</div>
  <div>
    Username: <span id="username">-</span>
  </div>
  <div>
    Users Connected: <span id="users">-</span>
  </div>
  <div id="events"></div>
  
  <button type="button" id="connect">Connect</button>
  <button type="button" id="disconnect">Disconnect</button>
  <form>
    <input type="text" id="message" required placeholder="send message">
    <button type="submit">Send</button>
  </form>
</main>
<script src="{main_js_url}"></script>
</body>"""


async def index(request):
    secure = 'https' in (request.scheme, request.headers.get('X-Forwarded-Proto'))
    ws_scheme = 'wss' if secure else 'ws'
    ctx = dict(
        title='Chat Test',
        styles_css_url='{static_root_url}/styles.css'.format(**request.app),
        main_js_url='{static_root_url}/main.js'.format(**request.app),
        ws_url=f'{ws_scheme}://{request.host}/ws'
    )
    return Response(text=BASE_PAGE.format(**ctx), content_type='text/html')


def send_event(ws, conn, pid, channel, payload):
    if not ws.closed:
        ws.send_str(payload)


async def disconnect_user(app, user):
    async with app['pg'].acquire() as conn:
        await conn.execute('UPDATE users SET connected = FALSE WHERE name = $1;', user)


async def websocket(request):
    ws = WebSocketResponse()
    await ws.prepare(request)
    send_event_ = partial(send_event, ws)
    user = None

    async with request.app['pg'].acquire() as conn:
        await conn.add_listener('events', send_event_)
        messages = await conn.fetch('SELECT row_to_json(messages) as v FROM messages ORDER BY ts DESC LIMIT 10')
        for msg in reversed(messages):
            ws.send_str(msg[0])

        while True:
            try:
                msg = await ws.receive(timeout=10)
            except asyncio.TimeoutError:
                if not ws.closed:
                    ws.ping()
            else:
                if msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSING, WSMsgType.CLOSED):
                    break
                elif msg.type == WSMsgType.ERROR:
                    logger.warning('ws connection closed with exception %s', ws.exception())
                    break
                assert msg.type == WSMsgType.TEXT, msg.type
                data = json.loads(msg.data)
                action = data['action']
                if action == 'message' and user:
                    args = user, data.get('message')
                    await conn.execute('INSERT INTO messages (username, message) VALUES ($1, $2)', *args)
                elif action == 'connected':
                    user = data['username']
                    await conn.execute('INSERT INTO users (name) VALUES ($1) '
                                       'ON CONFLICT (name) DO UPDATE SET connected=TRUE', user)
        if user:
            # this has to use create_task as a cancel error will otherwise kill the db query
            request.app.loop.create_task(disconnect_user(request.app, user))

    return ws
