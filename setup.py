#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
setup.py
A module that installs supervsior as a module
"""
from glob import glob
from os.path import basename, splitext

from setuptools import find_packages, setup

version = {}
with open('src/supervisor/version.py', encoding='utf-8') as fp:
    exec(fp.read(), version)

setup(
    name='agrc-supervisor',
    version=version['__version__'],
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
        'requests==2.28.*',
        'sendgrid==6.9.*',
    ],
    extras_require={
        'tests': [
            'pylint-quotes==0.2.*',
            'pylint==2.16.*',
            'pytest-cov==4.*',
            'pytest-instafail==0.4.*',
            'pytest-isort==3.1.*',
            'pytest-mock==3.10.*',
            'pytest-pylint==0.19.*',
            'pytest-watch==4.2.*',
            'pytest==7.2.*',
            'yapf==0.32.*',
        ]
    },
    setup_requires=[
        'pytest-runner',
    ],
)
