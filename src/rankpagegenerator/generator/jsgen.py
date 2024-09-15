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
from typing import Dict

import shutil
import json
from pandas.core.frame import DataFrame

from rankpagegenerator.utils import write_data, read_data
from rankpagegenerator.generator.staticgen import StaticGenerator
from rankpagegenerator.generator.utils import HTML_LICENSE, dict_to_html_table
from rankpagegenerator.data import DATA_DIR


SCRIPT_DIR = os.path.dirname(__file__)

_LOGGER = logging.getLogger(__name__)


def print_info(model_path):
    model: DataFrame = StaticGenerator.load(model_path)
    StaticGenerator.print_info(model)


def generate_pages(model_path, embed, output_path):
    generate_javascript(model_path, embed, output_path)


## ============================================


def generate_javascript(model_path, embed, output_path):
    os.makedirs(output_path, exist_ok=True)

    navigation_script_path = os.path.join(DATA_DIR, "navigate.js")

    model: DataFrame = StaticGenerator.load(model_path)
    config: Dict[str, str] = StaticGenerator.load_config(model_path)

    answer_column_id = None
    if config is not None:
        answer_column_id = config["answer_column"]
    else:
        columns = list(model.columns)
        answer_column_id = columns[0]

    _LOGGER.info("answer column id: %s", answer_column_id)

    json_data_str = model.to_json(orient="records")
    json_data = json.loads(json_data_str)
    # ensure every value is list (makes life easier in java script)
    for row_dict in json_data:
        for key, val in row_dict.items():
            if not isinstance(val, list):
                row_dict[key] = [val]

    answer_page_dir = generate_answer_details_pages(model, output_path)

    script_data_content = f"""\
const ANSWER_COLUMN = "{answer_column_id}";
const DATA = {json_data};
const ANSWER_PAGES = {answer_page_dir};"""

    page_script_content = ""
    if embed:
        _LOGGER.info("embedding content")
        navigation_script_content = read_data(navigation_script_path)
        page_script_content = f"""
<script>
{script_data_content}


{navigation_script_content}
</script>
"""
    else:
        out_navigation_path = os.path.join(output_path, "navigate.js")
        shutil.copyfile(navigation_script_path, out_navigation_path, follow_symlinks=True)
        page_script_content = f"""\
<script>
{script_data_content}
</script>

<script src="navigate.js"></script>"""

    content = ""
    content += f"""<html>
{HTML_LICENSE}
<head>

<style>
    .bottomspace {{
        margin-bottom: 16px;
    }}
</style>

{page_script_content}

</head>
<body onload="navigate([])">

<div class="bottomspace">
    <a href=''>back to index</a>
</div>

<div id="container"></div>

</body>
</html>
"""

    out_index_path = os.path.join(output_path, "index.html")
    _LOGGER.info("writing index page to %s", out_index_path)
    write_data(out_index_path, content)


def generate_answer_details_pages(model, output_path):
    ## generate answer pages
    ret_dict = {}
    pages_dir = "pages"
    out_pages_path = os.path.join(output_path, pages_dir)
    os.makedirs(out_pages_path, exist_ok=True)
    answer_counter = 0
    for _index, row in model.iterrows():
        field_list = model.columns.to_list()
        value_list = row.iloc[:].to_list()
        data_dict = dict(zip(field_list, value_list))
        description = dict_to_html_table(data_dict)
        content = ""
        content += f"""<html>
{HTML_LICENSE}
<head>
</head>
<body>
<div>
{description}
</div>
</body>
</html>
"""
        page_name = f"{answer_counter}.html"
        out_answer_path = os.path.join(out_pages_path, page_name)
        _LOGGER.info("writing page to %s", out_answer_path)
        write_data(out_answer_path, content)
        answer_counter += 1

        answer = value_list[0]
        rel_path = os.path.join(pages_dir, page_name)
        ret_dict[answer] = rel_path

    return ret_dict
