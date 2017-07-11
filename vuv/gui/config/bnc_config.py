from PyQt4 import QtCore, QtGui, uic
from labrad.util import getNodeName
from config_widget import SettingConfigWidget

class BNCConfig(SettingConfigWidget):
    regDir = ['', 'Servers', 'BNC Serial', getNodeName(), 'Links']
    serName = '%s_serial_server' % getNodeName().lower()
    
    def __init__(self, cxn):
        QtGui.QWidget.__init__()
        ui_class, ui_widget = uic.loadUiType('bnc_config.ui')
        self.ui = ui_class()
        self.ui.setupUi(self)
        
        self.cxn = cxn
        self.guiSetup()
        
    def guiSetup(self):
        self._populateBoxes()
        
    def _populateBoxes(self):
        ser = self.cxn[self.serName]
        
        port = ser.list_serial_ports()
        baud = ser.baudrate()
        
        self.ui.comBox.addItems(port)
        self.ui.baudBox.addItems(baud)
        
    def validate(self):
        return True
        
    def update(self):
        self._populateBoxes()
    
    def save(self):
        idN = int(self.ui.deviceBox.currentText())
        port = self.ui.comBox.currentText()
        baud = int(self.ui.baudBox.currentText())
        
        entry = (idN, port, baud)
        
        reg = self.cxn.registry
        reg.cd(self.regDir)
        vals = reg.get(self.serName)
        
        if entry not in vals:
            vals.append(entry)
            reg.set(self.serName, vals)
        