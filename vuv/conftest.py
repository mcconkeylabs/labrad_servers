import pytest, os
from vuv.app.startup import ManagerWrapper
from labrad import thread

@pytest.fixture(scope='session')
def environ_setup():
    os.environ['LABRADPASSWORD'] = '12345'
    os.environ['LABRADREGISTRY'] = r'file:///C:/LabRAD/registry.db'

@pytest.yield_fixture(scope='session')
def labrad_manager(environ_setup):
    mgr = ManagerWrapper()
    yield None
    mgr.stop()
    
@pytest.yield_fixture(scope='session')
def reactor_thread(environ_setup):
    thread.startReactor()
    yield None
    thread.stopReactor()