from PyQt4 import QtGui

class SettingConfigWidget(QtGui.QDialog):
    def validate(self):
        '''Should validate all widget inputs. Widget is responsible for indicating
        what data is invalid. Return True/False for valid/invalid data so 
        user can be notified that data is invalid somewhere.'''
        pass
    
    def update(self):
        '''Should update the widget with the latest LabRAD registry data.'''
        pass
    
    def save(self):
        '''Should save widget data to LabRAD registry.'''
        pass