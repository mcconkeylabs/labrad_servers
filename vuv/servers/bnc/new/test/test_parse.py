import pytest
import labrad.units as U
from itertools import chain

import new.parse as P

BOOL_VALUES = [(True, '1'), (False, '0')]
BOOL_STRINGS = [('1', True), ('0', False), ('five', True)]

INT_VALUES = [(1, '1'), (2, '2'), (3, '3')]
INT_STRINGS = [(b, a) for (a, b) in INT_VALUES]

TYPE_LOOKUP = {bool:(P.BoolType, BOOL_VALUES, BOOL_STRINGS),
               int : (P.IntType, INT_VALUES, INT_STRINGS)}

class TestPrimitiveTypes(object):
     @pytest.mark.parametrize('pType', TYPE_LOOKUP.keys())
     @pytest.mark.parametrize('case', TYPE_LOOKUP[pType][1])
     def test_value_to_string(self, pType, case):
          parser = TYPE_LOOKUP[pType][0]()
          value, string = case
          
          assert parser.string(value) == string
          
     @pytest.mark.parametrize('pType', TYPE_LOOKUP.keys())
     @pytest.mark.parametrize('case', TYPE_LOOKUP[pType][2])
     def test_string_to_value(self, pType, case):
          parser = TYPE_LOOKUP[pType][0]()
          string, value = case
          
          assert parser.value(string) == value
          
     