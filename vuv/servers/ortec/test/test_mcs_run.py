import pytest, mock
from labrad import util
from vuv.servers.ortec import mcs, jobs

MP = 'vuv.servers.ortec.mcs.Popen'

   
def test_start_with_running_process_throws(srv, mocker):
    mocker.patch.object(srv,'onScanStart')
    srv._isRunning.return_value = True
    with pytest.raises(mcs.MCSRunningError):
        srv.start(None)
        
def test_start_calls_process(srv, mocker):
    m = mocker.patch(MP)
    mocker.patch.object(srv,'onScanStart')
    srv.start(None)
    assert m.called
    
def test_run_job_opens_proc_with_correct_args(srv, mocker):
    m = mocker.patch(MP)
    srv._runJob([])
    m.assert_called_with([srv.exePath, '-J', srv.jobPath])
        
def test_stop_without_running_does_nothing(srv):
    srv.stop(None)
    srv.proc.terminate.assert_not_called()
    
def test_stop_while_running_terminates(srv, mocker):
    m = mocker.patch.object(srv, 'proc')
    srv._isRunning.return_value = True
    srv.stop(None)
    m.terminate.assert_called_with()
    
def test_clear_while_running_throws(srv):
    srv._isRunning.return_value = True    
    with pytest.raises(mcs.MCSRunningError):
        srv.clear_buffer(None)
        
def test_clear_while_idle_calls_job(srv, mocker):
    m = mocker.patch.object(srv, '_runJob')
    srv.clear_buffer(None)
    m.assert_called_with(jobs.CLEAR_LINES)
    
def test_save_data_while_running_throws(srv):
    srv._isRunning.return_value = True
    with pytest.raises(mcs.MCSRunningError):
        srv.save_data(None, 'test')
        
def test_start_sends_start_signal(srv):
    srv.start(None)
    srv.onScanStart.assert_called_once()
    
