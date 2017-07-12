from itertools import chain, izip_longest
from time import sleep
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue
from labrad.devices import DeviceWrapper
from labrad.errors import Error
from labrad.units import Value
from cmd import *

ECHO_CMD = ':SYST:COMM:SER:ECHO ON'
BYTE_SIZE = 8L
STOP_BITS = 1L
PARITY = 'N'
SERIAL_WAIT = 0.2

class InvalidCommandError(Error):
     '''Invalid BNC Pulser Command.'''
     code = 1101
     
class NoChannelNumberError(Error):
     '''Channel number not supplied.'''
     code = 1102

class BNCPulserWrapper(DeviceWrapper):
     
     #dict of channels {name : number}
     #initialize in connect function of subclass
     channels = {}
     
     #list of accpetable mode strings
     mode_types = []
     
     def connect(self, devType, server, *args):
          '''Implement in subclass. Initialize any server specific settings.
          devType - internal use
          server - handle to the server needed for communication
          args - list of any other parameters from registry
          '''
     
     @inlineCallbacks
     def query(self, cmd_string, get_response=True):
          """Implement this in the subclass. Send the cmd_string to the 
          device and if get_response is True, return the response string."""
          
     @inlineCallbacks
     def channel_mode(self, channel, mode=None, parameter=None):
          """Implement in subclass. Should accept a possible mode type
          and possible parameter. The channel should be set to the mode
          specified if the mode type is provided and is responsible for
          checking parameter types match the mode but it is guaranteed to
          be an integer or a tuple (int, int). 
          
          The method should return the type and parameters as (str, int) or
          (str, int, it)"""
     
     @inlineCallbacks
     def command(self, command, value=None, channel=None):
          """
          Executes the command command with possible input value.
          
          value is the possible input value. Accepts actual value of that command type.
          
          channel can be given if requried for the command. 
          Throws exception if command not found, input invalid or channel
          not given if required.
          
          get_response returns a formatted response value if True.
          
          Returns a properly parsed output value which will match input type.
          """
          
          cmd, parser = self.command_list[command]
          
          #since the tests are called multiple times, create variables
          isCh, isVal = command in CH_SET, value is None
          
          if isCh and channel is None:
               raise NoChannelNumberError()
               
          #for channel commands we need a :PULSE# prefix
          prefix = '' if not isCh else ':PULSE%d' % channel
          #if we're getting a value, 
          suffix = '?' if isVal else ' ' + parser.string(value)
          string = ''.join([prefix, cmd, suffix])
          
          returnValue(self.query(string, get_response = not isVal))
          
class BNCSerialWrapper(BNCPulserWrapper):
     @inlineCallbacks
     def connect(self, devType, server, port, baud):
          self.ser = server
          self.lock = DeferredLock()
          
          p = self.ser.packet()
          p.open(port)
          p.baudraude(baud)
          p.parity(PARITY)
          p.bytesize(BYTE_SIZE)
          p.stopbits(STOP_BITS)
          p.write_list(ECHO_CMD)
          yield p.send()
          
          ch_list = yield self.command('channel_list')
          self.channels = dict(ch_list)
          
     @inlineCallbacks
     def query(self, cmd_string, get_response):
          yield self.lock.acquire()
          
          p = self.server.packet()
          ret = yield p.write_line(cmd_string)\
                       .pause(Value(20.0, 'ms'))\
                       .read()\
                       .send()
  
          #This is a really bad way of checking for the echo
          text = ret['read']
          while not self._queryGood(text, cmd_string):
               add = yield self.server.read()
               text = text + add
          #################

          self.lock.release()
          
          if get_response: 
               returnValue(text.split('\r\n')[-2]) 
          else: 
               yield

class BNC555Wrapper(BNCPulserWrapper):
     @inlineCallbacks
     def channel_mode(self, channel, mode=None, parameter=None):
          pass
     
class BNC565Wrapper(BNCPulserWrapper):
     @inlineCallbacks
     def channel_mode(self, channel, mode=None, parameter=None):
          pass