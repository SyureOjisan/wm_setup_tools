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

from bpy.props import BoolProperty, StringProperty

from bpy.types import Panel, PropertyGroup

from .setting.setting_operators import SAMK_OT_CheckData, SAMK_OT_RemoveSpec, SAMK_OT_LoadSpecs, SAMK_OT_AddSpec, SAMK_OT_SetupOutliner

from .operators import SAMK_OT_FeedBack, SAMK_OT_ProfileShapeKey, SAMK_OT_ProfileBoneGroup, SAMK_OT_SetUp, SAMK_OT_SetUpAll, SAMK_OT_Translate, SAMK_OT_DebugQueue, SAMK_OT_DebugStrategy

from .syntax import Syntax


class SAMK_PT_Settings(Panel):
    # パネルのヘッダに表示される文字列[str]
    bl_label = 'WM Setup: Settings'
    # タブを登録するスペース[str]
    bl_space_type = 'VIEW_3D'
    # タブを登録するリージョン[str]
    bl_region_type = 'UI'
    # パネルを登録するタブ名。
    # 存在しないタブ名を指定した場合は、新たなタブを追加[str]
    bl_category = 'WM Setup'
    # パネルを表示するコンテキスト[str]
    bl_context = 'objectmode'

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context: bpy.context):
        layout = self.layout
        scene = context.scene

        column = layout.column()
        column.label(text='Spec Selection')
        row = column.row(align=True)
        row.prop(scene.samk, 'specs_enum', text='')
        row.operator(SAMK_OT_RemoveSpec.bl_idname, text='', icon='TRASH')
        row.operator(SAMK_OT_AddSpec.bl_idname, text='', icon='ADD')

        column.operator(SAMK_OT_SetupOutliner.bl_idname)
        column.operator(SAMK_OT_CheckData.bl_idname)
        layout.separator()


class SAMK_PT_Setup(Panel):
    # パネルのヘッダに表示される文字列[str]
    bl_label = 'WM Setup: Setup'
    # タブを登録するスペース[str]
    bl_space_type = 'VIEW_3D'
    # タブを登録するリージョン[str]
    bl_region_type = 'UI'
    # パネルを登録するタブ名。
    # 存在しないタブ名を指定した場合は、新たなタブを追加[str]
    bl_category = 'WM Setup'
    # パネルを表示するコンテキスト[str]
    bl_context = 'objectmode'

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # UIが変更されたオペレータプロパティを表示するボタンを配置する
        column = layout.column()
        column.operator(SAMK_OT_SetUp.bl_idname)
        column.operator(SAMK_OT_SetUpAll.bl_idname)
        layout.separator()

        if scene.samk.is_enabled_debug_mode:
            column = layout.column()
            column.operator(SAMK_OT_DebugQueue.bl_idname)
            layout.separator()
            column = layout.column()
            column.operator(SAMK_OT_DebugStrategy.bl_idname)
            layout.separator()


class SAMK_PT_Translation(Panel):
    # パネルのヘッダに表示される文字列[str]
    bl_label = 'WM Setup: Translation'
    # タブを登録するスペース[str]
    bl_space_type = 'VIEW_3D'
    # タブを登録するリージョン[str]
    bl_region_type = 'UI'
    # パネルを登録するタブ名。
    # 存在しないタブ名を指定した場合は、新たなタブを追加[str]
    bl_category = 'WM Setup'
    # パネルを表示するコンテキスト[str]
    bl_context = 'objectmode'

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        column = layout.column()
        column.operator(SAMK_OT_Translate.bl_idname)
        column.prop(scene.samk, 'translation_mode', text='Translate To')
        layout.separator()
        column = layout.column()
        column.operator(SAMK_OT_FeedBack.bl_idname)
        layout.separator()

        # UIが変更されたオペレータプロパティを表示するボタンを配置する
        if scene.samk.translation_mode == Syntax.MODE_UDEF:
            column = layout.column()
            column.prop(scene.samk, 'is_enabled_mat_replacing', text='Replace Material')
            column.prop(scene.samk.profile_bgroup, 'is_enabled_translation', text='Enable BoneGroup Translation')
            column.prop(scene.samk.profile_skey, 'is_enabled_translation', text='Enable ShapeKey Translation')
            column.prop(scene.samk, 'udef_mode_name', text='Mode Name')
            layout.separator()
        if (scene.samk.translation_mode == Syntax.MODE_MMD) or (scene.samk.translation_mode == Syntax.MODE_UDEF and scene.samk.profile_bgroup.is_enabled_translation):
            column = layout.column()
            column.alert = not scene.samk.profile_bgroup.is_syntax_ok
            column.operator(SAMK_OT_ProfileBoneGroup.bl_idname)
            column.label(text=f'BoneGroup Profile : {scene.samk.profile_bgroup.file_path}')
            layout.separator()
        if (scene.samk.translation_mode in (Syntax.MODE_MMD, Syntax.MODE_GE)) or (scene.samk.translation_mode == Syntax.MODE_UDEF and scene.samk.profile_skey.is_enabled_translation):
            column = layout.column()
            column.alert = not scene.samk.profile_skey.is_syntax_ok
            column.operator(SAMK_OT_ProfileShapeKey.bl_idname)
            column.label(text=f'ShapeKey Profile : {scene.samk.profile_skey.file_path}')
            layout.separator()


class SAMKProfileProperty(PropertyGroup):
    file_path: StringProperty(subtype='FILE_PATH')
    is_syntax_ok: BoolProperty(
        name='Whether profile check result is ok',
        description='Whether profile check result is ok',
        default=False
    )
    is_enabled_translation: BoolProperty(
        name='Enable translation by profile',
        description='Enable translation by profile',
        default=False
    )


classes = [
    SAMK_PT_Settings,
    SAMK_PT_Setup,
    SAMK_PT_Translation,
    SAMKProfileProperty,
]
