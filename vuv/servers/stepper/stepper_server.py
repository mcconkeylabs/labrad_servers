# Copyright (C) 2016  Jeffery Dech
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
### BEGIN NODE INFO
[info]
name = VUV Stepper Server
version = 1.0
description = Control server for VUV spectrometer stepper motor

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 6677901234
timeout = 20
### END NODE INFO
    
Server for VUV Stepper
"""

import labrad.units as U
import calc
from time import sleep
from labrad.server import LabradServer, setting, Signal
from labrad.errors import Error
from twisted.internet.defer import inlineCallbacks, returnValue

DIR_MAP = {'forward' : True,
           'backward' : False}

REG_LOC = ['', 'Servers', 'VUV Stepper']
MOVE_PERIOD = U.Value(50, 'ms')

class InvalidPosition(Error):
    '''Invalid stepper position'''
    code = 104

class VUVStepperServer(LabradServer):
    name = 'VUV Stepper Server'
    PULSE_STOP_ID = 88877
    
    onMoveComplete = Signal(87123, 'signal: move complete', '(ww)')
    
    @inlineCallbacks
    def initServer(self):
        self.reg = self.client.registry
        yield self._loadRegistry()
        
        #initialize pulser to None at first and then connect if it exists
        self.pulser = None
        if hasattr(self.client, self.pulserName):
            yield self._connectPulser()
    
    @inlineCallbacks
    def stopServer(self):
        yield self._updateRegistry()
    
    @inlineCallbacks
    def serverConnected(self, ID, name):
        if name == self.pulserName:
            yield self._connectPulser()
    
    def serverDisconnected(self, ID, name):
        if name == self.pulserName:
            self.pulser = None
    
    @inlineCallbacks
    def _loadRegistry(self):
        p = self.reg.packet()
        p.cd(REG_LOC, True)
        p.get('Channels', key='ch')
        p.get('Position', key='pos')
        p.get('Dwell Time', True, MOVE_PERIOD, key='dwell')
        p.get('Device', key='dev')
        resp = yield p.send()
        
        #load data
        self.chMap = dict(resp['ch'])
        self.posn = resp['pos']
        self.dwell = resp['dwell']
        self.pulserName, self.deviceName = resp['dev']
        
        #setup callback to update on changes in REG_LOC directory
        self.reg.addListener(self._loadRegistry)
        self.reg.notify_on_change(self.PULSE_STOP_ID, True)
        
    @inlineCallbacks
    def _updateRegistry(self):
        vals = {'Channels' : list(self.chMap.iteritems()),
                'Position' : self.posn,
                'Dwell Time' : self.dwell,
                'Device' : (self.pulserName, self.deviceName)}
                
        p = self.reg.packet()
        p.cd(REG_LOC, True)
        for (k, v) in vals.iteritems():
            p.set(k, v)
        yield p.send()        
        
    @inlineCallbacks
    def _connectPulser(self):
        self.pulser = self.client[self.pulserName]
        yield self.pulser.select_device(self.deviceName)
        
    @inlineCallbacks
    def _pulserSetup(self, steps, forward=True, only=False):
        p = self.pulser.packet()
        p.enable(self.chMap.values(), only)
        
        #advance channnel
        p.select_channel(self.chMap['Adv'])
        p.width(U.Value(10, 'us'))
        p.delay(U.Value(10, 'us'))
        p.polarity(True)
        p.mode('Normal')
        p.output(False)
        
        #direction channel
        p.select_channel(self.chMap['Dir'])
        p.width(U.Value(1, 'ms'))
        p.delay(U.Value(0, 's'))
        p.polarity(forward)
        p.mode('Normal')
        p.output(False)
        
        #trigger burst with step count
        p.select_channel(0)
        p.mode('Burst', steps)
        
        yield p.send()
        
        
    @inlineCallbacks
    def _setCh(self, ch, val=None):
        if val is not None:
            self.chMap[ch] = val
            self.reg.set('Channels', self.chMap.items())
        return self.chMap[ch]
        
    @inlineCallbacks
    def _isRunning(self):
        #check trigger and stepper advance channels
        check = [0, self.chMap['Adv']]
        
        #check the state of these channels on the pulser
        p = self.pulser.packet()
        p.select_device(self.deviceName)
        for ch in check:
            p.select_channel(ch)
            p.state(key=ch)
        resp = yield p.send()
        
        #device is running if all these channels are enabled
        running = all([resp[ch] for ch in check])
        returnValue(running)
        
    @inlineCallbacks
    def _moveSetup(self, steps, forward=True, now=False):
        #if moving now, lock pulser (only = now)
        yield self._pulserSetup(steps, forward, now)
        
        #register callback for pulser stopping
        yield self.pulser.signal__pulser_stopped(self.PULSE_STOP_ID)
        yield self.pulser.addListener(listener = self._pulserCallback,
                                      source = None, ID = self.PULSE_STOP_ID)
                                      
        #if moving now, setup pulser and run
        if now:
            p = self.pulser.packet()
            p.trigger_period(self.dwell)
            p.start()
            yield p.send()
          
    @inlineCallbacks                            
    def _pulserCallback(self, ctx, devName):
        if devName == self.deviceName:
            self.posn = self.newPosn
            self.newPosn = None
            yield self.pulser.removeListener(listener = self._pulserCallback,
                                             ID = self.PULSE_STOP_ID)
            
            self.onMoveComplete(self.posn[0:2])
        
    @setting(90, 'Advance Channel', channel='w', returns='w')
    def advance_channel(self, c, channel = None):
        returnValue(self._setCh('Adv', channel))
        
    @setting(91, 'Direction Channel', channel='w', returns='w')
    def direction_channel(self, c, channel=None):
        returnValue(self._setCh('Dir', channel))
    
#    @setting(100, 'Start')
#    def start(self, c):
#        pass
#    
#    @setting(101, 'Stop')
#    def stop(self, c):
#        pass
    
    @setting(102, 'Run State', returns='b')
    def run_state(self, c):
        returnValue(self._isRunning())
    
    @setting(200, 'Position',
             channel = 'w', partial = 'w', direction=['b', 's'],
             returns = '(wws)')
    def position(self, c, channel=None, partial=0, direction=True):
        '''Get or set the current stepper position.
        Input:
        channel - The current channel position
        partial - Channel fraction (8 steps per channel)
        direction - Either 'forward' or 'backward' or
                    True/False for forward and backward
        Returns:
        Current position and direction as a tuple with
        direction as a string
        (channel, partial, direction)
        '''
        if channel is not None:
            #if we're setting the channel by string, validate and set
            #boolean value as forward/backward (true/false)
            if type(direction) is str:
                d = direction.lower()
                if d not in DIR_MAP.keys():
                    raise Error('Direction must be Forward or Backward')
                dval = d == 'forward'
            else:
                dval = direction
                
            if not calc.isValidCh((channel, partial)):
                raise InvalidPosition()
                
            self.posn = (channel, partial, dval)
        
        c, f, d = self.posn
        dStr = 'Forward' if d else 'Backward'
        return (c, f, dStr)
    
    @setting(201, 'Dwell Time', dwell='v[s]', returns='v[s]')
    def dwell_time(self, c, dwell=None):
        '''Get or set current dwell time per channel (NOT PER STEP)'''
        if dwell is not None:
            self.dwell = dwell
        return self.dwell
        
    @setting(300, 'Move To', channel='w', partial='w', now='b',
             returns=['','(ww)'])
    def move_to(self, c, channel=None, partial=0, now=False):
        '''Set stepper to move to the specified channel position.
        Inputs:
        channel - Channel position on stepper to move to
        partial - Partial channel increments (8 per channel)
        
        Returns:
        (channel, partial) - Currently set move
        '''
        if channel is None:
            returnValue(self.newPosn[0:2] if self.newPosn else None)
                
        newPosn = (channel, partial)
        if not calc.isValidCh(newPosn):
            raise InvalidPosition()
            
        steps = calc.ch2steps(calc.chdiff(newPosn, self.posn[:2]))
        positive = steps >=0
        #XOR bits, if changing directions, add backlash
        if positive ^ self.posn[2]:
            sgn = 1 if positive else -1
            steps += sgn * 8
            
        self.newPosn = (channel, partial, positive)
        yield self._moveSetup(abs(steps), positive, now)
        returnValue(self.newPosn[0:2])
    
    @setting(301, 'Advance', steps=['i','w'], now='b', 
             returns=['','i'])
    def advance(self, c, steps=None, now=False):
        '''Set stepper to advance a given number of increments.
        NB: There are 8 increments per channel
        
        Inputs:
        steps - Number of steps to take. Negative moves backwards.
        
        Returns:
        steps - Current number of steps stepper set to take
        '''
        if steps is None:
            if not self.newPosn:
                returnValue(None)
            else:
                advs = calc.ch2steps(calc.chdiff(self.newPosn[0:2], 
                                                 self.posn[0:2]))
                if self.newPosn[2] != self.posn[2]:
                    sgn = 1 if self.newPosn[2] else -1
                    advs += sgn * 8
                returnValue(advs)
            
        ch, frac, forward = self.posn
        goForward = steps >= 0
        
        #XOR the bits, if not equal, include backlash for direction change
        if goForward ^ forward:
            sgn = 1 if goForward else -1
            shift = steps - sgn * 8
        else:
            shift = steps
            
        mathFn = calc.chadd if goForward else calc.chdiff
        newCh, newFrac = mathFn((ch, frac), calc.steps2ch(abs(shift)))
        
        if not calc.isValidCh((newCh, newFrac)):
            raise InvalidPosition()
            
        self.newPosn = (newCh, newFrac, goForward) 
        yield self._moveSetup(abs(steps), goForward, now)
        returnValue(steps)
    
        
__server__ = VUVStepperServer()        
        
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)