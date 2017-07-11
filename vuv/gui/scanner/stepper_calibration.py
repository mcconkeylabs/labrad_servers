import labrad.units as U
import vuv.scripts.vuv_scan as scan
import time
from PyQt4 import QtCore, QtGui, uic

STEPPER = 'VUV Stepper Server'

class CalibrationDialog(QtGui.QDialog):
    
    def __init__(self, cxn):
        QtGui.QDialog.__init__(self)
        ui_class, ui_widget = uic.loadUiType('stepper_calibration.ui')
        self.ui = ui_class()
        self.ui.setupUi(self)
        self.show()
        
        self.ui.positionInput.setValidator(QtGui.QIntValidator())
        
        self.cxn = cxn
        self.stepper = self.cxn[STEPPER]
        self.calStep = 0
        
    def moveNow(self, advs):
        self.stepper.advance(advs, True)
        
    def initCalibration(self):
        if not self.ui.positionInput.isModified():
            string = 'Input the current channel position.'
            self.ui.messageLabel.setText(string)
        
        self.stepper.advance(8, True)
        while self.stepper.run_state():
            time.sleep(0.2)
        self.stepper.advance(-8, True)
        
    @QtCore.pyqtSlot()
    def on_bigBackButton_clicked(self):
        self.moveNow(-4)
        
    @QtCore.pyqtSlot()
    def on_backButton_clicked(self):
        self.moveNow(-1)
        
    @QtCore.pyqtSlot()
    def on_forwardButton_clicked(self):
        self.moveNow(1)
        
    @QtCore.pyqtSlot()
    def on_bigForwardButton_clicked(self):
        self.moveNow(4)
        
    @QtCore.pyqtSlot()
    def on_calibrateButton_clicked(self):
        pass