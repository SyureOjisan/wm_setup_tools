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

from ..syntax import Icon, Syntax

from bpy.props import BoolProperty, StringProperty

from bpy.types import PropertyGroup, UIList


def change_to_unique_name(self, context):
    def spec_names():
        return list(spec.name for spec in context.scene.samk.specs)

    if len(set(spec_names())) == len(spec_names()):
        return

    for spec in reversed(context.scene.samk.specs):
        if spec_names().count(spec.name) > 1:
            index_rename = 0
            new_spec_name = spec.name
            while spec_names().count(new_spec_name) > 0:
                name_splitted = new_spec_name.split(Syntax.DOT)
                try:
                    index_rename = int(name_splitted[-1])
                except ValueError:
                    index_rename += 1
                    new_spec_name = Syntax.DOT.join(name_splitted)
                else:
                    index_rename += 1
                    if len(name_splitted) > 1:
                        new_spec_name = Syntax.DOT.join(name_splitted[:-1])
                    else:
                        new_spec_name = name_splitted[0]
                finally:
                    new_spec_name += '{}{:0=3}'.format(Syntax.DOT, index_rename)
            spec.name = new_spec_name


class SAMKSpec(PropertyGroup):
    name: StringProperty(
        name='Spec name',
        description='Spec name for setup.',
        default='Default',
        update=change_to_unique_name
    )

    is_enabled: BoolProperty(
        name='check box for enabled spec name',
        description='Check the specs for which setup is activated.',
        default=False
    )


class SAMK_UL_SpecList(UIList):
    def draw_item(self, context: bpy.context, layout, data, item, icon, active_data,
                  active_propname, index):

        scene = context.scene

        custom_icon = Icon.SPEC

        row = layout.row()

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row.label(text='', icon=custom_icon)
            row.prop(item, 'name', text='')
            row.prop(item, 'is_enabled', text='')

        elif self.layout_type in {'GRID'}:
            row.alignment = 'CENTER'
            row.label(text='', icon=custom_icon)
            row.prop(item, 'is_enabled', text='')


classes = [
    SAMKSpec,
    SAMK_UL_SpecList,
]
