"""Ensure all primary GeoLook modules can import with declared dependencies."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestRuntimeImports(unittest.TestCase):
    def test_primary_modules_import(self):
        import bootstrap  # noqa: F401
        import dashboard  # noqa: F401
        import geo  # noqa: F401
        import geolib  # noqa: F401
        import report  # noqa: F401
        import sample  # noqa: F401


if __name__ == "__main__":
    unittest.main()
