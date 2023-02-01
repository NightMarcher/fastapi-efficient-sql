import asyncio

from tortoise import Tortoise


def init_test_orm():
    """
    CREATE USER 'demo_test'@'localhost' IDENTIFIED BY 'demo_TEST#0';
    GRANT ALL ON demo.* TO 'demo_test'@'localhost';
    """
    config = {
        "timezone": "Asia/Shanghai",
        "connections": {
            "test": {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    "host": "localhost",
                    "port": 3306,
                    "user": "demo_test",
                    "password": "demo_TEST#0",
                    "database": "demo",
                    "pool_recycle": 3600,
                    "maxsize": 10,
                },
            },
        },
        "apps": {
            "demo": {
                "models": ["examples.service.models.demo"],
                "default_connection": "test"
            }
        }
    }
    asyncio.run(Tortoise.init(config=config))


init_test_orm()
