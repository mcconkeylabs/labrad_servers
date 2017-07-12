import labrad.units as U

MODE_TYPES = {'Normal' : 'NORM',
              'Single' : 'SING',
              'Burst' : 'BURS',
              'DutyCycle' : 'DCYC'}

CMODE_TYPES = {'Normal' : 'NORM',
              'Single' : 'SING',
              'Burst' : 'BURS',
              'Divide' : 'DIVI'}

OUTPUT_TYPES = {'TTL' : 'TTL',
                'Adjustable' : 'ADJ',
                '35V' : '35V'}

POLARITY_TYPES = {True : 'NORMAL',
                  False : 'INVERTED'}

class BNCTypeParser(object):    
     def value(self, string):
          pass

     def string(self, value):
          pass
     
     def value_from_response(self, resp):
          #clip off the command, value comes after the space
          return self.value(resp.split(' ')[1])
     
class BoolType(BNCTypeParser):
     @classmethod
     def value(cls, string):
          return bool(int(string))
     
     @classmethod
     def string(cls, value):
          return str(int(value))
     
class IntType(BNCTypeParser):
     @classmethod
     def value(cls, string):
          return int(string)
     
     @classmethod
     def string(cls, value):
          return str(value)
     
class ValueType(BNCTypeParser):
     def __init__(self, unit):
          self.unit = unit
          
     def value(self, string):
          return U.Value(float(string), self.unit)
     
     def string(self, value):
          return value[self.unit]
     
class MappedType(BNCTypeParser):
     def __init__(self, table):
          self.stbl = table
          self.vtbl = {v : k for (k, v) in table.iteritems()}
          
     def value(self, string):
          return self.stbl[string]
     
     def string(self, value):
          return self.vtbl[value]
     
class ChannelListType(BNCTypeParser):
     @classmethod
     def value(cls, string):
          elems = string.split(', ')
          return [(elems[i], int(elems[i+1])) 
                  for i in range(0, len(elems), 2)]
         
     @classmethod
     def string(cls, value):
          strs = ['%s, %d' % (a, b) for (a, b) in value]
          return ', '.join(strs)