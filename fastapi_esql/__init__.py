from logging.config import dictConfig

from .const.error import QsParsingError, WrongParamsError
from .orm.base_app import AppMetaclass
from .orm.base_manager import BaseManager
from .orm.base_model import BaseModel
from .utils.cursor_handler import CursorHandler
from .utils.decorator import timing
from .utils.sqlizer import RawSQL, SQLizer

__version__ = "0.0.1"

__all__ = [
    "AppMetaclass",
    "BaseManager",
    "BaseModel",
    "CursorHandler",
    "RawSQL",
    "SQLizer",
    "QsParsingError",
    "WrongParamsError",
    "timing",
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
