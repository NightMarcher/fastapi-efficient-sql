from logging import getLogger

from asynctest import TestCase, patch

from . import get_test_conn, init_tortoise
from fastapi_esql import CursorHandler

logger = getLogger(__name__)


class TestCursorHandler(TestCase):

    use_default_loop = True

    async def setUp(self):
        await init_tortoise()
        self.conn = get_test_conn()

    async def test_fetch_dicts(self):
        result = await CursorHandler.fetch_dicts("SELECT 1 idx", self.conn, logger)
        print(f"result => {result}")
        assert result

    @patch("tortoise.backends.mysql.client_class.execute_query")
    async def test_sum_row_cnt(self, mock_exec):
        mock_exec.return_value = 10, object()
        assert await CursorHandler.sum_row_cnt("SELECT true", self.conn, logger) == 10

    async def test_exec_if_ok(self):
        with patch(
            "tortoise.backends.mysql.client_class.execute_script",
        ) as mock_exec:
            mock_exec.side_effect = Exception("Error")
            assert await CursorHandler.exec_if_ok("SELECT true", self.conn, logger) == False
