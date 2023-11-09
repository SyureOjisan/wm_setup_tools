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
from ..function import clear_shape_keys, clone_object, delete_object, get_active_object, select_object, set_active_object, update_progress

from ..syntax import SAMKStructureError

# Original Author : mato.sus304


def apply_modifier(target_object=None, target_modifiers=None, tmpcoll=None):
    if target_object is None:
        obj_src = get_active_object()
    else:
        obj_src = target_object
        set_active_object(obj_src)  # added by SyureOjisan

    if not obj_src.modifiers:
        # if object has no modifier then skip
        return True

    # make single user
    if obj_src.data.users != 1:
        obj_src.data = obj_src.data.copy()

    # modified by SyureOjisan
    if obj_src.data.shape_keys is None and target_modifiers is not None:
        # if object has no shapekeys, just apply modifier
        # modified by SyureOjisan
        for name in target_modifiers:
            try:
                # modified by SyureOjisan
                bpy.ops.object.modifier_apply(modifier=name)
            except RuntimeError:
                pass
        return True
    obj_fin = clone_object(obj_src)

    if tmpcoll is None:
        pass
    else:
        bpy.context.scene.collection.objects.unlink(obj_fin)
        tmpcoll.objects.link(obj_fin)

    set_active_object(obj_fin)
    clear_shape_keys('Basis')

    if target_modifiers is None:
        target_modifiers = []
        for x in obj_fin.modifiers:
            if x.show_viewport:
                target_modifiers.append(x.name)

    for x in target_modifiers:
        try:
            bpy.ops.object.modifier_apply(modifier=x)
        except RuntimeError:
            pass

    list_skipped = []

    for i in range(1, len(obj_src.data.shape_keys.key_blocks)):
        tmp_name = obj_src.data.shape_keys.key_blocks[i].name
        obj_tmp = clone_object(obj_src)

        if tmpcoll is None:
            pass
        else:
            bpy.context.scene.collection.objects.unlink(obj_tmp)
            tmpcoll.objects.link(obj_tmp)

        set_active_object(obj_tmp)
        clear_shape_keys(tmp_name)

        for x in target_modifiers:
            try:
                bpy.ops.object.modifier_apply(modifier=x)
            except RuntimeError:
                pass

        bpy.ops.object.select_all(action='DESELECT')  # added by SyureOjisan
        select_object(obj_tmp, True)
        set_active_object(obj_fin)

        if bpy.ops.object.join_shapes() == {'CANCELLED'}:
            list_skipped.append(tmp_name)
            raise SAMKStructureError(f'The number of vertices does not match. Skipped keys : {list_skipped}')

        obj_fin.data.shape_keys.key_blocks[-1].name = tmp_name

        delete_object(obj_tmp)

        update_progress(
            'Object \'' + obj_src.name + '\' Apply', i / len(obj_src.data.shape_keys.key_blocks))
    update_progress('Object \'' + obj_src.name + '\' Apply', 1)

    # modified by SyureOjisan

    tmp_name = obj_src.name
    tmp_data_name = obj_src.data.name
    obj_fin.name = tmp_name + '.tmp'

    obj_src.data = obj_fin.data
    obj_src.data.name = tmp_data_name

    for x in target_modifiers:
        obj_src.modifiers.remove(obj_src.modifiers[x])

    delete_object(obj_fin)
    set_active_object(obj_src)
