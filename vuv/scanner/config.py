from collections import namedtuple
import labrad.units as U

#setup constants
ADV_PER_CH = 8
DEFAULT_TRIGGER_MODE = ('Burst', 1000)
MIN_DWELL_TIME = U.Value(50, 'ms')
MCS_DISC_LEVEL = U.Value(1.5, 'V')

#scan configuration
SCAN_FIELDS = ['channels',
               'passes',
               'dwellTime',
               'chPerBin',
               'saveFolder',
               'savePattern',
               'moveOnly']

ScanConfig = namedtuple('ScanConfig', SCAN_FIELDS)

DEFAULT_SCAN_CONFIG = ScanConfig._make([0,1,1.0,1,'','',False])

#pulser channel configuration
PULSER_FIELDS =  ['chno',
                  'state',
                  'width',
                  'delay',
                  'mode',
                  'polarity',
                  'output',
                  ]

PulseConfig = namedtuple('PulseConfig', PULSER_FIELDS)

DEFAULT_PULSE_SETTINGS = ['0',
                          True,
                          U.Value(10, 'us'),
                          U.Value(0, 's'),
                          'Normal',
                          True,
                          False]

DEFUALT_PULSE_CONFIG = PulseConfig._make(DEFAULT_PULSE_SETTINGS)