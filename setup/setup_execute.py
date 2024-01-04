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

import bpy

import logging

from .setup_collection import CollectionStatus, SourceCollectionStatus, SetupCollection

from ..syntax import Syntax


logger = logging.getLogger(f'{Syntax.TOOLNAME}.{__name__}')


class SetupExecution:
    def __init__(self, order: tuple[CollectionStatus]) -> bpy.types.Object:
        logger.info(f'Start Initiating Instance : {self.__class__.__name__}')
        self.order = order

    def execute(self):
        release_objects = list()
        is_exist_pure_abstract_root_collection = False
        for collection in reversed(self.order):
            logger.info(f'Setup collection : {collection.name}')
            # MemberObjectからSourceObjectとChildReleaseObjectに、CollectionStatusからSetupCollectionに移行・生成。
            setup_collection: SetupCollection = collection.migrate()
            if collection.is_pure_abstract_root:
                is_exist_pure_abstract_root_collection = True
                continue
            release_obj = setup_collection.setup()
            if type(collection) is SourceCollectionStatus:
                release_objects.append(release_obj)

        if is_exist_pure_abstract_root_collection:
            return tuple(release_objects)
        return (release_obj, )
