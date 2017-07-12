from parse import *

CHANNEL_COMMANDS = {'state' : (':STATE', BoolType()),
                    'width' : (':WIDTH', ValueType('s')),
                    'delay' : (':DELAY', ValueType('s')),
                    'polarity' : (':POLARITY', MappedType(POLARITY_TYPES)),
                    'output_mode' : (':OUTPUT:MODE', MappedType(OUTPUT_TYPES)),
                    'output_volts' : (':OUTPUT:AMPL', ValueType('V')),
                    'channel_mode' : (':CMODE', MappedType(CMODE_TYPES)),
                    'burst_counter' : (':BCO', IntType()),
                    'divide_counter' : (':DCO', IntType()),
                    'off_counter' : (':OCO', IntType()),
                    }

CH_SET = set(CHANNEL_COMMANDS.keys())

SYSTEM_COMMANDS = {'trigger_period' : (':PULSE0:PERIOD', ValueType('s')),
                   'channel_list' : (':INST:FULL?', ChannelListType())}