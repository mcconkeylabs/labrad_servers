import pytest
import mock
import labrad.units as U
from vuv.servers.vuvscanner.scanner import ScanServer

@pytest.fixture(scope = 'function')
def srv():
    server = ScanServer()
    server.pulser = mock.Mock()
    server.stepper = mock.Mock()
    
    #config settings
    server.chMap = {'Start' : 1, 'MCSAdv' : 2}
    server.ratio = 1.0
    server.sRange = ((10, 0), (100, 0))
    server.dwell = U.Value(1.0, 's')
    server.passes = 2
    server._running = False
    
    return server