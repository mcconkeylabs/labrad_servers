import pytest, mock
from vuv.servers.bnc import base_bnc as BNC
from vuv.servers.bnc import base_server as SRV

@pytest.fixture(scope = 'module')
def chMap():
    return {0 : 'To', 1 : 'A', 2 : 'B', 3 : 'C', 4 : 'D'}

@pytest.fixture(scope = 'function')
def dev(chMap):
    device = BNC.BNCPulser(1, 'Test')
    device.send = mock.Mock()
    device.query = mock.Mock(return_value = '0')
    device.chMap = chMap
    
    return device
    
@pytest.fixture(scope = 'function')
def srv(dev):
    server = SRV.BNCBaseServer()
    server.selectedDevice = mock.Mock(return_value = dev)
    
    return server