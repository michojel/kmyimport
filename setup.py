#!/usr/bin/env python3

from distutils.core import setup

setup(name='kmyimport',
      version='0.9',
      description='Conversion scripts for KMyMoney',
      author='Michal Minář',
      author_email='mic.liamg@gmail.com',
      scripts=['air2kmy.py', 'entropay2kmy.py', 'fio2kmy.py', 'roklen2kmy.py'],
      requires=['chardet'])
