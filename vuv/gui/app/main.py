from PyQt4 import QtCore, QtGui, uic
from vuv.gui.config import scan_config as SC

class MainWindow(QtGui.QMainWindow):
    def __init__(self, cxn):
        self.cxn = cxn
        
        QtGui.QMainWindow.__init__(self)
        ui_class, ui_widget = uic.loadUiType('main.ui')
        self.ui = ui_class()
        self.ui.setupUi(self)
        
        self.labradSetup(cxn)
        self.guiSetup()
        self.show()
        
    def labradSetup(self, cxn):
        self.cxn = cxn
        self.reg = cxn.registry
        pass
    
    def guiSetup(self):
        pass
    
    def _loadRegistry(self):
        p = self.reg.packet()
        pass
    
    @QtCore.pyqtSignal()
    def on_configButton_clicked(self):
        SC.ScanConfigDialog(self.cxn, None)
        
    @QtCore.pyqtSignal()
    def on_startButton_clicked(self):
        pass
    
    @QtCore.pyqtSignal()
    def on_stopButton_clicked(self):
        pass
    
    