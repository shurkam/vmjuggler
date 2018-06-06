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

from pyVim.task import WaitForTask
from pyVmomi import vim, vmodl
import logging


class VMJHelper(object):
    """Helper class"""

    @staticmethod
    def do_task(func, catch_exception=None, show_progress=True, **kwargs):
        """
        Perform task and wait for result.

        :param func: Function to execute.
        :param catch_exception: Exception to catch during execution.
        :param bool show_progress: Show task execution progress if specified.
        :param kwargs: Function arguments.
        :return: True on success, otherwise False.
        """
        common_exceptions = [vim.fault.NoPermission]
        exceptions_to_catch = tuple(set(common_exceptions + catch_exception)) if catch_exception else tuple(common_exceptions)
        on_progress = VMJHelper._show_progress if show_progress else None
        try:
            r = WaitForTask(func(**kwargs), raiseOnError=True, onProgressUpdate=on_progress)
            return r
        except exceptions_to_catch as e:
            logging.info(f'Error: {e.msg}')
            return False

    @staticmethod
    def _show_progress(task, status):
        """
        Show task execution progress.

        Callback function for do_task

        :param task: Task object.
        :param bool status: Task status.
        :return: n/a
        """
        if isinstance(status, int):
            logging.info(f'\rCompleted {status}%')
        elif isinstance(status, str) and status == 'created':
            logging.info(f'\rStarted on {task.info.startTime}')
        elif isinstance(status, str) and status == 'completed':
            logging.info(f'\rCompleted on {task.info.completeTime}')


class Logger(object):
    """Set the logging"""

    log_level = logging.INFO  #: Log level
    log_format = '%(message)s'  #: Message format

    @classmethod
    def set(cls):
        """Set logging configuration"""
        logging.basicConfig(level=cls.log_level, format=cls.log_format)
