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
import bmesh
from functools import wraps
import sys

from .syntax import SAMKStructureError, Syntax


def select_object(obj, value):
    obj.select_set(value)


def get_active_object():
    return bpy.context.window.view_layer.objects.active


def set_active_object(obj):
    bpy.context.view_layer.objects.active = obj


def clear_shape_keys(Name):
    obj = bpy.context.active_object
    if obj.data.shape_keys is None:
        return True
    obj.active_shape_key_index = len(obj.data.shape_keys.key_blocks) - 1
    while len(obj.data.shape_keys.key_blocks) > 1:
        if obj.data.shape_keys.key_blocks[obj.active_shape_key_index].name == Name:
            obj.active_shape_key_index = 0
        else:
            bpy.ops.object.shape_key_remove()
    bpy.ops.object.shape_key_remove()


def clone_object(obj):
    tmp_obj = obj.copy()
    tmp_obj.name = 'applymodifier_tmp_%s' % (obj.name)
    tmp_obj.data = tmp_obj.data.copy()
    tmp_obj.data.name = 'applymodifier_tmp_%s' % (obj.data.name)
    bpy.context.scene.collection.objects.link(tmp_obj)
    return tmp_obj


def delete_object(obj):
    if obj.data.users == 1:
        obj.data.user_clear()
    for scn in bpy.data.scenes:
        try:
            scn.collection.objects.unlink(obj)
        except Exception:
            pass


def set_active_only(obj):
    # bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    set_active_object(obj)


def deselect_all_vert(obj):
    set_active_object(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


def update_progress(job_title, progress):
    length = 20  # modify this to change the length
    block = int(round(length * progress))
    msg = '\r{0}: [{1}] {2}%'.format(
        job_title, '#' * block + '-' * (length - block), round(progress * 100, 2))
    if progress >= 1:
        msg += ' DONE\r\n'
    sys.stdout.write(msg)
    sys.stdout.flush()


def apply_single(obj, src_key_name, dst_key_name):
    mesh = obj.data

    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm_copy = bm.copy()
    bm.faces.ensure_lookup_table()
    bm_copy.faces.ensure_lookup_table()

    keys = mesh.shape_keys.key_blocks
    dst_keys_name = list()
    dst_keys_name = [dst_key_name]

    src_key_ly = bm_copy.verts.layers.shape[src_key_name]
    try:
        basis_key_ly = bm_copy.verts.layers.shape['Basis']
    except KeyError:
        raise SAMKStructureError('\'Basis\' shapekey not found. Don\'t change Basis key name.')

    dst_key_lys = list()
    for dst_key_name in dst_keys_name:
        dst_key_lys.append(bm.verts.layers.shape[dst_key_name])

    value = keys[src_key_name].value

    # if 'Basis' in dst_keys_name:
    #     for key in keys[1:]:
    #         not_basis_key_ly = bm.verts.layers.shape[key.name]
    #         for vert, vert_copy in zip(bm.verts, bm_copy.verts):
    #             vert[not_basis_key_ly] -= (vert_copy[src_key_ly] - vert_copy[basis_key_ly]) * value

    for idx, dst_key_ly in enumerate(dst_key_lys):
        if 'Basis' in dst_keys_name and idx == 0:
            for vert, vert_copy in zip(bm.verts, bm_copy.verts):
                vert.co += (vert_copy[src_key_ly] - vert_copy[basis_key_ly]) * value
        else:
            for vert, vert_copy in zip(bm.verts, bm_copy.verts):
                vert[dst_key_ly] += (vert_copy[src_key_ly] - vert_copy[basis_key_ly]) * value

    bm.to_mesh(mesh)
    bm.free()
    bm_copy.free()


def recur_coll(coll, search_name):
    if coll.name == search_name:
        return coll
    for child in coll.children:
        ret_coll = recur_coll(child, search_name)
        if ret_coll is None:
            pass
        else:
            return ret_coll


def deco_coll(func):
    @wraps(func)
    def __wrapper(*args, **kwargs):
        coll = bpy.context.view_layer.layer_collection
        kwargs['target_coll'] = recur_coll(coll, args[0])
        try:
            ret = func(*args, **kwargs)
        except AttributeError as e:
            raise SAMKStructureError(f'Collection \'{args[0]}\' not found. code:{e}')
        return ret
    return __wrapper


@deco_coll
def search_coll(name, target_coll=None):
    return target_coll


@deco_coll
def exclude_coll(name, value, target_coll=None):
    if not value:
        target_coll.exclude = True
        target_coll.exclude = False
    else:
        target_coll.exclude = True


@deco_coll
def hide_coll(name, value, target_coll=None):
    target_coll.hide_viewport = value


def exclude_all_child_coll(name, value):
    coll = bpy.context.view_layer.layer_collection
    target_coll = recur_coll(coll, name)
    for child in target_coll.children:
        try:
            child.exclude = value
        except AttributeError:
            pass


def delete_object_ops(obj):
    bpy.ops.object.select_all(action='DESELECT')
    select_object(obj, True)
    set_active_object(obj)
    bpy.ops.object.delete()
    bpy.ops.object.select_all(action='DESELECT')


def parent_name_in(src_name):
    src_name_split = src_name.split(Syntax.DOT)
    char_num = len(src_name) - len(src_name_split[-1]) - 1
    if len(src_name_split) <= 1:
        ret_name = src_name_split[0]
    else:
        ret_name = src_name[:char_num]
    return ret_name


def root_name_in(src_name):
    src_name_split = src_name.split(Syntax.DOT)
    return src_name_split[0]


def copy_nonlink(src_obj):
    new_obj = src_obj.copy()
    new_obj.data = src_obj.data.copy()  # リンク無しコピー
    return new_obj


def select_vert(obj, v_group_name, vert_idx_min, vert_idx_max):
    v_group_name_idx = {x.name: x.index for x in obj.vertex_groups}

    vert_idx_info = dict()
    for idx, vert in enumerate(obj.data.vertices):
        vert_idx_info.update({idx: {vgroup.group: vgroup.weight for vgroup in vert.groups}})

    for vert in obj.data.vertices:
        vert.select = False

    if len(obj.vertex_groups) == 0 or v_group_name is None:
        for vert_idx, vert_info in vert_idx_info.items():
            if vert_idx_min <= vert_idx < vert_idx_max:
                obj.data.vertices[vert_idx].select = True
        return True

    for v_group in obj.vertex_groups:
        v_group_idx = v_group_name_idx[v_group.name]
        for vert_idx, vert_info in vert_idx_info.items():
            try:
                weight = vert_info[v_group_idx]
            except KeyError:
                weight = 0.0
            if vert_idx_min <= vert_idx < vert_idx_max:
                if weight < 1.0 and v_group.name == v_group_name:
                    obj.data.vertices[vert_idx].select = True


def is_valid_objects(context, postfix):
    trans_objects = context.selected_objects
    postfix_kind = set()
    for trans_obj in trans_objects:
        try:
            trans_obj_name = trans_obj.name
        except AttributeError:
            return False
        trans_obj_name_split = trans_obj_name.split(Syntax.UNDER)
        split_len = len(trans_obj_name_split)
        if not trans_obj_name.endswith(postfix):
            return False
        if split_len != 2:
            return False
        postfix_kind.add(trans_obj_name_split[-1])
    if len(postfix_kind) != 1:
        return False
    return True


def loop_postprocess(objects, do_select_output_object=False):
    bpy.ops.object.select_all(action='DESELECT')
    if do_select_output_object:
        for obj in objects:
            select_object(obj, True)
        set_active_object(obj)
    containers_new_name = [obj.name for obj in objects]

    containers_new_name = '\', \''.join(containers_new_name)
    containers_new_name = '\'' + containers_new_name + '\''

    return containers_new_name


def loop_process(func):
    @wraps(func)
    def __wrapper(*args, **kwargs):
        rets = list()
        for it in args[0]:
            args_new = (it,) + args[1:]
            ret_func = func(*args_new, **kwargs)
            rets.append(ret_func)
            should_select_out = func.__name__ == 'do_translate'
        return loop_postprocess(rets, should_select_out)
    return __wrapper


def create_new_mesh_obj(name):
    new_mesh = bpy.data.meshes.new(name)
    new_mesh.update()

    new_obj = bpy.data.objects.new(name, new_mesh)
    new_obj.data = new_mesh

    return new_obj
