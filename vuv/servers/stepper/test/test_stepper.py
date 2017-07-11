# -*- coding: utf-8 -*-
"""
Created on Sun Dec 11 12:18:01 2016

@author: Jeff
"""

import pytest
from vuv.servers.stepper import stepper, calc
from labrad.errors import Error

DEFAULT_POSN = (100, 0, True)
BAD_CH_POSN = [(0, 9), (-1, 0), (4776, 0)]
GOOD_CH_POSN = [(0, 0), (4775, 8), (1000, 2)]

@pytest.fixture(scope='module')
def srv():
    '''Base server object'''
    s = stepper.StepperServer()
    return s

@pytest.fixture
def server_setup(srv):
    srv.posn = DEFAULT_POSN
    srv.chMap = {'Adv' : 1, 'Dir' : 2}

@pytest.fixture
def pulser(srv, mocker):
    srv.pulser = mocker.Mock()
    
class TestStepperPosition(object):
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('ch, part', GOOD_CH_POSN)
    def test_valid_positions_set(self, srv, ch, part):
        yield srv.current_position(None, ch, part)
        assert srv.posn == (ch, part, True)
        
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('ch, part', BAD_CH_POSN)
    def test_invalid_position_raises(self, srv, ch, part):
        with pytest.raises(stepper.InvalidPositionError):
            yield srv.current_position(None, ch, part)
            
    @pytest.inlineCallbacks
    def test_null_input_returns(self, srv, server_setup):
        ret = yield srv.current_position(None)
        assert ret == DEFAULT_POSN
        
@pytest.mark.usefixtures('server_setup')       
class TestMovePosition(object):
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('steps, posn', [(80, (110,0,True)), 
                                             (-80, (91, 0, False)), 
                                             (4, (100, 4, True)), (-8, (100, 0, False))])
    def test_input_steps_gives_right_position(self, srv, steps, posn):
        ret = yield srv._movePosn(steps)
        assert ret == posn

class TestMoveTo(object):
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('ch, part', BAD_CH_POSN)
    def test_invalid_position_raises(self, srv, ch, part):
        with pytest.raises(Error):
            yield srv.move_to(None, ch, part)
    
    @pytest.inlineCallbacks      
    @pytest.mark.usefixtures('server_setup')
    @pytest.mark.parametrize('ch, part, steps',
                             [(101, 0, 8), (99, 0, -16), 
                              (100, 4, 4), (98, 4, -20)])
    def test_channel_setup_called(self, srv, ch, part, steps, mocker):
        mcs = mocker.patch.object(srv, '_moveChannelSetup')
        
        #incorrect value but don't care here
        ret = (ch, part, True)
        mocker.patch.object(srv, '_movePosn', return_value=ret)
        
        resp = yield srv.move_to(None, ch, part)
        
        mcs.assert_called_once_with(steps)
        assert resp == ret[0:2]
  
@pytest.mark.usefixtures('server_setup', 'pulser')      
class TestAdvance(object):
    @pytest.inlineCallbacks
    @pytest.mark.parametrize('steps', [-50000, 37401, -809])
    def test_invalid_position_raises(self, srv, steps):
        with pytest.raises(Error):
            yield srv.advance(None, steps)