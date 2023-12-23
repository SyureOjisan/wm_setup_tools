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

from dataclasses import dataclass


class SAMKError(Exception):  # スーパークラスなのでこれは使わない
    pass


class SAMKSyntaxError(SAMKError):  # プレフィックスまたはコマンドの構文エラー
    pass


class SAMKStructureError(SAMKError):  # 構造エラー
    pass


class SAMKProfileError(SAMKError):  # プロファイルエラー
    pass


@dataclass(frozen=True)
class SYS_SPECS:
    DEFAULT = 'Default'
    DEFAULTONLY = 'DefaultOnly'
    DISABLE = 'Disable'


@dataclass(frozen=True)
class Props:
    SRC = 'source'
    DST = 'destination'
    DST_MDF = DST + '_mdf'
    DST_OBJ = DST + '_obj'
    DST_VG = DST + '_vg'
    MERGE_DIST = 'merge_distance'
    SPEC = 'spec'


def _member_list(CLS):
    return tuple(getattr(CLS, name) for name in dir(CLS) if not name.startswith('_'))


ALL_SYS_SPECS = _member_list(SYS_SPECS)

ALL_PROPS = _member_list(Props)

SELECTABLE_SYS_SPECS = tuple(
    (SYS_SPECS.DEFAULTONLY, ),
    )

UNSELECTABLE_SYS_SPECS = tuple(set(ALL_SYS_SPECS).difference(SELECTABLE_SYS_SPECS))


@dataclass(frozen=True)
class Icon:
    MDF = 'MODIFIER_DATA'
    OBJ = 'OBJECT_DATAMODE'
    VG = 'GROUP_VERTEX'
    OPT = 'OPTIONS'
    SPEC = 'PRESET'
    SK = 'SHAPEKEY_DATA'
    MT = 'MATERIAL_DATA'
    UV = 'UV'
    GHOST = 'GHOST_ENABLED'


@dataclass(frozen=True)
class Syntax:
    # Delimiter
    UNDER = '_'
    DOT = '.'

    # Prefix : delete after release
    TOOLNAME = 'samk'
    P_HEADER = 'samk' + UNDER

    COL_TMP = P_HEADER + 'temporary'  # automatic generation
    COL_TMP_STRATEGY = COL_TMP + '_strategy'  # automatic generation
    # COL_SRC = P_HEADER + 'src' + UNDER
    # COL_SUBSRC = P_HEADER + 'subsrc' + UNDER
    COL_SRC = 'src' + UNDER
    COL_SUBSRC = 'subsrc' + UNDER
    COL_RELEASE = UNDER + 'Release'  # automatic generation
    COL_AUTOGEN = 'wmsetup_autogen'

    OBJ_CNT = P_HEADER + 'container' + UNDER  # automatic generation
    OBJ_CNT_TMP = P_HEADER + 'tmpcontainer'  # automatic generation
    OBJ_RELEASE_TMP = P_HEADER + 'tmprelease'  # automatic generation

    VG_MERGE_VTX = P_HEADER + 'mergev'
    VG_MERGE_VTX_SRC = VG_MERGE_VTX + 'src' + UNDER  # automatic generation
    VG_MERGE_VTX_DST = VG_MERGE_VTX + 'dst' + UNDER  # automatic generation

    SHARP = '#'
    DISABLED = SHARP + P_HEADER

    # Postfix : not delete after release
    MODE_SP = UNDER + 'SP'  # SubstancePainter
    MODE_MMD = UNDER + 'MMD'  # MikuMikuDance
    MODE_GE = UNDER + 'GE'  # GameEngine(Unity, UnrealEngine)
    MODE_UDEF = UNDER + 'UDEF'  # User Defined

    OBJ_RELEASE = COL_RELEASE  # automatic generation
    OBJ_SUBRELEASE = UNDER + 'SubRelease'  # automatic generation

    TAG_L = 'L'
    TAG_R = 'R'

    # Const about Profile
    PROF_HEADER = P_HEADER.upper() + 'PROFILE'
    PROF_BG = 'BONEGROUP'
    PROF_SK = 'SHAPEKEY'
    PROF_PRC = 'PROCESS'
    PROF_MG = 'MERGE'
    PROF_RN = 'RENAME'

    # Syntax
    PREFIX_SYNTAX = {
        COL_SRC: (str, ),
        COL_SUBSRC: (str, ),

        OBJ_CNT: (str, ),

        VG_MERGE_VTX_SRC: (float, str, ),  # samk_mergevsrc_mergevalue_source
        VG_MERGE_VTX_DST: (str, ),  # samk_mergevdst_destination
    }


def prefix_parser(syntax_kind, input_strs):  # deprecated
    try:
        input_strings = input_strs.split(Syntax.UNDER)
    except AttributeError as e:
        raise SAMKSyntaxError(f'Invalid input input strings. code:{e}\ninput strings:{input_strs}')
    else:
        input_arguments = input_strings[2:]
        input_prefix = Syntax.UNDER.join(input_strings[:2]) + Syntax.UNDER
    try:
        ret_false = (False,) + tuple(None for _ in Syntax.PREFIX_SYNTAX[syntax_kind])
    except KeyError as e:  # 指定したプレフィックスではない場合
        raise SAMKSyntaxError(f'Unknown prefix. code:{e}\nsyntax kind strings:{syntax_kind}')
    if input_prefix != syntax_kind:  # 指定したプレフィックスではない場合
        return ret_false
    if input_prefix.startswith(Syntax.P_HEADER) and input_prefix not in Syntax.PREFIX_SYNTAX.keys():  # 任意のプレフィックスの場合
        return ret_false
    try:
        change_types = Syntax.PREFIX_SYNTAX[input_prefix]
    except KeyError as e:
        raise SAMKSyntaxError(f'Invalid prefix. code:{e}\ninput strings:{input_strs}')
    if len(input_arguments) != len(change_types):
        raise SAMKSyntaxError(f'Number of specified arguments does not match to standard syntax\'s one.\ninput strings:{input_strs}')
    output_values = list()
    for input_argument, change_type in zip(input_arguments, change_types):
        if len(input_argument) == 0:
            raise SAMKSyntaxError(f'Empty string exists.\ninput strings:{input_strs}')
        try:
            output_values.append(change_type(input_argument))
        except ValueError as e:
            raise SAMKSyntaxError(f'Invaid prefix arguments. code:{e}\ninput strings:{input_strs}')
    return (True,) + tuple(output_values)


def collection_parser(syntax_kind, input_strs):  # deprecated
    try:
        input_strings = input_strs.split(Syntax.UNDER)
    except AttributeError as e:
        raise SAMKSyntaxError(f'Invalid input input strings. code:{e}\ninput strings:{input_strs}')
    else:
        input_arguments = input_strings[1:]
        input_prefix = Syntax.UNDER.join(input_strings[:1]) + Syntax.UNDER
    try:
        ret_false = (False,) + tuple(None for _ in Syntax.PREFIX_SYNTAX[syntax_kind])
    except KeyError as e:  # 指定したプレフィックスではない場合
        raise SAMKSyntaxError(f'Unknown prefix. code:{e}\nsyntax kind strings:{syntax_kind}')
    if input_prefix != syntax_kind:  # 指定したプレフィックスではない場合
        return ret_false
    if input_prefix.startswith(Syntax.P_HEADER) and input_prefix not in Syntax.PREFIX_SYNTAX.keys():  # 任意のプレフィックスの場合
        return ret_false
    try:
        change_types = Syntax.PREFIX_SYNTAX[input_prefix]
    except KeyError as e:
        raise SAMKSyntaxError(f'Invalid prefix. code:{e}\ninput strings:{input_strs}')
    if len(input_arguments) != len(change_types):
        raise SAMKSyntaxError(f'Number of specified arguments does not match to standard syntax\'s one.\ninput strings:{input_strs}')
    output_values = list()
    for input_argument, change_type in zip(input_arguments, change_types):
        if len(input_argument) == 0:
            raise SAMKSyntaxError(f'Empty string exists.\ninput strings:{input_strs}')
        try:
            output_values.append(change_type(input_argument))
        except ValueError as e:
            raise SAMKSyntaxError(f'Invaid prefix arguments. code:{e}\ninput strings:{input_strs}')
    return (True,) + tuple(output_values)


def loop_parser(obj, iter, prefix, func_if_should_process, func_if_should_not_process):  # deprecated
    for idx, it in enumerate(iter):
        should_process, *args = prefix_parser(prefix, it.name)
        if should_process and func_if_should_process:
            func_if_should_process(obj, idx, it, args)
        if (not should_process) and func_if_should_not_process:
            func_if_should_not_process(obj, idx, it, args)


def del_parser(obj, iter, del_prefixes, del_func):
    for it in reversed(iter):
        for del_prefix in del_prefixes:
            if it.name.startswith(del_prefix):
                del_func(obj, it)
                break


def postfix_parser(postfix, object_name):
    if object_name.endswith(postfix):
        name_splitted = object_name.split(Syntax.UNDER)
        return (True,), tuple(name_splitted)
    return (False,), tuple()
