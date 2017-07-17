import pytest

from vuv.util.stepper import StepperPosition as SP

class TestMathOps(object):
     @pytest.mark.parametrize('inval,outv', [((1, 9), (2, 1)),
                                         ((0, 8), (1, 0)),
                                         ((0, 24), (3, 0)),
                                         ((10, 18), (12, 2))])
     def test_fraction_to_channel_conversion(self, inval, outv):
          pos = SP(*inval)
          
          assert (pos.channel, pos.fraction) == outv
          
     @pytest.mark.parametrize('val', range(5))
     def test_position_equality(self, val):
          x = SP(val, val)
          y = SP(val, val)
          
          assert x == y
          
     @pytest.mark.parametrize('v1, v2', [((0, 7), (0, 3)),
                                         ((1, 0), (0, 7)),
                                         ((0, -6), (-1, 0)),
                                         ((2, 0), (1, 5)),
                                         ((2, 0), (1, 0)),
                                         ((1, 4), (0, 10))])
     def test_less_than_works(self, v1, v2):
#          x, y = map(lambda (a, b): SP(a, b), [v1, v2])
          x, y = SP(*v1), SP(*v2)
          assert x > y
          
     @pytest.mark.parametrize('a,b,res', [((1, 0), (2, 0), (3, 0)),
                                          ((0, 6), (2, 0), (2, 6)),
                                          ((1, 0), (2, 9), (4, 1)),
                                          ((-1, 0), (2, 0), (1, 0)),
                                          ((-1, -4), (0, -4), (-2, 0)),
                                          ((-1, 0), (-2, 0), (-3, 0)),
                                          ((0, 0), (0, -6), (0, -6)),
                                          ((0, 0), (0, 0), (0, 0)),
                                          ((0, -6), (-1, -9), (-2, -7)),])
     def test_addition_works(self, a, b, res):
          x, y = SP(*a), SP(*b)
          exp = SP(*res)
          
          result = x + y
          print '{0}, {1}'.format(result.channel, result.fraction)
          
          assert exp == result
          
     @pytest.mark.parametrize('a,b,res', [((1, 0), (2, 0), (-1, 0)),
                                          ((1, 0), (-2, 0), (3, 0)),
                                          ((1, 4), (2, 0), (0, -4)),])
     def test_subtraction_works(self, a, b, res):
          x, y = SP(*a), SP(*b)
          exp = SP(*res)
          
          assert exp == (x - y)