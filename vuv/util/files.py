import os, stat, re
import itertools as I
from tempfile import mkdtemp
from labrad.errors import Error

PATTERN_REGEX_STRING = r'([\w]*)\*([\w]*)(\.[\w]+)'
PATTERN_REGEX = re.compile(PATTERN_REGEX_STRING)

DEFAULT_PATH = os.path.join(os.path.expanduser('~'), 'data')

class FileGenerator(object):
     PATTERN_REGEX = re.compile(PATTERN_REGEX_STRING)
     
     def __init__(self, directory=DEFAULT_PATH, pattern='*.txt'):
          self.directory = directory
          self.pattern = pattern
     
     @property
     def directory(self):
          return self._dir
     
     @directory.setter
     def directory(self, value):
          if not self.is_valid_dir(value):
               raise Error('Invalid directory path')
          self._dir = value
     
     @property
     def pattern(self):
          return self._pattern_sub('*')
     
     @pattern.setter
     def pattern(self, value):
          match = PATTERN_REGEX.match(value)
          if not match:
               raise Error('Invalid file pattern.')
          
          self._pre, self._mid, self._suff = match.groups()
          
          reg_str = r'{}([\d]+){}{}'.format(self._pre, self._mid, self._suff)
          self._regex = re.compile(reg_str)
          
          
     def _pattern_sub(self, val):
          return ''.join([self._pre, val, self._mid, self._suff])
     
     def generate_path(self):
          #regex all the files in the directory and find all that match 
          #the current pattern
          matches = list(I.ifilter(lambda x: x, 
                              map(self._regex.match, os.listdir(self._dir))))
                    
          #any stops at first true, returned for first item in list
          if matches == []:
               fnum = 1
          else:
               #pull the number from the file name and then set
               #the generated number to be one more than the max
               nums = map(lambda m: int(m.group(1)), matches)
               fnum = max(map(lambda m: int(m.group(1)), list(matches)))+1
               print nums

          return self._pattern_sub(str(fnum))
     
     @classmethod
     def is_valid_dir(cls, path):
          if os.path.isdir(path):
               return os.access(path, os.W_OK)
          else:
               try:
                    os.mkdir(path)
                    return True
               except Exception:
                    return False
     
     @staticmethod
     def is_valid_pattern(pattern):
          return bool(PATTERN_REGEX.match(pattern))