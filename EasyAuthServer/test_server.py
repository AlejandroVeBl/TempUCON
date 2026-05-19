from fastapi import FastAPI

from easyauth.server import EasyAuthServer

server = FastAPI()

server.auth = EasyAuthServer.create(
    server,
    '/auth/token',
    auth_secret='abcd1234',
    admin_title='EasyAuth - Company',
    admin_prefix='/admin',
    env_from_file='server_env.json'
)
