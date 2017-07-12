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
from functools import partial

LEN_MIN = 4
LEN_MAX = 65536

PASS_MIN = 0
PASS_MAX = 4294967295

RAMP_MIN = 0.0
RAMP_MAX = 10.0

DISC_MIN = -1.6
DISC_MAX = 3.0

DWELL_MIN = 5e-9
DWELL_MAX = 65535

ACQ_CMDS = {'RepSum' : 'ENABLE_AUTOCLR',
            'Rep' : 'SET_MODE_ACQUIRE 1',
            'Sum' : 'SET_MODE_ACQUIRE 0'}
            
CLEAR_LINES = ['SET_MCS 0', 'CLEAR', 'SET_MCS 1', 'CLEAR']
SCAN_LINES = ['SET_MCS 1', 'START', 'WAIT']

def fmtLine(tag, spec, value):
    string = tag + ' ' + spec
    return string % value
    
def fmtUnitLine(tag, spec, unit, value):
    return fmtLine(tag, spec, value[unit])
    
def boolLine(tag, value):
    bval = '1' if value else '0'
    return '%s %s' % (tag, bval)
    
def dwellSetting(dwell):
    isInt, val = dwell
    if isInt:
        tp = ('SET_DWELL', 's')
    else:
        #need to include set to external dwell command
        #before setting threshold
        #this is kind of a hack but outputs two lines when
        #setting outputs are assumed to be single line values
        tp = ('SET_DWELL_EXTERNAL\nSET_DWELL_ETHLD', 'V')
        
    tag, unit = tp
    return '%s %f' % (tag, val[unit])

def ramp(rampVals):
    if len(rampVals) == 1:
        ramp = [rampVals[i] for i in [0,0]]
    else:
        ramp = rampVals
        
    volts = ', '.join([str(v['V']) for v in ramp])
    return 'SET_RAMP %s' % volts
        
#table accepts parameter key and returns a function
#which transforms the value to the appropriate job command
PARAM_TBL = {'Length' : partial(fmtLine, 'SET_PASS_LENGTH', '%d'),
             'Passes' : partial(fmtLine, 'SET_PRESET_PASS', '%d'),
             'AcqMode' : lambda m : ACQ_CMDS[m],
             'DiscLevel' : partial(fmtUnitLine, 'SET_DISCRIMINATOR', '%f', 'V'),
             'DiscEdge' : partial(boolLine, 'SET_DISCRIMINATOR_EDGE'),
             'Impedance' : partial(boolLine, 'SET_INPED'),
             'Ramp' : ramp,
             'Dwell' : dwellSetting,
             'ExtTrigger' : lambda t : boolLine('SET_TRIGGER', not t),
            }
                 
def parameterLines(params):
    return [PARAM_TBL[i](params[i]) for i in params.keys()]
    
def saveLine(path):
    return 'SAVE \"%s\"' % path