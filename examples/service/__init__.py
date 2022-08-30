from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from .routers import api_router

app = FastAPI(
    title="FastAPI Efficient SQL Service Demo",
)


@app.on_event("startup")
async def startup():
    init_db(app)
    app.include_router(api_router, prefix="/api")


def init_db(app: FastAPI):
    """
    CREATE DATABASE demo;
    CREATE USER 'demo_rw'@'localhost' IDENTIFIED BY 'demo_RW#0';
    CREATE USER 'demo_ro'@'localhost' IDENTIFIED BY 'demo_RO#0';
    GRANT ALL ON demo.* TO 'demo_rw'@'localhost';
    GRANT SELECT ON demo.* TO 'demo_ro'@'localhost';
    """
    config = {
        "timezone": "Asia/Shanghai",
        "connections": {
            "demo_rw": {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    "host": "localhost",
                    "port": 3306,
                    "user": "demo_rw",
                    "password": "demo_RW#0",
                    "database": "demo",
                    "pool_recycle": 3600,
                    "maxsize": 10,
                },
            },
            "demo_ro": {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    "host": "localhost",
                    "port": 3306,
                    "user": "demo_ro",
                    "password": "demo_RO#0",
                    "database": "demo",
                    "pool_recycle": 3600,
                    "maxsize": 10,
                },
            },
        },
        "apps": {
        }
    }
    register_tortoise(
        app,
        config=config,
    )
