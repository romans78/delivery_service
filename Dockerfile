FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi==0.115.12 \
    uvicorn==0.34.2 \
    sqlalchemy==2.0.41 \
    pydantic==2.11.5 \
    asyncio==3.4.3 \
    environs==14.2.0 \
    alembic==1.16.1 \
    pymysql==1.1.1 \
    aiohttp==3.12.4 \
    aiomysql==0.2.0 \
    cryptography==45.0.3 \
    fastapi-pagination==0.13.1 \
    redis==6.2.0

COPY . .

EXPOSE 8888

CMD ["python", "main.py"]