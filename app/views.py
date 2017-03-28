import json
from functools import partial

from aiohttp import WSMsgType
from aiohttp.web import Response, WebSocketResponse


BASE_PAGE = """\
<title>{title}</title>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="{styles_css_url}" rel="stylesheet">
</head>
<body>
<main>
  <h1>{title}</h1>
  <div id="status">Initialising...</div>
  <div id="events"></div>
  
  <form>
    <input type="text" id="username" required placeholder="username">
    <input type="text" id="message" required placeholder="send message">
    <button type="submit">Send</button>
  </form>
</main>
<script src="{main_js_url}"></script>
</body>"""


async def index(request):
    ctx = dict(
        title='Chat Test',
        styles_css_url='{static_root_url}/styles.css'.format(**request.app),
        main_js_url='{static_root_url}/main.js'.format(**request.app),
    )
    return Response(text=BASE_PAGE.format(**ctx), content_type='text/html')


def send_event(ws, conn, pid, channel, payload):
    ws.send_str(payload)


async def websocket(request):
    ws = WebSocketResponse()
    await ws.prepare(request)
    send_event_ = partial(send_event, ws)

    async with request.app['pg'].acquire() as conn:
        await conn.add_listener('events', send_event_)
        messages = await conn.fetch('SELECT row_to_json(messages) as v FROM messages ORDER BY ts DESC LIMIT 10')
        for msg in reversed(messages):
            ws.send_str(msg[0])

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)
                args = data['action'], data['username'], data.get('message')
                await conn.execute('INSERT INTO messages (action, username, message) VALUES ($1, $2, $3)', *args)
            elif msg.type == WSMsgType.ERROR:
                print(f'ws connection closed with exception {ws.exception()}')

    print('websocket connection closed')
    return ws
