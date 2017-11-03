import pytest
from .. import scan_gui



@pytest.fixture
def scan(mocker):
    ctrl_stub = mocker.stub(name="ctl_stub") 
    dialog = scan_gui.ScanDialog(ctrl_stub)
    return dialog

