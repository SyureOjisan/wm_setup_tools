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

from abc import ABC, abstractmethod

from bpy.types import Operator, PropertyGroup, UIList

from bpy.props import BoolProperty, StringProperty

from .. import debug

from ..setting.setting_check import check_data

from ..syntax import Icon, Props, SAMKStructureError, SAMKSyntaxError, Syntax, SYS_SPECS, ALL_SYS_SPECS, SELECTABLE_SYS_SPECS

from ..function import set_active_only

import logging

from ..setup import setup_collection as sucoll

from ..setting.setting_command import SAMK_OT_AddCommand, SAMK_OT_RemoveCommand, ScopeType, current_scope


logger = logging.getLogger(f'{Syntax.TOOLNAME}')


def update_specs(self, context: bpy.context):
    scene = context.scene
    
    # delete all specs
    for _ in scene.samk.specs:
        scene.samk.specs.remove(0)

    # copy userdefs to specs
    for spec_userdef in scene.samk.specs_userdef:
        new_spec = scene.samk.specs.add()
        new_spec.name = spec_userdef.name
        new_spec.is_enabled = spec_userdef.is_enabled

    # register system reserved specs
    spec_names = tuple(spec.name for spec in scene.samk.specs)
    for sys_spec in ALL_SYS_SPECS:
        if sys_spec not in spec_names:
            new_spec = scene.samk.specs.add()
            new_spec.name = sys_spec

    # set is_enabled of default and disable
    for spec in scene.samk.specs:
        if spec.name == SYS_SPECS.DEFAULT:
            spec.is_enabled = True
            continue
        if spec.name == SYS_SPECS.DISABLE:
            spec.is_enabled = False
            continue


class SAMKSpec(PropertyGroup):
    name: StringProperty(
        name='Spec name',
        description='Spec name for setup.',
        default='Default'
    )

    is_enabled: BoolProperty(
        name='check box for enabled spec name',
        description='Check the specs for which setup is activated.',
        default=False
    )


class SAMKSpecUserDef(PropertyGroup):
    name: StringProperty(
        name='Spec name',
        description='Spec name for setup.',
        default='Default',
        update=update_specs
    )

    is_enabled: BoolProperty(
        name='check box for enabled spec name',
        description='Check the specs for which setup is activated.',
        default=False,
        update=update_specs
    )


class SAMK_UL_SpecList(UIList):
    def draw_item(self, context: bpy.context, layout, data, item, icon, active_data,
                  active_propname, index):

        scene = context.scene

        custom_icon = Icon.SPEC

        row = layout.row()

        # row.prop(item, 'name', text='')
        row.label(text=item.name, icon=custom_icon)
        row.prop(item, 'is_enabled', text='')
        remove_op = row.operator(SAMK_OT_RemoveSpec.bl_idname, text='', icon='TRASH')
        remove_op.index_delete = index


class SAMK_OT_AddSpec(Operator):
    bl_idname = 'samk.add_spec'
    bl_label = 'Add new spec'

    @debug.debug_execute(logger)
    def execute(self, context):
        scene = context.scene
        if self.is_already_exist_spec(context):
            return {'FINISHED'}
        if self.is_empty_spec_name(context):
            return {'FINISHED'}
        if self.is_system_reserved_name(context):
            return {'FINISHED'}
        new_spec = context.scene.samk.specs_userdef.add()
        new_spec.name = scene.samk.new_spec_name
        
        return {'FINISHED'}

    @debug.debug_invoke(logger)
    def invoke(self, context, event):
        scene = context.scene
        scene.samk.new_spec_name = ''

        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=800)

    def draw(self, context: bpy.context):
        scene = context.scene
        layout = self.layout
        column = layout.column()

        column.prop(scene.samk, 'new_spec_name')

        column.alert = True
        if self.is_already_exist_spec(context):
            column.label(text='Typed spec name is already exist.')
        if self.is_empty_spec_name(context):
            column.label(text='Typed spec name is empty.')
        if self.is_system_reserved_name(context):
            column.label(text='Typed spec name is system reserved.')

    
    def is_already_exist_spec(self, context):
        scene = context.scene
        return scene.samk.new_spec_name in [spec.name for spec in scene.samk.specs_userdef]

    def is_empty_spec_name(self, context):
        scene = context.scene
        return scene.samk.new_spec_name == ''

    def is_system_reserved_name(self, context):
        scene = context.scene
        return scene.samk.new_spec_name in ALL_SYS_SPECS


class SAMK_OT_RemoveSpec(Operator):
    bl_idname = 'samk.remove_spec'
    bl_label = 'Delete spec'
    
    index_delete: bpy.props.IntProperty(default=0)

    @classmethod
    def poll(cls, context):
        return True
        # return context.scene.samk.specs and (context.scene.samk.specs_enum != SYS_SPECS.DEFAULTONLY)

    @debug.debug_execute(logger)
    def execute(self, context: bpy.context):
        samk_specs = context.scene.samk.specs_userdef
        samk_specs.remove(self.index_delete)
        update_specs(self, context)

        return {'FINISHED'}


class SAMK_OT_LoadSpecs(Operator):
    bl_idname = 'samk.load_specs'
    bl_label = 'Load specs from objects'

    @classmethod
    def poll(cls, context):
        return context.scene.samk.specs

    @debug.debug_execute(logger)
    def execute(self, context):
        # do something

        return {'FINISHED'}


def update_property_candidates_by_scope_type(self, context: bpy.context):
    scope_type: ScopeType = current_scope()
    scope_type.update_all()

    context.scene.samk.command_for_add.strategy = scope_type.initialized_strategy_name()


def update_scoped_object(self, context: bpy.context):
    scoped_collection_name = context.scene.samk.scoped_collection
    try:
        scoped_real_collection = bpy.data.collections[scoped_collection_name]
    except KeyError:
        print(f'Collection \'{scoped_collection_name}\' not found.')
        return
    scoped_collection = sucoll.CollectionFactory.create_collection(scoped_real_collection)
    context.scene.samk.scoped_object = scoped_collection.source_objects[0].name


def source_collections():
    collections = list()

    def append_recursively(collection):
        if isinstance(collection, (sucoll.SourceCollectionStatus, sucoll.SubSourceCollectionStatus)):
            collections.append(collection)
            for member in collection.member_collections:
                append_recursively(member)

    root_source_collections = sucoll.CollectionFactory.root_source_colletions(bpy.context.scene.collection)

    for collection in root_source_collections:
        append_recursively(collection)

    return tuple(collections)


def exclude_source_collections(is_exclude: bool = False):
    for collection in source_collections():
        collection.exclude(is_exclude)


def scoped_collection_candidates(self, context: bpy.context):
    collection_candidates = list()
    for collection in source_collections():
        if len(collection.source_objects):
            collection_candidates.append(tuple(collection.name for _ in range(3)))

    return collection_candidates


def scoped_object_candidates(self, context: bpy.context):
    object_candidates = list()
    scoped_collection_name = context.scene.samk.scoped_collection
    try:
        scoped_real_collection = bpy.data.collections[scoped_collection_name]
    except KeyError:
        print(f'Collection \'{scoped_collection_name}\' is not found or invalid name.')
        return [('', '', '', )]
    scoped_collection = sucoll.CollectionFactory.create_collection(scoped_real_collection)

    for obj in scoped_collection.source_objects:
        object_candidates.append(tuple(obj.name for _ in range(3)))

    return object_candidates


def update_active_object(self, context):
    object_to_active = bpy.data.objects[context.scene.samk.scoped_object]
    set_active_only(object_to_active)

    update_property_candidates_by_scope_type(self, context)


class SAMK_OT_SetupOutliner(bpy.types.Operator):
    bl_idname = 'samk.setupoutliner'
    bl_label = 'Setup Outliner'
    bl_description = 'Launch setup outliner'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.context):
        active_obj = context.active_object

        collections = source_collections()

        if len(collections) == 0:
            return False

        for collection in collections:
            if active_obj in collection.real_source_objects:
                return True
        return False

    @debug.debug_execute(logger)
    def execute(self, context):
        scene = context.scene

        self.report({'INFO'}, 'WM Setup Tools: Setup Outliner is closed.')
        print(f'Operator \'{self.bl_idname}\' is executed')

        return {'FINISHED'}

    @debug.debug_invoke(logger)
    def invoke(self, context, event):
        self.is_error = False
        try:
            update_property_candidates_by_scope_type(self, context)

            active_obj = context.active_object

            exclude_source_collections()

            collections = source_collections()

            for collection in collections:
                if active_obj in collection.real_source_objects:
                    context.scene.samk.scoped_collection = collection.name
                    break

            context.scene.samk.scoped_object = active_obj.name

            for spec in context.scene.samk.specs:  # for fixing bug of spec enum
                spec.name = spec.name

        except SAMKSyntaxError as e:
            self.report({'ERROR'}, f'WM Setup Tools: Prefix Syntax error occurred. :\'{e}\'')
            print(f'Operator \'{self.bl_idname}\' is aborted')
            self.is_error = True
            self.error = e
        except SAMKStructureError as e:
            self.report({'ERROR'}, f'WM Setup Tools: Object structure error occurred. :\'{e}\'')
            print(f'Operator \'{self.bl_idname}\' is aborted')
            self.is_error = True
            self.error = e

        scene = context.scene
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=800)

    def draw(self, context: bpy.context):
        scene = context.scene
        layout = self.layout
        column = layout.column()

        if not self.is_error:
            column.prop(scene.samk, 'scoped_collection')
            column.prop(scene.samk, 'scoped_object')

            row = column.row(align=True)
            row.prop(scene.samk, 'scope_type_to_edit', expand=True)

            LayoutCommands.put(layout, context)
        else:
            column.label(text='Error occurred.')
            column.label(text=f'Error code : {self.error}')


class LayoutCommands:
    @staticmethod
    def put(layout, context):
        scene = context.scene

        layout.separator()
        column = layout.column()

        row = column.row(align=True)
        row.operator(SAMK_OT_AddCommand.bl_idname, text='', icon='ADD')
        row.prop(scene.samk.command_for_add, 'strategy', text='')

        column.label(text='Command List')
        column = layout.column(align=True)

        scope_type: ScopeType = current_scope()

        NUM_PROPERTIES = 4
        WIDTH_BUTTON = 0.025
        WIDTH_NAME = 0.2
        width_property = (1.0 - WIDTH_BUTTON - WIDTH_NAME) / NUM_PROPERTIES
        percent_of_total_width = [
            WIDTH_BUTTON,
            WIDTH_NAME,
        ]

        for _ in range(NUM_PROPERTIES):
            percent_of_total_width.append(width_property)

        percent_of_total_width = tuple(percent_of_total_width)

        factors = list()
        for idx, percent in enumerate(percent_of_total_width):
            remain = sum(percent_of_total_width[idx:])
            factors.append(percent / remain)

        split = LayoutRemoveOperator.put(layout, factors[0], scope_type)
        split = LayoutCommandName.put(split, factors[1], scope_type)
        LayoutProperty.put(split, scope_type, scene, NUM_PROPERTIES)


class LayoutItem(ABC):
    @classmethod
    def put(cls, layout, factor, scope_type):
        split = layout.split(factor=factor)
        column = split.column()
        for command in scope_type.this_type_commands():
            cls._item(column, command)
        return split

    @classmethod
    @abstractmethod
    def _item(cls, column, command):
        pass


class LayoutRemoveOperator(LayoutItem):
    @classmethod
    def _item(cls, column, command):
        operator_remove = column.operator(SAMK_OT_RemoveCommand.bl_idname, text='', icon='REMOVE')
        operator_remove.index = command.index


class LayoutCommandName(LayoutItem):
    @classmethod
    def _item(cls, column, command):
        column.label(text=command.name)


# New Command
# Strategy                      pos0    pos1            pos2                pos3
# SK_ApplySingle                source  destination                         spec

# MDF_Undivision                source                                      spec
# MDF_Delete                    source                                      spec

# UV_Select                     source                                      spec

# MT_Replace                    source  destination                         spec

# VG_NonDecimate                source  destination_mdf                     spec
# VG_DeleteLoop                 source                                      spec
# VG_MergeVertexSource          source  merge_distance                      spec
# VG_MergeVertexDestination     source  destination_obj destination_vg      spec
# VG_DeleteVertex               source                                      spec


class LayoutProperty:
    @staticmethod
    def put(layout: bpy.types.UILayout, scope_type, scene, num_properties):
        scope_type_icon = scope_type.icon_data()

        # property name : candidates, icon, position
        properties_alignment_order = {
            Props.SRC: ('extracted_source_candidates', scope_type_icon, 0),
            Props.DST_MDF: ('extracted_destination_mdf_candidates', Icon.MDF, 1),
            Props.DST_OBJ: ('extracted_destination_obj_candidates', Icon.OBJ, 1),
            Props.DST_VG: ('extracted_destination_vg_candidates', Icon.VG, 2),
            Props.DST: ('extracted_destination_candidates', scope_type_icon, 1),
            Props.MERGE_DIST: ('merge_distance', Icon.OPT, 1),
            Props.SPEC: ('extracted_spec_candidates', Icon.SPEC, 3),
        }

        for position in range(num_properties):

            extracted_properties_by_now_position = dict()
            for property_name, (candidates_name, icon_name, position_setting) in properties_alignment_order.items():
                if position == position_setting:
                    extracted_properties_by_now_position[property_name] = (candidates_name, icon_name)

            split = layout.split()
            column = split.column()
            for command in scope_type.this_type_commands():
                count_num = 0
                for property_name in extracted_properties_by_now_position.keys():
                    count_num += dir(command).count(property_name)
                if count_num == 0:
                    column.label(text='')
                    continue

                for property_name, (candidates_name, icon_name) in extracted_properties_by_now_position.items():
                    if property_name == Props.MERGE_DIST and property_name in dir(command):
                        column.prop(command, property_name, text='Merge distance', icon=icon_name)
                        break
                    if property_name in dir(command):
                        prop = getattr(command, property_name)
                        candidates = getattr(command, candidates_name)
                        is_exist_property = prop in [candidate.name for candidate in candidates]
                                
                        row = column.row()
                        row.alert = not is_exist_property
                        if not is_exist_property:
                            row.label(icon=Icon.GHOST)
                        row.prop_search(command, property_name, command, candidates_name, text='', icon=icon_name)
                        break


class SAMK_OT_CheckData(bpy.types.Operator):
    bl_idname = 'samk.checkdata'
    bl_label = 'Check Data'
    bl_description = 'Check source objects\' commands and collection structure'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.context):
        PREFIX = (Syntax.COL_SRC, Syntax.COL_SUBSRC)
        try:
            return context.active_object.users_collection[0].name.startswith(PREFIX)
        except AttributeError:
            return False

    @debug.debug_execute(logger)
    def execute(self, context):
        scene = context.scene

        self.report({'INFO'}, 'WM Setup Tools: Check commands is closed.')
        print(f'Operator \'{self.bl_idname}\' is executed')

        return {'FINISHED'}

    @debug.debug_invoke(logger)
    def invoke(self, context: bpy.context, event):
        try:
            self.root_collection = check_data(context.active_object)
        except SAMKStructureError as e:
            self.error_code = e
            self.can_setup = False
        except SAMKSyntaxError as e:
            self.error_code = e
            self.can_setup = False
        else:
            self.error_code = 'No error occurred.'
            self.can_setup = True

        scene = context.scene
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=700)

    def draw(self, context: bpy.context):
        scene = context.scene
        layout = self.layout
        column = layout.column()

        if not self.can_setup:
            column.alert = True
            column.label(text=f'Error Code : {self.error_code}')
            return
        column.label(text=f'Passed checking collection tree \'{self.root_collection.name}\'. {self.error_code}')


classes = [
    SAMK_OT_AddSpec,
    SAMK_OT_RemoveSpec,
    SAMK_OT_LoadSpecs,
    SAMK_OT_SetupOutliner,
    SAMK_OT_CheckData,
    SAMKSpec,
    SAMKSpecUserDef,
    SAMK_UL_SpecList,
]
