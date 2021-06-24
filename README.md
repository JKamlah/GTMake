GTMake
--------
![Python 3.6](https://img.shields.io/badge/python-3.6-yellow.svg)
![license](https://img.shields.io/badge/license-Apache%20License%202.0-blue.svg)

## Overview
**Creating gitrepobased GT-Linepairs with ease**
Here you find scripts to:
- generate gt-linepairs with tesserocr
- creating subsets
- create gitrepos for further processing e.g. GTCheck
- delete files if gt.txt get rejected e.g. by GTCheck 

## Installation

This installation is tested with Ubuntu and we expect that it should
work for other similar environments.

### 1. Requirements
- Python> 3.6

### 3. Installation into a Python Virtual Environment

    $ python3 -m venv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt

## Process steps

### Start the process

    $ python3 gtmake.py [Path-to-images] [--arguments] 

### To see all options 

    $ python3 gtmake.py --help 

Copyright and License
--------

Copyright (c) 2021 Universitätsbibliothek Mannheim

Author:
 * [Jan Kamlah](https://github.com/jkamlah)

**GTMake** is Free Software. You may use it under the terms of the Apache 2.0 License.
See [LICENSE](./LICENSE) for details.
