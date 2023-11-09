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

from logging.handlers import RotatingFileHandler
import bpy

from logging import DEBUG, Formatter, getLogger

from .setting.setting_check import check_data

from .file import check_profile

from .function import exclude_coll, hide_coll, is_valid_objects, loop_process, select_object, set_active_object, set_active_only

from .setup.setup_execute import SetupExecution

from .setup.setup_queue import SetupAllQueue, SetupQueue

from .syntax import SAMKProfileError, SAMKStructureError, SAMKSyntaxError, Syntax

from .translate import do_translate

logger = getLogger(Syntax.TOOLNAME)
logger.setLevel(DEBUG)

fh = RotatingFileHandler(filename=f'{Syntax.TOOLNAME}.log', mode='w', maxBytes=1000000, backupCount=3, encoding='utf-8')
fh.setLevel(DEBUG)
formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

logger.addHandler(fh)


class SAMKAbstractSetUp(bpy.types.Operator):

    bl_idname = ''
    bl_label = ''
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    SetupQueueClass = None

    @classmethod
    def poll(cls, context):
        PREFIX = (Syntax.COL_SRC, Syntax.COL_SUBSRC)
        try:
            return context.active_object.users_collection[0].name.startswith(PREFIX)
        except AttributeError:
            return False

    def execute(self, context):
        logger.info(f'Start operator : {self.bl_idname}')
        scene = context.scene

        if self.can_setup:
            obj = context.active_object

            queue = self.SetupQueueClass(obj)
            order = queue.get_order()

            execution = SetupExecution(order)
            release_obj = execution.execute()

            set_active_object(release_obj)
            select_object(release_obj, True)

            self.report({'INFO'}, f'WM Setup Tools: Setup Model \'{release_obj.name}\'')
            print(f'Operator \'{self.bl_idname}\' is executed')
            logger.info(f'Finished operator : {self.bl_idname}')

            return {'FINISHED'}

        self.report({'WARNING'}, f'WM Setup Tools: Setup error occurred. :\'{self.error_code}\'')
        print(f'Operator \'{self.bl_idname}\' is executed')
        logger.warning(f'Setup error occurred. operator : {self.bl_idname}')

        return {'FINISHED'}

    def invoke(self, context, event):
        obj = context.active_object
        try:
            check_data(context.active_object)
        except SAMKStructureError as e:
            self.error_code = e
            self.can_setup = False
        except SAMKSyntaxError as e:
            self.error_code = e
            self.can_setup = False
        else:
            self.error_code = 'No error occurred.'
            self.can_setup = True

        set_active_only(obj)        
        scene = context.scene
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        column = layout.column()
        if not self.can_setup:
            column.alert = True
            column.label(text=f'Error Code: {self.error_code}')


class SAMK_OT_SetUp(SAMKAbstractSetUp):

    bl_idname = 'samk.setup'
    bl_label = 'Setup Collection'
    bl_description = 'Setup selected object\'s collection'

    SetupQueueClass = SetupQueue

    def draw(self, context):
        super().draw(context)
        if self.can_setup:
            layout = self.layout
            column = layout.column()
            column.label(text='Start Setup?')
            column.alert = True
            column.label(text='Note: Models with many shape keys will take a long time to process.')


class SAMK_OT_SetUpAll(SAMKAbstractSetUp):

    bl_idname = 'samk.setupall'
    bl_label = 'Setup All'
    bl_description = 'Setup all collections of selected object\'s tree'

    SetupQueueClass = SetupAllQueue

    def draw(self, context):
        super().draw(context)
        if self.can_setup:
            layout = self.layout
            column = layout.column()
            column.label(text='Start Setup All?')
            column.alert = True
            column.label(text='Note: All collections will be setup.')
            column.label(text='Note: Models with many shape keys will take a long time to process.')


class SAMK_OT_Translate(bpy.types.Operator):

    bl_idname = 'samk.translate'
    bl_label = 'Translate in Selected Mode'
    bl_description = 'Translate in selected mode'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene = context.scene

        is_enabled_profile_bgroup = True
        is_enabled_profile_skey = True

        if scene.samk.translation_mode == Syntax.MODE_MMD:
            is_enabled_profile_bgroup = scene.samk.profile_bgroup.is_syntax_ok

        if scene.samk.translation_mode in (Syntax.MODE_MMD, Syntax.MODE_GE):
            is_enabled_profile_skey = scene.samk.profile_skey.is_syntax_ok

        if scene.samk.translation_mode == Syntax.MODE_UDEF:
            is_enabled_profile_bgroup = scene.samk.profile_bgroup.is_syntax_ok or not scene.samk.profile_bgroup.is_enabled_translation
            is_enabled_profile_skey = scene.samk.profile_skey.is_syntax_ok or not scene.samk.profile_skey.is_enabled_translation

        condition = (is_enabled_profile_bgroup, is_enabled_profile_skey, is_valid_objects(context, Syntax.OBJ_RELEASE))
        return all(condition)

    def execute(self, context):
        logger.info(f'Start operator : {self.bl_idname}')
        objects = context.selected_objects
        try:
            translated_objects_name = do_translate(objects)
        except SAMKStructureError as e:
            self.report({'WARNING'}, f'WM Setup Tools: Object structure error occurred. :\'{e}\'')
            print(f'Operator \'{self.bl_idname}\' is aborted')
            logger.warning(f'Translation error occurred. operator : {self.bl_idname}')

            return {'FINISHED'}

        self.report({'INFO'}, f'WM Setup Tools: Translate Model {translated_objects_name}')
        print(f'Operator \'{self.bl_idname}\' is executed')
        logger.info(f'Finished operator : {self.bl_idname}')

        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        self.mode = scene.samk.translation_mode
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text='Start Translate?')
        layout.separator()


class SAMK_OT_FeedBack(bpy.types.Operator):

    bl_idname = 'samk.feedback'
    bl_label = 'Feedback to Container'
    bl_description = 'Feedback translated object to container'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene = context.scene

        postfix = (
            Syntax.MODE_SP,
            Syntax.MODE_MMD,
            Syntax.MODE_GE,
            scene.samk.udef_mode_name,)

        return is_valid_objects(context, postfix)

    def execute(self, context):
        logger.info(f'Start operator : {self.bl_idname}')
        @loop_process
        def feedback_core(trans_obj):
            trans_obj_name = trans_obj.name
            container_name = Syntax.OBJ_CNT + trans_obj_name
            src_name = trans_obj_name.split(Syntax.UNDER)
            src_coll_name = Syntax.COL_SRC + src_name[0]

            try:
                # coll = bpy.data.collections[src_coll_name]
                coll = bpy.data.collections[Syntax.COL_AUTOGEN]
            except KeyError:
                coll = bpy.data.collections.new(Syntax.COL_AUTOGEN)
                bpy.context.collection.children.link(coll)
            finally:
                exclude_coll(coll.name, False)
                hide_coll(coll.name, False)

            bpy.ops.object.select_all(action='DESELECT')
            try:
                container = bpy.data.objects[container_name]
            except KeyError:
                pass
            else:
                select_object(container, True)
                set_active_object(container)
                bpy.ops.object.delete()
            bpy.ops.object.select_all(action='DESELECT')

            container_new = trans_obj.copy()
            container_new.data = trans_obj.data.copy()
            container_new.name = container_name
            container_new.data.name = container_name

            coll.objects.link(container_new)

            select_object(container_new, True)
            set_active_object(container_new)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.reveal()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

            if container_new.data.shape_keys:
                for key in container_new.data.shape_keys.key_blocks:
                    container_new.shape_key_remove(key)

            vgroups = container_new.vertex_groups
            for vg in vgroups:
                vgroups.active_index = vg.index
                bpy.ops.object.vertex_group_remove()

            container_new.hide_set(True)

            exclude_coll(coll.name, True)
            hide_coll(coll.name, True)

            return container_new

        objects = context.selected_objects
        try:
            containers_new_name = feedback_core(objects)
        except SAMKStructureError as e:
            self.report({'WARNING'}, f'WM Setup Tools: Object structure error occurred. :\'{e}\'')
            print(f'Operator \'{self.bl_idname}\' is aborted')
            logger.warning(f'Feedback error occurred. operator : {self.bl_idname}')

            return {'FINISHED'}

        self.report({'INFO'}, f'WM Setup Tools: Feedback to {containers_new_name}')
        print(f'Operator \'{self.bl_idname}\' is executed')
        logger.info(f'Finished operator : {self.bl_idname}')

        return {'FINISHED'}


class ReadProfile(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filename: bpy.props.StringProperty()
    directory: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(default='*.csv', options={'HIDDEN'})

    profile = None

    def execute(self, context):
        logger.info(f'Start operator : {self.bl_idname}')
        if not self.profile:
            raise SAMKProfileError('Internal Error. Kind of profile is not selected.')

        logger.info(f'Start operator : {self.__class__.__name__}')
        self.profile.is_syntax_ok = False
        try:
            check_profile(self.filepath, self.profile_type)
        except SAMKProfileError as e:
            self.report({'WARNING'}, f'WM Setup Tools : {self.profile_type.capitalize()} Profile, {e}')
            self.profile.file_path = '(Load Error)'
            logger.warning(f'Read file error occurred. operator : {self.__class__.__name__}')
            return {'FINISHED'}

        self.profile.is_syntax_ok = True

        filepath_tmp = bpy.path.relpath(self.filepath)
        self.report({'INFO'}, f'WM Setup Tools : {self.profile_type.capitalize()} Profile, [FilePath] {self.filepath}')
        self.profile.file_path = filepath_tmp
        logger.info(f'Finished operator : {self.__class__.__name__}')
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)

        return {'RUNNING_MODAL'}


class SAMK_OT_ProfileBoneGroup(ReadProfile):
    bl_idname = 'samk.profile_bone_group'
    bl_label = 'Load Bone Group Profile(*.csv)'
    bl_description = 'Show file browser(Bone Group)'
    bl_options = {'REGISTER', 'UNDO'}

    profile_type = Syntax.PROF_BG

    def execute(self, context):
        scene = context.scene
        self.profile = scene.samk.profile_bgroup

        return super().execute(context)


class SAMK_OT_ProfileShapeKey(ReadProfile):
    bl_idname = 'samk.profile_shape_key'
    bl_label = 'Load Shape Key Profile(*.csv)'
    bl_description = 'Show file browser(Shape Key)'
    bl_options = {'REGISTER', 'UNDO'}

    profile_type = Syntax.PROF_SK

    def execute(self, context):
        scene = context.scene
        self.profile = scene.samk.profile_skey

        return super().execute(context)


class NewCollection(bpy.types.Operator):

    bl_options = {'REGISTER', 'UNDO'}

    COLLECTION_PREFIX = None

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        logger.info(f'Start operator : {self.bl_idname}')
        scene = context.scene

        new_collection = bpy.data.collections.new(self.COLLECTION_PREFIX + 'NewSetupCollection')
        bpy.context.collection.children.link(new_collection)
        self._collection = new_collection

        self.report({'INFO'}, f'WM Setup Tools: Add Collection \'{new_collection.name}\'')
        print(f'Operator \'{self.bl_idname}\' is executed')
        logger.info(f'Finished operator : {self.bl_idname}')

        return {'FINISHED'}


class SAMK_OT_NewSourceCollection(NewCollection):

    bl_idname = 'samk.newsource'
    bl_label = 'New Setup Source Collection'
    bl_description = 'New setup source collection'

    COLLECTION_PREFIX = Syntax.COL_SRC


class SAMK_OT_NewSubSourceCollection(NewCollection):

    bl_idname = 'samk.newsubsource'
    bl_label = 'New Setup Subsource Collection'
    bl_description = 'New setup subsource collection'

    COLLECTION_PREFIX = Syntax.COL_SUBSRC


classes = [
    SAMK_OT_SetUp,
    SAMK_OT_SetUpAll,
    SAMK_OT_FeedBack,
    SAMK_OT_Translate,
    SAMK_OT_ProfileBoneGroup,
    SAMK_OT_ProfileShapeKey,
    SAMK_OT_NewSourceCollection,
    SAMK_OT_NewSubSourceCollection,
]
