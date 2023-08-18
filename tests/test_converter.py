from copy import deepcopy
from json import loads
from unittest import TestCase

from fastapi_esql import convert_dicts


class TestConvertDicts(TestCase):

    dicts = [{"id": 1, "value": "1"}, {"id": 2, "value": '{"k": [true, null]}'}]

    def test_normal(self):
        dicts = deepcopy(self.dicts)
        convert_dicts(dicts, {"value": loads})
        assert dicts == [{"id": 1, "value": 1}, {"id": 2, "value": {"k": [True, None]}}]

    def test_wrong_field(self):
        dicts = deepcopy(self.dicts)
        convert_dicts(dicts, {"wrong_value": loads})
        assert dicts == self.dicts

    def test_wrong_converter(self):
        dicts = deepcopy(self.dicts)
        convert_dicts(dicts, {"value": int})
        assert dicts == [{"id": 1, "value": 1}, {"id": 2, "value": '{"k": [true, null]}'}]
