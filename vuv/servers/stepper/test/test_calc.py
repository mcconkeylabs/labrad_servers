import unittest
import pytest
from vuv.servers.stepper import calc
from vuv.servers.stepper.calc import *

@pytest.mark.parametrize('ch, frac, res', [(0, 4, 4), (1, 4, 12), (1, 0, 8), 
                                           (-1, 0, -8), (0, -4, -4), (-1, -2, -10)])
def test_ch2steps_calc(ch, frac, res):
    assert calc.ch2steps(ch, frac) == res
    
@pytest.mark.parametrize('steps, res', [(10, (1, 2)), (8, (1, 0)), (-10, (-1, -2)),
                                        (4, (0, 4)), (-4, (0, -4)), (4, (0, 4)),
                                        (-16, (-2, 0)), (-18, (-2, -2)),
                                        (8, (1, 0)), (10, (1, 2))])
def test_steps2ch_calc(steps, res):
    assert calc.steps2ch(steps) == res
    
@pytest.mark.parametrize('ch1, ch2, res', [((1, 0), (2, 0), (3, 0)),
                                           ((1, 5), (1, 6), (3, 3)),
                                           ((0, 4), (-1, 0), (0, -4)),
                                           ((-1, 0), (-2, -4), (-3, -4))
])
def test_chadd_calc(ch1, ch2, res):
    assert calc.chadd(ch1, ch2) == res
    
@pytest.mark.parametrize('ch1, ch2, res', [((0, 4), (0, 2), (0, 2)),
                                           ((0, -4), (1, 2), (-1, -6)),
                                           ((1, 4), (0, 4), (1, 0)),
                                           ((1, 0), (1, 4), (0, -4)),
                                           ((2, 4), (0, 6), (1, 6)),
                                           ((3,0),(0,5),(2,3)),
                                           ((4,4),(3,0),(1,4)),
                                           ((4,4),(2,2),(2,2)),
                                           ((2,2),(4,4),(-2,-2))
])
def test_chdiff_calc(ch1, ch2, res):
    resp = calc.chdiff(ch1, ch2)
    assert resp == res

class CalcTest(unittest.TestCase):
    goodChSteps = [((1, 0), 8),
                   ((2, 4), 20),
                   ((3, 2), 26)
                  ]
                  
    def test_goodChTuple_steps(self):
        for (ch, s) in self.goodChSteps:
            steps = ch2steps(ch)
            self.assertEqual(steps, s)
            
    def test_goodChSeparate_steps(self):
        for (ch, s) in self.goodChSteps:
            steps = ch2steps(*ch)
            self.assertEqual(steps, s)
            
    def test_goodSteps_ch(self):
        for (ch, s) in self.goodChSteps:
            chs = steps2ch(s)
            self.assertEqual(ch, chs)
            
    def test_overFrac_steps(self):
        chList = [((0, 9), 9),
                  ((1, 10), 18)
                 ]
                 
        for (ch, s) in chList:
            chTuple = ch2steps(ch)
            chSep = ch2steps(*ch)
            
            self.assertEqual(chTuple, s, 'Ch tuple error')
            self.assertEqual(chSep, s, 'Ch separate args error')
            
    def test_chAdd(self):
        addList = [[(1, 0), (2, 0), (3, 0)],
                   [(1, 5), (2, 4), (4, 1)],
                   [(10, 0), (11, 4), (21, 4)]
                  ]
                  
        for (c1, c2, ans) in addList:
            ret = chadd(c1, c2)
            self.assertEqual(ret, ans)
            
@pytest.mark.parametrize('ch, frac', [(4775, 0),(0,0), (1, 4), (100, 7)])
def test_good_channel_positions_true(ch, frac):
    assert isValidCh((ch, frac))
    
@pytest.mark.parametrize('ch, frac', [(4775, 1), (-1, 0), (1, 9)])
def test_bad_channel_positions_false(ch, frac):
    assert not isValidCh((ch, frac))
    
@pytest.mark.parametrize('ch1, ch2, steps', [((0, 0), (2, 0), 16),
                                             ((0, 4), (2, 0), 12),
                                             ((1, 0), (2, 4), 12),
                                             ((3, 0), (2, 0), -16)])
def test_moveSteps_forward(ch1, ch2, steps):
    s = moveSteps(ch1, ch2, True)
    assert s == steps
    
@pytest.mark.parametrize('ch1, ch2, steps', [((0, 0), (2, 0), 24),
                                             ((0, 4), (2, 0), 20),
                                             ((1, 0), (2, 4), 20),
                                             ((3, 0), (2, 0), -8)])
def test_moveSteps_backward(ch1, ch2, steps):
    s = moveSteps(ch1, ch2, False)
    assert s == steps