import uvicorn
from fastapi import FastAPI
from middleware.session import SessionMiddleware
from endpoints import deliveries
from environs import Env
import os

env = Env()


def read_env_from_path(path: str):
    env.read_env(path=path, recurse=True)


app = FastAPI(
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redocs",
    swagger_ui_oauth2_redirect_url="/api/v1/docs/oauth2-redirect",
)

app.add_middleware(SessionMiddleware)


app.include_router(deliveries.router)

if __name__ == "__main__":
    read_env_from_path(os.path.join(os.getcwd(), ".env"))
    SERVER_HOST = env.str("SERVER_HOST")
    SERVER_PORT = env.int("SERVER_PORT")
    uvicorn.run("main:app", port=SERVER_PORT, host=SERVER_HOST, reload=True, log_level="info")
