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

from .. import syntax

from bpy.props import BoolProperty, StringProperty

from bpy.types import PropertyGroup


class SAMKSpec(PropertyGroup):
    name: StringProperty(
        name='Spec name',
        description='Spec name for setup.',
        default='Default'
        # update=change_to_unique_name
    )

    is_enabled: BoolProperty(
        name='check box for enabled spec name',
        description='Check the specs for which setup is activated.',
        default=False
    )


def specs_candidates(self, context):
    spec_list = list()
    selectable_all_specs = list()
    
    for spec in self.specs:
        if spec.name in syntax.UNSELECTABLE_SYS_SPECS:
            continue
        selectable_all_specs.append(spec.name)     

    for selectable_spec in selectable_all_specs:
        spec_list.append(tuple(selectable_spec for _ in range(3)))

    return spec_list


def update_specs(self, context: bpy.context):
    scene = context.scene

    spec_names = tuple(spec.name for spec in self.specs)
    for sys_spec in syntax.ALL_SYS_SPECS:
        if sys_spec not in spec_names:
            new_spec = self.specs.add()
            new_spec.name = sys_spec

    for spec in self.specs:
        if spec.name == self.specs_enum:
            spec.is_enabled = True
            continue
        if spec.name == syntax.SYS_SPECS.DEFAULT:
            spec.is_enabled = True
            continue
        spec.is_enabled = False


classes = [
    SAMKSpec,
]
