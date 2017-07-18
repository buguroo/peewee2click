# -*- coding: utf-8 -*-
"""
peewee2click
"""
from setuptools import setup
import os

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()

VERSION = '0.0.1'

setup(name='peewee2click',
      version=VERSION,
      long_description=README,
      classifiers=[
          'Development Status :: 4 - Beta',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
      ],
      keywords='peewee click arguments conversor',
      author='Samuel Herrero Bartolomé',
      author_email='sherrero@buguroo.com',
      url='https://github.com/buguroo/peewee2click',
      license='LGPLv3',
      py_modules=["peewee2click"],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'click==6.7',
          'peewee>=2.6',
          'tabulate==0.7.7',
      ])
