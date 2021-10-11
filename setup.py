from cx_Freeze import setup, Executable
import os

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages=[], excludes=[])

import sys
base = 'Win32GUI' if sys.platform == 'win32' else None

options = {
    'build_exe': {
        'include_files': [
            'templates',
            'icons',
            'products.csv',
            'configs',
            os.path.join(sys.base_prefix, 'DLLs', 'sqlite3.dll'),
            os.path.join(sys.base_prefix, 'DLLs', 'tk86t.dll'),
            os.path.join(sys.base_prefix, 'DLLs', 'tcl86t.dll'),
        ],
        'includes': ['PyQt5'],
        'packages': [
            #'PyQt5',
            #'PyQt5.QtGui',
            #'PyQt5.QtWidgets',
            #'PyQt5.QtCore',
        ],
        'excludes': [
            'django',
            'Image',
            'PyQt5.Qt',
        ],
        'bin_excludes': [
            '.gitattributes',
            '.gitignore',
        ],
    },
    #'bdist_msi': bdist_msi_options,
}

executables = [
    Executable(
        script='cash.py',
        base=base,
        icon="icons/cash.ico"
    )
]

# py3.7
#install_requires = ['https://github.com/francescpuig7/InvoiceGenerator/archive/master.zip',]

# py 3.9
# Clonar repo, pip install -e . i descomentar la seguent linia
#install_requires = ['InvoiceGenerator-master']

setup(name='cash',
      version='1.2.1',
      description='A cash program for a bars and restaurants',
      #options = dict(build_exe = buildOptions),
      options=options,
      executables=executables,
      install_requires=install_requires,
      author='Francesc Puig')
