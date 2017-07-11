from PyQt4 import QtCore, QtGui, uic
import vuv.constants as C
import labrad.units as U

CH_VALIDATOR = QtGui.QIntValidator(C.STEPPER_MIN, C.STEPPER_MAX)
FRAC_VALIDATOR = QtGui.QIntValidator(1, C.ADV_PER_STEPPER_CHANNEL)

class ScanConfigDialog(QtGui.QDialog):
    def __init__(self, cxn, stepperName=None):        
        QtGui.QDialog.__init__(self)
        ui_class, ui_widget = uic.loadUiType('main.ui')
        self.ui = ui_class()
        self.ui.setupUi(self)
        
        self.labradSetup(cxn, stepperName)
        self.guiSetup()
        
        self.show()
        
    def labradSetup(self, cxn, stepperName):
        self.cxn = cxn
        self.reg = cxn.registry
        
        if stepperName is None:
            pass
        else:
            self.stepper = cxn[stepperName]  
        
    def guiSetup(self):
        self.setValidators()
        
        def updateAccept():
            self.writeScanInfo()
            self.accept()
            
        self.ui.buttonBox.accepted.connect(updateAccept)
        self.ui.buttonBox.rejected.connect(self.reject)
    
    def setValidators(self):
        self.ui.startChannelInput.setValidator(CH_VALIDATOR)
        self.ui.stopChannelInput.setValidator(CH_VALIDATOR)

        self.ui.startFractionInput.setValidator(FRAC_VALIDATOR)
        self.ui.stopFractionInput.setValidator(FRAC_VALIDATOR)
        
        self.ui.passInput.setValidator(QtGui.QIntValidator())
        self.ui.dwellTimeInput.setValidator(QtGui.QDoubleValidator())
        self.ui.mcsBinInput.setValidator(QtGui.QDoubleValidator())
        
    def writeScanInfo(self):
        startCh = int(self.ui.startChannelInput.text())
        startFrac = int(self.ui.startFractionInput.text())
        
        stopCh = int(self.ui.stopChannelInput.text())
        stopFrac = int(self.ui.stopFractionInput.text())
        
        dwell = float(self.ui.dwellTimeInput.text())
        passes = int(self.ui.passInput.text())
        ratio = float(self.ui.mcsBinInput.text())
        
        p = self.scanner.packet()
        p.scan_range(startCh, startFrac, stopCh, stopFrac)
        p.dwell_time(U.Value(dwell, 's'))
        p.passes(passes)
        p.mcs_ratio(ratio)
        p.send()
        
    