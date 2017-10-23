import pytest
from .. import scan_gui


@pytest.fixture
def scan():
    dialog = scan_gui.ScanDialog()