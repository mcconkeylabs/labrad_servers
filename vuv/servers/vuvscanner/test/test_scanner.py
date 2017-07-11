import pytest, mock
import vuv.servers.vuvscanner.scanner as scan
from labrad.errors import Error

@pytest.fixture(scope='module')
def srv():
    server = scan.ScanServer()
    server.params = scan.PARAMETER_DEFAULTS
    server.pulserDeviceName = 'Test'
    return server
    
@pytest.mark.parametrize('ratio, doff', [(1.0, 7), (0.5, 3), (2.0, 15), (0.125, 0)])
def test_ratio_to_duty_cycle(ratio, doff):
    dcyc = scan.ratio2dutycycle(ratio)
    assert dcyc == (1, doff)
            
@pytest.mark.parametrize('ratio, rounded', [(0.126, 0.125), (0.124, 0.0), (0.267, 0.250)])
def test_ratio_rounds(srv, ratio, rounded):
    resp = srv.mcs_ratio(None, ratio)
    
    assert resp == rounded
    assert srv.params['MCS Ratio'] == rounded
      
class TestScannerRangeParam(object):
    def test_scan_range_none_returns_default(self, srv):
        resp = srv.scan_range(None)
        assert resp == scan.PARAMETER_DEFAULTS['Scan Range']
        
    def test_scan_no_stop_raises(self, srv):
        with pytest.raises(Error):
            srv.scan_range(None, 10, 0)
            
    @pytest.mark.parametrize('sC, sF', [(5, 0), (10, 0)])
    def test_scan_stop_before_start_raises(self, srv, sC, sF):
        with pytest.raises(Error):
            srv.scan_range(None, 10, 4, sC, sF)
            
    def test_scan_range_sets_parameter_with_correct_format(self, srv):
        sRange = ((5,0),(10,0))
        ret = srv.scan_range(None, 5,0,10,0)
        
        assert srv.params['Scan Range'] == sRange
        assert ret == sRange
    
class TestScannerStart(object):
    @pytest.fixture(scope='function')
    def iRun(self, srv, mocker):
        m = mocker.patch.object(srv, '_isRunning')
        m.return_value = False
        return m
        
    @pytest.inlineCallbacks
    def test_start_while_running_raises(self, srv, iRun):
        iRun.return_value = True
        with pytest.raises(Error):
            yield srv.start(None)
            
    
            
class TestScannerStop(object):
    @pytest.fixture(scope='function')
    def iRun(self, srv, mocker):
        m = mocker.patch.object(srv, '_isRunning')
        m.return_value = True
        return m
        
    @pytest.inlineCallbacks
    def test_stop_while_not_running_raises(self, srv, iRun):
        iRun.return_value = False
        with pytest.raises(Error):
            yield srv.stop(None)
            
class TestScanCallback(object):
    DEV_NAME = 'Test'
    MOCKS = ['_waitForStepper', 'onPassComplete', 'onScanComplete', '_prepPulser']
    
    @pytest.fixture(scope='function', autouse=True)
    def setup(self, srv, mocker):
        srv.params['Passes'] = 2
        srv.stepper = mocker.Mock()
        srv.pulser = mocker.Mock()
    
    @pytest.fixture(scope='function')
    def mocks(self, srv, mocker):
        ms = {}
        for m in self.MOCKS:
            ms[m] = mocker.patch.object(srv, m)
        return ms
    
    @pytest.inlineCallbacks
    def test_callback_on_different_device_does_nothing(self, srv):
        resp = yield srv._scanCallback(None, 'Not')
        assert resp is None
        
    @pytest.inlineCallbacks
    def test_callback_on_max_pass_stops(self, srv, mocks):
        srv.currentPass = 1
        yield srv._scanCallback(None, 'Test')
        
        assert mocks['onScanComplete'].called
        
    @pytest.inlineCallbacks
    def test_callback_below_max_continues(self, srv, mocks):
        srv.params['Passes'] = 2
        yield srv._scanCallback(None, 'Test')
        
        assert mocks['onPassComplete'].called
        