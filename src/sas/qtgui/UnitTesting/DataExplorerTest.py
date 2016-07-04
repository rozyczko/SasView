import sys
import unittest

from PyQt4.QtGui import *
from PyQt4.QtTest import QTest
from PyQt4.QtCore import *
from mock import MagicMock

# Local
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sascalc.dataloader.loader import Loader
from sas.sasgui.guiframe.data_manager import DataManager

from DataExplorer import DataExplorerWindow
from GuiManager import GuiManager
from GuiUtils import *
from UnitTesting.TestUtils import QtSignalSpy
from Plotter import Plotter

app = QApplication(sys.argv)

class DataExplorerTest(unittest.TestCase):
    '''Test the Data Explorer GUI'''
    def setUp(self):
        '''Create the GUI'''
        class MyPerspective(object):
            def communicator(self):
                return Communicate()
            def allowBatch(self):
                return False
            def setData(self, data_item=None):
                return None
            def title(self):
                return "Dummy Perspective"

        class dummy_manager(object):
            def communicator(self):
                return Communicate()
            def perspective(self):
                return MyPerspective()

        self.form = DataExplorerWindow(None, dummy_manager())

    def tearDown(self):
        '''Destroy the GUI'''
        self.form.close()
        self.form = None

    def testDefaults(self):
        '''Test the GUI in its default state'''
        # Tab widget
        self.assertIsInstance(self.form, QTabWidget)
        self.assertEqual(self.form.count(), 2)

        # Buttons - data tab
        self.assertEqual(self.form.cmdLoad.text(), "Load")
        self.assertEqual(self.form.cmdDeleteData.text(), "Delete")
        self.assertEqual(self.form.cmdDeleteTheory.text(), "Delete")
        self.assertEqual(self.form.cmdFreeze.text(), "Freeze Theory")
        self.assertEqual(self.form.cmdSendTo.text(), "...")
        self.assertEqual(self.form.cmdSendTo.iconSize(), QSize(32, 32))
        self.assertIsInstance(self.form.cmdSendTo.icon(), QIcon)
        self.assertEqual(self.form.chkBatch.text(), "Batch mode")
        self.assertFalse(self.form.chkBatch.isChecked())

        # Buttons - theory tab

        # Combo boxes
        self.assertEqual(self.form.cbSelect.count(), 6)
        self.assertEqual(self.form.cbSelect.currentIndex(), 0)

        # Models - data
        self.assertIsInstance(self.form.model, QStandardItemModel)
        self.assertEqual(self.form.treeView.model().rowCount(), 0)
        self.assertEqual(self.form.treeView.model().columnCount(), 0)
        self.assertEqual(self.form.model.rowCount(), 0)
        self.assertEqual(self.form.model.columnCount(), 0)
        self.assertIsInstance(self.form.data_proxy, QSortFilterProxyModel)
        self.assertEqual(self.form.data_proxy.sourceModel(), self.form.model)
        self.assertEqual("[^()]", str(self.form.data_proxy.filterRegExp().pattern()))
        self.assertIsInstance(self.form.treeView, QTreeView)

        # Models - theory
        self.assertIsInstance(self.form.theory_model, QStandardItemModel)
        self.assertEqual(self.form.freezeView.model().rowCount(), 0)
        self.assertEqual(self.form.freezeView.model().columnCount(), 0)
        self.assertEqual(self.form.theory_model.rowCount(), 0)
        self.assertEqual(self.form.theory_model.columnCount(), 0)
        self.assertIsInstance(self.form.theory_proxy, QSortFilterProxyModel)
        self.assertEqual(self.form.theory_proxy.sourceModel(), self.form.theory_model)
        self.assertEqual("[^()]", str(self.form.theory_proxy.filterRegExp().pattern()))
        self.assertIsInstance(self.form.freezeView, QTreeView)

        
    def testLoadButton(self):
        loadButton = self.form.cmdLoad

        filename = "cyl_400_20.txt"
        # Initialize signal spy instances
        spy_file_read = QtSignalSpy(self.form, self.form.communicator.fileReadSignal)

        # Return no files.
        QtGui.QFileDialog.getOpenFileNames = MagicMock(return_value=None)

        # Click on the Load button
        QTest.mouseClick(loadButton, Qt.LeftButton)

        # Test the getOpenFileName() dialog called once
        self.assertTrue(QtGui.QFileDialog.getOpenFileNames.called)
        QtGui.QFileDialog.getOpenFileNames.assert_called_once()

        # Make sure the signal has not been emitted
        #self.assertEqual(spy_file_read.count(), 0)

        # Now, return a single file
        QtGui.QFileDialog.getOpenFileNames = MagicMock(return_value=filename)
        
        # Click on the Load button
        QTest.mouseClick(loadButton, Qt.LeftButton)

        # Test the getOpenFileName() dialog called once
        self.assertTrue(QtGui.QFileDialog.getOpenFileNames.called)
        QtGui.QFileDialog.getOpenFileNames.assert_called_once()

        # Expected one spy instance
        #self.assertEqual(spy_file_read.count(), 1)
        #self.assertIn(filename, str(spy_file_read.called()[0]['args'][0]))

    def testDeleteButton(self):
        """
        Functionality of the delete button
        """
        deleteButton = self.form.cmdDeleteData

        # Mock the confirmation dialog with return=No
        QtGui.QMessageBox.question = MagicMock(return_value=QtGui.QMessageBox.No)

        # Populate the model
        filename = ["cyl_400_20.txt", "Dec07031.ASC", "cyl_400_20.txt"]
        self.form.readData(filename)

        # Assure the model contains three items
        self.assertEqual(self.form.model.rowCount(), 3)

        # Assure the checkboxes are on
        item1 = self.form.model.item(0)
        item2 = self.form.model.item(1)
        item3 = self.form.model.item(2)
        self.assertTrue(item1.checkState() == QtCore.Qt.Checked)
        self.assertTrue(item2.checkState() == QtCore.Qt.Checked)
        self.assertTrue(item3.checkState() == QtCore.Qt.Checked)

        # Click on the delete  button
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Test the warning dialog called once
        self.assertTrue(QtGui.QMessageBox.question.called)

        # Assure the model still contains the items
        self.assertEqual(self.form.model.rowCount(), 3)

        # Now, mock the confirmation dialog with return=Yes
        QtGui.QMessageBox.question = MagicMock(return_value=QtGui.QMessageBox.Yes)

        # Click on the delete  button
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Test the warning dialog called once
        self.assertTrue(QtGui.QMessageBox.question.called)

        # Assure the model contains no items
        self.assertEqual(self.form.model.rowCount(), 0)

        # Click delete once again to assure no nasty behaviour on empty model
        QTest.mouseClick(deleteButton, Qt.LeftButton)

    def testDeleteTheory(self):
        """
        Test that clicking "Delete" in theories tab removes selected indices
        """
        deleteButton = self.form.cmdDeleteTheory

        # Mock the confirmation dialog with return=No
        QtGui.QMessageBox.question = MagicMock(return_value=QtGui.QMessageBox.No)

        # Populate the model
        item1 = QtGui.QStandardItem(True)
        item1.setCheckable(True)
        item1.setCheckState(QtCore.Qt.Checked)
        item1.setText("item 1")
        self.form.theory_model.appendRow(item1)
        item2 = QtGui.QStandardItem(True)
        item2.setCheckable(True)
        item2.setCheckState(QtCore.Qt.Unchecked)
        item2.setText("item 2")
        self.form.theory_model.appendRow(item2)

        # Assure the model contains two items
        self.assertEqual(self.form.theory_model.rowCount(), 2)

        # Assure the checkboxes are on
        self.assertTrue(item1.checkState() == QtCore.Qt.Checked)
        self.assertTrue(item2.checkState() == QtCore.Qt.Unchecked)

        # Click on the delete  button
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Test the warning dialog called once
        self.assertTrue(QtGui.QMessageBox.question.called)

        # Assure the model still contains the items
        self.assertEqual(self.form.theory_model.rowCount(), 2)

        # Now, mock the confirmation dialog with return=Yes
        QtGui.QMessageBox.question = MagicMock(return_value=QtGui.QMessageBox.Yes)

        # Click on the delete  button
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Test the warning dialog called once
        self.assertTrue(QtGui.QMessageBox.question.called)

        # Assure the model contains 1 item
        self.assertEqual(self.form.theory_model.rowCount(), 1)

        # Set the remaining item to checked
        self.form.theory_model.item(0).setCheckState(QtCore.Qt.Checked)

        # Click on the delete button again
        QTest.mouseClick(deleteButton, Qt.LeftButton)

        # Assure the model contains no items
        self.assertEqual(self.form.theory_model.rowCount(), 0)

        # Click delete once again to assure no nasty behaviour on empty model
        QTest.mouseClick(deleteButton, Qt.LeftButton)


    def testSendToButton(self):
        """
        Test that clicking the Send To button sends checked data to a perspective
        """
        # Send empty data
        mocked_perspective = self.form.parent.perspective()
        mocked_perspective.setData = MagicMock()

        # Click on the Send To  button
        QTest.mouseClick(self.form.cmdSendTo, Qt.LeftButton)

        # The set_data method not called
        self.assertFalse(mocked_perspective.setData.called)
               
        # Populate the model
        filename = ["cyl_400_20.txt"]
        self.form.readData(filename)

        # setData is the method we want to see called
        mocked_perspective = self.form.parent.perspective()
        mocked_perspective.setData = MagicMock(filename)

        # Assure the checkbox is on
        self.form.cbSelect.setCurrentIndex(0)

        # Click on the Send To  button
        QTest.mouseClick(self.form.cmdSendTo, Qt.LeftButton)

        # Test the set_data method called once
        #self.assertTrue(mocked_perspective.setData.called)

        # open another file
        filename = ["cyl_400_20.txt"]
        self.form.readData(filename)

        # Mock the warning message
        QtGui.QMessageBox = MagicMock()

        # Click on the button
        QTest.mouseClick(self.form.cmdSendTo, Qt.LeftButton)

        # Assure the message box popped up
        QtGui.QMessageBox.assert_called_once()

    def testDataSelection(self):
        """
        Tests the functionality of the Selection Option combobox
        """
        # Populate the model with 1d and 2d data
        filename = ["cyl_400_20.txt", "Dec07031.ASC"]
        self.form.readData(filename)

        # Unselect all data
        self.form.cbSelect.setCurrentIndex(1)

        # Test the current selection
        item1D = self.form.model.item(0)
        item2D = self.form.model.item(1)
        self.assertTrue(item1D.checkState() == QtCore.Qt.Unchecked)
        self.assertTrue(item2D.checkState() == QtCore.Qt.Unchecked)        

        # Select all data
        self.form.cbSelect.setCurrentIndex(0)

        # Test the current selection
        self.assertTrue(item1D.checkState() == QtCore.Qt.Checked)
        self.assertTrue(item2D.checkState() == QtCore.Qt.Checked)        

        # select 1d data
        self.form.cbSelect.setCurrentIndex(2)

        # Test the current selection
        self.assertTrue(item1D.checkState() == QtCore.Qt.Checked)
        self.assertTrue(item2D.checkState() == QtCore.Qt.Unchecked)        

        # unselect 1d data
        self.form.cbSelect.setCurrentIndex(3)

        # Test the current selection
        self.assertTrue(item1D.checkState() == QtCore.Qt.Unchecked)
        self.assertTrue(item2D.checkState() == QtCore.Qt.Unchecked)        

        # select 2d data
        self.form.cbSelect.setCurrentIndex(4)

        # Test the current selection
        self.assertTrue(item1D.checkState() == QtCore.Qt.Unchecked)
        self.assertTrue(item2D.checkState() == QtCore.Qt.Checked)        

        # unselect 2d data
        self.form.cbSelect.setCurrentIndex(5)

        # Test the current selection
        self.assertTrue(item1D.checkState() == QtCore.Qt.Unchecked)
        self.assertTrue(item2D.checkState() == QtCore.Qt.Unchecked)        

        # choose impossible index and assure the code raises
        #with self.assertRaises(Exception):
        #    self.form.cbSelect.setCurrentIndex(6)

    def testFreezeTheory(self):
        """
        Assure theory freeze functionality works
        """
        # Not yet tested - agree on design first.
        pass

    def testRecursivelyCloneItem(self):
        """
        Test the rescursive QAbstractItem/QStandardItem clone
        """
        # Create an item with several branches
        item1 = QtGui.QStandardItem()
        item2 = QtGui.QStandardItem()
        item3 = QtGui.QStandardItem()
        item4 = QtGui.QStandardItem()
        item5 = QtGui.QStandardItem()
        item6 = QtGui.QStandardItem()

        item4.appendRow(item5)
        item2.appendRow(item4)
        item2.appendRow(item6)
        item1.appendRow(item2)
        item1.appendRow(item3)

        # Clone
        new_item = self.form.recursivelyCloneItem(item1)

        # assure the trees look identical
        self.assertEqual(item1.rowCount(), new_item.rowCount())
        self.assertEqual(item1.child(0).rowCount(), new_item.child(0).rowCount())
        self.assertEqual(item1.child(1).rowCount(), new_item.child(1).rowCount())
        self.assertEqual(item1.child(0).child(0).rowCount(), new_item.child(0).child(0).rowCount())

    def testReadData(self):
        """
        Test the low level readData() method
        """
        filename = ["cyl_400_20.txt"]
        self.form.manager.add_data = MagicMock()

        # Initialize signal spy instances
        spy_status_update = QtSignalSpy(self.form, self.form.communicator.statusBarUpdateSignal)
        spy_data_received = QtSignalSpy(self.form, self.form.communicator.fileDataReceivedSignal)

        # Read in the file
        self.form.readData(filename)

        # Expected two status bar updates
        self.assertEqual(spy_status_update.count(), 1)
        self.assertIn(filename[0], str(spy_status_update.called()[0]['args'][0]))


        # Check that the model contains the item
        self.assertEqual(self.form.model.rowCount(), 1)
        self.assertEqual(self.form.model.columnCount(), 1)

        # The 0th item header should be the name of the file
        model_item = self.form.model.index(0,0)
        model_name = str(self.form.model.data(model_item).toString())
        self.assertEqual(model_name, filename[0])

    def testDisplayHelp(self):
        """
        Test that the Help window gets shown correctly
        """
        partial_url = "sasgui/guiframe/data_explorer_help.html"
        button1 = self.form.cmdHelp
        button2 = self.form.cmdHelp_2

        # Click on the Help button
        QTest.mouseClick(button1, Qt.LeftButton)
        qApp.processEvents()

        # Check the browser
        self.assertIn(partial_url, str(self.form._helpView.url()))
        # Close the browser
        self.form._helpView.close()

        # Click on the Help_2 button
        QTest.mouseClick(button2, Qt.LeftButton)
        qApp.processEvents()
        # Check the browser
        self.assertIn(partial_url, str(self.form._helpView.url()))

    def testLoadFile(self):
        """
        Test the threaded call to readData()
        """
        #self.form.loadFile()
        pass

    def testGetWList(self):
        """
        Test the list of known extensions
        """
        w_list = self.form.getWlist()

        defaults = 'All (*.*);;canSAS files (*.xml);;SESANS files' +\
            ' (*.ses);;ASCII files (*.txt);;IGOR 2D files (*.asc);;' +\
            'IGOR/DAT 2D Q_map files (*.dat);;IGOR 1D files (*.abs);;'+\
            'HFIR 1D files (*.d1d);;DANSE files (*.sans);;NXS files (*.nxs)'
        default_list = defaults.split(';;')

        for format in default_list:
            self.assertIn(format, w_list)
       
    def testLoadComplete(self):
        """
        Test the callback method updating the data object
        """
        message="Loading Data Complete"
        data_dict = {"a1":Data1D()}
        output_data = (data_dict, message)

        self.form.manager.add_data = MagicMock()

        # Initialize signal spy instances
        spy_status_update = QtSignalSpy(self.form, self.form.communicator.statusBarUpdateSignal)
        spy_data_received = QtSignalSpy(self.form, self.form.communicator.fileDataReceivedSignal)

        # Read in the file
        self.form.loadComplete(output_data)

        # "Loading data complete" no longer sent in LoadFile but in callback
        self.assertIn("Loading Data Complete", str(spy_status_update.called()[0]['args'][0]))

        # Expect one Data Received signal
        self.assertEqual(spy_data_received.count(), 1)

        # Assure returned dictionary has correct data
        # We don't know the data ID, so need to iterate over dict
        data_dict = spy_data_received.called()[0]['args'][0]
        for data_key, data_value in data_dict.iteritems():
            self.assertIsInstance(data_value, Data1D)

        # Assure add_data on data_manager was called (last call)
        self.assertTrue(self.form.manager.add_data.called)

    def testNewPlot(self):
        """
        Creating new plots from Data1D/2D
        """
        loader = Loader()
        manager = DataManager()

        # get Data1D
        p_file="cyl_400_20.txt"
        output_object = loader.load(p_file)
        new_data = [manager.create_gui_data(output_object, p_file)]

        # Mask the plot show call
        Plotter.show = MagicMock()

        # Mask retrieval of the data
        self.form.plotsFromCheckedItems = MagicMock(return_value=new_data)

        # Call the plotting method
        self.form.newPlot()

        # The plot was displayed
        self.assertTrue(Plotter.show.called)

    def testUpdateModelFromPerspective(self):
        """
        Assure the model update is correct
        """
        good_item = QtGui.QStandardItem()
        bad_item = "I'm so bad"

        self.form.model.reset = MagicMock()

        self.form.updateModelFromPerspective(good_item)

        # See that the model got reset
        self.form.model.reset.assert_called_once()

        # See that the bad item causes raise
        with self.assertRaises(Exception):
            self.form.updateModelFromPerspective(bad_item)

if __name__ == "__main__":
    unittest.main()