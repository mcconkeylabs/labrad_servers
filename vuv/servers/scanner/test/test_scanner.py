import pytest
import vuv.servers.scanner.scanner as S
import labrad.units as U
from labrad.errors import Error

@pytest.fixture(scope='module')
def srv():
    srv = S.ScanServer()
    return srv
    
@pytest.fixture()
def settings_setup(srv):
    srv.dwell = U.Value(1, 's')
    srv.ratio = 1.0

@pytest.mark.usefixtures('settings_setup')
class TestScannerSettings(object):
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('dwell', [0.35, -1.0])
    def test_bad_dwell_time_raises(self, srv, dwell):
        time = U.Value(dwell, 's')
        with pytest.raises(Error):
            yield srv.dwell_time(None, time)
            
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('ratio', [-0.124, 0.124])
    def test_bad_channel_ratio_raises(self, srv, ratio):
        with pytest.raises(Error):
            yield srv.channel_ratio(None, ratio)
            
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('ratio', [0.125, 3.5])
    def test_good_channel_ratio_sets(self, srv, ratio):
        ret = srv.channel_ratio(None, ratio)
        
        assert ret == ratio
        assert srv.ratio == ratio
        
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('ratio, rnd', [(0.126, 0.125), (0.27, 0.25)])
    def test_channel_ratio_rounds_down(self, srv, ratio, rnd):
        ret = srv.channel_ratio(None, ratio)
        
        assert ret == rnd
        assert srv.ratio == rnd
        
    @pytest.inlineCallbacks
    def test_scan_range_raises_with_no_stop(self, srv):
        with pytest.raises(Error):
            srv.scan_range(None, 10)
            
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('sr', [((-100, 0), (100, 0)), ((1, 0),(-200, 0))])
    def test_invalid_scan_range_raises(self, srv, sr):
        with pytest.raises(Error):
            yield srv.scan_range(None, sr)
            
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('start, stop', [((1, 0), (2, 0)), (1, (2,4)), ((1,3), 4)])
    def test_valid_scan_range_sets(self, srv, start, stop):
        r1 = start if type(start) is tuple else (start, 0)
        r2 = stop if type(stop) is tuple else (stop, 0)
        
        ret = srv.scan_range(None, start, stop)
        assert srv.range == (r1, r2)
        assert ret == (r1, r2)
        
        