import unittest

# Main Window
from MainWindow.UnitTesting import AboutBoxTest
from MainWindow.UnitTesting import DataExplorerTest
from MainWindow.UnitTesting import WelcomePanelTest
from MainWindow.UnitTesting import DroppableDataLoadWidgetTest
from MainWindow.UnitTesting import GuiManagerTest
from MainWindow.UnitTesting import MainWindowTest

# Plotting
from Plotting.UnitTesting import AddTextTest
from Plotting.UnitTesting import PlotHelperTest
from Plotting.UnitTesting import PlotterBaseTest
from Plotting.UnitTesting import PlotterTest
from Plotting.UnitTesting import Plotter2DTest
from Plotting.UnitTesting import ScalePropertiesTest
from Plotting.UnitTesting import WindowTitleTest
from Plotting.UnitTesting import SetGraphRangeTest
from Plotting.UnitTesting import LinearFitTest
from Plotting.UnitTesting import PlotPropertiesTest
from Plotting.UnitTesting import PlotUtilitiesTest
from Plotting.UnitTesting import ColorMapTest
from Plotting.UnitTesting import BoxSumTest
from Plotting.UnitTesting import SlicerModelTest
from Plotting.UnitTesting import SlicerParametersTest

# Calculators
from Calculators.UnitTesting import KiessigCalculatorTest
from Calculators.UnitTesting import DensityCalculatorTest
from Calculators.UnitTesting import GenericScatteringCalculatorTest

# Utilities
from Utilities.UnitTesting import GuiUtilsTest
from Utilities.UnitTesting import SasviewLoggerTest

# Unit Testing
from UnitTesting import TestUtilsTest

# Perspectives
import path_prepare
from Perspectives.Fitting.UnitTesting import FittingWidgetTest
from Perspectives.Fitting.UnitTesting import FittingPerspectiveTest
from Perspectives.Fitting.UnitTesting import FittingLogicTest
from Perspectives.Fitting.UnitTesting import FittingUtilitiesTest
from Perspectives.Fitting.UnitTesting import FitPageTest


def suite():
    suites = (
        # Plotting
        unittest.makeSuite(PlotHelperTest.PlotHelperTest,             'test'),
        unittest.makeSuite(PlotterTest.PlotterTest,                   'test'),
        unittest.makeSuite(WindowTitleTest.WindowTitleTest,           'test'),
        unittest.makeSuite(PlotterBaseTest.PlotterBaseTest,           'test'),
        unittest.makeSuite(Plotter2DTest.Plotter2DTest,               'test'),
        unittest.makeSuite(AddTextTest.AddTextTest,                   'test'),
        unittest.makeSuite(ScalePropertiesTest.ScalePropertiesTest,   'test'),
        unittest.makeSuite(SetGraphRangeTest.SetGraphRangeTest,       'test'),
        unittest.makeSuite(LinearFitTest.LinearFitTest,               'test'),
        unittest.makeSuite(PlotPropertiesTest.PlotPropertiesTest,     'test'),
        unittest.makeSuite(PlotUtilitiesTest.PlotUtilitiesTest,       'test'),
        unittest.makeSuite(ColorMapTest.ColorMapTest,                 'test'),
        unittest.makeSuite(BoxSumTest.BoxSumTest,                     'test'),
        unittest.makeSuite(SlicerModelTest.SlicerModelTest,           'test'),
        unittest.makeSuite(SlicerParametersTest.SlicerParametersTest, 'test'),

        # Main window
        unittest.makeSuite(AboutBoxTest.AboutBoxTest,          'test'),
        unittest.makeSuite(DataExplorerTest.DataExplorerTest,  'test'),
        unittest.makeSuite(WelcomePanelTest.WelcomePanelTest,  'test'),
        unittest.makeSuite(DroppableDataLoadWidgetTest.DroppableDataLoadWidgetTest, 'test'),
        unittest.makeSuite(GuiManagerTest.GuiManagerTest,      'test'),
        unittest.makeSuite(GuiUtilsTest.GuiUtilsTest,          'test'),
        unittest.makeSuite(MainWindowTest.MainWindowTest,      'test'),

        # Utilities
        unittest.makeSuite(TestUtilsTest.TestUtilsTest,         'test'),
        unittest.makeSuite(SasviewLoggerTest.SasviewLoggerTest, 'test'),

        # Calculators
        unittest.makeSuite(KiessigCalculatorTest.KiessigCalculatorTest,                     'test'),
        unittest.makeSuite(DensityCalculatorTest.DensityCalculatorTest,                     'test'),
        unittest.makeSuite(GenericScatteringCalculatorTest.GenericScatteringCalculatorTest, 'test'),

        # Perspectives
        unittest.makeSuite(FittingPerspectiveTest.FittingPerspectiveTest, 'test'),
        unittest.makeSuite(FittingWidgetTest.FittingWidgetTest,           'test'),
        unittest.makeSuite(FittingLogicTest.FittingLogicTest,             'test'),
        unittest.makeSuite(FittingUtilitiesTest.FittingUtilitiesTest,     'test'),
        unittest.makeSuite(FitPageTest.FitPageTest,                       'test'),
    )
    return unittest.TestSuite(suites)

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
