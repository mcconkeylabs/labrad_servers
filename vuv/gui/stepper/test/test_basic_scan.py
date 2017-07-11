import pytest, mock
from vuv.gui.stepper.basic_scan import ScanWidget

@pytest.fixture
def widget(qtbot):
    w = ScanWidget(cxn = mock.Mock())    
    w.show()
    qtbot.addWidget(w)
    return w
    
