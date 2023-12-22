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

from ..setup import setup_collection

from .. import syntax

from . import setting_command

# simplified Mediator Pattern


# Mediator
class Mediator(ABC):
    def __init__(self, command) -> None:
        super().__init__()
        self.current_scope_type: setting_command.ScopeType = setting_command.current_scope()
        self.command = command

    def notify(self):
        extracted_names = self._extracted_names()

        for extracted_name in extracted_names:
            new_extraction = self.extracted_list.add()
            new_extraction.name = extracted_name

    @abstractmethod
    def _names(self):
        pass

    @abstractmethod
    def _black_list(self):
        pass

    def _extracted_names(self):
        extracted_names = self._names().difference(self._black_list())
        sorted_extracted_names = sorted(extracted_names)

        return sorted_extracted_names


class SourceMediator(Mediator):
    def __init__(self, command) -> None:
        super().__init__(command)
        self.extracted_list = self.command.extracted_source_candidates
        self.extracted_list.clear()

    def _names(self):
        if type(self.command) is setting_command.MDF_Undivision:
            return set(self.current_scope_type.names_subdivision())
        return set(self.current_scope_type.names())

    def _black_list(self):
        black_list = list()
        for command in self.current_scope_type.this_type_commands():
            if command.index == self.command.index:
                continue
            if command.spec != self.command.spec:
                continue
            if command.spec == '':
                continue

            black_list.append(command.source)

            try:
                black_list.append(command.destination)
            except AttributeError as e:
                print(e)

        return set(black_list)


class DestinationMediator(Mediator):
    def __init__(self, command) -> None:
        super().__init__(command)
        self.extracted_list = self.command.extracted_destination_candidates
        self.extracted_list.clear()

    def _names(self):
        if type(self.current_scope_type) is setting_command.Scope_MT:
            return set(material.name for material in bpy.data.materials)
        return set(self.current_scope_type.names())

    def _black_list(self):
        black_list = list()
        for command in self.current_scope_type.this_type_commands():
            if command.spec != self.command.spec:
                continue
            if command.spec == '':
                continue
            black_list.append(command.source)

        return set(black_list)


class ModifierMediator(Mediator):
    def __init__(self, command) -> None:
        super().__init__(command)
        self.extracted_list = self.command.extracted_destination_mdf_candidates
        self.extracted_list.clear()

    def _names(self):
        return set(modifier.name for modifier in bpy.context.active_object.modifiers if modifier.type == 'SUBSURF')

    def _black_list(self):
        black_list = list()
        for command in self.current_scope_type.this_type_commands():
            if command.index == self.command.index:
                continue
            if command.spec != self.command.spec:
                continue
            if command.spec == '':
                continue
            try:
                black_list.append(command.destination_mdf)
            except AttributeError as e:
                print(e)
        return set(black_list)


class ObjectMediator(Mediator):
    def __init__(self, command) -> None:
        super().__init__(command)
        self.extracted_list = self.command.extracted_destination_obj_candidates
        self.extracted_list.clear()

    def _names(self):
        obj = bpy.context.active_object
        collection = setup_collection.CollectionFactory.users_source_collection(obj)
        reachable_collections = setup_collection.CollectionFactory.reachable_collections(collection)

        scoped_all_objects = list()

        for scoped_collection in reachable_collections:
            for obj in scoped_collection.source_objects:
                scoped_all_objects.append(obj.name)

        return set(scoped_all_objects)

    def _black_list(self):
        return set()


class VertexGroupMediator(Mediator):
    def __init__(self, command) -> None:
        super().__init__(command)
        self.extracted_list = self.command.extracted_destination_vg_candidates
        self.extracted_list.clear()

        try:
            self._destination_obj = bpy.data.objects[self.command.destination_obj]
        except KeyError as e:
            print(e)
            self._destination_obj = None
        else:
            self._commands_destination_obj = tuple(command for command in setting_command.Scope_VG(self._destination_obj).this_type_commands() if type(command) is setting_command.VG_MergeVertexSource)

    def _names(self):
        if self._destination_obj:
            return set(command.source for command in self._commands_destination_obj)
        return set()

    def _black_list(self):
        black_list = list()
        for command in self.current_scope_type.this_type_commands():
            if command.index == self.command.index:
                continue
            if command.spec != self.command.spec:
                continue
            if command.spec == '':
                continue

            try:
                if command.destination_obj != self.command.destination_obj:
                    continue
            except AttributeError as e:
                print(e)
                continue

            black_list.append(command.destination_vg)

        if self._destination_obj:
            for command_destination_obj in self._commands_destination_obj:
                if command_destination_obj.spec == self.command.spec:
                    continue
                if self.command.spec == '':
                    continue

                black_list.append(command_destination_obj.source)

        return set(black_list)


class AbstractSpecMediator(ABC):
    def __init__(self, command) -> None:
        super().__init__()
        self.current_scope_type: setting_command.ScopeType = setting_command.current_scope()
        self.command = command

    def notify(self):
        extracted_names = self._extracted_names()

        for extracted_name in extracted_names:
            new_extraction = self.extracted_list.add()
            new_extraction.name = extracted_name

    @abstractmethod
    def _names(self):
        pass

    @abstractmethod
    def _black_list(self):
        pass

    def _extracted_names(self):
        extracted_names = self._names().difference(self._black_list())
        sorted_extracted_names = sorted(extracted_names)

        return sorted_extracted_names


class SpecMediator(AbstractSpecMediator):
    def __init__(self, command) -> None:
        super().__init__(command)
        self.extracted_list = self.command.extracted_spec_candidates
        self.extracted_list.clear()

    def _names(self):
        return set(spec.name for spec in bpy.context.scene.samk.specs if spec.name not in syntax.SELECTABLE_SYS_SPECS)

    def _black_list(self):
        return set()


class UndivisionSpecMediator(AbstractSpecMediator):
    def __init__(self, command) -> None:
        super().__init__(command)
        self.extracted_list = self.command.extracted_spec_candidates
        self.extracted_list.clear()

    def _names(self):
        names = set()
        names.add(syntax.SYS_SPECS.DEFAULT)
        return names

    def _black_list(self):
        return set()