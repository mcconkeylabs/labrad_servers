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

def passLength(length):
    return 'SET_PASS_LENGTH %d' % length
    
def sweeps(sweepN):
    return 'SET_PRESET_PASS %d' % sweepN
    
def dwell(dwellVal):
    internal, param = dwellVal
    
    if internal:
        return 'SET_DWELL_TIME %f' % param['s']
    else:
        lines = ['SET_DWELL_EXTERNAL',
                 'SET_DWELL_ETHLD %f' % param['V']]
        return lines
        
def trigger(ext):
    return 'SET_TRIGGER %d' % int(ext)
    
def discrim(dval):
    edge, thld = dval
    lines = ['ENABLE_DISCRIMINATOR',
             'SET_DISCRIMINATOR_EDGE %d' % int(edge),
             'SET_DISCRIMINATOR %f' % thld['V']]
    return lines
    
def imped(imval):
    return 'SET_INPED %d' % int(imval)
    
def ramp(rampvolts):
    vals = [str(x['V']) for x in rampvolts]
    return 'SET_RAMP %s' % ', '.join(vals)
    
def acq(mode):
    if mode == 'Rep':
        return 'SET_MODE_ACQUIRE 1'
    elif mode == 'Sum':
        return 'SET_MODE_ACQUIRE 0'
    else:
        return 'ENABLE_AUTOCLR'

DEFAULTS = {'PassLength' : 1024,
            'Sweeps' : 1,
            'IntDwell' : (False, U.Value(1.2, 'V')),
            'ExtTrigger' : True,
            'DiscRise' : (True, U.Value(0.5, 'V')),
            'Imp1K' : False,
            'Ramp' : [U.Value(0.0, 'V'),
                      U.Value(0.0, 'V')],
            'AcqMode' : 'RepSum',
           }
           
SETTING_PARSE = {'PassLength' : passLength,
                 'Sweeps' : sweeps,
                 'IntDwell' : dwell,
                 'ExtTrigger' : trigger,
                 'DiscRise' : discrim,
                 'Imp1K' : imped,
                 'Ramp' : ramp,
                 'AcqMode' : acq
                 }
                 
def scanJobLines(settings = DEFAULTS, savePath = None):
    jobLines = ['SET_MCS 1']
    
    for k, v in settings.items():
        line = SETTING_PARSE[k](v)
        if type(line) is list:
            jobLines = jobLines + line
        else:
            jobLines.append(line)
        
    jobLines = jobLines + ['CLEAR', 'START', 'WAIT']
    if savePath is not None:
        jobLines.append('SAVE \"%s\"' % savePath)
    jobLines.append('QUIT')
    
    return ['%s\n' % x for x in jobLines]