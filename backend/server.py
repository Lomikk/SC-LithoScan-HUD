import asyncio
import json
import logging
import websockets

logger = logging.getLogger("lithoscan-hud")

class WebSocketServer:
    def __init__(self, controller, host="localhost", port=8765):
        self.controller = controller
        self.host = host
        self.port = port
        self.clients = set()
        
        # Пробрасываем ссылку на сервер в контроллер, чтобы он мог отправлять данные
        self.controller.set_server(self)

    async def register_client(self, websocket):
        self.clients.add(websocket)
        logger.info("[WS] Frontend подключился")
        try:
            await self.controller.on_client_connected()
            async for message in websocket:
                data = json.loads(message)
                await self.controller.handle_frontend_message(data)
        except websockets.exceptions.ConnectionClosed:
            logger.info("[WS] Frontend отключился")
        finally:
            self.clients.remove(websocket)

    async def broadcast(self, payload: dict):
        """Отправка JSON всем подключенным клиентам"""
        if self.clients:
            msg = json.dumps(payload)
            await asyncio.gather(*(client.send(msg) for client in self.clients))

    async def start(self):
        logger.info(f"[WS] Запуск WebSocket сервера на {self.host}:{self.port}")
        async with websockets.serve(self.register_client, self.host, self.port):
            await asyncio.Future()