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
from logging import getLogger
import bpy
from ..function import exclude_coll, hide_coll, root_name_in

from ..setup import setup_objects as suobj

from ..syntax import SAMKStructureError, Syntax, postfix_parser, collection_parser


module_logger = getLogger(f'{Syntax.TOOLNAME}.{__name__}')


# Abstract Factory Pattern


class CollectionStatus(ABC):
    ReleaseObjectStatusClass = None
    SetupCollectionClass = None
    RELEASE_OBJ_POSTFIX = None

    def __init__(self, real_collection: bpy.types.Collection, character_name: str) -> None:
        super().__init__()
        module_logger.info(f'Start Initiating Instance : {self.__class__.__name__}')
        self._collection = real_collection
        self._character_name = character_name
        self.name = real_collection.name
        module_logger.info(f'Collection name : {self.name}')
        # self.exclude(False)

    def migrate(self):
        setup_collection = self.SetupCollectionClass(self)
        return setup_collection

    def exclude(self, is_exclude: bool):
        exclude_coll(self._collection.name, is_exclude)
        hide_coll(self._collection.name, is_exclude)

    @property
    def character_name(self):
        return self._character_name

    @property
    def real(self):
        return self._collection

    @property
    def member_collections(self) -> tuple:
        member_collections = tuple(CollectionFactory.create_collection(collection) for collection in self._collection.children)
        return member_collections

    @staticmethod
    def _create_member_objects(objects):
        return set(suobj.MemberObjectStatus(obj) for obj in objects)

    @property
    def _all_real_objects(self):
        return self._collection.all_objects

    @property
    def member_objects(self) -> tuple:
        member_objects = set(self._all_real_objects)
        for member_collection in self.member_collections:
            member_objects.difference_update(set(member_collection._all_real_objects))
        return tuple(suobj.MemberObjectStatus(obj) for obj in member_objects)

    @property
    @abstractmethod
    def release_collection(self):
        pass

    @property
    def parent_collection(self):
        parent_collection_status = None
        for collection in bpy.data.collections:
            if self._collection in collection.children[:]:
                parent_collection_status = CollectionFactory.create_collection(collection)  # 親コレクションを返す
                break
        if type(parent_collection_status) is SourceCollectionStatus:
            return parent_collection_status
        if type(parent_collection_status) is SubSourceCollectionStatus:
            return parent_collection_status
        if type(self) is SourceCollectionStatus:
            return NormalCollection()
        raise SAMKStructureError(f'Subsource collection\'{self.name}\' cannot be root source collection.')

    @property
    def should_append_queue_in_this_tree(self):
        def _should_append_queue_in_this_tree(collections: tuple[CollectionStatus]):
            for collection in collections:
                if (type(collection) is not SourceCollectionStatus) and (type(collection) is not SubSourceCollectionStatus):
                    continue
                if not collection.is_exist_release_object_in_release_collection:
                    return True
                if _should_append_queue_in_this_tree(collection.member_collections):
                    return True
            return False
        return _should_append_queue_in_this_tree(self.member_collections)

    @property
    def release_object(self) -> suobj.ReleaseObjectStatus:
        release_object_name = self._character_name + self.RELEASE_OBJ_POSTFIX
        try:
            release_object = bpy.data.objects[release_object_name]
        except KeyError:
            return suobj.ObjectNotFound(release_object_name)
        return self.ReleaseObjectStatusClass(release_object)

    @property
    def is_exist_release_object_in_strange_place(self) -> bool:
        if type(self.release_object) is suobj.ObjectNotFound:
            return False
        member_objects_of_release_collection = tuple(obj.real for obj in self.release_collection.member_objects)
        return self.release_object.real not in member_objects_of_release_collection

    @property
    def is_exist_release_object_in_release_collection(self) -> bool:
        if type(self.release_object) is suobj.ObjectNotFound:
            return False
        member_objects_of_release_collection = tuple(obj.real for obj in self.release_collection.member_objects)
        return self.release_object.real in member_objects_of_release_collection

    @property
    def child_release_objects(self) -> tuple[suobj.SourceObject]:
        objects_list = list()
        for collection in self.member_collections:
            if type(collection) is not SubSourceCollectionStatus:
                continue
            if type(collection.release_object) is suobj.ObjectNotFound:
                continue
            objects_list.append(suobj.MemberObjectStatus(collection.release_object.real))

        objects_tuple = tuple(objects_list)

        return objects_tuple

    @property
    def source_objects(self) -> tuple[suobj.SourceObject]:
        objects_list = list()
        for obj in self.member_objects:
            if obj.name.startswith(Syntax.SHARP):
                continue
            if obj.real.type != 'MESH':
                continue
            if obj.name.endswith(Syntax.OBJ_RELEASE):
                continue
            if obj.name.endswith(Syntax.OBJ_SUBRELEASE):
                continue
            if obj.name.startswith(Syntax.P_HEADER):
                continue
            objects_list.append(suobj.MemberObjectStatus(obj.real))

        objects_tuple = tuple(objects_list)

        return objects_tuple

    @property
    def real_source_objects(self) -> tuple[bpy.types.Object]:
        objects_tuple = tuple(obj.real for obj in self.source_objects)
        return objects_tuple


class SetupCollection(ABC):
    ReleaseObjectClass = None
    RELEASE_OBJ_POSTFIX = None

    def __init__(self, collection_status: CollectionStatus) -> None:
        super().__init__()
        module_logger.info(f'Start Initiating Instance : {self.__class__.__name__}')
        self.collection_status = collection_status
        self._collection = self.collection_status.real
        self.name = self.collection_status.name
        self._character_name = self.collection_status.character_name
        
        module_logger.info(f'Collection name : {self.name}')

        self.exclude(False)

        if type(self.collection_status.release_collection) is CollectionNotFound:
            release_collection_name = root_name_in(self._character_name) + Syntax.COL_RELEASE
            self._release_collection = NewReleaseCollection(release_collection_name)
        else:
            self._release_collection = self.collection_status.release_collection

        exclude_coll(self._release_collection.name, False)
        hide_coll(self._release_collection.name, False)

        if type(self.collection_status.release_object) is suobj.ObjectNotFound:
            self.release_object = self.collection_status.release_object
        else:
            self.release_object = self.ReleaseObjectClass(self.collection_status.release_object.real)

    def exclude(self, is_exclude: bool):
        exclude_coll(self._collection.name, is_exclude)
        hide_coll(self._collection.name, is_exclude)

    def setup(self):
        module_logger.info(f'Start setup collection : {self.name}')
        tmp_collection = TemporaryCollection(Syntax.COL_TMP)

        self.child_release_objects = tuple(suobj.ChildReleaseObject(obj.real, tmp_collection) for obj in self.collection_status.child_release_objects)
        self.source_objects = tuple(suobj.SourceObject(obj.real, tmp_collection) for obj in self.collection_status.source_objects)

        self.release_object.delete()

        new_release_obj = suobj.NewReleaseObject()
        self.link_to_release_collection(new_release_obj)

        for source_obj in self.source_objects:
            source_obj.do_strategy()
            source_obj.merge_to(new_release_obj)

        for child_release_obj in self.child_release_objects:
            child_release_obj.merge_to(new_release_obj)

        self.rename(new_release_obj)
        self.cleanup(new_release_obj)

        self.exclude(True)

        del tmp_collection

        module_logger.info(f'Finished setup collection : {self.name}')

        return new_release_obj.real

    @staticmethod
    @abstractmethod
    def cleanup(obj: suobj.NewReleaseObject):
        pass

    def rename(self, obj: suobj.NewReleaseObject):
        obj.rename(self._character_name, self.RELEASE_OBJ_POSTFIX)

    def link_to_release_collection(self, obj: suobj.NewReleaseObject):
        self._release_collection.real.objects.link(obj.real)  # NewReleaseCollectionとReleaseCollectionStatusでダックタイピング


class SetupSourceCollection(SetupCollection):
    ReleaseObjectClass = suobj.ReleaseObject
    RELEASE_OBJ_POSTFIX = Syntax.OBJ_RELEASE

    def __init__(self, collection_status: CollectionStatus) -> None:
        super().__init__(collection_status)

    @staticmethod
    def cleanup(obj: suobj.NewReleaseObject):
        obj.cleanup()
        pass


class SetupSubSourceCollection(SetupCollection):
    ReleaseObjectClass = suobj.SubReleaseObject
    RELEASE_OBJ_POSTFIX = Syntax.OBJ_SUBRELEASE

    def __init__(self, collection_status: CollectionStatus) -> None:
        super().__init__(collection_status)

    @staticmethod
    def cleanup(obj: suobj.NewReleaseObject):
        pass


class SourceCollectionStatus(CollectionStatus):
    ReleaseObjectStatusClass = suobj.ReleaseObjectStatus
    SetupCollectionClass = SetupSourceCollection
    RELEASE_OBJ_POSTFIX = Syntax.OBJ_RELEASE

    @property
    def release_collection(self):
        self._release_collection_name = root_name_in(self._character_name) + Syntax.OBJ_RELEASE
        try:
            release_collection = bpy.data.collections[self._release_collection_name]
        except KeyError:  # リリースコレクションが無かった場合はリリースコレクション内のオブジェクトは無し
            return CollectionNotFound(self._release_collection_name)
        return CollectionFactory.create_collection(release_collection)


class SubSourceCollectionStatus(CollectionStatus):
    ReleaseObjectStatusClass = suobj.SubReleaseObjectStatus
    SetupCollectionClass = SetupSubSourceCollection
    RELEASE_OBJ_POSTFIX = Syntax.OBJ_SUBRELEASE

    @property
    def release_collection(self):
        return self.parent_collection


class ReleaseCollectionStatus(CollectionStatus):
    def __init__(self, real_collection: bpy.types.Collection, character_name: str) -> None:
        super().__init__(real_collection, character_name)

    @property
    def release_collection(self):
        assert False, f'This method is unable to use in {self.__class__.__name__}'

    @property
    def should_append_queue_in_this_tree(self):
        assert False, f'This method is unable to use in {self.__class__.__name__}'


class CollectionNotFound:
    def __init__(self, name) -> None:
        self.name = name


class NormalCollection:
    pass


class CollectionFactory:
    @staticmethod
    def create_collection(real_collection: bpy.types.Collection):
        # コレクション名からキャラクター名称を抽出(args_src)
        is_source_collection, *args_src = collection_parser(Syntax.COL_SRC, real_collection.name)
        if is_source_collection:
            return SourceCollectionStatus(real_collection, args_src[0])
        is_subsource_collection, *args_src = collection_parser(Syntax.COL_SUBSRC, real_collection.name)
        if is_subsource_collection:
            return SubSourceCollectionStatus(real_collection, args_src[0])
        is_release_collection, *args_src = postfix_parser(Syntax.COL_RELEASE, real_collection.name)
        if is_release_collection:
            return ReleaseCollectionStatus(real_collection, args_src[0])
        return NormalCollection()

    @staticmethod
    def root_source_colletions(collection: bpy.types.Collection) -> tuple[CollectionStatus]:
        root_collections = list()
        for child_collection in collection.children:
            current_collection = CollectionFactory.create_collection(child_collection)
            if type(current_collection) is SubSourceCollectionStatus:
                raise SAMKStructureError(f'Subsource collection \'{current_collection.name}\' cannot be root source collection.')
            if type(current_collection) is SourceCollectionStatus:
                root_collections.append(current_collection)
                continue
            root_collections.extend(CollectionFactory.root_source_colletions(child_collection))
        return tuple(root_collections)

    @staticmethod
    def root_collection_has_object(obj):
        for root_collection in CollectionFactory.root_source_colletions(bpy.context.scene.collection):
            if obj in root_collection.real.all_objects[:]:
                return root_collection

    @staticmethod
    def reachable_collections(collection: CollectionStatus):
        reachable_collections = list()

        def _reachable_collections(current_collection: CollectionStatus):
            if type(current_collection) not in (SourceCollectionStatus, SubSourceCollectionStatus):
                return
            if current_collection.real in tuple(collection.real for collection in reachable_collections):
                return

            reachable_collections.append(current_collection)

            for member_collection in current_collection.member_collections:
                if type(member_collection) is SubSourceCollectionStatus:
                    _reachable_collections(member_collection)
            try:
                _reachable_collections(current_collection.parent_collection)
            except SAMKStructureError as e:
                print(e)

        _reachable_collections(collection)

        return tuple(reachable_collections)

    @staticmethod
    def users_source_collection(obj) -> CollectionStatus:
        users_source_collections = list()
        for collection in obj.users_collection:
            created_collection = CollectionFactory.create_collection(collection)
            if type(created_collection) in (SourceCollectionStatus, SubSourceCollectionStatus):
                users_source_collections.append(created_collection)

        if len(users_source_collections) > 1:
            raise SAMKStructureError(f'[{obj.name}] More than one source collection has same object')
        elif len(users_source_collections) == 0:
            return None
        # オブジェクトが必ずソースコレクションまたはサブソースコレクションに入っていることが前提。
        return users_source_collections[0]


class NewCollection(ABC):
    def __init__(self, collection_name: str):
        super().__init__()
        module_logger.info(f'Start Initiating Instance : {self.__class__.__name__}')
        self._name = collection_name
        new_collection = bpy.data.collections.new(self._name)
        bpy.context.scene.collection.children.link(new_collection)
        self._collection = new_collection

        
        module_logger.info(f'Collection name : {self.name}')

        self.exclude(False)

    @property
    def real(self):
        return self._collection

    @property
    def name(self):
        return self._name

    def exclude(self, is_exclude: bool):
        exclude_coll(self.name, is_exclude)
        hide_coll(self.name, is_exclude)


class NewReleaseCollection(NewCollection):
    pass


class TemporaryCollection(NewCollection):
    def __del__(self):
        module_logger.info(f'Delete temporary collection name : {self.name}')
        bpy.data.collections.remove(self._collection)
