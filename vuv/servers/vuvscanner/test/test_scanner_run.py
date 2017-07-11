import pytest, mock
from functools import partial

#@pytest.mark.parametrize('passes', [x for x in range(1, 5)])
#@pytest.inlineCallbacks
#def test_scanner_pass_count(srv, passes):
#    srv.passes = passes
#    yield srv.start(None)
#    
#    assert srv._completePasses == passes

@pytest.inlineCallbacks
def test_move_to_start_calls(srv):
    #have move state 'take a while' by returning True a few times
    posn = (5, 2)
    srv.stepper.move_state.side_effect = [True, True, False,
                                          True, True, False]
    srv.sRange = (posn, (300, 0))
    yield srv._moveToStartChannel()
    
    ch, frac = posn
    calls = [mock.call(ch - 1, frac, True),
             mock.call(ch, frac, True)]
    srv.stepper.move_to.assert_has_calls(calls)
    
@pytest.mark.parametrize('passes', [1, 5])
def test_scan_callback_called_correct_number_of_times(srv, passes):
    srv.passes = passes
    #mock scan pass so we can just ensure both scanPass and callback
    #are called the correct number of times without dealing with
    #outside world
    srv._scanPass = mock.Mock(side_effect = partial(srv._scanCallback, 
                                                    'Test'))
    
    srv.start(None)
    
    #just track mock calls
    assert srv._scanPass.call_count == passes