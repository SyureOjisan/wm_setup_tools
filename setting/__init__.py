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

if 'bpy' in locals():
    import imp
    imp.reload(setting_candidates)
    imp.reload(setting_check)
    imp.reload(setting_command)
    imp.reload(setting_operators)
    imp.reload(setting_spec)
else:
    from . import setting_candidates
    from . import setting_check
    from . import setting_command
    from . import setting_operators
    from . import setting_spec
