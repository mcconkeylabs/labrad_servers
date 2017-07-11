"""
### BEGIN NODE INFO
[info]
name = Stepper Server
version = 1.0
description = Control server for VUV spectrometer stepper motor

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 6677901234
timeout = 20
### END NODE INFO
    
Server for VUV Stepper Motor
"""

import labrad.units as U
import calc
from labrad.errors import Error
from labrad.server import LabradServer, setting
from twisted.internet.defer import inlineCallbacks, returnValue

REG_DIR = ['', 'Servers', 'VUV Stepper']

class InvalidPositionError(Error):
    '''Invalid stepper channel position'''
    code = 1010

class StepperServer(LabradServer):
    name = 'VUV Stepper'
    ID = 57544
    
    pulserStartID = 112233
    pulserStopID = 112234
    
    @inlineCallbacks
    def initServer(self):
        yield self._loadRegistryData()
        
        #add listener to track pulser movement
        yield self.pulser.signal_pulser_started(self.pulserStartID)
        yield self.pulser.addListener(listener = self._pulserStartListener,
                                      source = None, ID = self.pulserStartID)
    
    @inlineCallbacks
    def stopServer(self):
        yield self._updateRegistryData()
    
    @inlineCallbacks
    def serverConnected(self, ID, name):
        pass
    
    def serverDisconnected(self, ID, name):
        pass
    
    @inlineCallbacks
    def _loadRegistryData(self):
        p = self.client.registry.packet()
        p.cd(REG_DIR, True)
        p.get('Pulser', key='pulser')
        p.get('Position', key='posn')
        p.get('Channels', key='chs')
        resp = yield p.send()
        
        srv, dev = resp['Pulser']
        self.pulser = self.client[srv]
        yield self.pulser.select_device(dev)
        
        self.posn = resp['Position']
        self.chMap = dict(resp['chs'])
        
    @inlineCallbacks
    def _updateRegistryData(self):
        yield self.client.registry.set('Position', self.posn)
        
    @inlineCallbacks
    def _movePosn(self, move=None):
        '''Determine the new position of the stepper.
        Input:
            move - Optional number of steps to calculate move from
                 - If None, directly calucates based on what is in the pulser
        Returns:
            (channel, partial, direction)
                The channel and partial amount to move and the direction the
                stepper will be in.
        '''
        if move is not None:
            isForward = move > 0
            steps = move
        else:
            print 'Checking pulser'
            isOn = yield self.running(None)
            
            #if the motor isn't stepping we don't care if pulser runs
            if not isOn:
                returnValue(self.posn)
            
            #get information on positioning
            p = self.pulser.packet()
            p.select_channel(0)
            p.mode(key='tmode')
            p.select_channel(self.chMap['Adv'])
            p.mode(key='amode')
            p.select_channel(self.chMap['Dir'])
            p.polarity(key='pol')
            resp = yield p.send()
            
            #now do calculation
            isForward = resp['pol']
            steps = min([resp[x][1] for x in ['tmode', 'amode'] if resp[x][0] == 'Burst'])
            
        #if we change direction, account for hysteresis    
        if isForward != self.posn[2]:
            sgn = 1 if isForward else -1
            steps -= sgn * calc.STEPS_PER_CH
            
        newPos = calc.chadd(self.posn, calc.steps2ch(steps)) + (isForward,)
        returnValue(newPos)
    
    @inlineCallbacks
    def _pulserStartListener(self):
        self.newPosn = yield self._movePosn()            
        yield self.pulser.signal_pulser_stopped(self.pulserStopID)
        yield self.pulser.addListener(listener = self._pulserStopListener,
                                      source=None, ID = self.pulserStopID)
                                      
    @inlineCallbacks
    def _pulserStopListener(self):
        self.posn = self.newPosn
        yield self.pulser.removeListener(self._pulserStopListener)
    
    @inlineCallbacks
    def _initializeChannels(self):
        p = self.pulser.packet()
        
        #step advance channel
        p.select_channel(self.chMap['Adv'])
        p.state(True)
        p.width(U.Value(10, 'us'))
        p.delay(U.Value(10, 'us'))
        p.mode('Normal')
        p.polarity(True)
        p.output(False)
        
        #direction channel
        p.select_channel(self.chMap['Dir'])
        p.state(True)
        p.width(U.Value(1, 'ms'))
        p.delay(U.Value(0.0, 's'))
        p.mode('Normal')
        p.polarity(True)
        p.output(False)
        
        yield p.send()
        
    @inlineCallbacks
    def _moveChannelSetup(self, steps):
        p = self.pulser.packet()
        
        #direction based on isForward
        p.select_channel(self.chMap['Dir'])
        p.polarity(steps > 0)
        
        #set step channel
        p.select_channel(self.chMap['Adv'])
        p.mode('Burst', abs(steps))
        
        yield p.send()
        
    
    @setting(100, 'Current Position', channel='w', partial='w', 
             isForward='b', returns='(wwb)')
    def current_position(self, c, channel=None, partial=0, isForward=True):
        '''Set or query current stepper position.
        Inputs:
            channel - Stepper channel number
            partial - Partial channel increment (0 - 8)
        
        Returns the current (channel, partial) tuple'''
        
        if channel is not None:
            if channel < calc.COUNT_MIN or channel > calc.COUNT_MAX:
                raise InvalidPositionError()
            if partial < 0 or partial > calc.STEPS_PER_CH:
                raise InvalidPositionError()
            
            self.posn = (channel, partial, isForward)
            
        return self.posn
        
    @setting(101, 'Running', returns = 'b')
    def running(self, c):
        p = self.pulser.packet()
        p.run_state(key='Trig')
        p.select_channel(self.chMap['Adv'])
        p.state(key='Adv')
        resp = yield p.send()
        
        isOn = all([resp[x] for x in ['Trig', 'Adv']])
        returnValue(isOn)
        
    @setting(200, 'Move To', channel='w', partial='w', returns='(ww)')
    def move_to(self, c, channel=None, partial=0):
        '''Set or query the channel to move to on the next run.
        Inputs:
            channel - Stepper channel to move to
            partial - Partial position
        
        Returns: 
        The channel that current settings will move to. (current, partial)'''
        
        if channel is not None:
            if not calc.isValidCh((channel, partial)):
                raise InvalidPositionError()
            
            deltaCh = calc.chdiff((channel, partial), self.posn[0:2])
            steps = calc.ch2steps(deltaCh)
            
            #if not moving same direction, add hysteresis
            if (steps > 0) != self.posn[2]:
                sgn = 1 if (steps >= 0) else -1
                steps += sgn * calc.STEPS_PER_CH
                
            yield self._moveChannelSetup(steps)
        
        posn = yield self._movePosn()
        returnValue(posn[0:2])
    
    @setting(201, 'Advance', steps='i')
    def advance(self, c, steps=None):
        '''Set or query steps to advance stepper.
        NOTE: Will not account for stepper hysteresis.
        Inputs:
            steps - Number of steps to advance. Negative indicates backwards move
        Returns:
            Number of steps to advance.
        '''
        
        if steps is not None:
            #verify legitmate position
            newPos = yield self._movePosn(steps)
            if not calc.isValidCh(newPos[0:2]):
                raise InvalidPositionError()
                
            yield self._moveChannelSetup(steps)
            returnValue(steps)
            
        else:
            newPos = yield self._movePosn()
            delta = calc.chdiff(newPos[0:2], self.posn[0:2])
            returnValue(calc.ch2steps(delta))
    
    @setting(300, 'Execute')
    def execute(self, c):
        '''Executes the currently programmed move. Disables any channels
        which do not exclusively belong to the stepper motor before activation
        and then enables them after move.'''
        yield self.pulser.start()
        
__server__ = StepperServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)