import pytest
from vuv.servers.ortec import jobs
import labrad.units as U
from itertools import izip
    
TEST_PARAMS = [('Length', 1024),
               ('Passes', 1),
               ('AcqMode', 'RepSum'),
               ('DiscLevel', U.Value(0.5, 'V')),
               ('DiscEdge', 'Rising'),
               ('Impedance', True),
               ('Ramp', [U.Value(0.0, 'V'), U.Value(1.0, 'V')]),
               ('Dwell', (False, U.Value(0.5, 'V'))),
               ('ExtTrigger', False)
              ]
              
TEST_JOB = ['SET_PASS_LENGTH 1024',
            'SET_PRESET_PASS 1',
            'ENABLE_AUTOCLR',
            'SET_DISCRIMINATOR %f' % 0.5,
            'SET_DISCRIMINATOR_EDGE 1',
            'SET_INPED 1',
            'SET_RAMP 0.0, 1.0',
            'SET_DWELL_EXTERNAL\nSET_DWELL_ETHLD %f' % 0.5,
            'SET_TRIGGER 1'
           ]
           
@pytest.mark.parametrize('key, value, line',\
                         izip([x[0] for x in TEST_PARAMS],\
                         [x[1] for x in TEST_PARAMS],\
                         TEST_JOB))
def test_parameter_lines(key, value, line):
    response = jobs.PARAM_TBL[key](value)    
    assert response == line
          
def test_parameterLines_reponse_good():
    response = jobs.parameterLines(dict(TEST_PARAMS))
    
    #assert over all items
    for line in response:
        assert line in TEST_JOB
        
def test_internal_dwell_setting():
    resp = jobs.dwellSetting((True, U.Value(5.0, 'ms')))
    string = 'SET_DWELL %f' % 0.005
    assert resp == string
    
def test_external_dwell_setting():
    resp = jobs.dwellSetting((False, U.Value(2.5, 'V')))
    string = 'SET_DWELL_EXTERNAL\nSET_DWELL_ETHLD %f' % 2.5
    assert resp == string
    
def test_save_path_line():
    resp = jobs.saveLine('test.file')
    assert resp == 'SAVE \"test.file\"'