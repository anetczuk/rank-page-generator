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

    model_json = to_json(model)
    answer_details = StaticGenerator.load_details(model_path)
    answer_json = to_json(answer_details)
    answer_page_dir = generate_answer_details_pages(model_json, answer_json, output_path)

    script_data_content = f"""\
const ANSWER_COLUMN = "{answer_column_id}";
const DATA = {model_json};
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


def generate_answer_details_pages(model_json, answer_json, output_path):
    ## generate answer pages
    ret_dict = {}
    pages_dir = "pages"
    out_pages_path = os.path.join(output_path, pages_dir)
    os.makedirs(out_pages_path, exist_ok=True)
    answer_counter = 0
    rows_num = len(model_json)
    for row_dict in model_json:
        field_list = list(row_dict.keys())      # column names
        value_list = list(row_dict.values())    # values
        data_dict = dict(zip(field_list, value_list))

        answer = value_list[0][0]
        details_dict = None
        for item in answer_json:
            item_detail = list(item.values()) # list of lists
            if item_detail[0][0] == answer:
                details_dict = item
                details_dict.pop(next(iter(details_dict)))  # remove first key
                data_dict.update(details_dict)
                break

        characteristics = dict_to_html_table(data_dict)

        prev_link = "prev"
        if answer_counter > 0:
            prev_href = f"{answer_counter - 1}.html"
            prev_link = f"""<a href="{prev_href}">{prev_link}</a>"""
        next_link = "next"
        if answer_counter < rows_num - 1:
            next_href = f"{answer_counter + 1}.html"
            next_link = f"""<a href="{next_href}">{next_link}</a>"""

        content = f"""<html>
{HTML_LICENSE}
<head>
<style>
.characteristics th {{
    text-align: left;
}}
.empty {{
    color: red;
}}
</style>
</head>
<body>
<div>
<span>{prev_link}</span> <span>{next_link}</span>
</div>
<div class="characteristics">
{characteristics}
</div>
</body>
</html>
"""
        page_name = f"{answer_counter}.html"
        out_answer_path = os.path.join(out_pages_path, page_name)
        _LOGGER.info("writing page to %s", out_answer_path)
        write_data(out_answer_path, content)
        answer_counter += 1

        rel_path = os.path.join(pages_dir, page_name)
        ret_dict[answer] = rel_path

    return ret_dict


def to_json(content: DataFrame):
    if content is None:
        return None
    json_data_str = content.to_json(orient="records")
    json_data = json.loads(json_data_str)
    # ensure every value is list (makes life easier in java script)
    for row_dict in json_data:
        for key, val in row_dict.items():
            if not isinstance(val, list):
                row_dict[key] = [val]
    return json_data
