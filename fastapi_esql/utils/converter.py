from logging import getLogger
from typing import Dict, Callable

logger = getLogger(__name__)


def convert_dicts(dicts, converters: Dict[str, Callable]):
    if not converters:
        return
    for d in dicts:
        for f, cvt in converters.items():
            v = d[f]
            try:
                d[f] = cvt(v)
            except Exception as e:
                logger.warning(f"Converting value `{v}` by `{cvt.__name__}` failed => {e}")
