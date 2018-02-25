#!/usr/bin/env python3

from distutils.core import setup

with open('README.rst', 'r') as readme:
    long_description = readme.read()

setup(name='kmyimport',
      version='0.9',
      description='Conversion scripts for KMyMoney',
      long_descriptions=long_description,
      author='Michal Minář',
      author_email='mic.liamg@gmail.com',
      url="https://github.com/michojel/kmyimport",
      scripts=['air2kmy.py', 'entropay2kmy.py', 'fio2kmy.py', 'roklen2kmy.py'],
      requires=['chardet'])
