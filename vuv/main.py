import sys
from time import sleep
import app.subprocs.labrad_procs as LS
from gui.log.logger import LogWidget
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    procs = [LS.ManagerProcess(),
             LS.WebServerProcess()]
    
    w = LogWidget(procs)
    w.show()
    
    for p in procs:
         p.start()
         
         while not p.running():
              sleep(0.5)
         
    
    sys.exit(app.exec_())