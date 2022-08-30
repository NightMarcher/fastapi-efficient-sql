from enum import Enum, IntEnum


class StrEnum(str, Enum):
    ...


class GenderEnum(IntEnum):
    unknown = 0
    male = 1
    female = 2


class LocaleEnum(StrEnum):
    en_US = "en_US"
    ru_RU = "ru_RU"
    zh_CN = "zh_CN"
    en_GB = "en_GB"
    fr_FR = "fr_FR"
    de_DE = "de_DE"
    ja_JP = "ja_JP"
    en_IN = "en_IN"
