import os
import sys

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from PyQt5 import QtGui, QtCore, QtWidgets

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary

from sas.qtgui.Perspectives.Fitting.UI.ConstraintWidgetUI import Ui_ConstraintWidgetUI
from sas.qtgui.Perspectives.Fitting.FittingWidget import FittingWidget
from sas.qtgui.Perspectives.Fitting.ComplexConstraint import ComplexConstraint
from sas.qtgui.Perspectives.Fitting.Constraints import Constraint

class ConstraintWidget(QtWidgets.QWidget, Ui_ConstraintWidgetUI):
    """
    Constraints Dialog to select the desired parameter/model constraints.
    """

    def __init__(self, parent=None):
        super(ConstraintWidget, self).__init__()
        self.parent = parent
        self.setupUi(self)
        self.currentType = "FitPage"

        # Remember previous content of modified cell
        self.current_cell = ""

        # Tabs used in simultaneous fitting
        # tab_name : True/False
        self.tabs_for_fitting = {}

        # Set up the widgets
        self.initializeWidgets()

        # Set up signals/slots
        self.initializeSignals()

        # Create the list of tabs
        self.initializeFitList()

    def acceptsData(self):
        """ Tells the caller this widget doesn't accept data """
        return False

    def initializeWidgets(self):
        """
        Set up various widget states
        """
        labels = ['FitPage', 'Model', 'Data', 'Mnemonic']
        # tab widget - headers
        self.editable_tab_columns = [labels.index('Mnemonic')]
        self.tblTabList.setColumnCount(len(labels))
        self.tblTabList.setHorizontalHeaderLabels(labels)
        self.tblTabList.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.tblTabList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tblTabList.customContextMenuRequested.connect(self.showModelContextMenu)

        # disabled constraint 
        labels = ['Constraint']
        self.tblConstraints.setColumnCount(len(labels))
        self.tblConstraints.setHorizontalHeaderLabels(labels)
        self.tblConstraints.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tblConstraints.setEnabled(False)

        self.tblConstraints.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tblConstraints.customContextMenuRequested.connect(self.showConstrContextMenu)

    def initializeSignals(self):
        """
        Set up signals/slots for this widget
        """
        # simple widgets
        self.btnSingle.toggled.connect(self.onFitTypeChange)
        self.btnBatch.toggled.connect(self.onFitTypeChange)
        self.cbCases.currentIndexChanged.connect(self.onSpecialCaseChange)
        self.cmdFit.clicked.connect(self.onFit)
        self.cmdHelp.clicked.connect(self.onHelp)

        # QTableWidgets
        self.tblTabList.cellChanged.connect(self.onTabCellEdit)
        self.tblTabList.cellDoubleClicked.connect(self.onTabCellEntered)
        self.tblConstraints.cellChanged.connect(self.onConstraintChange)

        # External signals
        #self.parent.tabsModifiedSignal.connect(self.initializeFitList)
        self.parent.tabsModifiedSignal.connect(self.onModifiedTabs)

    def updateSignalsFromTab(self, tab=None):
        """
        Intercept update signals from fitting tabs
        """
        if tab is not None:
            ObjectLibrary.getObject(tab).constraintAddedSignal.connect(self.initializeFitList)
            ObjectLibrary.getObject(tab).newModelSignal.connect(self.initializeFitList)

    def onFitTypeChange(self, checked):
        """
        Respond to the fit type change
        single fit/batch fit
        """
        source = self.sender().objectName()
        self.currentType = "BatchPage" if source == "btnBatch" else "FitPage"
        self.initializeFitList()

    def onSpecialCaseChange(self, index):
        """
        Respond to the combobox change for special case constraint sets
        """
        pass

    def onFit(self):
        """
        Perform the constrained/simultaneous fit
        """
        pass

    def onHelp(self):
        """
        Display the help page
        """
        pass

    def onTabCellEdit(self, row, column):
        """
        Respond to check/uncheck and to modify the model moniker actions
        """
        item = self.tblTabList.item(row, column)
        if column == 0:
            # Update the tabs for fitting list
            tab_name = item.text()
            self.tabs_for_fitting[tab_name] = (item.checkState() == QtCore.Qt.Checked)
            # Enable fitting only when there are models to fit
            self.cmdFit.setEnabled(any(self.tabs_for_fitting.values()))

        if column not in self.editable_tab_columns:
            return
        new_moniker = item.data(0)

        # The new name should be validated on the fly, with QValidator
        # but let's just assure it post-factum
        is_good_moniker = self.validateMoniker(new_moniker)
        if not is_good_moniker:
            item.setBackground(QtCore.Qt.red)
            self.cmdFit.setEnabled(False)
            return
        self.tblTabList.blockSignals(True)
        item.setBackground(QtCore.Qt.white)
        self.tblTabList.blockSignals(False)
        self.cmdFit.setEnabled(True)
        if not self.current_cell:
            return
        # Remember the value
        if self.current_cell not in self.available_tabs:
            return
        temp_tab = self.available_tabs[self.current_cell]
        # Remove the key from the dictionaries
        self.available_tabs.pop(self.current_cell, None)
        # Change the model name
        model = temp_tab.kernel_module
        model.name = new_moniker
        # Replace constraint name
        temp_tab.replaceConstraintName(self.current_cell, new_moniker)
        # Replace constraint name in the remaining tabs
        for tab in self.available_tabs.values():
            tab.replaceConstraintName(self.current_cell, new_moniker)
        # Reinitialize the display
        self.initializeFitList()

    def onConstraintChange(self, row, column):
        """
        Modify the constraint in-place.
        """
        item = self.tblConstraints.item(row, column)
        if column == 0:
            # Update the tabs for fitting list
            constraint = self.available_constraints[row]
            constraint.active = (item.checkState() == QtCore.Qt.Checked)

    def onTabCellEntered(self, row, column):
        """
        Remember the original tab list cell data.
        Needed for reverting back on bad validation
        """
        if column != 3:
            return
        self.current_cell = self.tblTabList.item(row, column).data(0)

    def onModifiedTabs(self):
        """
        Respond to tabs being deleted by deleting involved constraints

        This should probably be done in FittingWidget as it is the owner of
        all the fitting data, but I want to keep the FW oblivious about
        dependence on other FW tabs, so enforcing the constraint deletion here.
        """
        # Get the list of all constraints from querying the table
        #constraints = getConstraintsForModel()

        # Get the current list of tabs
        #tabs = ObjectLibrary.listObjects()

        # Check if any of the constraint dependencies got deleted
        # Check the list of constraints
        self.initializeFitList()
        pass

    def isTabImportable(self, tab):
        """
        Determines if the tab can be imported and included in the widget
        """
        if not self.currentType in tab: return False
        object = ObjectLibrary.getObject(tab)
        if not isinstance(object, FittingWidget): return False
        if object.data is None: return False
        return True

    def showModelContextMenu(self, position):
        """
        Show context specific menu in the tab table widget.
        """
        menu = QtWidgets.QMenu()
        rows = [s.row() for s in self.tblTabList.selectionModel().selectedRows()]
        num_rows = len(rows)
        if num_rows <= 0:
            return
        # Select for fitting
        param_string = "Fit Page " if num_rows==1 else "Fit Pages "
        to_string = "to its current value" if num_rows==1 else "to their current values"

        self.actionSelect = QtWidgets.QAction(self)
        self.actionSelect.setObjectName("actionSelect")
        self.actionSelect.setText(QtCore.QCoreApplication.translate("self", "Select "+param_string+" for fitting"))
        # Unselect from fitting
        self.actionDeselect = QtWidgets.QAction(self)
        self.actionDeselect.setObjectName("actionDeselect")
        self.actionDeselect.setText(QtCore.QCoreApplication.translate("self", "De-select "+param_string+" from fitting"))

        self.actionRemoveConstraint = QtWidgets.QAction(self)
        self.actionRemoveConstraint.setObjectName("actionRemoveConstrain")
        self.actionRemoveConstraint.setText(QtCore.QCoreApplication.translate("self", "Remove all constraints on selected models"))

        self.actionMutualMultiConstrain = QtWidgets.QAction(self)
        self.actionMutualMultiConstrain.setObjectName("actionMutualMultiConstrain")
        self.actionMutualMultiConstrain.setText(QtCore.QCoreApplication.translate("self", "Mutual constrain of parameters in selected models..."))

        menu.addAction(self.actionSelect)
        menu.addAction(self.actionDeselect)
        menu.addSeparator()

        #menu.addAction(self.actionRemoveConstraint)
        if num_rows >= 2:
            menu.addAction(self.actionMutualMultiConstrain)

        # Define the callbacks
        #self.actionConstrain.triggered.connect(self.addSimpleConstraint)
        #self.actionRemoveConstraint.triggered.connect(self.deleteConstraint)
        self.actionMutualMultiConstrain.triggered.connect(self.showMultiConstraint)
        self.actionSelect.triggered.connect(self.selectModels)
        self.actionDeselect.triggered.connect(self.deselectModels)
        try:
            menu.exec_(self.tblTabList.viewport().mapToGlobal(position))
        except AttributeError as ex:
            logging.error("Error generating context menu: %s" % ex)
        return

    def showConstrContextMenu(self, position):
        """
        Show context specific menu in the tab table widget.
        """
        menu = QtWidgets.QMenu()
        rows = [s.row() for s in self.tblConstraints.selectionModel().selectedRows()]
        num_rows = len(rows)
        if num_rows <= 0:
            return
        # Select for fitting
        param_string = "constraint " if num_rows==1 else "constraints "
        to_string = "to its current value" if num_rows==1 else "to their current values"

        self.actionSelect = QtWidgets.QAction(self)
        self.actionSelect.setObjectName("actionSelect")
        self.actionSelect.setText(QtCore.QCoreApplication.translate("self", "Select "+param_string+" for fitting"))
        # Unselect from fitting
        self.actionDeselect = QtWidgets.QAction(self)
        self.actionDeselect.setObjectName("actionDeselect")
        self.actionDeselect.setText(QtCore.QCoreApplication.translate("self", "De-select "+param_string+" from fitting"))

        self.actionRemoveConstraint = QtWidgets.QAction(self)
        self.actionRemoveConstraint.setObjectName("actionRemoveConstrain")
        self.actionRemoveConstraint.setText(QtCore.QCoreApplication.translate("self", "Remove "+param_string))

        menu.addAction(self.actionSelect)
        menu.addAction(self.actionDeselect)
        menu.addSeparator()
        menu.addAction(self.actionRemoveConstraint)

        # Define the callbacks
        #self.actionConstrain.triggered.connect(self.addSimpleConstraint)
        self.actionRemoveConstraint.triggered.connect(self.deleteConstraint)
        #self.actionMutualMultiConstrain.triggered.connect(self.showMultiConstraint)
        self.actionSelect.triggered.connect(self.selectConstraints)
        self.actionDeselect.triggered.connect(self.deselectConstraints)
        try:
            menu.exec_(self.tblConstraints.viewport().mapToGlobal(position))
        except AttributeError as ex:
            logging.error("Error generating context menu: %s" % ex)
        return

    def selectConstraints(self):
        """
        Selected constraints are chosen for fitting
        """
        status = QtCore.Qt.Checked
        self.setRowSelection(self.tblConstraints, status)

    def deselectConstraints(self):
        """
        Selected constraints are removed for fitting
        """
        status = QtCore.Qt.Unchecked
        self.setRowSelection(self.tblConstraints, status)

    def selectModels(self):
        """
        Selected models are chosen for fitting
        """
        status = QtCore.Qt.Checked
        self.setRowSelection(self.tblTabList, status)

    def deselectModels(self):
        """
        Selected models are removed for fitting
        """
        status = QtCore.Qt.Unchecked
        self.setRowSelection(self.tblTabList, status)

    def selectedParameters(self, widget):
        """ Returns list of selected (highlighted) parameters """
        return [s.row() for s in widget.selectionModel().selectedRows()]

    def setRowSelection(self, widget, status=QtCore.Qt.Unchecked):
        """
        Selected models are chosen for fitting
        """
        # Convert to proper indices and set requested enablement
        for row in self.selectedParameters(widget):
            widget.item(row, 0).setCheckState(status)

    def deleteConstraint(self):#, row):
        """
        Delete all selected constraints.
        """
        # Removing rows from the table we're iterating over,
        # so prepare a list of data first
        constraints_to_delete = []
        for row in self.selectedParameters(self.tblConstraints):
            constraints_to_delete.append(self.tblConstraints.item(row, 0).data(0))
        for constraint in constraints_to_delete:
            moniker = constraint[:constraint.index(':')]
            param = constraint[constraint.index(':')+1:constraint.index('=')].strip()
            tab = self.available_tabs[moniker]
            tab.deleteConstraintOnParameter(param)
        # Constraints removed - refresh the table widget
        self.initializeFitList()

    def uneditableItem(self, data=""):
        """
        Returns an uneditable Table Widget Item
        """
        item = QtWidgets.QTableWidgetItem(data)
        item.setFlags( QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )
        return item

    def updateFitLine(self, tab):
        """
        Update a single line of the table widget with tab info
        """
        fit_page = ObjectLibrary.getObject(tab)
        model = fit_page.kernel_module
        if model is None:
            return
        tab_name = tab
        model_name = model.id
        moniker = model.name
        model_data = fit_page.data
        model_filename = model_data.filename
        self.available_tabs[moniker] = fit_page

        # Update the model table widget
        pos = self.tblTabList.rowCount()
        self.tblTabList.insertRow(pos)
        item = self.uneditableItem(tab_name)
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsUserCheckable)
        if tab_name in self.tabs_for_fitting:
            state = QtCore.Qt.Checked if self.tabs_for_fitting[tab_name] else QtCore.Qt.Unchecked
            item.setCheckState(state)
        else:
            item.setCheckState(QtCore.Qt.Checked)
            self.tabs_for_fitting[tab_name] = True

        self.tblTabList.setItem(pos, 0, item)
        self.tblTabList.setItem(pos, 1, self.uneditableItem(model_name))
        self.tblTabList.setItem(pos, 2, self.uneditableItem(model_filename))
        # Moniker is editable, so no option change
        item = QtWidgets.QTableWidgetItem(moniker)
        # Disable signals so we don't get infinite call recursion
        self.tblTabList.blockSignals(True)
        self.tblTabList.setItem(pos, 3, item)
        self.tblTabList.blockSignals(False)

        # Check if any constraints present in tab
        constraint_names = fit_page.getConstraintsForModel()
        constraints = fit_page.getConstraintObjectsForModel()
        if not constraints: 
            return
        self.tblConstraints.setEnabled(True)
        for constraint, constraint_name in zip(constraints, constraint_names):
            # Create the text for widget item
            label = moniker + ":"+ constraint_name[0] + " = " + constraint_name[1]
            pos = self.tblConstraints.rowCount()
            self.available_constraints[pos] = constraint

            # Show the text in the constraint table
            item = self.uneditableItem(label)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)
            self.tblConstraints.insertRow(pos)
            self.tblConstraints.setItem(pos, 0, item)

    def initializeFitList(self):
        """
        Fill the list of model/data sets for fitting/constraining
        """
        # look at the object library to find all fit tabs
        # Show the content of the current "model"
        objects = ObjectLibrary.listObjects()

        # Tab dict
        # moniker -> (kernel_module, data)
        self.available_tabs = {}
        # Constraint dict
        # moniker -> [constraints]
        self.available_constraints = {}

        # Reset the table widgets
        self.tblTabList.setRowCount(0)
        self.tblConstraints.setRowCount(0)

        # Fit disabled
        self.cmdFit.setEnabled(False)

        if not objects:
            return

        tabs = [tab for tab in ObjectLibrary.listObjects() if self.isTabImportable(tab)]
        for tab in tabs:
            self.updateFitLine(tab)
            self.updateSignalsFromTab(tab)
            # We have at least 1 fit page, allow fitting
            self.cmdFit.setEnabled(True)

    def validateMoniker(self, new_moniker=None):
        """
        Check new_moniker for correctness.
        It must be non-empty.
        It must not be the same as other monikers.
        """
        if not new_moniker:
            return False

        for existing_moniker in self.available_tabs:
            if existing_moniker == new_moniker and existing_moniker != self.current_cell:
                return False

        return True

    def getObjectByName(self, name):
        for object_name in ObjectLibrary.listObjects():
            object = ObjectLibrary.getObject(object_name)
            if isinstance(object, FittingWidget):
                try:
                    if object.kernel_module.name == name:
                        return object
                except AttributeError:
                    # Disregard atribute errors - empty fit widgets
                    continue
        return None

    def showMultiConstraint(self):
        """
        Invoke the complex constraint editor
        """
        selected_rows = self.selectedParameters(self.tblTabList)
        assert(len(selected_rows)==2)

        tab_list = [ObjectLibrary.getObject(self.tblTabList.item(s, 0).data(0)) for s in selected_rows]
        # Create and display the widget for param1 and param2
        cc_widget = ComplexConstraint(self, tabs=tab_list)
        if cc_widget.exec_() != QtWidgets.QDialog.Accepted:
            return

        constraint = Constraint()
        model1, param1, operator, constraint_text = cc_widget.constraint()

        constraint.func = constraint_text
        constraint.param = param1
        # Find the right tab
        constrained_tab = self.getObjectByName(model1)
        if constrained_tab is None:
            return

        # Find the constrained parameter row
        constrained_row = constrained_tab.getRowFromName(param1)

        # Update the tab
        constrained_tab.addConstraintToRow(constraint, constrained_row)
        pass
