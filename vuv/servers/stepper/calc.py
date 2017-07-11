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

STEPS_PER_CH = 8.0
COUNT_MIN = 0
COUNT_MAX = 4775

def ch2steps(channel, fraction=0):
    if type(channel) is tuple:
        ch = channel[0]
        fraction = channel[1]
    else:
        ch = channel
        
    return int(ch * STEPS_PER_CH) + fraction
    
def steps2ch(steps):
    ch = int(steps / STEPS_PER_CH)
    frac = int(steps - (ch * STEPS_PER_CH))
    return (ch, frac)
    
def chadd(ch1, ch2):
    '''Add two channel values together
    Inputs: ch1, ch2   Tuples containing channel and fraction    
    '''
    N1, N2 = map(ch2steps, [ch1, ch2])
    return steps2ch(N1 + N2)

def chdiff(ch1, ch2):
    '''Subtract two channel values ch1 - ch2
    Inputs: ch1, ch2    Tuples containing channel and fraction
    '''
    N1, N2 = map(ch2steps, [ch1, ch2])
    return steps2ch(N1 - N2)            
    
def isValidCh(ch):
    channel, frac = ch #steps2ch(ch2steps(ch))
    if channel < COUNT_MIN or channel > COUNT_MAX:
        return False
    elif channel == COUNT_MAX and frac != 0:
        return False
    else:
        if frac < 0 or frac > STEPS_PER_CH:
            return False
        else:
            return True
            
def moveSteps(ch1, ch2, isForward):
    '''Determine number of steps to move from current position.
    Inputs:
    ch1       Current channel position (full, fraction)
    ch2       New channel position (full, fraction)
    isForward True if stepper currently moving forward
    '''
    
    s1, s2 = map(ch2steps, [ch1, ch2])
    steps = s2 - s1
    pos = steps > 0
    
    #determine if hysteresis needs to be added
    #if not moving, return
    if steps == 0:
        return 0
    elif pos == isForward:
            return steps
    else:
        sgn = 1 if pos else -1
        hys = sgn * int(STEPS_PER_CH)
        return steps + hys