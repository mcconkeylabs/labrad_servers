from itertools import ifilter, chain
from time import sleep

from labrad.devices import DeviceServer
from labrad.server import Signal, setting
from labrad.errors import Error
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.threads import callMultipleInThread

import wrapper

SLEEP_TIME = 0.5

COMM_CODES = {'S' : wrapper.BNCSerialWrapper,
              }

MODEL_CODES = {'555' : wrapper.BNC555Wrapper,
               '565' : wrapper.BNC565Wrapper,
               }

class NoChannelSelectedError(Error):
    '''No channel selected in the current context.'''
    code = 1007
    
class InvalidChannelError(Error):
    '''No such channel exists for current device.'''
    code = 1008

class BNCPulserServer(DeviceServer):
     
     name = 'BNC Pulser Server'

     onStart = Signal(501, 'signal: pulser started', 's')
     onStop = Signal(502, 'signal: pulser stopped', 's')
     
     @setting(100, 'Start')
     def start(self, ctx):
          dev = self.selectDevice(ctx)
          yield dev.command('state', True, 0)
          self.onStart(dev.name)
          
          #monitor for stop
          def monitor():
               running = True
               while running:
                    sleep(SLEEP_TIME)
                    running = yield dev.command('state', channel = 0)
               
               self.onStop(dev.name)
            
          callMultipleInThread([(monitor, [], {})])
               
     
     @setting(101, 'Stop')
     def stop(self, ctx):
          yield self.selectedDevice(ctx).command('state', False, 0)
     
     @setting(102, 'Run State', returns='b')
     def run_state(self, ctx):
          returnValue(self.selectedDevice(ctx).command('state', channel=0))
     
     @setting(103, 'Channel List', 
              returns='*(ws) : List of channel (numbers, names)')
     def channel_list(self, ctx):
          returnValue(self.run_call('channel_list', context=ctx))
     
     @setting(104, 'Select Channel', 
              channel=['w : Channel number', 
                       's : Channel name'], 
              returns='(ws) : Current channel (number, name)')
     def select_channel(self, ctx, channel=None):
          if channel is not None:
               dev = self.selectedDevice(ctx)
               ctx['bnc_channel'] = channel if type(channel) is int \
                                            else dev.channels[channel]
               
          return ctx['bnc_channel']
     
     @setting(105, 'Trigger Period', period='v[s]', returns='v[s]')
     def trigger_period(self, ctx, period=None):
          dev = self.selectedDevice(ctx)
          returnValue(dev.command('trigger_period', period))
     
     @setting(200, 'State', state='b', returns='b')
     def state(self, ctx, state=None):
          returnValue(self.run_call('state', state, ctx))
     
     @setting(201, 'Width', width='v[s]', returns='v[s]')
     def width(self, ctx, width=None):
          returnValue(self.run_call('width', width, ctx))
     
     @setting(202, 'Delay', delay='v[s]', returns='v[s]')
     def delay(self, ctx, delay=None):
          returnValue(self.run_call('delay', delay, ctx))
     
     @setting(203, 'Polarity', polarity='b', returns='b')
     def polarity(self, ctx, polarity=None):
          returnValue(self.run_call('polarity', polarity, ctx))
     
     @setting(204, 'Output Mode',
              outputType = ['b : True if Adjustable',
                            's : TTL or Adjustable'],
              voltage = 'v[V]',
              returns = '(bsv[V]) : State as bool and string with voltage')
     def output_mode(self, ctx, outputType=None, voltage=None):
          if type(outputType) is bool:
               out = 'Adjustable' if outputType else 'TTL'
          else:
               out = outputType
               
          outMode = yield self.run_call('output_mode', out, ctx)
          
          if outMode == 'Adjustable':
               volts = yield self.run_call('output_volts', voltage, ctx)
               
          returnValue((outMode, volts))
     
     @setting(205, 'Channel Mode',
              modeType = 's', parameter = ['w', '(ww)'],
              returns = ['(sw)', '(sww)'])
     def channel_mode(self, ctx, modeType = None, parameter = None):
          mode = yield self.run_call('channel_mode', modeType)
          
          val = None
          if mode == 'Divide':
               val = yield self.run_call('divide_counter', parameter)
          elif mode == 'Burst':
               val = yield self.run_call('burst_counter', parameter)
          
          returnValue((mode, val))
     
     @setting(300, 'Enable Channels', 
              channels=['*w', '*s'], enableAll='b',
              returns='*(ws)')
     def enable_channels(self, ctx, channels=None, enableAll=False):
          returnValue(self.state_list(ctx, channels, enableAll, True))
          
     
     @setting(301, 'Disable Channels',
              channels=['*w', '*s'], disableAll='b',
              returns='*(ws)')
     def disable_channels(self, ctx, channels=None, disableAll=False):
          returnValue(self.state_list(ctx, channels, disableAll, False))
     
     @inlineCallbacks
     def findDevices(self):
          #Return [(name, args, kw)] tuples where args and kw
          #are passed to the DeviceWrapper given name
          dev_list = yield self.getDeviceList()
          
          devices = []
          for (name, params) in dev_list:
               #params is ordered (device_type, name, *rest_of_params)
               server_name = params[1]
               #if server not present
               if not hasattr(self.client, server_name):
                    print 'Connect connect to device %s on server %s. Skipping'\
                          % (name, server_name)
               else:
                    #create tuple with device typecode and server 
                    initData = (params[0], self.client[server_name])
                    #group both tuples together to send to device
                    args = tuple(chain(initData, params[2:]))
                    devices += [(name, args, {})]
               
          returnValue(devices)
     
     def chooseDeviceWrapper(self, name, *args, **kw):
          #lookup the communication protocol and model classes
          #put in tuple to create type inheriting both
          #the type code is arranged 'CMOD' where C is the comm type
          # S = Serial, G = GPIB
          # MOD is the model number (eg. 555 or 565)
          types = (COMM_CODES[args[0][0]], MODEL_CODES[args[0][1:]])
          
          #using the print statement for the class name ensure no
          #name clashes. it doesn't affect anything and avoids possible bugs
          return type('BNCDevice%s' % name, types, {})
          
     
     def initContext(self, ctx):
          super(BNCPulserServer, self).initContext(ctx)
          ctx['bnc_channel'] = 1
          
     @inlineCallbacks
     def run_call(self, command_tag, value=None, context=None):
          dev = self.selectedDevice(context)
          ch = context['bnc_channel']
          
          yield dev.command(command_tag, value, ch)
          resp = yield dev.command(command_tag, None, ch)
          returnValue(resp)
     
     @inlineCallbacks
     def state_list(self, ctx, channels, onAll, state):
          #this messy function prevents diplication of enable/disable patterns
          #for multiple channels
          dev = self.selectedDevice(ctx)
          if onAll:
               chs = dev.channels.values()
          elif channels is not None:
               if type(channels[0]) is str:
                    chs = [dev.channels[x] for x in channels]
               else:
                    chs = channels
          else:
               chs = []

          #making the list empty (and False) for non-query prevents a couple 
          #extra logic checks by just doing this test here
          if chs:
               for ch in chs:
                    yield dev.command('state', state, ch)
          
          states = {}
          for ch in dev.channels.values():
               states[ch] = yield dev.command('state', channel=ch)
               
          returnValue(states)
     
     def c2i(self, ctx):
          '''Convert context to device and channel data'''
          dev = self.selectedDevice(ctx)
          ch = ctx['bnc_channel']
          return (dev, ch)
     
     @inlineCallbacks
     def getDeviceList(self):
          reg = self.client.registry
          
          p = reg.packet()
          p.cd(self.reg_directory(), True)
          p.dir()
          resp = yield p.send()
          dirs, keys = resp['dir']
          
          p = reg.packet()
          for k in keys:
               p.get(k, key=k)
          resp = yield p.send()
          
          dev_list = [(k, resp[k]) for k in keys]
          returnValue(dev_list)
          
     def reg_directory(self):
          pass
     
     @classmethod
     def type_lookup(cls, type_key):
          pass