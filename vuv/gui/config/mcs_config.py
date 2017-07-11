from PyQt4 import QtCore, QtGui, uic
import os.path
from labrad.util import getNodeName
from config_widget import SettingConfigWidget

class MCSConfig(SettingConfigWidget):
    node = ['', 'Servers', 'OrtecMCS', getNodeName()]    
    
    def __init__(self, cxn):
        QtGui.QWidget.__init__()
        ui_class, ui_widget = uic.loadUiType('main.ui')
        self.ui = ui_class()
        self.ui.setupUi(self)
        
        self.reg = cxn.registry
        self.guiSetup()
        
    def guiSetup(self):
        self.update()   
        
    @QtCore.pyqtSlot()
    def on_exeDialogButton_clicked(self):
        current = self.ui.exePathEdit.text()
        d, f = os.path.split(current)
        path = QtGui.QFileDialog.getOpenFileName(self, 'Exe Path',
                                                 d, "Executable (*.exe)")
        self.ui.exePathEdit.setText(path)
        
    def _exePathValid(self):
        self.ui.exeValidLabel.setText('')
        path = self.ui.exePathEdit.text()
        if os.path.exists(path):
            if os.path.isfile(path):
                d, f = os.path.split(path)
                parts = f.split('.')
                if parts[-1] == 'exe':
                    self.ui.exeValidLabel.setText('')
                    return True
        
        #if we got to here, it's invalid
        invStr = r'<font color="red">Invalid file location.</font>'
        self.ui.exeValidLabel.setText(invStr)
        return False
        
    def validate(self):
        vals = [self._exePathValid()]
        return all(vals)
    
    def update(self):
        p = self.reg.packet()
        p.cd(self.node)
        p.get('ExePath', key='exe')
        resp = p.send()
        
        self.ui.exePathEdit.setText(resp['exe'])
        self.ui.exeValidLabel.setText('')
    
    def save(self):
        path = self.ui.exePathEdit.text()
        
        p = self.reg.packet()
        p.cd(self.node)
        p.set('ExePath', path)
        p.send()