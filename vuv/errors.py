# -*- coding: utf-8 -*-
"""
Created on Tue Apr 05 22:02:33 2016

@author: Jeff
"""

from labrad.errors import Error

class InvalidParameterError(Error):
    code = 1500
    
    def __init__(self, parameter = None, value = None):
        self.parameter = parameter
        self.value = value

class OutOfBoundsError(InvalidParameterError):
    '''The parameter is out of bounds.'''
    code = 1501
    
    def __init__(self, parameter = None, value = None, 
                 minVal = None, maxVal = None):
        InvalidParameterError.__init__(self, parameter, value)
        self.minVal = minVal
        self.maxVal = maxVal