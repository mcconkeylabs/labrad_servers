import pytest, mock
import labrad.units as U
from labrad.errors import Error
from vuv.servers.bnc.bnc_types import MODE_TYPES

class TestSettingParameters:           
    @pytest.inlineCallbacks
    def test_set_param_adds_channel(self, dev):
        yield dev._param(':TEST', channel = 1)
        dev.query.assert_called_with(':PULSE1:TEST?')
        
    @pytest.inlineCallbacks
    def test_set_param_called_send_with_parameter(self, dev):
        yield dev._param('TEST', True)
        dev.send.assert_called_with('TEST 1')
        
    @pytest.inlineCallbacks
    def test_channel_list(self, dev):
        dev.query.return_value = 'A, 1, B, 2'
        ret = yield dev.channel_list()
        
        assert ret == [(1, 'A'), (2, 'B')]
        
    @pytest.inlineCallbacks
    def test_output_ttl(self, dev):
        yield dev.output(1, False)
        dev.send.assert_called_with(':PULSE1:OUTPUT:MODE TTL')
        
    @pytest.inlineCallbacks
    def test_output_adjustable(self, dev):
        yield dev.output(1, True, U.Value(2.0, 'V'))
        
        dev.send.assert_any_call(':PULSE1:OUTPUT:MODE ADJ')
        dev.send.assert_any_call(':PULSE1:OUTPUT:AMPL 2.0')
        
    @pytest.inlineCallbacks
    def test_mode_trigger_mode_tag(self, dev):
        yield dev.mode(0)
        dev.query.assert_called_with(':PULSE0:MODE?')
        
    @pytest.inlineCallbacks
    def test_mode_channel_mode_tag(self, dev):
        yield dev.mode(1)
        dev.query.assert_called_with(':PULSE1:CMODE?')
        
    @pytest.inlineCallbacks
    def test_mode_normal_mode(self, dev):
        yield dev.mode(1, 'Normal')
        dev.send.assert_called_with(':PULSE1:CMODE NORM')
        
    @pytest.inlineCallbacks
    def test_mode_single_shot(self, dev):
        yield dev.mode(1, 'Single')
        dev.send.assert_called_with(':PULSE1:CMODE SING')
        
    @pytest.inlineCallbacks
    def test_mode_burst(self, dev):
        yield dev.mode(1, 'Burst', 1024)
     
        dev.send.assert_any_call(':PULSE1:CMODE BURS')
        dev.send.assert_any_call(':PULSE1:BCO 1024')
        
    @pytest.inlineCallbacks
    def test_mode_duty_cycle(self, dev):
        yield dev.mode(1, 'DutyCycle', (1, 7))
        
        dev.send.assert_any_call(':PULSE1:CMODE DCYC')
        dev.send.assert_any_call(':PULSE1:PCO 1')
        dev.send.assert_any_call(':PULSE1:OCO 7')
        
    @pytest.inlineCallbacks
    def test_invalid_modes_raise_error(self, dev):
        with pytest.raises(Error):
            yield dev.mode(1, 'Test')
        
    @pytest.inlineCallbacks
    def test_trigger_period(self, dev):
        yield dev.trigger_period(U.Value(1.0, 's'))
        
        dev.send.assert_called_with(':PULSE0:PER 1.0')
        
class TestGettingParameters:
    @pytest.inlineCallbacks
    def test_set_param_query_adds_question_mark(self, dev):
        ret = yield dev._param('TEST')
        
        dev.query.assert_called_with('TEST?')
        assert ret == False  
        
    @pytest.inlineCallbacks
    def test_output_query_ttl(self, dev):
        dev.query.return_value = 'TTL'
        resp = yield dev.output(1)
        
        dev.query.assert_called_with(':PULSE1:OUTPUT:MODE?')
        assert resp == (False, None)
        
    @pytest.inlineCallbacks
    def test_output_query_adjustable(self, dev):
        dev.query.side_effect = ['ADJ', '2.0000']
        resp = yield dev.output(1)
        
        dev.query.assert_any_call(':PULSE1:OUTPUT:MODE?')
        dev.query.assert_any_call(':PULSE1:OUTPUT:AMPL?')
        assert resp == (True, U.Value(2.0, 'V'))
        
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('outval, inval', 
                             [i for i in MODE_TYPES.iteritems()])
    def test_mode_query_responses(self, dev, outval, inval):
        dev.query.return_value = inval
        if outval == 'Burst':
            dev.query.side_effect = ['BURS', '10']
        elif outval == 'DutyCycle':
            dev.query.side_effect = ['DCYC', '1', '2']
            
        resp = yield dev.mode(1)
        
        dev.query.assert_any_call(':PULSE1:CMODE?')
        assert resp[0] == outval
        
    @pytest.inlineCallbacks
    def test_mode_burst_response_parameter(self, dev):
        dev.query.side_effect = ['BURS', '1024']
        resp = yield dev.mode(1)
        
        dev.query.assert_any_call(':PULSE1:BCO?')
        assert resp == ('Burst', 1024)
        
    @pytest.inlineCallbacks
    def test_mode_duty_cycle_response_parameter(self, dev):
        dev.query.side_effect = ['DCYC', '1', '3']
        resp = yield dev.mode(1)
        
        dev.query.assert_any_call(':PULSE1:PCO?')
        dev.query.assert_any_call(':PULSE1:OCO?')
        assert resp == ('DutyCycle', (1, 3))