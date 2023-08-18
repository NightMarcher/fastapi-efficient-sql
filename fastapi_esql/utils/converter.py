from logging import getLogger
from typing import Dict, Callable

logger = getLogger(__name__)


def convert_dicts(dicts, converters: Dict[str, Callable]):
    if not converters:
        return
    for d in dicts:
        for field, converter in converters.items():
            if field not in d:
                logger.warning(f"Item `{field}` does not exist in dict `{d}`")
                continue

            value = d[field]
            try:
                d[field] = converter(value)
            except Exception as e:
                logger.warning(f"Converting value `{value}` by `{converter.__name__}` failed => {e}")
