# Copyright (C) 2015  Jeffery Dech
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
vuv.serial_device
Superclass of serial device servers.
"""

from labrad import types as T, constants as C
from labrad.devices import DeviceWrapper
from labrad.gpib import ManagedDeviceServer
from labrad.server import setting

from twisted.internet.defer import inlineCallbacks, returnValue

class SerialDeviceWrapper(DeviceWrapper):
    """A wrapper for a serial device."""
    
    @inlineCallbacks
    def connect(self, ser, portName):
        self.serial = ser #wrapper for the serial device server
        self.portName = portName
        self._context = ser.context()
        self._timeout = T.Value(C.TIMEOUT, 's')
        
        pass
    
    def _packet(self):
        return self.serial.packet(context = self._context)
        
    @inlineCallbacks
    def write(self, s, timeout=None):
        p = self._packet()
        if timeout is not None:
            p.timeout(timeout)
        p.write(s)
        if timeout is not None:
            p.timeout(self._timeout)
        response = yield p.send()
        returnValue(response.write)
        
    @inlineCallbacks
    def write_line(self, line, timeout=None):
        p = self._packet()
        if timeout is not None:
            p.timeout(timeout)
        p.write_line(line)
        if timeout is not None:
            p.timeout(self._timeout)
        response = yield p.send()
        returnValue(response.write_line)
        
    @inlineCallbacks
    def read(self, nbytes=None, timeout=None):
        """Read a string from the serial device."""
        
        p = self._packet()
        if timeout is not None:
            p.timeout(timeout)
        p.read(nbytes)
        if timeout is not None:
            p.timeout(self._timeout)
        response = yield p.send()
        returnValue(response.read)
        
    @inlineCallbacks
    def read_line(self, timeout=None):
        """Read a line fromt the serial device.
        
        Strips LFs and CRs.
        """
        
        p = self._packet()
        if timeout is not None:
            p.timeout(timeout)
        p.read_line()
        if timeout is not None:
            p.timeout(self._timeout)
        response = yield p.send()
        returnValue(response.read_line)
        
    @inlineCallbacks
    def timeout(self, seconds):
        """Set the timeout for this serial device."""
        
        self._timeout = T.Value(seconds, 's')
        p = self._packet()
        p.timeout(self._timeout)
        yield p.send()
        
        
    def initialize(self):
        """Called when first connecting to the device.
        
        Override this in subclasses to perform any device
        specific initialization and to synchronize the
        wrapper state with the device state.
        """
        
    
        
    
class SerialManagedServer(ManagedDeviceServer):
    """Server for a serial device.
    
    Similar to labrad.gpib.GPIBManagedServer, creates a 
    SerialDeviceWrapper for each device it finds that is
    appropriately named. Provides standard settings for
    listing devices, selecting a device based on the current
    context, and refreshing device lists. Also provides support
    to read to, write to and query the serial port directly.
    """
    
    name = 'Generic Serial Device Server'
    deviceManager = 'Device Manager'
    deviceName = 'Generic Serial Device'
    deviceWrapper = SerialDeviceWrapper
    
    #
    #server settings
    #
    
    @setting(1001, 'Serial Write Line', line='s', 
             timeout='v[s]', returns='')
    def serial_write(self, c, line, timeout=None):
        """Write a line to the device over RS-232"""
        return self.selectedDevice(c).write_line(line, timeout)
        
    @setting(1002, 'Serial Read Line', timeout='v[s]', returns='')
    def serial_read(self, c, timeout=None):
        """Read a line from the device over RS-232"""
        return self.selectedDevice(c).read_line(timeout)
        
    