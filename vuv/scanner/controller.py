import labrad.units as U
from threading import Thread
from time import sleep

import config

PULSER_TAG = 'Pulser Server'
PULSER_DEV = 'Pulser Device'
CHMAP_TAG = 'Channel Map'

CH_LIST = ['MCS Start', 'MCS Advance', 'Stepper Advance', 'Stepper Direction']
MOVE_CHS = ['Stepper Advance', 'Stepper Direction']

#Channel specific default options for pulser channels
#These values will be overridden when setting up the defaults
#via gen_default_pulse_settings
PULSE_DELAY = U.Value(1, 'ms')
START = {'mode' : 'Single',}
MCS_ADV = {'delay' : PULSE_DELAY,
          }
STEP_ADV = {'delay' : PULSE_DELAY,}
STEP_DIR = {'width' : PULSE_DELAY * 4,}
CH_DEFAULTS_MAP = {'MCS Start' : START,
                   'MCS Advance' : MCS_ADV,
                   'Stepper Advance' : STEP_ADV,
                   'Stepper Direction' : STEP_DIR,
                   }


class LabradController(object):
     reg_path = ['','VUV', 'gui']
     
     def __init__(self, cxn):
          self.cxn = cxn
          self.reg_init()
          self.config = config.DEFAULT_CONFIG
          self.settings = self.gen_default_pulse_settings()
          
     @property
     def scan_config(self):
          return self.config
     
     @scan_config.setter
     def scan_config(self, configuration):
          #add verification code
          self.config = configuration
          
     def state(self):
          pass
     
     def abort(self):
          pass
     
          
     def reg_init(self):
          reg = self.cxn.registry
          
          p = reg.packet()
          p.cd(self.reg_path)
          p.get(PULSER_TAG, key='pulser')
          p.get(PULSER_DEV, key='device')
          p.get(CHMAP_TAG, key='chs')
          resp = p.send()
          
          self.pulser = self.cxn[resp['pulser']]
          self.pulser.select_device(resp['device'])
          
          self.ch_map = dict(resp['chs'])
          
     def init_pulser(self):
          pulses = self.gen_default_pulse_settings()
          
          p = self.pulser.packet()
          
          p.select_channel(0)
          p.mode(*config.DEFAULT_TRIGGER_MODE)
          
          for data in pulses.itervalues():
               self.write_packet_data(p, data)
          
          p.send()
          
     def set_move(self, settings=None):
          run = self.config if settings is None else settings
          pulses = self.config2pulse(run)
          
          p = self.pulser.packet()
               
          #configure master trigger settings
          p.select_channel(0)
          p.mode('Burst', abs(run.channels))
          p.trigger_period(U.Value(run.dwellTime, 's'))
          
          #set individual pulse channels
          for data in pulses.itervalues():
               self.write_packet_data(p, data)
          
          p.send()
     
     def gen_default_pulse_settings(self):
          config = dict({k : config.DEFUALT_PULSE_CONFIG for k in CH_LIST})
          for (k, elems) in CH_DEFAULTS_MAP.iteritems():
               elems['chno'] = self.ch_map[k]
               config[k] = config[k]._replace(**elems)
          
          return config
     
     def config2pulse(self, settings):     
          pulse = self.gen_default_pulse_settings()
          
          steps = abs(settings.channels) * config.ADV_PER_CH
          #duty cycle for MCS for every Nth, 1 on, N-1 off
          dcyc = (1, settings.ratio * config.ADV_PER_CH - 1)
          
          
          replacements = {'Stepper Direction' : {'polarity' : settings.channels >= 0},
                          'Stepper Advance' : {'mode' : ('Burst', steps)},
                          'MCS Advance' : {'mode' : ('DutyCycle', dcyc)}
                         }
          
          for (ch, data) in replacements.iteritems():
               pulse[ch] = pulse[ch]._replace(**data)
               
          return pulse
     
     @classmethod
     def write_packet_data(cls, p, data):
          p.select_channel(data.chno)
          p.state(data.state)
          p.width(data.width)
          p.delay(data.delay)
          p.mode(*data.mode)
          p.polarity(data.polarity)
          p.output(data.output)