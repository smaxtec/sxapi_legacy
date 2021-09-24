#!/usr/bin/python
# coding: utf8

import os
import re

from setuptools import setup, find_packages

requirements = ["requests", "pendulum>=2.0.2"]

test_requirements = ["pytest", "mock"]

with open("README.md") as readme_file:
    readme = readme_file.read()

# parse version
with open(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "sxapi", "__init__.py")
) as fdp:
    pattern = re.compile(r".*__version__ = '(.*?)'", re.S)
    VERSION = "0.15"

config = {
    "description": "smaXtec API client",
    "author": "Matthias Wutte",
    "long_description": readme,
    "url": "",
    "download_url": "https://github.com/smaxtec/sxapi_legacy",
    "author_email": "matthias.wutte@gmail.com",
    "version": VERSION,
    "install_requires": requirements,
    "tests_require": test_requirements,
    "packages": find_packages(),
    "scripts": [],
    "name": "sxapi",
}

setup(**config)
