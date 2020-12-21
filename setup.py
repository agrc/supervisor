#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
setup.py
A module that installs supervsior as a module
"""
from glob import glob
from os.path import basename, splitext

from setuptools import find_packages, setup

setup(
    name='supervisor',
    version='1.0.0',
    license='MIT',
    description='A watchdog module for scheduled scripts that sends notifications, including any uncaught exceptions.',
    author='Jake Adams, AGRC',
    author_email='jdadams@utah.gov',
    url='https://github.com/agrc/supervisor',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
    ],
    project_urls={
        'Issue Tracker': 'https://github.com/agrc/supervisor/issues',
    },
    keywords=['gis'],
    install_requires=[
        'requests',
    ],
    extras_require={
        'tests': [
            'pylint-quotes==0.2.*',
            'pylint==2.5.*',
            'pytest-cov==2.9.*',
            'pytest-instafail==0.4.*',
            'pytest-isort==1.0.*',
            'pytest-mock',
            'pytest-pylint==0.17.*',
            'pytest-watch==4.2.*',
            'pytest==5.4.*',
            'yapf==0.30.*',
        ]
    },
    setup_requires=[
        'pytest-runner',
    ],
)
