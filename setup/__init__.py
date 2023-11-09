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
    imp.reload(setup_apply)
    imp.reload(setup_collection)
    imp.reload(setup_execute)
    imp.reload(setup_objects)
    imp.reload(setup_queue)
    imp.reload(setup_strategy)
else:
    from . import setup_apply
    from . import setup_collection
    from . import setup_execute
    from . import setup_objects
    from . import setup_queue
    from . import setup_strategy
