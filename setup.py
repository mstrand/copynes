#!/usr/bin/python3
from distutils.core import setup

setup(name='copynes',
      version='alpha',
      description='Command line client for CopyNES',
      long_description='Supports ROM dumping and RAM cart transfer',
      author='Martin Strand',
      author_email='mstrand@eml.cc',
      url='https://github.com/mstrand/copynes',
      license='Public domain',
      platforms='Any',
      packages=['copynes'],
)