from logging.config import dictConfig

from tortoise.converters import escape_string
from tortoise.queryset import Q

from .const import (
    QsParsingError,
    WrongParamsError,
)
from .orm import (
    AppMetaclass,
    BaseManager,
    BaseModel,
)
from .utils import (
    CursorHandler,
    Cases,
    RawSQL,
    SQLizer,
    Singleton,
    convert_dicts,
    timing,
    wrap_backticks,
)

__version__ = "0.0.14"

__all__ = [
    "QsParsingError",
    "WrongParamsError",
    "AppMetaclass",
    "BaseManager",
    "BaseModel",
    "CursorHandler",
    "Cases",
    "Q",
    "RawSQL",
    "SQLizer",
    "Singleton",
    "convert_dicts",
    "escape_string",
    "timing",
    "wrap_backticks",
]

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
