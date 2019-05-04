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
            'configs/config.cfg',
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
    Executable('cash.py', base=base)
]

setup(name='cash',
      version = '0.0.1a',
      description = 'A cash program for a bars and restaurants',
      #options = dict(build_exe = buildOptions),
      options=options,
      executables = executables,
      author='Francesc Puig')
