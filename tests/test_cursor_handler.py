from logging import getLogger

from asynctest import CoroutineMock, TestCase, patch

from . import get_test_conn
from fastapi_esql import CursorHandler

logger = getLogger(__name__)


class TestCursorHandler(TestCase):

    conn = get_test_conn()

    async def test_fetch_dicts(self):
        with patch(
            "tortoise.backends.mysql.client_class.execute_query_dict",
            # new=CoroutineMock()
        ) as mock_exec:
            mock_exec.side_effect = Exception("Error")
            assert await CursorHandler.fetch_dicts("SELECT true", self.conn, logger) is None

    @patch("tortoise.backends.mysql.client_class.execute_query")
    async def test_sum_row_cnt(self, mock_exec):
        mock_exec.return_value = 10, object()
        assert await CursorHandler.sum_row_cnt("SELECT true", self.conn, logger) == 10

    async def test_exec_if_ok(self):
        # True means test connection is reachable
        assert await CursorHandler.exec_if_ok("SELECT true", self.conn, logger) == True
