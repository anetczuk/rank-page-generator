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
from rankpagegenerator.dataloader import load_transaltion, get_translation


SCRIPT_DIR = os.path.dirname(__file__)

_LOGGER = logging.getLogger(__name__)


def print_info(model_path):
    model: DataFrame = StaticGenerator.load(model_path)
    StaticGenerator.print_info(model)


def generate_pages(model_path, translation_path, embed, output_path):
    generate_javascript(model_path, translation_path, embed, output_path)


## ============================================


def generate_javascript(model_path, translation_path, embed, output_path):
    os.makedirs(output_path, exist_ok=True)

    navigation_script_path = os.path.join(DATA_DIR, "navigate.js")
    css_styles_path = os.path.join(DATA_DIR, "styles.css")

    translation_dict = load_transaltion(translation_path)

    model: DataFrame = StaticGenerator.load(model_path)
    config: Dict[str, str] = StaticGenerator.load_config(model_path)

    answer_column_id = config.get("answer_column")
    if answer_column_id is None:
        columns = list(model.columns)
        answer_column_id = columns[0]

    _LOGGER.info("answer column id: %s", answer_column_id)

    page_title = config.get("page_title", "")
    if page_title:
        page_title = f"""<title>{page_title}</title>"""

    model_json = to_json(model)
    answer_details = StaticGenerator.load_details(model_path)
    details_json = to_json(answer_details)
    details_page_dir = generate_answer_details_pages(model_json, details_json, config, translation_dict, output_path)

    weights_dict = StaticGenerator.load_weights(model_path)
    if weights_dict is None:
        weights_dict = {}

    options_dict = StaticGenerator.load_values(model_path)

    script_data_content = f"""\
const ANSWER_COLUMN = "{answer_column_id}";
const VALUES_DICT = {options_dict};
const DETAILS_PAGE = {details_page_dir};
const WEIGHTS_DICT = {weights_dict};
const TRANSLATION_DICT = {translation_dict};"""

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

    shutil.copy(css_styles_path, output_path, follow_symlinks=True)

    content = ""
    content += f"""<html>
{HTML_LICENSE}
<head>
{page_title}
<link rel="stylesheet" type="text/css" href="styles.css">

{page_script_content}

</head>
<body class="mainpage" onload="start_navigate()">

<div class="bottomspace">
    <a href='?'>{get_translation(translation_dict, "Reset")}</a>
</div>

<div id="container"></div>

</body>
</html>
"""

    out_index_path = os.path.join(output_path, "index.html")
    _LOGGER.info("writing index page to %s", out_index_path)
    write_data(out_index_path, content)


# model_json - list of dicts (key is column name)
def generate_answer_details_pages(model_json, details_json, config_dict, translation_dict, output_path):
    if details_json is None:
        details_json = {}
    ## generate answer pages
    page_title = config_dict.get("page_title", "")

    ret_dict = {}
    pages_dir = "pages"
    out_pages_path = os.path.join(output_path, pages_dir)
    os.makedirs(out_pages_path, exist_ok=True)
    answer_counter = 0
    rows_num = len(model_json)
    for row_dict in model_json:
        field_list = list(row_dict.keys())  # column names
        value_list = list(row_dict.values())  # values
        data_dict = dict(zip(field_list, value_list))

        answer = value_list[0][0]
        details_dict = None
        for item in details_json:
            item_detail = list(item.values())  # list of lists
            if item_detail[0][0] == answer:
                details_dict = item
                details_dict.pop(next(iter(details_dict)))  # remove first key
                data_dict.update(details_dict)
                break

        characteristics = dict_to_html_table(data_dict, translation_dict)

        curr_page_title = page_title
        if curr_page_title:
            curr_page_title = f"""<title>{answer} - {curr_page_title}</title>"""

        prev_link = get_translation(translation_dict, "Prev")
        if answer_counter > 0:
            prev_href = f"{answer_counter - 1}.html"
            prev_link = f"""<a href="{prev_href}">{prev_link}</a>"""
        next_link = get_translation(translation_dict, "Next")
        if answer_counter < rows_num - 1:
            next_href = f"{answer_counter + 1}.html"
            next_link = f"""<a href="{next_href}">{next_link}</a>"""

        content = f"""<html>
{HTML_LICENSE}
<head>
{curr_page_title}
<link rel="stylesheet" type="text/css" href="../styles.css">
</head>
<body>
<div>
<a href="../index.html">{get_translation(translation_dict, "Back to Filters")}</a>
</div>
<div class="bottomspace">
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
