import os
from contextlib import asynccontextmanager

import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi_pagination import add_pagination
from environs import Env

from middleware.session import SessionMiddleware
from endpoints import deliveries, admin
from tasks.usd_rate_task import usd_rate_task as urt
from tasks.calculate_delivery_cost_task import calculate_delivery_cost_task as cdct

env = Env()


def read_env_from_path(path: str):
    env.read_env(path=path, recurse=True)


usd_rate_task = None
calculate_delivery_cost_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global usd_rate_task, calculate_delivery_cost_task
    usd_rate_task = asyncio.create_task(urt())
    calculate_delivery_cost_task = asyncio.create_task(cdct())
    yield


app = FastAPI(
    openapi_url='/api/v1/openapi.json',
    docs_url='/api/v1/docs',
    redoc_url='/api/v1/redocs',
    swagger_ui_oauth2_redirect_url='/api/v1/docs/oauth2-redirect',
    lifespan=lifespan
)

app.add_middleware(SessionMiddleware)
add_pagination(app)

app.include_router(deliveries.router)
app.include_router(admin.router)

if __name__ == '__main__':
    read_env_from_path(os.path.join(os.getcwd(), '.env'))
    SERVER_HOST = env.str('SERVER_HOST')
    SERVER_PORT = env.int('SERVER_PORT')
    uvicorn.run('main:app', port=SERVER_PORT, host=SERVER_HOST, reload=True, log_level='info')
