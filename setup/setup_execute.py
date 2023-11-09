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

from logging import getLogger
import bpy

from ..syntax import Syntax

from .setup_collection import CollectionStatus, SetupCollection


module_logger = getLogger(f'{Syntax.TOOLNAME}.{__name__}')


class SetupExecution:
    def __init__(self, order: tuple[CollectionStatus]) -> bpy.types.Object:
        module_logger.info(f'Start Initiating Instance : {self.__class__.__name__}')
        self.order = order

    def execute(self):
        for collection in reversed(self.order):
            module_logger.info(f'Setup collection : {collection.name}')
            # MemberObjectからSourceObjectとChildReleaseObjectに、CollectionStatusからSetupCollectionに移行・生成。
            setup_collection: SetupCollection = collection.migrate()
            release_obj = setup_collection.setup()
        return release_obj
