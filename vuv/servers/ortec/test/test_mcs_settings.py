import pytest
import labrad.units as U
from labrad.errors import Error
    
def check_param(server, call, key, value, valid):
    handle = getattr(server, call)
    if valid:
        response = handle(None, value)
        
        assert response == value
        assert server.params[key] == value
    else:
        with pytest.raises(Error):
            handle(None, value)
    
@pytest.mark.parametrize('length, good', [(3, False), (4, True), 
                                          (65536, True), (65537, False)])
def test_pass_length(srv, length, good):
    check_param(srv, 'pass_length', 'Length', length, good)
    
@pytest.mark.parametrize('sweeps, good', [(-1, False), (0, True),
                                          (4294967295, True), (4294967296, False)])
def test_sweeps(srv, sweeps, good):
    check_param(srv, 'sweeps', 'Passes', sweeps, good)
    
@pytest.mark.parametrize('mode', ['Sum', 'Rep', 'RepSum'])
def test_good_acquisition_mode(srv, mode):
    resp = srv.acquisition_mode(None, mode)
    
    assert resp == mode
    assert srv.params['AcqMode'] == resp
    
@pytest.mark.parametrize('mode', ['nothing', 'woozlewazzle', 'sumrep'])
def test_bad_acquisition_mode(srv, mode):
    with pytest.raises(Error):
        srv.acquisition_mode(None, mode)
        
@pytest.mark.parametrize('voltage, good', [(-1.65, False), (-1.6, True),
                                           (0.0, True), (3.0, True), (3.1, False)])
def test_disc_level(srv, voltage, good):
    value = U.Value(voltage, 'V')
    check_param(srv, 'discriminator_level', 'DiscLevel', value, good)
    
@pytest.mark.parametrize('val', ['Rising', 'rising', True, 'rIsInG'])
def test_rising_edge_value(srv, val):
    resp = srv.discriminator_edge(None, val)
    assert resp == 'Rising'
    assert srv.params['DiscEdge'] is True
    
@pytest.mark.parametrize('val', ['Falling', 'falling', False, 'FaLlInG'])
def test_falling_edge_value(srv, val):
    resp = srv.discriminator_edge(None, val)
    assert resp == 'Falling'
    assert srv.params['DiscEdge'] is False
    
@pytest.mark.parametrize('val', ['Nothing', 'test', 'faling', 'rissing'])
def test_bad_edge_value(srv, val):
    with pytest.raises(Error):
        srv.discriminator_edge(None, val)
        
@pytest.mark.parametrize('imped', [U.Value(50, 'Ohm'), True])
def test_fifty_ohm_impedance(srv, imped):
    resp = srv.input_impedance(None, imped)
    assert resp == U.Value(50, 'Ohm')
    assert srv.params['Impedance'] is True
    
@pytest.mark.parametrize('imped', [U.Value(1000, 'Ohm'), False])
def test_thousand_ohm_impedance(srv, imped):
    resp = srv.input_impedance(None, imped)
    assert resp == U.Value(1e3, 'Ohm')
    assert srv.params['Impedance'] is False
    
@pytest.mark.parametrize('imped', [10, 20, 500, 1e4])
def test_bad_impedance(srv, imped):
    value = U.Value(imped, 'Ohm')
    with pytest.raises(Error):
        srv.input_impedance(None, value)
        
@pytest.mark.parametrize('time, good', [(4e-9, False), (5e-9, True),
                                        (5e-6, True), (65535, True), 
                                        (65535.5, False)])
def test_internal_dwell_time(srv, time, good):
    value = U.Value(time, 's')
    
    if good:
        string, respVal = srv.dwell(None, value)
        
        assert respVal == value
        assert srv.params['Dwell'] == (True, value)
        assert string == 'Internal'
    else:
        with pytest.raises(Error):
            srv.dwell(None, value)
    
@pytest.mark.parametrize('voltage, good', [(-1.65, False), (-1.6, True),
                                           (0.0, True), (3.0, True), (3.1, False)])
def test_external_dwell_threshold(srv, voltage, good):
    value = U.Value(voltage, 'V')
    
    if good:
        string, respVal = srv.dwell(None, value)
        
        assert respVal == value
        assert srv.params['Dwell'] == (False, value)
        assert string == 'External'
    else:
        with pytest.raises(Error):
            srv.dwell(None, value)

