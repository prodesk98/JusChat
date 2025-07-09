import socketio
from loguru import logger
from fastapi import FastAPI


def handle_connect(sid, environ):
    logger.info(f"Socket connected with sid {sid}")

class SocketManager:
    def __init__(self, origins: list[str] = None):
        if origins is None: origins = []
        self.server = socketio.AsyncServer(
            cors_allowed_origins=origins,
            async_mode="asgi",
        )
        self.app = socketio.ASGIApp(self.server)

    @property
    def on(self):
        return self.server.on

    @property
    def send(self):
        return self.server.send

    @property
    def emit(self):
        return self.server.emit

    def mount_to(self, path: str, app: FastAPI):
        app.mount(path, self.app)