#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
setup.py
A module that installs supervisor as a module
"""

from glob import glob
from os.path import basename, splitext

from setuptools import find_packages, setup

version = {}
with open("src/supervisor/version.py", encoding="utf-8") as fp:
    exec(fp.read(), version)

setup(
    name="ugrc-supervisor",
    version=version["__version__"],
    license="MIT",
    description="A watchdog module for scheduled scripts that sends notifications, including any uncaught exceptions.",
    author="UGRC",
    author_email="ugrc-developers@utah.gov",
    url="https://github.com/agrc/supervisor",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Utilities",
    ],
    project_urls={
        "Issue Tracker": "https://github.com/agrc/supervisor/issues",
    },
    keywords=["gis"],
    install_requires=[
        "sendgrid==6.*",
    ],
    extras_require={
        "tests": [
            "pytest-cov>=6,<8",
            "pytest-instafail==0.5.*",
            "pytest-mock==3.*",
            "pytest-watch==4.*",
            "pytest==8.*",
            "ruff==0.*",
        ]
    },
    setup_requires=[
        "pytest-runner",
    ],
)
