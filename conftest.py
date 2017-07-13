import pytest
import subprocess as SP

@pytest.yield_fixture(scope='session')
def labrad_manager():
    proc = SP.Popen('labrad_start.bat')
    yield None
    SP.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)])

@pytest.yield_fixture(scope='session')
def labrad_node():
    proc = SP.open('python -m labrad.node --name VUV')
    yield None
    proc.terminate()

@pytest.fixture(scope='session')
@pytest.mark.usefixtures('labrad_manager')
def labrad_connection():
    import labrad
    
    cxn = labrad.connect()
    return cxn