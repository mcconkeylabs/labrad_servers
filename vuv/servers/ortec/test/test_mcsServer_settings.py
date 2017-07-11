import pytest
from labrad.errors import Error

@pytest.mark.parametrize('length, valid',
                         [(-1, False),
                          (0, False),
                          (4, True),
                          (500, True),
                          (10000, True),
                          (65536, True),
                          (100000, False)
                         ])
def test_pass_length_input(mcs, context, length, valid):
    if valid:
        ret = mcs.pass_length(context, length)
        assert ret == mcs.mcsSettings['PassLength']
    else:
        with pytest.raises(Error):
            mcs.pass_length(context, length)

#@pytest.mark.parametrize('sweeps', 'valid',
#                         [(-5, False), (0, True), (5, True),
#                          (1000, True), (4294967295, True),
#                          (5294967295,False)])
#def test_sweeps_input(mcs, context, sweeps, valid):
#    if valid:
#        ret = mcs.sweeps(context, sweeps)
#        assert ret == mcs.mcsSettings['Sweeps']
#    else:
#        with pytest.raises(Error):
#            mcs.sweeps(context, sweeps)
            
