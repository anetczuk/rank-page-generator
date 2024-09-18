#!/usr/bin/python3
#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause license found in the
# LICENSE file in the root directory of this source tree.
#

import os
import logging
import validators

from rankpagegenerator.dataloader import get_translation


SCRIPT_DIR = os.path.dirname(__file__)

_LOGGER = logging.getLogger(__name__)


HTML_LICENSE = """\
<!--
File was automatically generated using 'rank-page-generator' project (https://github.com/anetczuk/rank-page-generator).
Project is distributed under the BSD 3-Clause license.
-->"""


def dict_to_html_table(data_dict, translation_dict=None, header=True, table_class=None):
    if data_dict is None:
        return None
    if translation_dict is None:
        translation_dict = {}
    table_css = ""
    if table_class:
        table_css = """ class='detailstable'"""
    content = ""
    content += f"""<table{table_css}>\n"""
    if header:
        content += f"""<tr> <th>{get_translation(translation_dict, "Parameter")}:</th>\
 <th>{get_translation(translation_dict, "Value")}:</th> </tr>\n"""
    for key, val in data_dict.items():
        val_str = ""
        if isinstance(val, list):
            val_str = [convert_value(item) for item in val]
            val_str = ", ".join(val_str)
        else:
            val_str = convert_value(val)
        if not val_str:
            val_str = f"""<span class="empty">[{get_translation(translation_dict, "empty")}]</span>"""
        content += f"""<tr> <td>{key}</td> <td>{val_str}</td> </tr>\n"""
    content += """</table>"""
    return content


def convert_value(val):
    if validators.url(val):
        return f"""<a href="{val}">{val}</a>"""
    return str(val)


def convert_int_range(data: str):
    ret_list = []
    items = data.split(",")
    for item in items:
        if "-" not in item:
            # single number
            ret_list.append(int(item))
            continue
        int_range = item.split("-")
        if len(int_range) != 2:
            raise RuntimeError("invalid range")
        min_val = int(int_range[0])
        max_val = int(int_range[1]) + 1
        values = range(min_val, max_val)
        ret_list.extend(values)
    ret_list = list(set(ret_list))
    ret_len = len(ret_list)
    if ret_len < 1:
        raise RuntimeError("invalid range")
    if ret_len == 1:
        return ret_list[0]
    return ret_list


def convert_str_list(data: str, sort_list=True):
    items = data.split(",")
    ret_list = list(dict.fromkeys(items))  # set changes order of items
    ret_len = len(ret_list)
    if ret_len < 1:
        raise RuntimeError("invalid range")
    if ret_len == 1:
        return ret_list[0]
    ret_list = [item.strip() for item in ret_list]
    if sort_list:
        ret_list = sorted(ret_list)
    return ret_list
