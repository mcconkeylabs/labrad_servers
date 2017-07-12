import pytest
import tempfile
from shutil import rmtree
from os.path import join
from vuv.servers.ortec import mcs

@pytest.yield_fixture(scope='module')
def tmpdir():
    tdir = tempfile.mkdtemp()
    yield tdir
    rmtree(tdir)
    
@pytest.fixture(scope='function')
def srv(tmpdir, mocker):
    server = mcs.MCSServer()
    
    #setup in lieu of reading from registry
    server.params = mcs.DEFAULT_PARAMETERS
    server.tmpDir = tmpdir
    server.jobPath = join(tmpdir, mcs.JOB_NAME)
    server.exePath = ''
    
    #by default mock the calls to the MCS exe
    server.proc = mocker.Mock()
    server._isRunning = mocker.Mock(return_value = False)
    
    server.onScanStart = mocker.Mock()
    server.onScanComplete = mocker.Mock()
    
    return server