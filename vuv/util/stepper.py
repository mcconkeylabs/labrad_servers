from functools import total_ordering

CH_FRAC = 8

@total_ordering
class StepperPosition(object):
     def __init__(self, channel=0, fraction=0, forward=True):
          self._ch = 0
          self._frac = 0
          
          self.set_posn(channel, fraction)
          self.direction = forward
          
     @property
     def channel(self):
          return self._ch
     
     @channel.setter
     def channel(self, value):
          self._ch = int(value)
     
     @property
     def fraction(self):
          return self._frac
     
     @fraction.setter
     def fraction(self, value):
          pf = int(value)
          self._ch += pf / CH_FRAC
          self._frac = pf % CH_FRAC
          
     def set_posn(self, channel, frac):
          self.channel = channel
          self.frac = frac
          
     def __eq__(self, other):
          return (self._ch == other._ch) and (self._frac == other._frac)
     
     def __lt__(self, other):
          if self._ch < other._ch:
               return True
          elif self._ch == other._ch:
               return self._frac < other._frac
          else:
               return False
          
     def __add__(self, other):
          plus = StepperPosition.toinc(self._ch, self._frac) + \
                    StepperPosition.toinc(other._ch, other._frac)
          ch, frac = StepperPosition.frominc(plus)
          return StepperPosition(ch, frac)
     
     def __sub__(self, other):
          minus = StepperPosition.toinc(self._ch, self._frac) - \
                    StepperPosition.toinc(other._ch, other._frac)
          ch, frac = StepperPosition.frominc(minus)
          return StepperPosition(ch, frac)
          
     @staticmethod
     def toinc(ch, frac):
          return (ch * CH_FRAC) + frac
     
     @staticmethod
     def frominc(inc):
          ch = inc / CH_FRAC
          frac = inc % CH_FRAC
          return (ch, frac)
               