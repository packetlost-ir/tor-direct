import unittest
from unittest.mock import MagicMock, patch
import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from t0rd.network.tor import get_controller, create_onion_service
from t0rd.ui.app import T0rdApp

class TestTorInit(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.patcher_controller = patch("t0rd.network.tor.Controller")
        self.mock_controller_class = self.patcher_controller.start()
        self.mock_controller = self.mock_controller_class.from_port.return_value
        
    def tearDown(self):
        self.patcher_controller.stop()

    def test_get_controller_success(self):
        self.mock_controller.is_authenticated.return_value = True
        ctrl = get_controller(9051, "password")
        self.mock_controller.authenticate.assert_called_with(password="password")
        self.assertEqual(ctrl, self.mock_controller)

    def test_get_controller_fail_auth(self):
        self.mock_controller.authenticate.side_effect = Exception("Auth failed")
        with self.assertRaises(PermissionError):
            get_controller(9051, "password")

    @patch("t0rd.network.tor.wait_for_bootstrap")
    def test_create_onion_service(self, mock_wait_bootstrap):
        mock_wait_bootstrap.return_value = True
        self.mock_controller.create_ephemeral_hidden_service.return_value = MagicMock(
            service_id="abc.onion",
            private_key_type="ED25519-V3",
            private_key="key"
        )
        
        service_id, key_type, key = create_onion_service(self.mock_controller, 5666)
        self.assertEqual(service_id, "abc")
        self.assertEqual(key, "key")
        self.mock_controller.create_ephemeral_hidden_service.assert_called()

if __name__ == "__main__":
    unittest.main()
