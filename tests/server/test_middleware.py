from unittest import TestCase
from server.game_handler.middlewares import is_valid_uuid


class TestMiddlewares(TestCase):

    def setUp(self):
        pass

    def test_is_uuid(self):
        assert is_valid_uuid("283e1f5e-3411-44c5-9bc5-037358c47100")
        assert not is_valid_uuid("283e1f5e-341144c5-9bc5-037358c47100")
