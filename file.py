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

import csv
from .syntax import SAMKProfileError, Syntax


def check_profile(filepath, profile_type):
    if filepath.endswith('.csv'):
        pass
    else:
        raise SAMKProfileError('File is not csv.')
    try:
        with open(filepath) as f:
            reader = csv.reader(f)
            data = [row for row in reader]
    except FileNotFoundError as e:
        raise SAMKProfileError(f'Profile not found. code:{e}')
    if len(data) < 1:
        raise SAMKProfileError('Profile is empty.')
    if len(data) < 2:
        raise SAMKProfileError('Data setting is empty.')
    if data[0] != [Syntax.PROF_HEADER, profile_type]:
        raise SAMKProfileError('Missed profile is selected.')
    for row in data:
        if len(row) <= 2:
            pass
        else:
            raise SAMKProfileError('Number of column is greater than 2.')
    for row in data:
        if len(row) == 0:
            raise SAMKProfileError('Empty column exist.')
        else:
            pass
    if profile_type == Syntax.PROF_BG:
        if [Syntax.PROF_PRC, Syntax.PROF_MG] not in data:
            raise SAMKProfileError(f'\'{Syntax.PROF_MG}\' is not in profile.')
        if [Syntax.PROF_PRC, Syntax.PROF_RN] not in data:
            raise SAMKProfileError(f'\'{Syntax.PROF_RN}\' is not in profile.')
    return True


def read_profile(filepath):
    with open(filepath) as f:
        reader = csv.reader(f)
        data = [row for row in reader]
    return data
