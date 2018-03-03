#!/usr/bin/env python3

from distutils.core import setup

with open('README.rst', 'r') as readme:
    long_description = readme.read()

setup(name='kmyimport',
      version='0.9.1',
      description='Conversion scripts for KMyMoney',
      long_description=long_description,
      author='Michal Minář',
      author_email='mic.liamg@gmail.com',
      url="https://github.com/michojel/kmyimport",
      packages=['kmyimport'],
      scripts=['bin/air2kmy.py', 'bin/entropay2kmy.py', 'bin/fio2kmy.py', 'bin/roklen2kmy.py'],
      requires=['chardet'])
