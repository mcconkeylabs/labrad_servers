import sys
import app.subprocs.labrad_procs as LS
from gui.log.logger import LogWidget
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication()
    
    procs = [LS.LabradExecutable(),
             LS.ManagerProcess()]
    
    w = LogWidget()
    w.show()
    
    sys.exit(app.exec_())