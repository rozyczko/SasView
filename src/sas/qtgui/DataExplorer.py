# global
import sys
import os
import logging

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtWebKit
from PyQt4.Qt import QMutex

from twisted.internet import threads

# SAS
from GuiUtils import *
from Plotter import Plotter
from sas.sascalc.dataloader.loader import Loader
from sas.sasgui.guiframe.data_manager import DataManager

from DroppableDataLoadWidget import DroppableDataLoadWidget

# This is how to get data1/2D from the model item
# data = [selected_items[0].child(0).data().toPyObject()]

class DataExplorerWindow(DroppableDataLoadWidget):
    # The controller which is responsible for managing signal slots connections
    # for the gui and providing an interface to the data model.

    def __init__(self, parent=None, guimanager=None):
        super(DataExplorerWindow, self).__init__(parent, guimanager)

        # Main model for keeping loaded data
        self.model = QtGui.QStandardItemModel(self)

        # Secondary model for keeping frozen data sets
        self.theory_model = QtGui.QStandardItemModel(self)

        # GuiManager is the actual parent, but we needed to also pass the QMainWindow
        # in order to set the widget parentage properly.
        self.parent = guimanager
        self.loader = Loader()
        self.manager = DataManager()

        # Be careful with twisted threads.
        self.mutex = QMutex()

        # Connect the buttons
        self.cmdLoad.clicked.connect(self.loadFile)
        self.cmdDeleteData.clicked.connect(self.deleteFile)
        self.cmdDeleteTheory.clicked.connect(self.deleteTheory)
        self.cmdFreeze.clicked.connect(self.freezeTheory)
        self.cmdSendTo.clicked.connect(self.sendData)
        self.cmdNew.clicked.connect(self.newPlot)
        self.cmdHelp.clicked.connect(self.displayHelp)
        self.cmdHelp_2.clicked.connect(self.displayHelp)

        # Display HTML content
        self._helpView = QtWebKit.QWebView()

        # Connect the comboboxes
        self.cbSelect.currentIndexChanged.connect(self.selectData)

        #self.closeEvent.connect(self.closeEvent)
        # self.aboutToQuit.connect(self.closeEvent)

        self.communicator.fileReadSignal.connect(self.loadFromURL)

        # Proxy model for showing a subset of Data1D/Data2D content
        self.data_proxy = QtGui.QSortFilterProxyModel(self)
        self.data_proxy.setSourceModel(self.model)

        # Don't show "empty" rows with data objects
        self.data_proxy.setFilterRegExp(r"[^()]")

        # The Data viewer is QTreeView showing the proxy model
        self.treeView.setModel(self.data_proxy)

        # Proxy model for showing a subset of Theory content
        self.theory_proxy = QtGui.QSortFilterProxyModel(self)
        self.theory_proxy.setSourceModel(self.theory_model)

        # Don't show "empty" rows with data objects
        self.theory_proxy.setFilterRegExp(r"[^()]")

        # Theory model view
        self.freezeView.setModel(self.theory_proxy)

    def closeEvent(self, event):
        """
        Overwrite the close event - no close!
        """
        event.ignore()

    def displayHelp(self):
        """
        Show the "Loading data" section of help
        """
        _TreeLocation = "html/user/sasgui/guiframe/data_explorer_help.html"
        self._helpView.load(QtCore.QUrl(_TreeLocation))
        self._helpView.show()

    def loadFromURL(self, url):
        """
        Threaded file load
        """
        load_thread = threads.deferToThread(self.readData, url)
        load_thread.addCallback(self.loadComplete)

    def loadFile(self, event=None):
        """
        Called when the "Load" button pressed.
        Opens the Qt "Open File..." dialog
        """
        path_str = self.chooseFiles()
        if not path_str:
            return
        self.loadFromURL(path_str)

    def loadFolder(self, event=None):
        """
        Called when the "File/Load Folder" menu item chosen.
        Opens the Qt "Open Folder..." dialog
        """
        folder = QtGui.QFileDialog.getExistingDirectory(self, "Choose a directory", "",
              QtGui.QFileDialog.ShowDirsOnly | QtGui.QFileDialog.DontUseNativeDialog)
        if folder is None:
            return

        folder = str(folder)

        if not os.path.isdir(folder):
            return

        # get content of dir into a list
        path_str = [os.path.join(os.path.abspath(folder), filename)
                        for filename in os.listdir(folder)]

        self.loadFromURL(path_str)

    def deleteFile(self, event):
        """
        Delete selected rows from the model
        """
        # Assure this is indeed wanted
        delete_msg = "This operation will delete the checked data sets and all the dependents." +\
                     "\nDo you want to continue?"
        reply = QtGui.QMessageBox.question(self, 'Warning', delete_msg,
                QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.No:
            return

        # Figure out which rows are checked
        ind = -1
        # Use 'while' so the row count is forced at every iteration
        while ind < self.model.rowCount():
            ind += 1
            item = self.model.item(ind)
            if item and item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
                # Delete these rows from the model
                self.model.removeRow(ind)
                # Decrement index since we just deleted it
                ind -= 1

        # pass temporarily kept as a breakpoint anchor
        pass

    def deleteTheory(self, event):
        """
        Delete selected rows from the theory model
        """
        # Assure this is indeed wanted
        delete_msg = "This operation will delete the checked data sets and all the dependents." +\
                     "\nDo you want to continue?"
        reply = QtGui.QMessageBox.question(self, 'Warning', delete_msg,
                QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.No:
            return

        # Figure out which rows are checked
        ind = -1
        # Use 'while' so the row count is forced at every iteration
        while ind < self.theory_model.rowCount():
            ind += 1
            item = self.theory_model.item(ind)
            if item and item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
                # Delete these rows from the model
                self.theory_model.removeRow(ind)
                # Decrement index since we just deleted it
                ind -= 1

        # pass temporarily kept as a breakpoint anchor
        pass

    def sendData(self, event):
        """
        Send selected item data to the current perspective and set the relevant notifiers
        """
        # should this reside on GuiManager or here?
        self._perspective = self.parent.perspective()

        # Set the signal handlers
        self.communicator = self._perspective.communicator()
        self.communicator.updateModelFromPerspectiveSignal.connect(self.updateModelFromPerspective)

        # Figure out which rows are checked
        selected_items = []
        for index in range(self.model.rowCount()):
            item = self.model.item(index)
            if item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
                selected_items.append(item)

        if len(selected_items) < 1:
            return

        # Which perspective has been selected?
        if len(selected_items) > 1 and not self._perspective.allowBatch():
            msg = self._perspective.title() + " does not allow multiple data."
            msgbox = QtGui.QMessageBox()
            msgbox.setIcon(QtGui.QMessageBox.Critical)
            msgbox.setText(msg)
            msgbox.setStandardButtons(QtGui.QMessageBox.Ok)
            retval = msgbox.exec_()
            return

        # Dig up the item
        data = selected_items

        # TODO
        # New plot or appended?

        # Notify the GuiManager about the send request
        self._perspective.setData(data_item=data)

    def freezeTheory(self, event):
        """
        Freeze selected theory rows.

        "Freezing" means taking the plottable data from the filename item
        and copying it to a separate top-level item.
        """
        # Figure out which _inner_ rows are checked
        # Use 'while' so the row count is forced at every iteration
        outer_index = -1
        theories_copied = 0
        while outer_index < self.model.rowCount():
            outer_index += 1
            outer_item = self.model.item(outer_index)
            if not outer_item:
                continue
            for inner_index in xrange(outer_item.rowCount()): # Should be just two rows: data and Info
                subitem = outer_item.child(inner_index)
                if subitem and subitem.isCheckable() and subitem.checkState() == QtCore.Qt.Checked:
                    theories_copied += 1
                    new_item = self.recursivelyCloneItem(subitem)
                    self.theory_model.appendRow(new_item)
            self.theory_model.reset()

        freeze_msg = ""
        if theories_copied == 0:
            return
        elif theories_copied == 1:
            freeze_msg = "1 theory sent to Theory tab"
        elif theories_copied > 1:
            freeze_msg = "%i theories sent to Theory tab" % theories_copied
        else:
            freeze_msg = "Unexpected number of theories copied: %i" % theories_copied
            raise AttributeError, freeze_msg
        self.communicator.statusBarUpdateSignal.emit(freeze_msg)
        # Actively switch tabs
        self.setCurrentIndex(1)

    def recursivelyCloneItem(self, item):
        """
        Clone QStandardItem() object
        """
        new_item = item.clone()
        # clone doesn't do deepcopy :(
        for child_index in xrange(item.rowCount()):
            child_item = self.recursivelyCloneItem(item.child(child_index))
            new_item.setChild(child_index, child_item)
        return new_item

    def newPlot(self):
        """
        Create a new matplotlib chart from selected data

        TODO: Add 2D-functionality
        """

        plots = plotsFromCheckedItems(self.model)

        # Call show on requested plots
        new_plot = Plotter()
        for plot_set in plots:
            new_plot.data(plot_set)
            new_plot.plot()

        new_plot.show()

    def chooseFiles(self):
        """
        Shows the Open file dialog and returns the chosen path(s)
        """
        # List of known extensions
        wlist = self.getWlist()

        # Location is automatically saved - no need to keep track of the last dir
        # But only with Qt built-in dialog (non-platform native)
        paths = QtGui.QFileDialog.getOpenFileNames(self, "Choose a file", "",
                wlist, None, QtGui.QFileDialog.DontUseNativeDialog)
        if paths is None:
            return

        #if type(paths) == QtCore.QStringList:
        if isinstance(paths, QtCore.QStringList):
            paths = [str(f) for f in paths]

        if paths.__class__.__name__ != "list":
            paths = [paths]

        return paths

    def readData(self, path):
        """
        verbatim copy-paste from
           sasgui.guiframe.local_perspectives.data_loader.data_loader.py
        slightly modified for clarity
        """
        message = ""
        log_msg = ''
        output = {}
        any_error = False
        data_error = False
        error_message = ""

        for p_file in path:
            basename = os.path.basename(p_file)
            _, extension = os.path.splitext(basename)
            if extension.lower() in EXTENSIONS:
                any_error = True
                log_msg = "Data Loader cannot "
                log_msg += "load: %s\n" % str(p_file)
                log_msg += """Please try to open that file from "open project" """
                log_msg += """or "open analysis" menu\n"""
                error_message = log_msg + "\n"
                logging.info(log_msg)
                continue

            try:
                message = "Loading Data... " + str(basename) + "\n"

                # change this to signal notification in GuiManager
                self.communicator.statusBarUpdateSignal.emit(message)

                output_objects = self.loader.load(p_file)

                # Some loaders return a list and some just a single Data1D object.
                # Standardize.
                if not isinstance(output_objects, list):
                    output_objects = [output_objects]

                for item in output_objects:
                    # cast sascalc.dataloader.data_info.Data1D into
                    # sasgui.guiframe.dataFitting.Data1D
                    # TODO : Fix it
                    new_data = self.manager.create_gui_data(item, p_file)
                    output[new_data.id] = new_data

                    # Model update should be protected
                    self.mutex.lock()
                    self.updateModel(new_data, p_file)
                    self.model.reset()
                    QtGui.qApp.processEvents()
                    self.mutex.unlock()

                    if hasattr(item, 'errors'):
                        for error_data in item.errors:
                            data_error = True
                            message += "\tError: {0}\n".format(error_data)
                    else:

                        logging.error("Loader returned an invalid object:\n %s" % str(item))
                        data_error = True

            except Exception as ex:
                logging.error(sys.exc_value)

                any_error = True
            if any_error or error_message != "":
                if error_message == "":
                    error = "Error: " + str(sys.exc_info()[1]) + "\n"
                    error += "while loading Data: \n%s\n" % str(basename)
                    error_message += "The data file you selected could not be loaded.\n"
                    error_message += "Make sure the content of your file"
                    error_message += " is properly formatted.\n\n"
                    error_message += "When contacting the SasView team, mention the"
                    error_message += " following:\n%s" % str(error)
                elif data_error:
                    base_message = "Errors occurred while loading "
                    base_message += "{0}\n".format(basename)
                    base_message += "The data file loaded but with errors.\n"
                    error_message = base_message + error_message
                else:
                    error_message += "%s\n" % str(p_file)
                info = "error"

        if any_error or error_message:
            self.communicator.statusBarUpdateSignal.emit(error_message)

        else:
            message = "Loading Data Complete! "
        message += log_msg

        return output, message

    def getWlist(self):
        """
        Wildcards of files we know the format of.
        """
        # Display the Qt Load File module
        cards = self.loader.get_wildcards()

        # get rid of the wx remnant in wildcards
        # TODO: modify sasview loader get_wildcards method, after merge,
        # so this kludge can be avoided
        new_cards = []
        for item in cards:
            new_cards.append(item[:item.find("|")])
        wlist = ';;'.join(new_cards)

        return wlist

    def selectData(self, index):
        """
        Callback method for modifying the TreeView on Selection Options change
        """
        if not isinstance(index, int):
            msg = "Incorrect type passed to DataExplorer.selectData()"
            raise AttributeError, msg

        # Respond appropriately
        if index == 0:
            # Select All
            for index in range(self.model.rowCount()):
                item = self.model.item(index)
                if item.isCheckable() and item.checkState() == QtCore.Qt.Unchecked:
                    item.setCheckState(QtCore.Qt.Checked)
        elif index == 1:
            # De-select All
            for index in range(self.model.rowCount()):
                item = self.model.item(index)
                if item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
                    item.setCheckState(QtCore.Qt.Unchecked)

        elif index == 2:
            # Select All 1-D
            for index in range(self.model.rowCount()):
                item = self.model.item(index)
                item.setCheckState(QtCore.Qt.Unchecked)

                try:
                    is1D = item.child(0).data().toPyObject().__class__.__name__ == 'Data1D'
                except AttributeError:
                    msg = "Bad structure of the data model."
                    raise RuntimeError, msg

                if is1D:
                    item.setCheckState(QtCore.Qt.Checked)

        elif index == 3:
            # Unselect All 1-D
            for index in range(self.model.rowCount()):
                item = self.model.item(index)

                try:
                    is1D = item.child(0).data().toPyObject().__class__.__name__ == 'Data1D'
                except AttributeError:
                    msg = "Bad structure of the data model."
                    raise RuntimeError, msg

                if item.isCheckable() and item.checkState() == QtCore.Qt.Checked and is1D:
                    item.setCheckState(QtCore.Qt.Unchecked)

        elif index == 4:
            # Select All 2-D
            for index in range(self.model.rowCount()):
                item = self.model.item(index)
                item.setCheckState(QtCore.Qt.Unchecked)
                try:
                    is2D = item.child(0).data().toPyObject().__class__.__name__ == 'Data2D'
                except AttributeError:
                    msg = "Bad structure of the data model."
                    raise RuntimeError, msg

                if is2D:
                    item.setCheckState(QtCore.Qt.Checked)

        elif index == 5:
            # Unselect All 2-D
            for index in range(self.model.rowCount()):
                item = self.model.item(index)

                try:
                    is2D = item.child(0).data().toPyObject().__class__.__name__ == 'Data2D'
                except AttributeError:
                    msg = "Bad structure of the data model."
                    raise RuntimeError, msg

                if item.isCheckable() and item.checkState() == QtCore.Qt.Checked and is2D:
                    item.setCheckState(QtCore.Qt.Unchecked)

        else:
            msg = "Incorrect value in the Selection Option"
            # Change this to a proper logging action
            raise Exception, msg


    def loadComplete(self, output):
        """
        Post message to status bar and update the data manager
        """
        # Reset the model so the view gets updated.
        self.model.reset()
        assert type(output) == tuple

        output_data = output[0]
        message = output[1]
        # Notify the manager of the new data available
        self.communicator.statusBarUpdateSignal.emit(message)
        self.communicator.fileDataReceivedSignal.emit(output_data)
        self.manager.add_data(data_list=output_data)

    def updateModel(self, data, p_file):
        """
        Add data and Info fields to the model item
        """
        # Structure of the model
        # checkbox + basename
        #     |-------> Data.D object
        #     |-------> Info
        #                 |----> Title:
        #                 |----> Run:
        #                 |----> Type:
        #                 |----> Path:
        #                 |----> Process
        #                          |-----> process[0].name
        #

        # Top-level item: checkbox with label
        checkbox_item = QtGui.QStandardItem(True)
        checkbox_item.setCheckable(True)
        checkbox_item.setCheckState(QtCore.Qt.Checked)
        checkbox_item.setText(os.path.basename(p_file))

        # Add the actual Data1D/Data2D object
        object_item = QtGui.QStandardItem()
        object_item.setData(QtCore.QVariant(data))

        checkbox_item.setChild(0, object_item)

        # Add rows for display in the view
        info_item = infoFromData(data)

        # Set info_item as the only child
        checkbox_item.setChild(1, info_item)

        # New row in the model
        self.model.appendRow(checkbox_item)

    def updateModelFromPerspective(self, model_item):
        """
        Receive an update model item from a perspective
        Make sure it is valid and if so, replace it in the model
        """
        # Assert the correct type
        if type(model_item) != QtGui.QStandardItem:
            msg = "Wrong data type returned from calculations."
            raise AttributeError, msg

        # TODO: Assert other properties

        # Reset the view
        self.model.reset()

        # Pass acting as a debugger anchor
        pass


if __name__ == "__main__":
    app = QtGui.QApplication([])
    dlg = DataExplorerWindow()
    dlg.show()
    sys.exit(app.exec_())