#!/usr/bin/env python

from os.path import exists
from setuptools import setup, find_packages

from sqlalchemy_fileattach import __version__

setup(
    name='sqlalchemy-fileattach',
    version=__version__,
    # Your name & email here
    author='Adam Charnock',
    author_email='adam@adamcharnock.com',
    # If you had sqlalchemy_fileattach.tests, you would also include that in this list
    packages=find_packages(),
    # Any executable scripts, typically in 'bin'. E.g 'bin/do-something.py'
    scripts=[],
    # REQUIRED: Your project's URL
    url='https://github.com/adamcharnock/sqlalchemy-fileattach',
    # Put your license here. See LICENSE.txt for more information
    license='MIT',
    # Put a nice one-liner description here
    description='',
    long_description=open('README.rst').read() if exists("README.rst") else "",
    tests_require=['nose', 'path.py'],
    # Any requirements here, e.g. "Django >= 1.1.1"
    install_requires=[
        'sqlalchemy',
    ],
)
