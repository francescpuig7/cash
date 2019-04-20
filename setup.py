from distutils.core import setup
import os
import py2exe
from cash import __version__ as version

includes = [
    "PyQt5",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "pandas",
]

setup(
    name='Kaisher',
    version=version,
    author='Francesc Puig Plana',
    packages=['Kaisher'],
    windows=['cash.py'],
    options = {
        'py2exe': {
            'packages': ['pandas', 'PyQt5'],
            'includes': includes,
        }
    }
)
