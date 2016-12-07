from PyQt4 import QtGui

from sas.sasgui.guiframe.dataFitting import Data2D

# Local UI
from sas.qtgui.UI.MaskEditorUI import Ui_MaskEditorUI
from sas.qtgui.Plotter2D import Plotter2DWidget

class MaskEditor(QtGui.QDialog, Ui_MaskEditorUI):
    def __init__(self, parent=None, data=None):
        super(MaskEditor, self).__init__()

        assert(isinstance(data, Data2D))

        self.setupUi(self)

        self.data = data
        filename = data.name
        self.setWindowTitle("Mask Editor for %s" % filename)

        self.plotter = Plotter2DWidget(self, manager=parent, quickplot=True)
        self.plotter.data = self.data

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.frame.setLayout(layout)
        layout.addWidget(self.plotter)

        self.plotter.plot()

