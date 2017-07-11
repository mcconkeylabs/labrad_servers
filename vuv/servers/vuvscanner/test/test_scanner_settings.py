import pytest, mock
import labrad.units as U
from labrad.errors import Error
from vuv.servers.vuvscanner.scanner import ratio2dutycycle, ScanServer

@pytest.mark.parametrize('ratio, off', 
                         [(1.0, 7), (0.5, 3), (0.25, 1), (2.0, 15)])
def test_ratio_to_duty_cycle(ratio, off):
    dcyc = ratio2dutycycle(ratio)
    assert dcyc == (1, off)
    
@pytest.inlineCallbacks
def test_start_initialization(srv):
    srv._scanPass = mock.Mock()
    
    yield srv.start(None)
    
    assert srv._completePasses == 0
    assert srv._running == True
    
def test_mcs_ratio_minimum_raises(srv):
    with pytest.raises(Error):
        srv.mcs_ratio(None, 1.0 / 16)

@pytest.mark.parametrize('actual, rounded',
                          [(0.126, 0.125), (0.9, 0.875)])        
def test_mcs_ratio_rounds(srv, actual, rounded):
    ratio = srv.mcs_ratio(None, actual)
    
    assert ratio == rounded
    
def test_scan_range_incomplete_throws(srv):
    with pytest.raises(Error):
        srv.scan_range(None, 5)
        
@pytest.mark.parametrize('start, stop', [(1, 20), (50, 1000)])
def test_scan_range_sets(srv, start, stop):
    sRange = srv.scan_range(None, start, stop)
    
    assert sRange == ((start, 0), (stop, 0))
    
def test_small_dwell_throws(srv):
    with pytest.raises(Error):
        srv.dwell_time(None, U.Value(10, 'us'))
  
@pytest.inlineCallbacks      
def test_scan_pass_callback_under_max_continues(srv):
    srv._completePasses = 0
    srv._scanPass = mock.Mock()

    yield srv._scanCallback(None)
       
    srv._scanPass.assert_called_with()
    
@pytest.inlineCallbacks
def test_scan_pass_callback_at_max_stops(srv):
    srv._completePasses = 1
    
    yield srv._scanCallback(None)
    
    assert srv.pulser.removeListener.called