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

from ..function import select_object, set_active_only

from ..setting.setting_command import ScopeType

from ..syntax import Props, SAMKStructureError, SAMKSyntaxError, Syntax

from ..setup import setup_collection as sucoll


def check_data(obj):
    source_collections: list[sucoll.CollectionStatus] = list()

    def _try_collection_recursively(collection, count=0):
        count += 1
        for member_collection in collection.member_collections:
            if type(member_collection) is sucoll.SourceCollectionStatus:
                if count > 1:
                    raise SAMKStructureError(f'Source collection \'{member_collection.name}\' must be placed directly under root source collection.')
                source_collections.append(member_collection)
                _try_collection_recursively(member_collection, count)
                continue
            if type(member_collection) is sucoll.SubSourceCollectionStatus:
                source_collections.append(member_collection)
                _try_collection_recursively(member_collection, count)
                continue
            if type(member_collection) is sucoll.ReleaseCollectionStatus:
                raise SAMKStructureError(f'Release collection \'{member_collection.name}\' cannot be placed in setup collection.')

    root_collection = sucoll.CollectionFactory.root_collection_has_object(obj)
    _try_collection_recursively(root_collection)
    source_collections.append(root_collection)

    for source_collection in source_collections:
        source_collection.exclude(False)
        for source_obj in source_collection.source_objects:
            set_active_only(source_obj.real)
            select_object(source_obj.real, True)
            if Syntax.UNDER in source_obj.name:
                raise SAMKStructureError(f'Object: \'{source_obj.name}\' Underscores are not allowed in object name.')
            for ScopeTypeClass in ScopeType.__subclasses__():
                current_scope_type = ScopeTypeClass(source_obj.real)
                bpy.context.scene.samk.scope_type_to_edit = ScopeTypeClass.__name__.split(Syntax.UNDER)[1]
                for command in current_scope_type.this_type_commands():
                    command.update(None)
                    for prop_name in (Props.SRC, Props.DST, Props.DST_MDF, Props.DST_OBJ, Props.DST_VG, Props.SPEC):
                        candidates_name = 'extracted_' + prop_name + '_candidates'
                        if prop_name not in dir(command):
                            continue
                        prop = getattr(command, prop_name)
                        candidates = getattr(command, candidates_name)
                        if prop == '':
                            raise SAMKSyntaxError(f'Object: \'{source_obj.name}\' Command: \'{command.__class__.__name__}\' Property: \'{prop_name}\' Key is blank.')
                        if prop not in candidates:
                            raise SAMKSyntaxError(f'Object: \'{source_obj.name}\' Command: \'{command.__class__.__name__}\' Property: \'{prop_name}\' Key: \'{prop}\' is not exist.')

    return root_collection
