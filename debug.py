# Copyright (C) 2022 SyureOjisan
#
# This file is part of WM Setup Tools.
#
# WM Setup Tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# WM Setup Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WM Setup Tools.  If not, see <http://www.gnu.org/licenses/>.


import logging

from logging.handlers import RotatingFileHandler

from .syntax import Syntax

class LoggingContext:
    def __init__(self, logger, level=None, handler=None, close=True):
        self.logger = logger
        self.level = level
        self.handler = handler
        self.close = close

    def __enter__(self):
        if self.level is not None:
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)
        if self.handler:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            self.handler.setFormatter(formatter)
            self.logger.addHandler(self.handler)

    def __exit__(self, et, ev, tb):
        if self.level is not None:
            self.logger.setLevel(self.old_level)
        if self.handler:
            self.logger.removeHandler(self.handler)
        if self.handler and self.close:
            self.handler.close()


def debug_execute(logger):
    def __func_wrapper(func):
        def __wrapper(self, context):
            fh = RotatingFileHandler(filename=f'{Syntax.TOOLNAME}_{self.__class__.__name__}.log', mode='w', maxBytes=1000000, encoding='utf-8')
            
            with LoggingContext(logger, level=logging.DEBUG, handler=fh) as _:            
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                fh.setFormatter(formatter)

                return func(self, context)

        return __wrapper 

    return __func_wrapper


def debug_invoke(logger):
    def __func_wrapper(func):
        def __wrapper(self, context, event):
            fh = RotatingFileHandler(filename=f'{Syntax.TOOLNAME}_{self.__class__.__name__}.log', mode='w', maxBytes=1000000, encoding='utf-8')
            
            with LoggingContext(logger, level=logging.DEBUG, handler=fh) as _:            
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                fh.setFormatter(formatter)

                return func(self, context, event)

        return __wrapper   
    return __func_wrapper
