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

from abc import ABC

from . import setup_collection as sucoll

from ..function import copy_nonlink, create_new_mesh_obj, delete_object, select_object, set_active_object, set_active_only

import logging

from . import setup_strategy as sust

from ..syntax import Syntax


logger = logging.getLogger(f'{Syntax.TOOLNAME}.{__name__}')


class ObjectStatus(ABC):
    def __init__(self, real_obj: bpy.types.Object):
        self._obj = real_obj
        self.name = real_obj.name

    @property
    def real(self) -> bpy.types.Object:
        return self._obj


class MemberObjectStatus(ObjectStatus):
    pass


class ReleaseObjectStatus(ObjectStatus):
    pass


class SubReleaseObjectStatus(ObjectStatus):
    pass


class ObjectNotFound:
    def __init__(self, name):
        self.name = name

    def delete(self):
        pass


class NewReleaseObject:
    def __init__(self) -> None:
        logger.info(f'Start Initiating Instance : {self.__class__.__name__}')
        release_obj = create_new_mesh_obj(Syntax.OBJ_RELEASE_TMP)
        self.name = release_obj.name
        self._obj = release_obj
        logger.info(f'Object name : {self.name}')

    @property
    def real(self) -> bpy.types.Object:
        return self._obj

    def cleanup(self):
        logger.info(f'Cleanup object : {self.name}')
        sust.Prefix_VG_MergeVertex(self._obj).execute()
        sust.CleanupRelease_SK(self._obj).execute()
        sust.CleanupRelease_VG(self._obj).execute()

    def rename(self, character_name, postfix):
        self._obj.name = character_name + postfix
        self._obj.data.name = character_name + postfix
        logger.info(f'Rename object : {self.name} -> {self._obj.name}')


class SetupObject(ABC):
    def __init__(self, real_obj: bpy.types.Object, tmp_collection):
        super().__init__()
        logger.info(f'Start Initiating Instance : {self.__class__.__name__}')
        self.name = real_obj.name
        self._obj = self.copy(real_obj)
        tmp_collection.real.objects.link(self._obj)
        logger.info(f'Object name : {self.name}')

    @property
    def real(self):
        return self._obj

    def copy(self, real_obj: bpy.types.Object):
        copy_obj = copy_nonlink(real_obj)

        return copy_obj

    def merge_to(self, new_release_obj: NewReleaseObject):
        # Join function should be defined in the future.
        logger.info(f'Merge object : {self._obj.name} -> {new_release_obj.real.name}')
        bpy.ops.object.select_all(action='DESELECT')
        orphan_mesh_name = self._obj.data.name
        logger.info(f'merged mesh name : {orphan_mesh_name}')
        select_object(self._obj, True)
        select_object(new_release_obj.real, True)
        set_active_object(new_release_obj.real)
        bpy.ops.object.join()
        
        tmp_collection = sucoll.TemporaryCollection(Syntax.COL_TMP)

        orphan_obj = bpy.data.objects.new(orphan_mesh_name, bpy.data.meshes[orphan_mesh_name])
        tmp_collection.real.objects.link(orphan_obj)

        logger.info(f'Deleted orphan object name : {orphan_obj.name}')
        logger.info(f'Deleted orphan mesh name (must be equal to merged mesh) : {orphan_obj.data.name}')
        delete_object(orphan_obj)
        
        bpy.ops.object.select_all(action='DESELECT')
        
        set_active_only(new_release_obj.real)
        
        del tmp_collection


class SourceObject(SetupObject):
    def do_strategy(self):
        logger.info(f'Do strategy object : {self.name}')
        sust.Strategy_SK_ApplySingle(self).execute()
        sust.Strategy_VG_DeleteLoop(self).execute()
        sust.Strategy_MDF_Delete(self).execute()

        tmp_collection = sucoll.TemporaryCollection(Syntax.COL_TMP_STRATEGY)
        sust.Strategy_MDF_Undivision(self, tmp_collection.real, None).execute()
        sust.Strategy_VG_MergeVertexDestination(self).execute()
        sust.Strategy_VG_MergeVertexSource(self).execute()
        sust.Strategy_VG_DeleteVertex(self).execute()

        sust.Strategy_UV_Select(self).execute()
        sust.Strategy_MT_Replace(self).execute()

        sust.CleanupPropertySource_SK(self).execute()
        sust.CleanupPropertySource_VG(self).execute()
        
        logger.info(f'Source object name(do_strategy) : {self._obj.name}')

        del tmp_collection


class ChildReleaseObject(SetupObject):
    pass


class DeletableObject:
    def delete(self):
        logger.info(f'Delete object : {self.name}')
        delete_object(self._obj)


class ReleaseObjectClass(ABC):
    def __init__(self, real_obj: bpy.types.Object):
        super().__init__()
        logger.info(f'Start Initiating Instance : {self.__class__.__name__}')
        self.name = real_obj.name
        self._obj = real_obj
        logger.info(f'Object name : {self.name}')

    @property
    def real(self):
        return self._obj


class ReleaseObject(ReleaseObjectClass, DeletableObject):
    pass


class SubReleaseObject(ReleaseObjectClass, DeletableObject):
    pass
