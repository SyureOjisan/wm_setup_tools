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

from functools import wraps

import bpy

from ..setting import setting_command

from . import setup_objects

import logging

from .setup_apply import apply_modifier

from ..function import apply_single, select_vert, set_active_object, set_active_only

from ..syntax import ALL_PROPS, Props, SAMKSyntaxError, Syntax, del_parser


logger = logging.getLogger(f'{Syntax.TOOLNAME}.{__name__}')


def mesh_operator(func):
    @wraps(func)
    def __wrapper(*args, **kwargs):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        func(*args, **kwargs)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
    return __wrapper


def delete_selected_edgeloop():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.delete_edgeloop()


class SetupStrategy(ABC):
    def __init__(self, obj) -> None:
        if type(obj) is not setup_objects.SourceObject:
            raise TypeError('')
        super().__init__()
        logger.info(f'Start Initiating Instance : {self.__class__.__name__}')
        self._obj = obj.real
        self._obj_name = obj.name
        set_active_only(self._obj)

    @abstractmethod
    def execute_if_processing(self, idx, element, command):
        pass

    @abstractmethod
    def execute_if_not_processing(self, idx, element, command):
        pass

    def execute(self):
        CommandParser.parser(self)


class Strategy_SK_ApplySingle(SetupStrategy):
    def __init__(self, obj) -> None:
        super().__init__(obj)
        if self._obj.data.shape_keys:
            self._it = self._obj.data.shape_keys.key_blocks
        else:
            self._it = tuple()

    def execute_if_processing(self, idx, element: bpy.types.ShapeKey, command):
        apply_single(self._obj, element.name, command[Props.DST])
        element.value = 0.0

    def execute_if_not_processing(self, idx, element: bpy.types.ShapeKey, command):
        pass


class Strategy_VG_DeleteLoop(SetupStrategy):
    def __init__(self, obj) -> None:
        super().__init__(obj)
        self._it = self._obj.vertex_groups

    @mesh_operator
    def execute_if_processing(self, idx, element: bpy.types.VertexGroup, command):
        self._obj.vertex_groups.active_index = idx
        bpy.ops.object.vertex_group_select()

        delete_selected_edgeloop()

    def execute_if_not_processing(self, idx, element, command):
        pass


class Strategy_MDF_Delete(SetupStrategy):
    def __init__(self, obj) -> None:
        super().__init__(obj)
        self._it = self._obj.modifiers

    def execute_if_processing(self, idx, element, command):
        bpy.ops.object.modifier_remove(modifier=element.name)
        bpy.ops.object.select_all(action='DESELECT')

    def execute_if_not_processing(self, idx, element, command):
        pass


class Strategy_UV_Select(SetupStrategy):
    _elements_to_remove: list[bpy.types.MeshUVLoopLayer] = list()
    _is_processed_once: bool = False

    def __init__(self, obj) -> None:
        super().__init__(obj)
        self._it = self._obj.data.uv_layers

    def execute_if_processing(self, idx, element, command):
        if self._is_processed_once:
            self._elements_to_remove.append(element)
            return
        element.name = command[Props.SRC]
        self._is_processed_once = True

    def execute_if_not_processing(self, idx, element, command):
        self._elements_to_remove.append(element)

    def execute(self):
        super().execute()

        for element in reversed(self._elements_to_remove):
            if len(self._it) > 1:
                self._it.remove(element)
        set_active_object(self._obj)
        bpy.ops.object.select_all(action='DESELECT')


class Strategy_MT_Replace(SetupStrategy):
    def __init__(self, obj) -> None:
        super().__init__(obj)
        self._it = self._obj.material_slots

    def execute_if_processing(self, idx, element: bpy.types.MaterialSlot, command):
        destination_name = command[Props.DST]
        if len(destination_name) == 0:
            raise SAMKSyntaxError
        try:
            element.material = bpy.data.materials[destination_name]
        except KeyError:
            mat_new = element.material.copy()
            mat_new.name = destination_name
            element.material = mat_new

    def execute_if_not_processing(self, idx, element, command):
        pass


class Strategy_VG_MergeVertexSource(SetupStrategy):
    def __init__(self, obj) -> None:
        super().__init__(obj)
        self._it = self._obj.vertex_groups

    def execute_if_processing(self, idx, element: bpy.types.VertexGroup, command):
        # samk_mergevsrc_objectname_sourcename_mergedistance
        element.name = Syntax.VG_MERGE_VTX_SRC + self._obj_name + Syntax.UNDER + command[Props.SRC] + Syntax.UNDER + str(command[Props.MERGE_DIST])

    def execute_if_not_processing(self, idx, element, command):
        pass

    def execute(self):
        super().execute()


class Strategy_VG_MergeVertexDestination(SetupStrategy):
    def __init__(self, obj) -> None:
        super().__init__(obj)
        self._it = self._obj.vertex_groups

    def execute_if_processing(self, idx, element, command):
        element.name = Syntax.VG_MERGE_VTX_DST + command[Props.DST_OBJ] + Syntax.UNDER + command[Props.DST_VG]

    def execute_if_not_processing(self, idx, element, command):
        pass


class Strategy_VG_DeleteVertex(SetupStrategy):
    def __init__(self, obj) -> None:
        super().__init__(obj)
        self._it = self._obj.vertex_groups

    @mesh_operator
    def execute_if_processing(self, idx, element, command):
        self._obj.vertex_groups.active_index = element.index
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='VERT')

    def execute_if_not_processing(self, idx, element, command):
        pass


class SetupStrategyMDF(ABC):
    def __init__(self, obj, collection: bpy.types.Collection = None, preview_instance: SetupStrategy = None) -> None:
        if type(obj) is not setup_objects.SourceObject:
            raise TypeError('')
        super().__init__()
        self._obj = obj.real
        self._obj_name = obj.name
        self._self = obj
        set_active_only(self._obj)

        if collection is None:
            self._collection = bpy.context.scene.collection
        else:
            self._collection = collection
        self._preview_instance = preview_instance

    def update_num_vert(self):
        self._num_vert = len(self._obj.data.vertices)


class Strategy_MDF_Undivision(SetupStrategyMDF):
    def __init__(self, obj, collection: bpy.types.Collection = None, preview_instance: SetupStrategy = None) -> None:
        super().__init__(obj, collection, preview_instance)
        self._it = self._obj.modifiers

    def execute_if_undiv(self, elements_name):
        self.elements_name = elements_name
        set_active_only(self._obj)
        self.update_num_vert()

        apply_modifier(
            target_object=self._obj,
            target_modifiers=elements_name,
            tmpcoll=self._collection
        )

        Strategy_VG_NonDecimate(self._self, None, self).execute()

    def execute_if_not_undiv(self, elements_name):
        set_active_only(self._obj)
        apply_modifier(
            target_object=self._obj,
            target_modifiers=elements_name,
            tmpcoll=self._collection
        )

    def execute(self):
        ModifierParser.parser(self)


class Strategy_VG_NonDecimate(SetupStrategyMDF):
    def __init__(self, obj, collection: bpy.types.Collection = None, preview_instance: SetupStrategy = None) -> None:
        super().__init__(obj, collection, preview_instance)
        self._it = self._obj.vertex_groups

    @property
    def preview_instance(self):
        return self._preview_instance

    def execute_if_processing(self, idx, element, command):
        num_vert_old = self._preview_instance._num_vert
        self.update_num_vert()
        num_vert_new = self._num_vert
        select_vert(self._obj, element.name, num_vert_old, num_vert_new)
        delete_selected_edgeloop()

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

    def execute_if_not_processing(self, idx, element, command):
        pass

    def execute(self):
        NonDecimateParser.parser(self)


class Prefix_VG_MergeVertex:
    def __init__(self, obj: bpy.types.Object) -> None:
        self._obj = obj
        self._it = obj.vertex_groups
        logger.info(f'Start Initiating Instance : {self.__class__.__name__}')

    @mesh_operator
    def execute_if_processing(self, idx, element: bpy.types.VertexGroup, source_obj_name, source_name, merge_distance):
        self._obj.vertex_groups.active_index = element.index
        bpy.ops.object.vertex_group_select()
        destination_name = Syntax.VG_MERGE_VTX_DST + source_obj_name + Syntax.UNDER + source_name
        for element_destination in self._it:
            if element_destination.name.startswith(destination_name):
                try:
                    self._obj.vertex_groups.active_index = element_destination.index
                except KeyError:
                    logger.info('Not destination prefix.')
                    pass
                bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.remove_doubles(threshold=merge_distance)

    def execute(self):
        for idx, element in enumerate(self._it):
            # samk_mergevsrc_objectname_sourcename_mergedistance
            element_name = element.name
            splitted_name = element_name.split(Syntax.UNDER)
            if not element_name.startswith(Syntax.VG_MERGE_VTX_SRC):
                logger.info('Not source prefix.')
                continue
            if len(splitted_name) != 5:
                raise SAMKSyntaxError('Invalid syntax.')
            if len(splitted_name[2]) == 0:
                raise SAMKSyntaxError('Invalid source_obj_name.')
            source_obj_name = splitted_name[2]
            if len(splitted_name[3]) == 0:
                raise SAMKSyntaxError('Invalid source_name.')
            source_name = splitted_name[3]
            try:
                merge_distance = float(splitted_name[4])
            except ValueError as e:
                raise SAMKSyntaxError(f'Not float number. code: {e}')

            logger.info(f'Source object : {source_obj_name}, Source : {source_name}, Merge distance : {merge_distance}')

            self.execute_if_processing(idx, element, source_obj_name, source_name, merge_distance)


class MTReplaceForTranslating:
    def __init__(self, obj: bpy.types.Object, postfix: str = '_postfixname') -> None:
        logger.info(f'Start Initiating Instance : {self.__class__.__name__}')
        self._obj = obj
        set_active_only(self._obj)
        self._postfix = postfix
        self._it = self._obj.material_slots

    def execute(self):
        logger.info(f'Do execute : {self.__class__.__name__}')
        for idx, element in enumerate(self._it):
            mat_orig = element.material
            mat_name_new = mat_orig.name + self._postfix
            try:
                element.material = bpy.data.materials[mat_name_new]
            except KeyError:
                mat_new = element.material.copy()
                mat_new.name = mat_name_new
                element.material = mat_new


class CleanupPropertySource(ABC):
    def __init__(self, obj) -> None:
        logger.info(f'Start Initiating Instance : {self.__class__.__name__}')
        super().__init__()
        if type(obj) is not setup_objects.SourceObject:
            raise TypeError('')
        self._obj = obj.real
        set_active_only(self._obj)

    @abstractmethod
    def execute_if_processing(self, element):
        pass

    def execute(self):
        logger.info(f'Do execute : {self.__class__.__name__}')
        strategy_class_name = self.__class__.__name__

        bpy.context.scene.samk.scope_type_to_edit = strategy_class_name.lstrip('CleanupPropertySource').lstrip(Syntax.UNDER)
        current_scope_type = setting_command.current_scope()

        command_source_names = [command.source for command in current_scope_type.this_type_commands()]

        for element in reversed(self._it):
            if element.name in command_source_names:
                self.execute_if_processing(element)


class CleanupPropertySource_SK(CleanupPropertySource):
    def __init__(self, obj) -> None:
        super().__init__(obj)
        if self._obj.data.shape_keys:
            self._it = self._obj.data.shape_keys.key_blocks
        else:
            self._it = tuple()

    def execute_if_processing(self, element):
        logger.info(f'Cleanp key : {element.name}')
        self._obj.shape_key_remove(element)


class CleanupPropertySource_VG(CleanupPropertySource):
    def __init__(self, obj: bpy.types.Object) -> None:
        super().__init__(obj)
        self._it = self._obj.vertex_groups

    def execute_if_processing(self, element):
        logger.info(f'Cleanp key : {element.name}')
        self._it.active_index = element.index
        bpy.ops.object.vertex_group_remove()


class CleanupRelease(ABC):
    def __init__(self, obj: bpy.types.Object) -> None:
        super().__init__()
        logger.info(f'Start Initiating Instance : {self.__class__.__name__}')
        self._obj = obj
        set_active_only(self._obj)
        self._keys = (Syntax.P_HEADER, Syntax.DISABLED)

    @abstractmethod
    def execute_if_processing(self, obj: bpy.types.Object, element):
        pass

    def execute(self):
        logger.info(f'Do execute : {self.__class__.__name__}')
        del_parser(self._obj, self._it, self._keys, self.execute_if_processing)


class CleanupRelease_SK(CleanupRelease):
    def __init__(self, obj: bpy.types.Object) -> None:
        super().__init__(obj)
        if obj.data.shape_keys:
            self._it = obj.data.shape_keys.key_blocks
        else:
            self._it = tuple()

    def execute_if_processing(self, obj: bpy.types.Object, element):
        logger.info(f'Cleanp key : {element.name}')
        obj.shape_key_remove(element)


class CleanupRelease_VG(CleanupRelease):
    def __init__(self, obj: bpy.types.Object) -> None:
        super().__init__(obj)
        self._it = obj.vertex_groups

    def execute_if_processing(self, obj: bpy.types.Object, element):
        logger.info(f'Cleanp key : {element.name}')
        self._it.active_index = element.index
        bpy.ops.object.vertex_group_remove()


strategy_classes = [
    Strategy_SK_ApplySingle,
    Strategy_VG_DeleteLoop,
    Strategy_MDF_Delete,
    Strategy_MDF_Undivision,
    Strategy_VG_NonDecimate,
    Strategy_UV_Select,
    Strategy_MT_Replace,
    Strategy_VG_MergeVertexSource,
    Strategy_VG_MergeVertexDestination,
    Strategy_VG_DeleteVertex,
]


def strategy_classes_callback(scene, context):

    items = list()

    for strategy_class in strategy_classes:
        items.append(tuple(strategy_class.__name__ for _ in range(3)))

    return items


class Parser(ABC):
    @classmethod
    def parser(cls, setup_strategy_instance: SetupStrategy):
        logger.info(f'Start Parser Class : {cls.__name__}')
        cls.setup_strategy = setup_strategy_instance
        strategy_class_name = cls.setup_strategy.__class__.__name__
        command_property_name = strategy_class_name.lstrip('Strategy').lstrip(Syntax.UNDER).lower()
        commands_source = eval(f'bpy.context.active_object.samk_strategies.{command_property_name}')

        commands = dict()
        for command_source in commands_source:
            properties_for_add = dict()
            # for property_name in ('source', 'destination', 'destination_obj', 'merge_distance', 'spec'):
            for property_name in ALL_PROPS:
                try:
                    properties_for_add[property_name] = getattr(command_source, property_name)
                except AttributeError:
                    logger.info(f'property \'{property_name}\' is not found, skipped.')
                    continue
                commands[command_source.source] = properties_for_add

        specs = dict()
        for spec in bpy.context.scene.samk.specs:
            specs[spec.name] = spec.is_enabled

        cls._initialize_preprocess()

        for idx, element in enumerate(cls.setup_strategy._it):
            try:
                command = commands[element.name]
            except KeyError:
                logger.info(f'source key \'{element.name}\' is not found in commands. \'do_process\' is set to False.')
                cls.do_process = False
                command = None
            else:
                logger.info(f'source key \'{element.name}\' is found in commands. \'do_process\' is set to True.')
                cls.do_process = True

                spec_name = command[Props.SPEC]

                try:
                    cls.is_enabled_spec = specs[spec_name]
                except KeyError:
                    logger.info(f'spec \'{spec_name}\' is not found in specs. \'is_enabled_spec\' is set to False.')
                    cls.is_enabled_spec = False
                else:
                    logger.info(f'spec \'{spec_name}\' is found in specs. \'is_enabled_spec\' is set to {cls.is_enabled_spec}.')

                cls._eval_destination_mdf(command)

            cls._execute_loop_part(idx, element, command)

        cls._execute_postprocess()

    @classmethod
    def _initialize_preprocess(cls):
        pass

    @classmethod
    def _execute_postprocess(cls):
        pass

    @classmethod
    def _execute_loop_part(cls, idx, element, command):
        if cls.do_process and cls.is_enabled_spec:
            cls.setup_strategy.execute_if_processing(idx, element, command)
            logger.info(f'{cls.setup_strategy.__class__.__name__}\'s execute_if_processing func is executed.')
            return
        cls.setup_strategy.execute_if_not_processing(idx, element, command)
        logger.info(f'{cls.setup_strategy.__class__.__name__}\'s execute_if_not_processing func is executed.')

    @classmethod
    @abstractmethod
    def _eval_destination_mdf(cls, command):
        pass


class CommandParser(Parser):
    @classmethod
    def parser(cls, setup_strategy_instance: SetupStrategy):
        if not isinstance(setup_strategy_instance, SetupStrategy) or isinstance(setup_strategy_instance, Strategy_MDF_Undivision):
            raise TypeError
        return super().parser(setup_strategy_instance)

    @classmethod
    def _execute_loop_part(cls, idx, element, command):
        if cls.do_process and cls.is_enabled_spec:
            cls.setup_strategy.execute_if_processing(idx, element, command)
            logger.info(f'{cls.setup_strategy.__class__.__name__}\'s execute_if_processing func is executed.')
            return
        cls.setup_strategy.execute_if_not_processing(idx, element, command)
        logger.info(f'{cls.setup_strategy.__class__.__name__}\'s execute_if_not_processing func is executed.')

    @classmethod
    def _eval_destination_mdf(cls, command):
        pass


class NonDecimateParser(Parser):
    @classmethod
    def _eval_destination_mdf(cls, command):
        try:
            destination_mdf = command[Props.DST_MDF]
        except KeyError:
            logger.info('Key \'destination_mdf\' is not found in command.')
        else:
            elements_name = cls.setup_strategy.preview_instance.elements_name
            if len(elements_name) == 0:
                element_name = ''
            elif len(elements_name) == 1:
                element_name = elements_name[0]
            else:
                raise SAMKSyntaxError('The number of Subdivision modifiers with undivision command that can be set on an object is limited to one.')

            logger.info(f'{destination_mdf}, {element_name}')
            if destination_mdf == element_name:
                cls.do_process = True
            else:
                cls.do_process = False
            logger.info(f'Key \'destination_mdf\' is found in command. \'do_process\' is set to {cls.do_process}.')


class ModifierParser(Parser):
    @classmethod
    def parser(cls, setup_strategy_instance: Strategy_MDF_Undivision):
        if not isinstance(setup_strategy_instance, Strategy_MDF_Undivision):
            raise TypeError
        return super().parser(setup_strategy_instance)

    @classmethod
    def _initialize_preprocess(cls):
        cls.modifier_names_before_undiv = list()
        cls.modifier_names_undiv = list()
        cls.modifier_names_after_undiv = list()

    @classmethod
    def _execute_loop_part(cls, idx, element, command):
        if cls.do_process and cls.is_enabled_spec:
            cls.modifier_names_undiv.append(element.name)
            return
        if len(cls.modifier_names_undiv) > 0:
            cls.modifier_names_after_undiv.append(element.name)
            return
        cls.modifier_names_before_undiv.append(element.name)

    @classmethod
    def _execute_postprocess(cls):
        logger.info(f'Do execute keys : {cls.modifier_names_before_undiv}')
        cls.setup_strategy.execute_if_not_undiv(cls.modifier_names_before_undiv)
        logger.info(f'Do execute keys : {cls.modifier_names_undiv}')
        cls.setup_strategy.execute_if_undiv(cls.modifier_names_undiv)
        logger.info(f'Do execute keys : {cls.modifier_names_after_undiv}')
        cls.setup_strategy.execute_if_not_undiv(cls.modifier_names_after_undiv)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

    @classmethod
    def _eval_destination_mdf(cls, command):
        pass
