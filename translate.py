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

from functools import wraps

import bpy

from .file import read_profile

from .function import clear_shape_keys, copy_nonlink, create_new_mesh_obj, delete_object, exclude_coll, root_name_in, select_object, set_active_object

import logging

from .setup.setup_strategy import MTReplaceForTranslating

from .syntax import SAMKStructureError, Syntax


logger = logging.getLogger(f'{Syntax.TOOLNAME}.{__name__}')


def logger_deco(func):
    @wraps(func)
    def __wrapper(*args, **kwargs):
        logger.info(f'Start Processing function : {func.__name__}')
        ret = func(*args, **kwargs)
        logger.info(f'Finished Processing function : {func.__name__}')
        return ret
    return __wrapper


def loop_postprocess(objects, should_select_object=False):
    bpy.ops.object.select_all(action='DESELECT')
    if should_select_object:
        for obj in objects:
            select_object(obj, True)
        set_active_object(obj)
    containers_new_name = [obj.name for obj in objects]

    containers_new_name = '\', \''.join(containers_new_name)
    containers_new_name = '\'' + containers_new_name + '\''

    return containers_new_name


@logger_deco
def loop_process(func):
    @wraps(func)
    def __wrapper(*args, **kwargs):
        rets = list()
        for it in args[0]:
            args_new = (it,) + args[1:]
            ret_func = func(*args_new, **kwargs)
            rets.append(ret_func)
            should_select_object = func.__name__ == 'do_translate'
        return loop_postprocess(rets, should_select_object)
    return __wrapper


@logger_deco
def translate_obj_check(obj, postfix):
    if obj.name.endswith(Syntax.OBJ_RELEASE):
        released_obj_orig = obj
    else:
        raise SAMKStructureError('Not release object')
    name_split = obj.name.split(Syntax.UNDER)
    src_name = name_split[0]
    container_name = Syntax.OBJ_CNT + src_name
    collection_src_name = Syntax.COL_SRC + src_name

    try:
        collection_autogen = bpy.data.collections[Syntax.COL_AUTOGEN]
    except KeyError:
        raise SAMKStructureError(f'Collection \'{collection_src_name}\' not found.')
    exclude_coll(collection_autogen.name, False)

    try:
        container_orig = bpy.data.objects[container_name + postfix]
    except KeyError:
        container_orig = create_new_mesh_obj(container_name + postfix)
        collection_autogen.objects.link(container_orig)

    try:
        collection_trans = bpy.data.collections[root_name_in(src_name) + postfix]
    except KeyError:
        collection_trans = bpy.data.collections.new(root_name_in(src_name) + postfix)
        bpy.context.scene.collection.children.link(collection_trans)  # シーンとコレクションの紐づけ
    exclude_coll(collection_trans.name, False)

    collection_to = bpy.data.collections.new(Syntax.COL_TMP)  # コレクションの新規作成
    bpy.context.scene.collection.children.link(collection_to)  # シーンとコレクションの紐づけ

    try:
        released_obj_old = bpy.data.objects[src_name + postfix]
    except KeyError:
        pass
    else:
        delete_object(released_obj_old)

    released_obj = copy_nonlink(released_obj_orig)
    collection_to.objects.link(released_obj)  # コレクションに移動
    container = copy_nonlink(container_orig)
    bpy.context.scene.collection.objects.link(container)  # シーンコレクションに移動

    collection_release_name = root_name_in(src_name) + Syntax.COL_RELEASE
    exclude_coll(collection_release_name, True)
    exclude_coll(collection_autogen.name, True)

    return released_obj, container, collection_to, collection_trans, src_name


@logger_deco
def translate_bonegroup(released_obj, bgroup_fpath):
    # load profile
    bgroup_fpath_abso = bpy.path.abspath(bgroup_fpath)
    data = read_profile(bgroup_fpath_abso)
    for idx, row in enumerate(data):
        if row == [Syntax.PROF_PRC, Syntax.PROF_MG]:
            idx_header_mg = idx
        if row == [Syntax.PROF_PRC, Syntax.PROF_RN]:
            idx_header_rn = idx
    merge_list = data[idx_header_mg + 1:idx_header_rn]
    rename_list = data[idx_header_rn + 1:]

    # merge vertex group
    bpy.ops.object.select_all(action='DESELECT')
    select_object(released_obj, True)
    set_active_object(released_obj)
    for modifier in reversed(released_obj.modifiers):
        released_obj.modifiers.remove(modifier)
        # bpy.ops.object.modifier_remove()
    for merge_vnames in merge_list:
        if len(merge_vnames[1]) != 0:
            modifier_tmp = released_obj.modifiers.new(name='modifier_tmp', type='VERTEX_WEIGHT_MIX')
            modifier_tmp.vertex_group_a = merge_vnames[1]  # dst
            modifier_tmp.vertex_group_b = merge_vnames[0]  # src
            modifier_tmp.mix_mode = 'ADD'
            modifier_tmp.mix_set = 'ALL'
            try:
                bpy.ops.object.modifier_apply(modifier='modifier_tmp')
            except RuntimeError:
                bpy.ops.object.modifier_remove()
    bpy.ops.object.select_all(action='DESELECT')
    for merge_vnames in merge_list:
        vg_delete = released_obj.vertex_groups.get(merge_vnames[0])
        if vg_delete:
            released_obj.vertex_groups.remove(vg_delete)  # ソース側の頂点グループを削除

    # rename vertex group
    for vg in released_obj.vertex_groups:
        for rename_vname in rename_list:
            vg.name = vg.name.replace(rename_vname[0], rename_vname[1])


@logger_deco
def translate_clear_shapekey(released_obj):
    bpy.ops.object.select_all(action='DESELECT')
    select_object(released_obj, True)
    set_active_object(released_obj)
    clear_shape_keys(Syntax.MODE_SP[1:])
    bpy.ops.object.select_all(action='DESELECT')


@logger_deco
def translate_shapekey(released_obj, skey_fpath):
    # load profile
    skey_fpath_abso = bpy.path.abspath(skey_fpath)
    data = read_profile(skey_fpath_abso)
    for idx, row in enumerate(data):
        if row == [Syntax.PROF_HEADER, Syntax.PROF_SK]:
            idx_header_sk = idx
    skey_list = data[idx_header_sk + 1:]

    skey_dict = dict(skey_list)
    try:
        keys = released_obj.data.shape_keys.key_blocks
    except AttributeError:
        pass
    else:
        for key in reversed(keys):
            for skey_name_orig, skey_name_new in skey_dict.items():
                if key.name == skey_name_orig or (skey_name_orig.endswith(Syntax.DOT) and key.name.startswith(skey_name_orig)):
                    if len(skey_name_new) == 0:
                        released_obj.shape_key_remove(key)
                    else:
                        key.name = skey_name_new
                    break

    pass
    # apply shape key(SPmode only)


@logger_deco
def translate_mat_replace(released_obj, postfix):
    # for idx, mtslot in enumerate(released_obj.material_slots):
    #     mat_orig = mtslot.material
    #     mat_name_orig = mat_orig.name.split(Syntax.UNDER)
    #     # mat_name_new = mat_name_orig[0] + postfix
    #     mat_name_new = mat_orig.name + postfix
    #     subprocess_mt_replace(released_obj, idx, mtslot, [mat_name_new])
    MTReplaceForTranslating(released_obj, postfix).execute()


@logger_deco
def translate_join(released_obj, container, collection_to, collection_trans, src_name, postfix):
    # Join function should be defined in the future.
    orphan_mesh_name = released_obj.data.name
    logger.info(f'merged mesh name : {orphan_mesh_name}')

    bpy.ops.object.select_all(action='DESELECT')
    select_object(released_obj, True)
    select_object(container, True)
    set_active_object(container)
    bpy.ops.object.join()
    bpy.ops.object.select_all(action='DESELECT')
    container.name = src_name + postfix
    container.data.name = src_name + postfix

    orphan_release_obj = bpy.data.objects.new(orphan_mesh_name, bpy.data.meshes[orphan_mesh_name])
    collection_to.objects.link(orphan_release_obj)

    logger.info(f'Deleted orphan object name : {orphan_release_obj.name}')
    logger.info(f'Deleted orphan mesh name (must be equal to merged mesh) : {orphan_release_obj.data.name}')
    delete_object(orphan_release_obj)

    collection_trans.objects.link(container)  # オブジェクトをリリースコレクションに移動
    bpy.context.scene.collection.objects.unlink(container)

    # temporaryコレクションを削除
    bpy.data.collections.remove(collection_to)

    return container


@loop_process
def do_translate(obj):
    logger.info(f'Translation object : {obj.name}')
    scene = bpy.context.scene
    translate_mode = scene.samk.translation_mode
    bgroup_fpath = scene.samk.profile_bgroup.file_path
    skey_fpath = scene.samk.profile_skey.file_path
    bgroup_enable = scene.samk.profile_bgroup.is_enabled_translation
    skey_enable = scene.samk.profile_skey.is_enabled_translation

    logger.info(f'Translation mode : {translate_mode}')
    logger.info(f'Valid BoneGroup : {bgroup_enable}')
    logger.info(f'Valid ShapeKey : {skey_enable}')

    if translate_mode != Syntax.MODE_UDEF:
        postfix = translate_mode
    else:
        postfix = Syntax.UNDER + scene.samk.udef_mode_name

    released_obj, container, collection_to, collection_trans, src_name = \
        translate_obj_check(obj, postfix)

    if translate_mode == Syntax.MODE_MMD or (translate_mode == Syntax.MODE_UDEF and bgroup_enable):
        translate_bonegroup(released_obj, bgroup_fpath)

    if translate_mode == Syntax.MODE_SP:
        translate_clear_shapekey(released_obj)

    if translate_mode not in (Syntax.MODE_SP, Syntax.MODE_UDEF) or (translate_mode == Syntax.MODE_UDEF and skey_enable):
        translate_shapekey(released_obj, skey_fpath)

    if translate_mode != Syntax.MODE_UDEF or (translate_mode == Syntax.MODE_UDEF and scene.samk.is_enabled_mat_replacing):
        translate_mat_replace(released_obj, postfix)

    return translate_join(released_obj, container, collection_to, collection_trans, src_name, postfix)
