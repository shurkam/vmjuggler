#!/usr/bin/env python
# -*- coding: future_fstrings -*-

# MIT License
#
# Copyright (c) 2018 Alexandr Malygin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
VMJuggler provides the simple high level API to VMWare’s SDK.

It built around :mod:`pyvmomi` library with aim to simplify interaction to VMWare VCenter and it's managed objects
for DevOps crowd and those who don't want to plunge deeply to object's relations. At the same time ability
to perform actions on low level was preserved.
"""

__author__ = "Alexandr Malygin"
__copyright__ = "Copyright (c) 2018 Alexandr Malygin"
__license__ = "MIT"
__version__ = "0.1.1"

import logging
from .base_objects import VCenter, BaseVCObject, VirtualMachine, Datacenter, Folder, VApp, Network, Datastore, Host
from .base_objects import VMSnapshot
from .helpers import Logger
from .exceptions import WrongObjectTypeError

if __name__ == '__main__':
    exit(0)

Logger.log_level = logging.INFO
Logger.set()



