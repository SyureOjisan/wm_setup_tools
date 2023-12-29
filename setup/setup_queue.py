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

import logging

from .setup_collection import CollectionFactory, CollectionStatus, SourceCollectionStatus, SubSourceCollectionStatus

from .setup_objects import ObjectNotFound

from ..syntax import SAMKStructureError, Syntax


logger = logging.getLogger(f'{Syntax.TOOLNAME}.{__name__}')


class AbstractSetupQueue(ABC):
    def __init__(self, obj: bpy.types.Object) -> None:
        super().__init__()
        logger.info(f'Start Initiating Instance : {self.__class__.__name__}')
        self._obj = obj

    def queue(self, current_collection: CollectionStatus, recursive_count: int = 0) -> list[CollectionStatus]:
        order = list()

        if (type(current_collection) is not SourceCollectionStatus) and (type(current_collection) is not SubSourceCollectionStatus):
            return order

        should_append_to_order = self.setup_condition(current_collection, recursive_count)

        if should_append_to_order:
            order.append(current_collection)

        order_children = list()
        for child_collection in current_collection.member_collections:
            # 子コレクション内に更にセットアップコレクションがある場合は、スケジューリングを再帰的に実行
            order_child = self.queue(child_collection, recursive_count + 1)
            order_children.extend(order_child)

        order.extend(order_children)

        return order

    @abstractmethod
    def get_order(self) -> tuple[CollectionStatus]:
        pass

    @abstractmethod
    def setup_condition(self, current_collection, recursive_count) -> bool:
        pass


class SetupQueue(AbstractSetupQueue):
    def get_order(self) -> tuple[CollectionStatus]:
        order = list()
        collections_have_obj = self._obj.users_collection
        if len(collections_have_obj) != 1:
            raise SAMKStructureError(f'Number of object \'{self._obj.name}\' \'s collection should be only one.')
        collection_has_obj = collections_have_obj[0]  # 一つ目のコレクションを取得

        current_collection = CollectionFactory.create_collection(collection_has_obj)

        order.extend(self.queue(current_collection))

        return tuple(order)

    def setup_condition(self, current_collection, recursive_count) -> bool:

        should_append_to_order = bool()

        release_object = current_collection.release_object
        if type(release_object) is ObjectNotFound:
            # リリースオブジェクトがどこにも無い場合は、セットアップする。
            logger.info(f'[{current_collection.name}] release object\'{release_object.name}\' not found in anywhere. Setup collection will be added to setup queue.')
            should_append_to_order = True
        else:
            logger.info(f'[{current_collection.name}] release object\'{release_object.name}\' found.')

        if current_collection.is_exist_release_object_in_strange_place:
            # リリースオブジェクトはあるけど関係のない別のコレクションにある場合はリリースオブジェクトを消去してからセットアップし直し
            logger.info(f'[{current_collection.name}] release object\'{release_object.name}\' exist but not in release collection\'{current_collection.release_collection.name}\'. Delete the release object and add setup collection to the setup queue.')
            should_append_to_order = True
        else:
            logger.info(f'[{current_collection.name}] release object\'{release_object.name}\' exist in release collection\'{current_collection.release_collection.name}\'.')

        if current_collection.should_append_queue_in_this_tree:
            # 子コレクション以下の階層のコレクションのセットアップがされていない場合(リリースオブジェクトが無い)は芋づる式に親コレクションをセットアップ
            logger.info(f'[{current_collection.name}] Because child collections of the setup collection are not set up, collections of the same tree are also added to the setup queue.')
            should_append_to_order = True
        else:
            logger.info(f'[{current_collection.name}] setup of this collection tree is not required.')

        if recursive_count == 0:
            # 選択したオブジェクトがある階層のコレクションは、必ずセットアップする
            logger.info(f'[{current_collection.name}] Setup collection with selected objects are always set up.')
            should_append_to_order = True
        else:
            logger.info(f'[{current_collection.name}] No setup is required for this collection as it is the second or later tier collection.')

        return should_append_to_order


class SetupAllQueue(AbstractSetupQueue):
    def get_order(self) -> tuple[CollectionStatus]:
        order = list()

        root_collection = CollectionFactory.root_collection_has_object(self._obj)
        order.extend(self.queue(root_collection))

        return tuple(order)

    def setup_condition(self, current_collection, recursive_count) -> bool:
        logger.info(f'[{current_collection.name}] Setup Collections are always set up in Setup All operator.')
        return True
