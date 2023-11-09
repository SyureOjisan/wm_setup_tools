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

from abc import ABC, abstractmethod
import bpy

from bpy.props import CollectionProperty, EnumProperty, FloatProperty, IntProperty, StringProperty

from bpy.types import Operator, PropertyGroup

from . import setting_candidates

from ..syntax import Icon, Syntax


def sort_by_index(commands):
    return tuple(sorted(commands, key=lambda c: c.index))


def current_scope(obj=None):
    return globals()['Scope_' + bpy.context.scene.samk.scope_type_to_edit](obj)


class ScopeType(ABC):
    def __init__(self, obj=None) -> None:
        super().__init__()
        if obj is None:
            self._obj = bpy.context.active_object
        else:
            self._obj = obj

    def this_type_strategies(self) -> tuple:
        strategies = list()
        scope_type_name = self.__class__.__name__.lstrip('Scope').lstrip(Syntax.UNDER)
        for key, Class in globals().items():
            if key.startswith(scope_type_name):
                strategies.append(Class)
        return strategies

    def initialized_strategy_name(self):
        return self.this_type_strategies()[0].__name__

    def this_type_commands(self) -> tuple:
        commands = list()
        for strategy in self.this_type_strategies():
            for command in strategy.commands(self._obj):
                commands.append(command)
        commands_sorted = sort_by_index(commands)
        return commands_sorted

    @abstractmethod
    def icon_data(self):
        pass

    @abstractmethod
    def names(self):
        pass

    def update_all(self):
        for command in self.this_type_commands():
            command.update(None)


class Scope_VG(ScopeType):
    def icon_data(self):
        return Icon.VG

    def names(self):
        deform_bone_names = list()
        for mdf in self._obj.modifiers:
            if mdf.type != 'ARMATURE':
                continue
            if mdf.object is None:
                continue
            for bone in mdf.object.data.bones:
                deform_bone_names.append(bone.name)

        deform_bone_names = set(deform_bone_names)
        vgroup_names = set(vg.name for vg in self._obj.vertex_groups)

        new_vgroup_names = vgroup_names.difference(deform_bone_names)

        return tuple(new_vgroup_names)


class Scope_SK(ScopeType):
    def icon_data(self):
        return Icon.SK

    def names(self):
        if self._obj.data.shape_keys is not None:
            return tuple(key.name for key in self._obj.data.shape_keys.key_blocks)
        return tuple()


class Scope_UV(ScopeType):
    def icon_data(self):
        return Icon.UV

    def names(self):
        return tuple(uv.name for uv in self._obj.data.uv_layers)


class Scope_MDF(ScopeType):
    def icon_data(self):
        return Icon.MDF

    def names(self):
        return tuple(modifier.name for modifier in self._obj.modifiers)

    def names_subdivision(self):
        return tuple(modifier.name for modifier in self._obj.modifiers if modifier.type == 'SUBSURF')

class Scope_MT(ScopeType):
    def icon_data(self):
        return Icon.MT

    def names(self):
        return tuple(mtslot.material.name for mtslot in self._obj.material_slots)
        # return tuple(material.name for material in bpy.data.materials)


class SearchProperty(PropertyGroup):
    name: StringProperty(
        name='name for property search',
        description='Name for property search.'
    )


class ExtractedSourceCandidate(SearchProperty):
    pass


class ExtractedDestinationCandidate(SearchProperty):
    pass


class ExtractedDestinationMDFCandidate(SearchProperty):
    pass


class ExtractedDestinationVGCandidate(SearchProperty):
    pass


class ExtractedDestinationOBJCandidate(SearchProperty):
    pass


def update_all(self, context):
    current_scope_type: ScopeType = current_scope()
    current_scope_type.update_all()


class SAMKPropertyGroup(PropertyGroup):
    def update_source(self, context):
        setting_candidates.SourceMediator(self).notify()

    def update_destination(self, context):
        pass

    def update_modifier(self, context):
        pass

    def update_vertexgroup(self, context):
        pass

    def update_object(self, context):
        pass

    def update(self, context):
        self.update_source(context)
        self.update_destination(context)
        self.update_modifier(context)
        self.update_vertexgroup(context)
        self.update_object(context)

    name: StringProperty(
        name='Strategy name',
        description='Strategy name.'
    )
    index: IntProperty(
    )
    spec: StringProperty(
        name='Spec name',
        description='Spec name for setup.',
        update=update_all
    )
    source: StringProperty(
        name='Source item name',
        description='Source item name.',
        update=update_all
    )
    extracted_source_candidates: CollectionProperty(
        type=ExtractedSourceCandidate
    )

    @classmethod
    def commands(cls, obj=None):
        if obj is None:
            cls._obj = bpy.context.active_object
        else:
            cls._obj = obj
        class_name = cls.__name__.lower()
        commands = getattr(cls._obj.samk_strategies, class_name)

        return commands

    @classmethod
    def this_type_scope(cls):
        class_name = cls.__name__
        scope_class_name = 'Scope_' + class_name.split(Syntax.UNDER)[0]
        ScopeClass = globals()[scope_class_name]

        return ScopeClass


class SAMKPropertyGroupWithDestination(SAMKPropertyGroup):
    def update_destination(self, context):
        setting_candidates.DestinationMediator(self).notify()

    destination: StringProperty(
        name='Destination item name',
        description='Destination item name.',
        update=update_all
    )
    extracted_destination_candidates: CollectionProperty(
        type=ExtractedDestinationCandidate
    )


class SK_ApplySingle(SAMKPropertyGroupWithDestination):
    pass


class MDF_Undivision(SAMKPropertyGroup):
    pass


class MDF_Delete(SAMKPropertyGroup):
    pass


class UV_Select(SAMKPropertyGroup):
    pass


class MT_Replace(SAMKPropertyGroupWithDestination):
    pass


class VG_NonDecimate(SAMKPropertyGroup):
    def update_modifier(self, context):
        setting_candidates.ModifierMediator(self).notify()

    destination_mdf: StringProperty(
        name='Destination modifier name',
        description='Destination modifier name.',
        update=update_all
    )
    extracted_destination_mdf_candidates: CollectionProperty(
        type=ExtractedDestinationMDFCandidate
    )


class VG_DeleteLoop(SAMKPropertyGroup):
    pass


class VG_MergeVertexSource(SAMKPropertyGroup):
    merge_distance: FloatProperty(
        name='Vertices merge distance',
        description='Vertices merge distance',
        default=0.001,
        min=0.0,
        max=1.0,
        step=1,
        precision=3
    )


class VG_MergeVertexDestination(SAMKPropertyGroup):
    def update_vertexgroup(self, context):
        setting_candidates.VertexGroupMediator(self).notify()

    destination_vg: StringProperty(
        name='Destination vertex group name',
        description='Destination vertex group name.',
        update=update_all
    )
    extracted_destination_vg_candidates: CollectionProperty(
        type=ExtractedDestinationVGCandidate
    )

    def update_object(self, context):
        setting_candidates.ObjectMediator(self).notify()

    destination_obj: StringProperty(
        name='Destination object name',
        description='Destination object name.',
        update=update_all
    )
    extracted_destination_obj_candidates: CollectionProperty(
        type=ExtractedDestinationOBJCandidate
    )


class VG_DeleteVertex(SAMKPropertyGroup):
    pass


def get_commands_for_add_callback(scene, context):
    items = list()

    current_scope_type: ScopeType = current_scope()
    for strategy in current_scope_type.this_type_strategies():
        item_name = strategy.__name__
        items.append((item_name, item_name.split(Syntax.UNDER)[1], ''))

    return items


class SAMKCommandForAdd(PropertyGroup):
    strategy: EnumProperty(
        items=get_commands_for_add_callback,
        name='Strategy name',
        description='Strategy name for setup.',
    )


class SAMKStrategies(PropertyGroup):
    sk_applysingle: CollectionProperty(
        type=SK_ApplySingle
    )

    mdf_undivision: CollectionProperty(
        type=MDF_Undivision
    )

    mdf_delete: CollectionProperty(
        type=MDF_Delete
    )

    uv_select: CollectionProperty(
        type=UV_Select
    )

    mt_replace: CollectionProperty(
        type=MT_Replace
    )

    vg_nondecimate: CollectionProperty(
        type=VG_NonDecimate
    )

    vg_deleteloop: CollectionProperty(
        type=VG_DeleteLoop
    )

    vg_mergevertexsource: CollectionProperty(
        type=VG_MergeVertexSource
    )

    vg_mergevertexdestination: CollectionProperty(
        type=VG_MergeVertexDestination
    )

    vg_deletevertex: CollectionProperty(
        type=VG_DeleteVertex
    )


def all_commands(obj=None):
    if obj is None:
        obj = bpy.context.active_object
    commands = list()
    for ScopeTypeClass in ScopeType.__subclasses__():
        commands.extend(ScopeTypeClass(obj).this_type_commands())
    return sort_by_index(commands)


def renumber():
    for idx, command in enumerate(all_commands()):
        command.index = idx


class SAMK_OT_AddCommand(Operator):
    bl_idname = 'samk.add_command'
    bl_label = 'Add a new command'

    def execute(self, context: bpy.context):
        command_next_name = context.scene.samk.command_for_add.strategy
        command_for_add = command_next_name.lower()
        commands = eval(f'context.active_object.samk_strategies.{command_for_add}')
        next_index = len(all_commands())
        command_next = commands.add()
        command_next.index = next_index
        command_next.name = command_next_name.split(Syntax.UNDER)[1]

        renumber()

        update_all(None, None)

        return {'FINISHED'}


class SAMK_OT_RemoveCommand(Operator):
    bl_idname = 'samk.remove_command'
    bl_label = 'Delete a command'

    index: IntProperty(
        name='Index number for removing command',
        description='Index number for removing command',
        default=0
    ) 

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        current_scope_type: ScopeType = current_scope()
        for strategy in current_scope_type.this_type_strategies():
            commands = strategy.commands()
            for index_local, command in enumerate(commands):
                if command.index == self.index:
                    commands.remove(index_local)

        renumber()

        update_all(None, None)

        return {'FINISHED'}


classes = [
    ExtractedSourceCandidate,
    ExtractedDestinationCandidate,
    ExtractedDestinationMDFCandidate,
    ExtractedDestinationVGCandidate,
    ExtractedDestinationOBJCandidate,
    SK_ApplySingle,
    MDF_Undivision,
    MDF_Delete,
    UV_Select,
    MT_Replace,
    VG_NonDecimate,
    VG_DeleteLoop,
    VG_MergeVertexSource,
    VG_MergeVertexDestination,
    VG_DeleteVertex,
    SAMKStrategies,
    SAMKCommandForAdd,
    SAMK_OT_AddCommand,
    SAMK_OT_RemoveCommand,
]
