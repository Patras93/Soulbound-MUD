"""The current bootstrap transfers its listener without namespace injection."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.runtime_transport import register_boot_socket, take_boot_socket


class BootstrapTransportTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNone(take_boot_socket())

    def tearDown(self):
        take_boot_socket()

    def test_transfer_preserves_the_existing_listener(self):
        listener = object()
        register_boot_socket(listener)
        self.assertIs(take_boot_socket(), listener)
        self.assertIsNone(take_boot_socket())

    def test_second_registration_cannot_replace_the_listener(self):
        listener = object()
        register_boot_socket(listener)
        with self.assertRaises(RuntimeError):
            register_boot_socket(object())
        self.assertIs(take_boot_socket(), listener)


if __name__ == "__main__":
    unittest.main()
