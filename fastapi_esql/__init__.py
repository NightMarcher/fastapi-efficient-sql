from logging.config import dictConfig


dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s %(name)s:%(funcName)s:+%(lineno)d %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "fastapi_esql.utils.sqlizer": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "fastapi_esql.orm.base_manager": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    }
})
