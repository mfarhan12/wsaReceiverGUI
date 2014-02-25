import sys
from PySide import QtGui
from gui import MainWindow

# pyinstaller + qt4reactor workaround:
sys.modules.pop('twisted.internet.reactor', None)
import qt4reactor

def main():
    app = QtGui.QApplication(sys.argv)
    qt4reactor.install() # requires QApplication to exist
    ex = MainWindow() # requires qt4reactor to be installed
    #late import because installReactor is being used
    from twisted.internet import reactor
    reactor.run()



