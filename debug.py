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
from bpy.props import EnumProperty

from .function import copy_nonlink

from .setup.setup_queue import SetupQueue

# do not delete
from .setup.setup_strategy import CleanupRelease_SK, CleanupRelease, CleanupRelease_VG, \
    MTReplaceForTranslating, Strategy_MDF_Delete, Strategy_MDF_Undivision, Strategy_MT_Replace, Strategy_SK_ApplySingle, \
    Strategy_UV_Select, Strategy_VG_DeleteLoop, Strategy_VG_DeleteVertex, Strategy_VG_MergeVertexSource, \
    Strategy_VG_MergeVertexDestination, strategy_classes_callback


class SAMK_OT_DebugStrategy(bpy.types.Operator):

    bl_idname = 'samk.debugstrategy'
    bl_label = 'Debug strategy'
    bl_description = 'Debug strategy'
    bl_options = {'REGISTER', 'UNDO'}

    debug_strategy: EnumProperty(
        name='Debug Strategy',
        description='Debug Strategy',
        items=strategy_classes_callback
    )

    @classmethod
    def poll(cls, context: bpy.context):
        scene = context.scene

        return len(context.selected_objects) == 1

    def execute(self, context: bpy.context):
        collection = context.scene.collection
        act_obj = context.active_object
        obj = copy_nonlink(act_obj)
        collection.objects.link(obj)
        obj.name = 'debug_result_object_' + self.debug_strategy

        debug_strategy = globals()[self.debug_strategy]
        debug_strategy(obj).execute()

        self.report({'INFO'}, f'WM Setup Tools: debug {self.debug_strategy}')
        print(f'Operator \'{self.bl_idname}\' is executed')

        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class SAMK_OT_DebugQueue(bpy.types.Operator):

    bl_idname = 'samk.debugqueue'
    bl_label = 'Debug queue'
    bl_description = 'Debug queue'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.context):
        scene = context.scene

        return len(context.selected_objects) == 1

    def execute(self, context: bpy.context):
        obj = context.active_object

        queue = SetupQueue(obj)
        order = queue.get_order()

        self.report({'INFO'}, f'WM Setup Tools: debug queue / order : {[od.name for od in order]}')
        print(f'Operator \'{self.bl_idname}\' is executed')

        return {'FINISHED'}


classes = [
    SAMK_OT_DebugStrategy,
    SAMK_OT_DebugQueue,
]
