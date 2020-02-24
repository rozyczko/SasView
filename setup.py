# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
    Setup for SasView
    TODO: Add checks to see that all the dependencies are on the system
"""
from __future__ import print_function

import os
import subprocess
import shutil
import sys
from distutils.command.build_ext import build_ext
from distutils.core import Command

import numpy as np
from setuptools import Extension, setup

try:
    import tinycc.distutils
except ImportError:
    pass

# Manage version number ######################################
with open(os.path.join("src", "sas", "sasview", "__init__.py")) as fid:
    for line in fid:
        if line.startswith('__version__'):
            VERSION = line.split('"')[1]
            break
    else:
        raise ValueError("Could not find version in src/sas/sasview/__init__.py")
##############################################################

package_dir = {}
package_data = {}
packages = []
ext_modules = []

CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SASVIEW_BUILD = os.path.join(CURRENT_SCRIPT_DIR, "build")

# TODO: build step should not be messing with existing installation!!
sas_dir = os.path.join(os.path.expanduser("~"), '.sasview')
if os.path.isdir(sas_dir):
    f_path = os.path.join(sas_dir, "sasview.log")
    if os.path.isfile(f_path):
        os.remove(f_path)
    f_path = os.path.join(sas_dir, 'config', "custom_config.py")
    if os.path.isfile(f_path):
        os.remove(f_path)

# Optionally clean before build.
dont_clean = 'update' in sys.argv
if dont_clean:
    sys.argv.remove('update')
elif os.path.exists(SASVIEW_BUILD):
    print("Removing existing build directory", SASVIEW_BUILD, "for a clean build")
    shutil.rmtree(SASVIEW_BUILD)

# 'sys.maxsize' and 64bit: Not supported for python2.5
is_64bits = sys.maxsize > 2**32

# determine if this run requires building of Qt GUI ui->py
build_qt = True
# _standard_ commands which shouldn't trigger the Qt build
no_build_commands = ['clean', 'sdist', 'bdist', 'check', 'upload', 'register']
# also, any command with --help
no_build_commands.append('--help')

for c in no_build_commands:
    if any([c in b for b in sys.argv]):
        build_qt = False
        break

enable_openmp = False
if sys.platform == 'darwin':
    if not is_64bits:
        # Disable OpenMP
        enable_openmp = False
    else:
        # Newer versions of Darwin don't support openmp
        try:
            darwin_ver = int(os.uname()[2].split('.')[0])
            if darwin_ver >= 12:
                enable_openmp = False
        except:
            print("PROBLEM determining Darwin version")

# Options to enable OpenMP
copt = {'msvc': ['/openmp'],
        'mingw32': ['-fopenmp'],
        'unix': ['-fopenmp']}
lopt = {'msvc': ['/MANIFEST'],
        'mingw32': ['-fopenmp'],
        'unix': ['-lgomp']}

# Platform-specific link options
platform_lopt = {'msvc': ['/MANIFEST']}
platform_copt = {}

# Set copts to get compile working on OS X >= 10.9 using clang
if sys.platform == 'darwin':
    try:
        darwin_ver = int(os.uname()[2].split('.')[0])
        if darwin_ver >= 13 and darwin_ver < 14:
            platform_copt = {
                'unix': ['-Wno-error=unused-command-line-argument-hard-error-in-future']}
    except:
        print("PROBLEM determining Darwin version")


class DisableOpenMPCommand(Command):
    description = "The version of MinGW that comes with Anaconda does not come with OpenMP :( "\
                  "This commands means we can turn off compiling with OpenMP for this or any "\
                  "other reason."
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()
        global enable_openmp
        enable_openmp = False

    def run(self):
        pass


class build_ext_subclass(build_ext):
    def build_extensions(self):
        # Get 64-bitness
        c = self.compiler.compiler_type
        print("Compiling with %s (64bit=%s)" % (c, str(is_64bits)))

        # OpenMP build options
        if enable_openmp:
            if c in copt:
                for e in self.extensions:
                    e.extra_compile_args = copt[c]
            if c in lopt:
                for e in self.extensions:
                    e.extra_link_args = lopt[c]

        # Platform-specific build options
        if c in platform_lopt:
            for e in self.extensions:
                e.extra_link_args = platform_lopt[c]

        if c in platform_copt:
            for e in self.extensions:
                e.extra_compile_args = platform_copt[c]

        build_ext.build_extensions(self)


class BuildSphinxCommand(Command):
    description = "Build Sphinx documentation."
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        ''' First builds the sasmodels documentation if the directory
        is present. Then builds the sasview docs.
        '''
        ### AJJ - Add code for building sasmodels docs here:
        # check for doc path
        SASMODELS_DOCPATH = os.path.abspath(os.path.join(os.getcwd(), '..', 'sasmodels', 'doc'))
        print("========= check for sasmodels at", SASMODELS_DOCPATH, "============")
        if os.path.exists(SASMODELS_DOCPATH):
            if os.path.isdir(SASMODELS_DOCPATH):
                # if available, build sasmodels docs
                print("============= Building sasmodels model documentation ===============")
                smdocbuild = subprocess.call([
                    "make",
                    "PYTHON=%s" % sys.executable,
                    "-C", SASMODELS_DOCPATH,
                    "html"
                ])
        else:
            # if not available warning message
            print("== !!WARNING!! sasmodels directory not found. Cannot build model docs. ==")

        #Now build sasview (+sasmodels) docs
        sys.path.append("docs/sphinx-docs")
        import build_sphinx
        build_sphinx.rebuild()

if build_qt:
    _ = subprocess.call([sys.executable, "src/sas/qtgui/convertUI.py"])


# sas module
package_dir["sas"] = os.path.join("src", "sas")
packages.append("sas")

# sas module
# qt module
package_dir["sas.qtgui"] = os.path.join("src", "sas", "qtgui")
packages.append("sas.qtgui")

# sas module
package_dir["sas.sascalc"] = os.path.join("src", "sas", "sascalc")
packages.append("sas.sascalc")

# sas.sascalc.invariant
package_dir["sas.sascalc.invariant"] = os.path.join(
    "src", "sas", "sascalc", "invariant")
packages.extend(["sas.sascalc.invariant"])


# sas.sascalc.dataloader
package_dir["sas.sascalc.dataloader"] = os.path.join(
    "src", "sas", "sascalc", "dataloader")
package_data["sas.sascalc.dataloader.readers"] = ['schema/*.xsd']
packages.extend(["sas.sascalc.dataloader", "sas.sascalc.dataloader.readers",
                 "sas.sascalc.dataloader.readers.schema"])


# sas.sascalc.calculator
package_dir["sas.sascalc.calculator"] = os.path.join(
    "src", "sas", "sascalc", "calculator")
packages.append("sas.sascalc.calculator")


# sas.sascalc.pr
srcdir = os.path.join("src", "sas", "sascalc", "pr", "c_extensions")
package_dir["sas.sascalc.pr"] = os.path.join("src", "sas", "sascalc", "pr")
packages.append("sas.sascalc.pr")
ext_modules.append(Extension("sas.sascalc.pr._pr_inversion",
                             sources=[os.path.join(srcdir, "Cinvertor.c"),
                                      os.path.join(srcdir, "invertor.c"),
                                      ],
                             include_dirs=[],
                             ))


# sas.sascalc.file_converter
mydir = os.path.join("src", "sas", "sascalc", "file_converter", "c_ext")
package_dir["sas.sascalc.file_converter"] = os.path.join(
    "src", "sas", "sascalc", "file_converter")
packages.append("sas.sascalc.file_converter")
ext_modules.append(Extension("sas.sascalc.file_converter._bsl_loader",
                             sources=[os.path.join(mydir, "bsl_loader.c")],
                             include_dirs=[np.get_include()],
                             ))

# sas.sascalc.corfunc
package_dir["sas.sascalc.corfunc"] = os.path.join(
    "src", "sas", "sascalc", "corfunc")
packages.append("sas.sascalc.corfunc")

# sas.sascalc.fit
package_dir["sas.sascalc.fit"] = os.path.join("src", "sas", "sascalc", "fit")
packages.append("sas.sascalc.fit")

# Data util
package_dir["sas.sascalc.data_util"] = os.path.join(
    "src", "sas", "sascalc", "data_util")
packages.append("sas.sascalc.data_util")

# QTGUI
## UI
package_dir["sas.qtgui.UI"] = os.path.join(
    "src", "sas", "qtgui", "UI")
packages.append("sas.qtgui.UI")

## UnitTesting
package_dir["sas.qtgui.UnitTesting"] = os.path.join(
    "src", "sas", "qtgui", "UnitTesting")
packages.append("sas.qtgui.UnitTesting")

## Utilities
package_dir["sas.qtgui.Utilities"] = os.path.join(
    "src", "sas", "qtgui", "Utilities")
packages.append("sas.qtgui.Utilities")
package_dir["sas.qtgui.UtilitiesUI"] = os.path.join(
    "src", "sas", "qtgui", "Utilities","UI")
packages.append("sas.qtgui.Utilities.UI")

package_dir["sas.qtgui.Calculators"] = os.path.join(
    "src", "sas", "qtgui", "Calculators")
package_dir["sas.qtgui.Calculators.UI"] = os.path.join(
    "src", "sas", "qtgui", "Calculators", "UI")
packages.extend(["sas.qtgui.Calculators", "sas.qtgui.Calculators.UI"])

package_dir["sas.qtgui.MainWindow"] = os.path.join(
    "src", "sas", "qtgui", "MainWindow")
package_dir["sas.qtgui.MainWindow.UI"] = os.path.join(
    "src", "sas", "qtgui", "MainWindow", "UI")
packages.extend(["sas.qtgui.MainWindow", "sas.qtgui.MainWindow.UI"])

## Perspectives
package_dir["sas.qtgui.Perspectives"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives")
packages.append("sas.qtgui.Perspectives")

package_dir["sas.qtgui.Perspectives.Invariant"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Invariant")
package_dir["sas.qtgui.Perspectives.Invariant.UI"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Invariant", "UI")
packages.extend(["sas.qtgui.Perspectives.Invariant", "sas.qtgui.Perspectives.Invariant.UI"])

package_dir["sas.qtgui.Perspectives.Fitting"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Fitting")
package_dir["sas.qtgui.Perspectives.Fitting.UI"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Fitting", "UI")
packages.extend(["sas.qtgui.Perspectives.Fitting", "sas.qtgui.Perspectives.Fitting.UI"])

package_dir["sas.qtgui.Perspectives.Inversion"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Inversion")
package_dir["sas.qtgui.Perspectives.Inversion.UI"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Inversion", "UI")
packages.extend(["sas.qtgui.Perspectives.Inversion", "sas.qtgui.Perspectives.Inversion.UI"])

package_dir["sas.qtgui.Perspectives.Corfunc"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Corfunc")
package_dir["sas.qtgui.Perspectives.Corfunc.UI"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Corfunc", "UI")
packages.extend(["sas.qtgui.Perspectives.Corfunc", "sas.qtgui.Perspectives.Corfunc.UI"])

## Plotting
package_dir["sas.qtgui.Plotting"] = os.path.join(
    "src", "sas", "qtgui", "Plotting")
package_dir["sas.qtgui.Plotting.UI"] = os.path.join(
    "src", "sas", "qtgui", "Plotting", "UI")
package_dir["sas.qtgui.Plotting.Slicers"] = os.path.join(
    "src", "sas", "qtgui", "Plotting", "Slicers")
package_dir["sas.qtgui.Plotting.Masks"] = os.path.join(
    "src", "sas", "qtgui", "Plotting", "Masks")
packages.extend(["sas.qtgui.Plotting", "sas.qtgui.Plotting.UI",
                 "sas.qtgui.Plotting.Slicers", "sas.qtgui.Plotting.Masks"])

EXTENSIONS = [".c", ".cpp"]


def append_file(file_list, dir_path):
    """
    Add sources file to sources
    """
    for f in os.listdir(dir_path):
        if os.path.isfile(os.path.join(dir_path, f)):
            _, ext = os.path.splitext(f)
            if ext.lower() in EXTENSIONS:
                file_list.append(os.path.join(dir_path, f))
        elif os.path.isdir(os.path.join(dir_path, f)) and \
                not f.startswith("."):
            sub_dir = os.path.join(dir_path, f)
            for new_f in os.listdir(sub_dir):
                if os.path.isfile(os.path.join(sub_dir, new_f)):
                    _, ext = os.path.splitext(new_f)
                    if ext.lower() in EXTENSIONS:
                        file_list.append(os.path.join(sub_dir, new_f))


# Comment out the following to avoid rebuilding all the models
file_sources = []

# SasView
package_data['sas'] = ['logging.ini']
package_data['sas.sasview'] = ['images/*',
                               'media/*',
                               'test/*.txt',
                               'test/1d_data/*',
                               'test/2d_data/*',
                               'test/convertible_files/*',
                               'test/coordinate_data/*',
                               'test/image_data/*',
                               'test/media/*',
                               'test/other_files/*',
                               'test/save_states/*',
                               'test/sesans_data/*',
                               'test/upcoming_formats/*',
                               ]
packages.append("sas.sasview")
package_data['sas.qtgui'] = ['Calculators/UI/*',
                             'MainWindow/UI/*',
                             'Perspectives/Corfunc/UI/*',
                             'Perspectives/Fitting/UI/*',
                             'Perspectives/Invariant/UI/*',
                             'Perspectives/Inversion/UI/*',
                             'Plotting/UI/*',
                             'Utilities/UI/*',
                             'UI/*',
                             'UI/res/*',
                             ]
packages.append("sas.qtgui")

required = [
    'bumps>=0.7.5.9', 'periodictable>=1.5.0', 'pyparsing>=2.0.0',
    'lxml', 'h5py',

    # The following dependecies won't install automatically, so assume them
    # The numbers should be bumped up for matplotlib and wxPython as well.
    # 'numpy>=1.4.1', 'scipy>=0.7.2', 'matplotlib>=0.99.1.1',
    # 'wxPython>=2.8.11', 'pil',
]

if os.name == 'nt':
    required.extend(['html5lib', 'reportlab'])
else:
    # 'pil' is now called 'pillow'
    required.extend(['pillow'])

# Set up SasView
setup(
    name="sasview",
    version=VERSION,
    description="SasView application",
    author="SasView Team",
    author_email="developers@sasview.org",
    url="http://sasview.org",
    license="PSF",
    keywords="small-angle x-ray and neutron scattering analysis",
    download_url="https://github.com/SasView/sasview.git",
    package_dir=package_dir,
    packages=packages,
    package_data=package_data,
    ext_modules=ext_modules,
    install_requires=required,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            "sasview=sas.qtgui.MainWindow.MainWindow:run_sasview",
        ]
    },
    cmdclass={'build_ext': build_ext_subclass,
              'docs': BuildSphinxCommand,
              'disable_openmp': DisableOpenMPCommand}
)
