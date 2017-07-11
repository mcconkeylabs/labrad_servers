import pytest, mock
import labrad.units as U
from labrad.errors import Error
from vuv.servers.stepper import calc, stepper_server as S

BASE_POSN = (10, 0, True)
BAD_CH_POSN_LIST = [(-1, 0, True), (0, 9, True), (4775, 1, True), 
                    (4776, 0, True)]

@pytest.fixture(scope='module')
def srv():
    s = S.VUVStepperServer()
    s.pulser = mock.Mock()
    return s
    
class TestStepperPosition(object):
    def test_position_none_input_returns_position(self, srv):
        srv.posn = BASE_POSN
        resp = srv.position(None)
        assert resp == (10, 0, 'Forward')
        
    @pytest.mark.parametrize('ch, frac, forward', BAD_CH_POSN_LIST)
    def test_invalid_position_raises(self, srv, ch, frac, forward):
        with pytest.raises(S.InvalidPosition):
            srv.position(None, ch, frac, forward)
            
    @pytest.mark.parametrize('direc', ['Frwrd', 'forwardd', 'something'])
    def test_invalid_direction_text_fails(self, srv, direc):
        with pytest.raises(Error):
            srv.position(None, 10, 0, direc)
        
    @pytest.mark.parametrize('direc', [False, 'Backward', 'backward', 'BaCkWaRd'])
    def test_position_backwards_sets_all_input_types(self, srv, direc):
        resp = srv.position(None, 20, 5, direc)
        assert resp == (20, 5, 'Backward')
        
    @pytest.mark.parametrize('direc', [True, 'Forward', 'forward', 'FoRwArD'])
    def test_position_backwards_sets_all_input_types(self, srv, direc):
        resp = srv.position(None, 20, 5, direc)
        assert resp == (20, 5, 'Forward')
        
class TestStepperMoveTo(object):
    @pytest.fixture(scope='function', autouse=True)
    def patch_move_call(self, srv):
        srv.posn = BASE_POSN
        
    @pytest.fixture(scope='function')
    def ms(self, srv, mocker):
        m = mocker.patch.object(srv, '_moveSetup')
        return m
        
    @pytest.inlineCallbacks
    def test_move_to_null_input_returns(self, srv):
        srv.newPosn = (20, 0, True)
        resp = yield srv.move_to(None)
        assert resp == (20, 0)
        
    @pytest.inlineCallbacks
    def test_move_to_invalid_channel_raises(self, srv):
        with pytest.raises(S.InvalidPosition):
            yield srv.move_to(None, -1, 0)
            
    @pytest.inlineCallbacks
    def move_test(self, srv, ms, ch, frac, steps, direc):
        resp = yield srv.move_to(None, ch, frac)
        
        assert resp == (ch, frac)
        assert srv.newPosn == (ch, frac, direc)
        ms.assert_called_with(steps, direc, False)
    
    @pytest.mark.parametrize('ch, frac, steps', [(11, 0, 8), (11, 4, 12), (10, 4, 4)])
    def test_move_to_continues_forward(self, srv, ms, ch, frac, steps):
        self.move_test(srv, ms, ch, frac, steps, True)
    
    @pytest.mark.parametrize('ch, frac, steps', [(9, 0, 8), (8, 4, 12), (9, 4, 4)])
    def test_move_to_continues_backward(self, srv, ms, ch, frac, steps):
        srv.posn = (10, 0, False)
        self.move_test(srv, ms, ch, frac, steps, False)
        
    @pytest.mark.parametrize('ch, frac, steps', [(10, 0, 8), (9, 0, 16)])
    def test_move_to_forward_changes_to_backward(self, srv, ms, ch, frac, steps):
        self.move_test(srv, ms, ch, frac, steps, False)
        
    @pytest.mark.parametrize('ch, frac, steps', [(10, 0, 8), (11, 0, 16)])
    def test_move_to_backward_changed_to_forward(self, srv, ms, ch, frac, steps):
        srv.posn = (10, 0, False)
        self.move_test(srv, ms, ch, frac, steps, True)
    
class TestStepperAdvance(object):
    @pytest.fixture(scope='function', autouse=True)
    def init(self, srv):
        srv.posn = BASE_POSN
        
    @pytest.fixture(scope='function')
    def ms(self, srv, mocker):
        m = mocker.patch.object(srv, '_moveSetup')
        return m
        
    @pytest.inlineCallbacks
    def test_advance_none_newposn_none_returns_none(self, srv):
        srv.newPosn = None
        resp = yield srv.advance(None)
        assert resp is None
        
    @pytest.inlineCallbacks
    def test_advance_invalid_raises(self, srv):
        with pytest.raises(S.InvalidPosition):
            yield srv.advance(None, 800000)
    
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('npos, steps', [((10, 0, False), -8),
                                             ((11, 0, True), 8),
                                             ((9, 4, False), -12),
                                             ((10, 4, True), 4)])
    def test_advance_none_returns_proper_steps(self, srv, npos, steps):
        srv.newPosn = npos
        resp = yield srv.advance(None)
        assert resp == steps
        
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('npos, steps', [((9, 4, False), -12),
                                             ((11, 0, True), 8),
                                             ((10, 0, False), -8)])
    def test_advance_calls_and_sets_correctly(self, srv, ms, npos, steps):
        resp = yield srv.advance(None, steps)
        
        assert srv.newPosn == npos
        assert resp == steps
        ms.assert_called_with(abs(steps), npos[2], False)
        
class TestStepperMoveSetup(object):
    @pytest.fixture(scope='function')
    def pls(self, srv, mocker):
        mocker.patch.object(srv, '_pulserSetup')
        return mocker.patch.object(srv, 'pulser')
        
    @pytest.inlineCallbacks
    def test_move_not_now_wont_set_trigger_or_start(self, srv, pls):
        yield srv._moveSetup(10, True, False)
        assert not pls.packet.called
        
    @pytest.inlineCallbacks
    def test_move_now_sets_trigger_and_starts(self, srv, pls, mocker):
        DWELL = U.Value(1, 's')
        
        srv.dwell = DWELL
        yield srv._moveSetup(10, True, True)
        
        pls.packet().trigger_period.assert_called_with(DWELL)
        pls.packet().start.assert_called_with()