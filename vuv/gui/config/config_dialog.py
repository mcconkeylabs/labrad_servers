from PyQt4 import QtCore, QtGui, uic
from vuv.gui.config import mcs_config, bnc_config

class ConfigDialog(QtGui.QDialog):  
    
    def __init__(self, cxn):
        QtGui.QDialog.__init__()
        ui_class, ui_widget = uic.loadUiType('main.ui')
        self.ui = ui_class()
        self.ui.setupUi(self)
        
        self.tabs = {'BNC Pulser' : bnc_config.BNCConfig(cxn),
                     'Ortec MCS' : mcs_config.MCSConfig(cxn)}
        
        self.reg = cxn.registry
        self.guiSetup()
        
    def guiSetup(self):
        self._tabSetup()
    
    def _tabSetup(self):
        for (name, widget) in self.tabs.iteritems():
            self.ui.tabWidget.addTab(widget, name)
    
    def accept(self):
        vals = [t.validate() for t in self.tabs.values()]
        
        #if not all tabs valid, generate the dialog and halt accept
        if not all(vals):
            text = 'One or more inputs are invalid. Please check the\
                    configuration again or cancel.'
            msg = QtGui.QMessageBox(QtGui.QMessageBox.Critical, '', text,
                                    QtGui.QMessageBox.Ok)
            msg.exec_()
        #otherwise continue with usual process after saving to registry
        else:
            for t in self.tabs:
                t.save()
            super(ConfigDialog, self).accept()