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

bl_info = {
    'name': 'WM Setup Tools',
    'author': 'SyureOjisan',
    'version': (1, 0, 0),  # big modifying, small modifying, bug fix or refactoring
    'blender': (2, 93, 0),
    'location': 'Properties > Object Data Properties',
    'description': 'Setup Tools for character modeling',
    'warning': '',
    'support': 'COMMUNITY',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Object'
}


if 'bpy' in locals():
    import imp
    imp.reload(debug)
    imp.reload(file)
    imp.reload(function)
    imp.reload(interface)
    imp.reload(operators)
    imp.reload(preferences)
    imp.reload(setting)
    imp.reload(setup)
    imp.reload(syntax)
    imp.reload(translate)
else:
    from . import debug
    from . import file
    from . import function
    from . import interface
    from . import operators
    from . import preferences
    from . import setting
    from . import setup
    from . import syntax
    from . import translate


import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, IntProperty, PointerProperty, StringProperty

from bpy.types import PropertyGroup

from .operators import SAMK_OT_NewSourceCollection, SAMK_OT_NewSubSourceCollection

from .setting.setting_operators import update_active_object, update_property_candidates_by_scope_type, scoped_collection_candidates, update_scoped_object, scoped_object_candidates, SAMKSpec, SAMKSpecUserDef

from .setting.setting_command import SAMKCommandForAdd, SAMKStrategies

from .syntax import Syntax


class SAMKAllProperty(PropertyGroup):
    new_spec_name: StringProperty(
        name='New spec name',
        description='type unique new spec name',
        default=''
    )
    specs: CollectionProperty(
        type=SAMKSpec
    )
    specs_userdef: CollectionProperty(
        type=SAMKSpecUserDef
    )
    specs_userdef_index: IntProperty(
        name='Index for spec list',
        default=0
    )
    scoped_collection: EnumProperty(
        name='Scoped collection',
        description='Scoped collection',
        items=scoped_collection_candidates,
        update=update_scoped_object
    )
    scoped_object: EnumProperty(
        name='Scoped object',
        description='Scoped object',
        items=scoped_object_candidates,
        update=update_active_object
    )
    translation_mode: EnumProperty(
        name='Translate Mode Property',
        description='Translate Mode Property',
        items=[
            (Syntax.MODE_SP, 'Substance Painter', 'Substance Painter'),
            (Syntax.MODE_MMD, 'MikuMikuDance', 'MikuMikuDance'),
            (Syntax.MODE_GE, 'Game Engine', 'Game Engine'),
            (Syntax.MODE_UDEF, 'User Defined', 'User Defined'),
        ],
        default=Syntax.MODE_MMD
    )
    profile_bgroup: PointerProperty(
        type=interface.SAMKProfileProperty,
        name='BoneGroup Profile',
        description='BoneGroup Profile'
    )
    profile_skey: PointerProperty(
        type=interface.SAMKProfileProperty,
        name='ShapeKey Profile',
        description='ShapeKey Profile'
    )
    is_enabled_mat_replacing: BoolProperty(
        name='Replace Material',
        description='Replace Material',
        default=False
    )
    udef_mode_name: StringProperty(
        name='User Defined Mode Name',
        description='User Defined Mode Name',
        default=Syntax.MODE_UDEF[1:]
    )
    is_enabled_debug_mode: BoolProperty(
        name='Enable debug interface',
        description='Enable debug interface',
        default=False
    )
    scope_type_to_edit: EnumProperty(
        name='Scope type to edit',
        description='Scope type to edit',
        items=[
            ('VG', 'Vertex Groups', 'Vertex Groups', 'GROUP_VERTEX', 0),
            ('SK', 'Shape Keys', 'Shape Keys', 'SHAPEKEY_DATA', 1),
            ('UV', 'UV Maps', 'UV Maps', 'UV', 2),
            ('MDF', 'Modifiers', 'Modifiers', 'MODIFIER_DATA', 3),
            ('MT', 'Materials', 'Materials', 'MATERIAL_DATA', 4),
        ],
        default='VG',
        update=update_property_candidates_by_scope_type
    )
    command_for_add: PointerProperty(
        type=SAMKCommandForAdd
    )


classes = interface.classes + \
    operators.classes + \
    preferences.classes + \
    setting.setting_command.classes + \
    setting.setting_spec.classes + \
    setting.setting_operators.classes + \
    [SAMKAllProperty, ]


def init_props():
    obj = bpy.types.Object
    obj.samk_strategies = PointerProperty(
        type=SAMKStrategies
    )

    scene = bpy.types.Scene
    scene.samk = PointerProperty(
        type=SAMKAllProperty
    )


def clear_props():
    obj = bpy.types.Object
    del obj.samk_strategies

    scene = bpy.types.Scene
    del scene.samk


def outliner_menu(self, context):
    self.layout.operator(SAMK_OT_NewSourceCollection.bl_idname)
    self.layout.operator(SAMK_OT_NewSubSourceCollection.bl_idname)


def register():
    bpy.types.OUTLINER_MT_context_menu.append(outliner_menu)
    bpy.types.OUTLINER_MT_collection.append(outliner_menu)
    bpy.types.OUTLINER_MT_collection_new.append(outliner_menu)

    for c in classes:
        bpy.utils.register_class(c)

    init_props()

    print('Add-on \'{}\' is enabled'.format(bl_info['name']))


def unregister():
    bpy.types.OUTLINER_MT_context_menu.remove(outliner_menu)
    bpy.types.OUTLINER_MT_collection.remove(outliner_menu)
    bpy.types.OUTLINER_MT_collection_new.remove(outliner_menu)

    for c in classes:
        bpy.utils.unregister_class(c)

    clear_props()

    print('Add-on \'{}\' is disabled'.format(bl_info['name']))


if __name__ == '__main__':
    register()
