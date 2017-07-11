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
    
    def write(self, line):
        pass
    
    def read(self):
        pass
    
    def readWrite(self, line):
        pass
        
    @inlineCallbacks
    def all_ch_states(self):
        chList = yield self.channel_list()
        states = [n for (n, name) in chList]
        for (num, name) in chList:
            states[num] = yield self.state(num)
            
        returnValue(states)
    
    @inlineCallbacks
    def _setParam(self, tag, value=None, typeTag = 'bool', channel = None):
        #set and query a parameter
        inp, outp = TYPE_MAP[typeTag]
        prefix = '' if channel is None else ':PULSE%d' % channel
        cmd = prefix + tag
                
        if value is not None:
            setTag = '%s %s' % (cmd, inp(value))
            yield self.write(setTag)
        else:
            query = cmd + '?'
            yield self.write(query)
            
            resp = yield self.read()
            print resp
            #keep reading until echo line
            while resp != query:
                resp = yield self.read()
                print resp
            #now get response
            #now get response
            resp = ''
            ret = yield self.read()
            while ret != '':
                resp = resp + ret
                ret = yield self.read()
            print 'rest %s' % resp
            returnValue(outp(resp))
    
    @inlineCallbacks
    def channel_list(self):
        yield self.write(':INST:FULL?')
        resp = yield self.read()
        print resp
        #keep reading until echo line
        while resp != ':INST:FULL?':
            resp = yield self.read()
            print resp
            
        #now get response
        resp = ''
        ret = yield self.read()
        while ret != '':
            resp = resp + ret
            ret = yield self.read()
        print 'rest %s' % resp
        elems = resp.split(', ')
        chList = [(int(elems[i+1]), elems[i]) for i in range(0, len(elems), 2)]
        returnValue(chList)
        
    @inlineCallbacks
    def run_state(self):
        resp = yield self.readWrite(':SYST:STATE')
        stateStr = resp.split(' ')[0]
        returnValue(stateStr == 'ACTIVE')
        
    @inlineCallbacks
    def state(self, ch, enabled=None):
        '''Set and query channel state (True = Enabled)'''
        ret = yield self._setParam(':STATE', enabled, 'bool', ch)
        returnValue(ret)
        
    @inlineCallbacks
    def width(self, ch, width=None):
        resp = yield self._setParam(':WIDTH', width, 'time', ch)
        returnValue(resp)
        
    @inlineCallbacks
    def delay(self, ch, delay=None):
        resp = yield self._setParam(':DELAY', delay, 'time', ch)
        returnValue(resp)
        
    @inlineCallbacks
    def polarity(self, ch, activeHigh=None):
        resp = yield self._setParam(':POL', activeHigh, 'polarity', ch)
        returnValue(resp)
        
    @inlineCallbacks
    def output(self, ch, isAdjustable=None, adjVoltage = None):
        adjText = 'Adjustable' if isAdjustable else 'TTL'
        adj = yield self._setParam(':OUTPUT:MODE', adjText, 'output', ch)
        
        if adj is not None:
            isAdj = adj == 'Adjustable'
            if isAdj:
                volts = yield self._setParam(':OUTPUT:AMPL', adjVoltage,
                                             'voltage', ch)
            else:
                volts = U.Value(0.0, 'V')
                
            returnValue((isAdj, volts))
        
    @inlineCallbacks
    def mode(self, ch, mode = None, modeParameter = None):
        tag = ':MODE' if ch == 0 else ':CMODE'
        modeVal = yield self._setParam(tag, mode, 'mode', ch)
        
        if modeVal is not None:
            if modeVal == 'Burst':
                param = yield self._setParam(':BCO', modeParameter,'int', ch)
            elif modeVal == 'DutyCycle':
                pco = yield self._setParam(':PCO', modeParameter[0], 'int', ch)
                nco = yield self._setParam(':NCO', modeParameter[1], 'int', ch)
                param = (pco, nco)
            else:
                param = 0
                
            returnValue((modeVal, param))
        
    def channel_modes(self, ch):
        return MODE_TYPES.keys()
    
    @inlineCallbacks
    def trigger_period(self, period=None):
        resp = yield self._setParam(':PER', period, 'time', 0)
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
        
    @inlineCallbacks
    def readWrite(self, cmd):
        yield self._portLock.acquire()
        p = self.server.packet()
        p.read()                    #clear buffer
        p.write_line(cmd)
        p.pause(U.Value(40.0, 'ms'))
        p.read_line()
        resp = yield p.send()
        self._portLock.release()
        
        print 'RW CLEAR: %s' % resp['read']
        returnValue(resp['read_line'])
        
    @inlineCallbacks
    def write(self, line):
        yield self._portLock.run(self.server.write_line, line)
        
    @inlineCallbacks
    def read(self):
        resp = yield self._portLock.run(self.server.read_line)
        returnValue(resp)
        
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