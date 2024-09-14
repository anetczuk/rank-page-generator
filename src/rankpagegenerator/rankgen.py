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
import math

import shutil
import json
import pandas
from pandas.core.frame import DataFrame

from rankpagegenerator.utils import write_data, read_data


SCRIPT_DIR = os.path.dirname(__file__)

_LOGGER = logging.getLogger(__name__)


def print_info(model_path):
    model: DataFrame = StaticGenerator.load(model_path)
    StaticGenerator.print_info(model)


def generate_pages(model_path, embed, output_path):
    # gen = StaticGenerator()
    # gen.generate(model_path, output_path)
    generate_javascript(model_path, embed, output_path)


## ============================================


def generate_javascript(model_path, embed, output_path):
    os.makedirs(output_path, exist_ok=True)

    navigation_script_path = os.path.join(SCRIPT_DIR, "data", "navigate.js")

    model: DataFrame = StaticGenerator.load(model_path)

    columns = list(model.columns)
    answer_column_id = columns[0]

    json_data_str = model.to_json(orient="records")
    json_data = json.loads(json_data_str)
    # ensure every value is list (makes life easier in java script)
    for row_dict in json_data:
        for key, val in row_dict.items():
            if not isinstance(val, list):
                row_dict[key] = [val]

    page_script_content = ""
    if embed:
        _LOGGER.info("embedding content")
        navigation_script_content = read_data(navigation_script_path)
        page_script_content = f"""
<script>
const ANSWER_COLUMN = "{answer_column_id}";
const DATA = {json_data};


{navigation_script_content}
</script>
"""
    else:
        out_navigation_path = os.path.join(output_path, "navigate.js")
        shutil.copyfile(navigation_script_path, out_navigation_path, follow_symlinks=True)
        page_script_content = f"""
<script src="navigate.js"></script>

<script>
const ANSWER_COLUMN = "{answer_column_id}";
const DATA = {json_data};
</script>
"""

    content = ""
    content += f"""<html>
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


## ===========================================================


##
## Generating all possibilities is time consuming.
## For n categories there is following number of possibilities:
##    n! * n1 * n2 * ... * nn
## where
##    n  is number categories
##    nx is number of values in category
##
class StaticGenerator:
    def __init__(self):  # noqa: F811
        self.page_counter = 0
        self.total_count = 0
        self.out_root_dir = None
        self.out_rank_dir = None
        self.out_index_path = None

        self.label_back_to_main = "powrót"
        self.label_characteristic = "cecha"
        self.label_value = "wartość"

    def generate(self, model_path, output_path):
        self.page_counter = 0

        self.out_root_dir = output_path
        os.makedirs(self.out_root_dir, exist_ok=True)

        self.out_index_path = os.path.join(self.out_root_dir, "index.html")
        gen_index_page(self.out_index_path)

        self.out_rank_dir = os.path.join(self.out_root_dir, "rank")
        os.makedirs(self.out_rank_dir, exist_ok=True)

        model: DataFrame = self.load(model_path)
        self.total_count = self.get_total_count(model)
        self._generate_submodel(model, [])

    def _generate_submodel(self, model, curr_state):
        page_path = os.path.join(self.out_rank_dir, f"{self.page_counter}.html")
        self.page_counter += 1

        content = ""
        content += f""" \
<html>
<head></hrad>
<body>
<div>
<a href="{self.out_index_path}">{self.label_back_to_main}</a>
</div>
<div>
"""

        column_names = list(model.columns)
        char_names = column_names[1:]

        if len(char_names) == 1:
            # bottom page
            result_name = column_names[0]
            char_name = char_names[0]
            content += """<table>\n"""
            content += f"""<tr> <th>{char_name}</th> <th></th> </tr>\n"""

            model_column = model[char_name]
            values_list = model_column.tolist()
            values_list = to_flat_list(values_list)
            values_set = set(values_list)
            values_set = sorted(values_set)

            for value in values_set:
                submodel = model[model_column == value]
                result_column = submodel[result_name]
                result_set = set(result_column.tolist())
                resilt_str = " ".join(result_set)
                content += f"""<tr> <td>{value}</td> <td>{resilt_str}</td> </tr>\n"""
            content += """</table>\n"""

        else:
            content += """<table>\n"""
            content += f"""<tr> <th>{self.label_characteristic}:</th> <th>{self.label_value}:</th> </tr>\n"""
            for char_name in char_names:
                model_column = model[char_name]
                values_list = model_column.tolist()
                values_list = to_flat_list(values_list)
                values_set = set(values_list)
                values_set = sorted(values_set)
                links_list = []
                for value in values_set:
                    submodel = model[model_column == value]
                    submodel = submodel.drop(char_name, axis=1)
                    next_state = list(curr_state)
                    next_state.append((char_name, value))
                    subpage_path = self._generate_submodel(submodel, next_state)
                    link_data = f"""<a href="{subpage_path}">{value}</a>\n"""
                    links_list.append(link_data)
                links_str = " ".join(links_list)
                content += f"""<tr> <td>{char_name}</td> <td>{links_str}</td> </tr>\n"""
            content += """</table>\n"""

        content += """
</div>
</body>
</html>
"""
        progress = self.page_counter / self.total_count * 100
        # progress = int(self.page_counter / self.total_count * 10000) / 100
        _LOGGER.debug("%f%% %s writing page: %s", progress, curr_state, page_path)
        write_data(page_path, content)
        return page_path

    @staticmethod
    def load(model_path) -> DataFrame:
        model: DataFrame = pandas.read_excel(model_path)
        model = model.astype(str)

        try:
            data_desc: DataFrame = pandas.read_excel(model_path, sheet_name=1)
            data_desc = data_desc.astype(str)

            columns = list(data_desc.columns)
            col_id_name = columns[0]
            col_type_name = columns[1]
            col_id_list = data_desc[col_id_name]
            for col_id in col_id_list:
                column_desc = data_desc[data_desc[col_id_name] == col_id]
                data_type = column_desc[col_type_name]
                data_type = data_type.tolist()
                data_type = data_type[0]

                if data_type == "int":
                    model_column = model[col_id]
                    model[col_id] = model_column.astype("int")
                    continue

                if data_type == "int range":
                    model_column = model[col_id]
                    for index, val in enumerate(model_column):
                        model_column[index] = convert_int_range(val)
                    continue

                if data_type == "str list":
                    model_column = model[col_id]
                    for index, val in enumerate(model_column):
                        model_column[index] = convert_str_list(val)
                    continue

                raise RuntimeError(f"unknown column type {data_type} for column {col_id}")

        except ValueError:
            _LOGGER.debug("model does not contain data description")

        model = model.replace("nan", "")

        # column_names = list(model.columns)
        # result_name = column_names[0]
        # model_column = model[result_name]
        # model_column = model_column.astype(str)
        # model_column = model_column.replace('nan', '')
        # model[result_name] = model_column.astype(str)

        return model

    @staticmethod
    def get_total_count(model):
        total_count = 1
        column_names = list(model.columns)
        char_names = column_names[1:]
        for char_name in char_names:
            values_list = model[char_name].tolist()
            values_list = to_flat_list(values_list)
            values_set = set(values_list)
            # if "" in values_set:
            #     values_set.remove("")
            length = len(values_set)
            total_count *= length
        col_len = len(char_names)
        total_count *= math.factorial(col_len)
        # total_count *= col_len
        return total_count

    @staticmethod
    def print_info(model):
        print(model)
        column_names = list(model.columns)
        char_names = column_names[1:]
        for char_name in char_names:
            values_list = model[char_name].tolist()
            values_list = to_flat_list(values_list)
            values_set = set(values_list)
            values_set = sorted(values_set)
            # if "" in values_set:
            #     values_set.remove("")
            length = len(values_set)
            print(f"{char_name}: {length} {values_set}")
        total_count = StaticGenerator.get_total_count(model)
        print("total_count:", total_count)


def gen_index_page(output_path):
    content = """ \
<html>
<head></hrad>
<body>
<div>
<a href="rank/0.html">start</a>
</div>
</body>
</html>
"""
    write_data(output_path, content)


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


def convert_str_list(data: str):
    items = data.split(",")
    ret_list = list(set(items))
    ret_len = len(ret_list)
    if ret_len < 1:
        raise RuntimeError("invalid range")
    if ret_len == 1:
        return ret_list[0]
    ret_list = [item.strip() for item in ret_list]
    ret_list = sorted(ret_list)
    return ret_list


def to_flat_list(data_list):
    ret_list = []
    for item in data_list:
        if isinstance(item, list):
            ret_list.extend(item)
        else:
            ret_list.append(item)
    ret_list = sorted(ret_list)
    return ret_list
