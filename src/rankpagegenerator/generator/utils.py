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


SCRIPT_DIR = os.path.dirname(__file__)

_LOGGER = logging.getLogger(__name__)


HTML_LICENSE = """\
<!--
File was automatically generated using 'rank-page-generator' project (https://github.com/anetczuk/rank-page-generator).
Project is distributed under the BSD 3-Clause license.
-->"""


def dict_to_html_table(data_dict):
    content = ""
    content += """<table>\n"""
    content += """<tr> <th>cecha:</th> <th>wartość:</th> </tr>\n"""
    for key, val in data_dict.items():
        val_str = ""
        if isinstance(val, list):
            val_str = [str(item) for item in val]
            val_str = ", ".join(val_str)
        else:
            val_str = str(val)
        if not val_str:
            val_str = "&lt;empty&gt;"
        content += f"""<tr> <td>{key}</td> <td>{val_str}</td> </tr>\n"""
    content += """</table>"""
    return content
