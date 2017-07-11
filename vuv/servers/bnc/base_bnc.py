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

import labrad.units as U
from labrad.devices import DeviceWrapper
from labrad.errors import Error
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock
from bnc_types import TYPE_MAP, MODE_TYPES

WIDTH_MIN = 25e-9
WIDTH_MAX = 99999

DELAY_MIN = WIDTH_MIN
DELAY_MAX = WIDTH_MAX

BURST_MIN = 1
BURST_MAX = 99999

ADJ_MIN = 2.0
ADJ_MAX = 12.0

TRIGGER_MIN = 0.2
TRIGGER_MAX = 10.0

PERIOD_MIN = 1e-3
PERIOD_MAX = 99.999999
              
class BNCPulser(DeviceWrapper):
    
    def send(self, line):
        pass
    
    def query(self, line):
        pass
        
    @inlineCallbacks
    def all_ch_states(self):
        chList = yield self.channel_list()
        states = [n for (n, name) in chList]
        for (num, name) in chList:
            states[num] = yield self.state(num)
            
        returnValue(states)
    
    @inlineCallbacks
    def _param(self, tag, value=None, typeTag = 'bool', channel = None):
        #set and query a parameter
        inp, outp = TYPE_MAP[typeTag]
        prefix = '' if channel is None else ':PULSE%d' % channel
        cmd = prefix + tag
                
        if value is not None:
            setTag = '%s %s' % (cmd, inp(value))
            yield self.send(setTag)
        else:
            queryTag = cmd + '?'
            resp = yield self.query(queryTag)
            returnValue(outp(resp))
    
    @inlineCallbacks
    def channel_list(self):
        resp = yield self.query(':INST:FULL?')
        elems = resp.split(', ')
        chList = [(int(elems[i+1]), elems[i]) for i in range(0, len(elems), 2)]
        returnValue(chList)
        
    @inlineCallbacks
    def run_state(self):
        resp = yield self._param(':PULSE0:STATE', typeTag = 'bool')
        returnValue(resp)
        
    @inlineCallbacks
    def state(self, ch, enabled=None):
        '''Set and query channel state (True = Enabled)'''
        ret = yield self._param(':STATE', enabled, 'bool', ch)
        returnValue(ret)
        
    @inlineCallbacks
    def width(self, ch, width=None):
        resp = yield self._param(':WIDTH', width, 'time', ch)
        returnValue(resp)
        
    @inlineCallbacks
    def delay(self, ch, delay=None):
        resp = yield self._param(':DELAY', delay, 'time', ch)
        returnValue(resp)
        
    @inlineCallbacks
    def polarity(self, ch, activeHigh=None):
        resp = yield self._param(':POL', activeHigh, 'polarity', ch)
        returnValue(resp)
        
    @inlineCallbacks
    def output(self, ch, isAdjustable=None, adjVoltage = None):
        modeTag = ':OUTPUT:MODE'
        voltTag = ':OUTPUT:AMPL'
        
        if isAdjustable is None:
            mode = yield self._param(modeTag, None, 'output', ch)
            print 'Mode is %s' % mode
            isAdj = mode == 'Adjustable'
            
            if isAdj:
                volts = yield self._param(voltTag, None, 'voltage', ch)
            else:
                volts = None
            
            returnValue((isAdj, volts))
        else:
            mval = 'Adjustable' if isAdjustable else 'TTL'
            yield self._param(modeTag, mval, 'output', ch)
            
            if isAdjustable:
                yield self._param(voltTag, adjVoltage, 'voltage', ch)
        
    @inlineCallbacks
    def mode(self, ch, mode = None, modeParameter = None):
        if mode is not None:
            if mode not in MODE_TYPES.keys():
                raise Error('Mode type invalid.')
                
        tag = ':MODE' if ch == 0 else ':CMODE'
        modeVal = yield self._param(tag, mode, 'mode', ch)
        
        m = modeVal if mode is None else mode
        if m == 'Burst':
            param = yield self._param(':BCO', modeParameter,'int', ch)
        elif m == 'DutyCycle':
            inP = (None, None) if modeParameter is None else modeParameter
            pco = yield self._param(':PCO', inP[0], 'int', ch)
            nco = yield self._param(':OCO', inP[1], 'int', ch)
            param = (pco, nco)
        else:
            param = 0
          
        if mode is None:
            returnValue((modeVal, param))
        
    def channel_modes(self, ch):
        return MODE_TYPES.keys()
    
    @inlineCallbacks
    def trigger_period(self, period=None):
        resp = yield self._param(':PER', period, 'time', 0)
        returnValue(resp)
        
class BNCSerial(BNCPulser):
    
    @inlineCallbacks
    def connect(self, server, port, baud):
        self.server = server
        
        #usage ensures only one read/write operation at a time
        self._portLock = DeferredLock()
        
        print 'connecting to "%s" on port "%s"...' % (server.name, port)
        
        p = self.server.packet()
        p.open(port)
        p.baudrate(baud)
        p.parity('N')           #no parity bit
        p.bytesize(8L)
        p.stopbits(1L)
        p.write_line(':SYST:COMM:SER:ECHO ON')
        yield p.send()
        
        chList = yield self.channel_list()
        self.chMap = dict(chList)
        print 'connected to %s...' % server.name
        
    @staticmethod
    def _queryGood(text, tag):
        '''Check device response is complete.'''
        #if last characters aren't newline, can't be done
        if text[-2:] == '\r\n':
            lines = text.split('\r\n')
            
            #now ensure that echo and response lines present
            #lines[-3:] should be [echo, response, '']
            if len(lines) > 2:
                if lines[-3] == tag:
                    return True
        return False
        
    @inlineCallbacks
    def query(self, line):
        yield self._portLock.acquire()
        p = self.server.packet()
        ret = yield p.write_line(line)\
                     .pause(U.Value(20.0, 'ms'))\
                     .read()\
                     .send()
                      
        text = ret['read']
        while not self._queryGood(text, line):
            add = yield self.server.read()
            text = text + add
        
        self._portLock.release()
        returnValue(text.split('\r\n')[-2])
        
    @inlineCallbacks
    def send(self, line):
        yield self._portLock.run(self.server.write_line, line)
        
    @inlineCallbacks
    def all_ch_states(self):
        chns = self.chMap.keys()
        p = self.server.packet()
        p.read()                    #clear buffer
        for n in chns:
            p.write(':PULSE%d:STATE?' % n)
            p.pause(U.Value(30, 'ms'))
            p.read(key = str(n))
        resp = yield p.send()
        
        parser = TYPE_MAP['bool'][1]
        returnValue([(n, parser(resp[str(n)])) for n in chns])