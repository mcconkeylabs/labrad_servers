import pytest, mock
from vuv.servers.bnc.bnc555 import BNC555Pulser, CMODE_TYPES

@pytest.fixture
def bnc555():
    dev = BNC555Pulser(1, 'Test')
    dev.send = mock.Mock()
    dev.query = mock.Mock()
    
    return dev
    
@pytest.inlineCallbacks
def test_mode_trigger_query(bnc555):
    bnc555.query.return_value = 'NORM'
    yield bnc555.mode(0)
    
    bnc555.query.assert_called_with(':PULSE0:MODE?')
    
@pytest.inlineCallbacks
@pytest.mark.parametrize('outval, effect', 
                         [('Normal', ['NORM']),
                          ('Single', ['SING']),
                          ('Burst',  ['BURS', '1000']),
                          ('Divide', ['DIVI', '8'])
                         ])
def test_mode_query_type(bnc555, outval, effect):
    bnc555.query.side_effect = effect
    resp = yield bnc555.mode(1)
    
    bnc555.query.assert_any_call(':PULSE1:CMODE?')
    assert resp[0] == outval
    
@pytest.inlineCallbacks
def test_mode_query_burst(bnc555):
    bnc555.query.side_effect = ['BURS', '10']
    resp = yield bnc555.mode(1)
    
    bnc555.query.assert_any_call(':PULSE1:BCO?')
    assert resp == ('Burst', 10)
    
@pytest.inlineCallbacks
def test_mode_query_divide(bnc555):
    bnc555.query.side_effect = ['DIVI', '7']
    resp = yield bnc555.mode(1)
    
    bnc555.query.assert_any_call(':PULSE1:DCO?')
    assert resp == ('Divide', 7)