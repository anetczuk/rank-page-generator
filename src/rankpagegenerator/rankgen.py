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

HTML_LICENSE = """\
<!--
File was automatically generated using 'rank-page-generator' project (https://github.com/anetczuk/rank-page-generator).
Project is distributed under the BSD 3-Clause license.
-->
"""


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

{HTML_LICENSE}

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
<head>
{HTML_LICENSE}
</head>
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
        model_data: DataFrame = load_table_from_excel(model_path, "Data:", assume_default=True)

        try:
            data_types: DataFrame = load_table_from_excel(model_path, "Data type:")
            if data_types is not None:
                columns = list(data_types.columns)
                col_id_name = columns[0]
                col_type_name = columns[1]
                col_id_list = data_types[col_id_name]
                for col_id in col_id_list:
                    column_desc = data_types[data_types[col_id_name] == col_id]
                    data_type = column_desc[col_type_name]
                    data_type = data_type.tolist()
                    data_type = data_type[0]

                    if data_type == "int":
                        model_column = model_data[col_id]
                        model_data[col_id] = model_column.astype("int")
                        continue

                    if data_type == "int range":
                        model_column = model_data[col_id]
                        for index, val in enumerate(model_column):
                            model_column[index] = convert_int_range(val)
                        continue

                    if data_type == "str list":
                        model_column = model_data[col_id]
                        for index, val in enumerate(model_column):
                            model_column[index] = convert_str_list(val)
                        continue

                    raise RuntimeError(f"unknown column type {data_type} for column {col_id}")
            # else no config table

        except ValueError:
            _LOGGER.debug("model does not contain data description")

        model = model_data.replace("nan", "")

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


def load_table_from_excel(data_path, marker, assume_default=False) -> DataFrame:
    content: DataFrame = pandas.read_excel(data_path)
    content = content.astype(str)

    first_col = content.iloc[:, 0]
    data_item = first_col.loc[first_col == marker]
    if data_item.empty:
        # marker not found
        if assume_default is False:
            return None
        model_data = content

    else:
        # marker found

        data_index = data_item.index.tolist()[0]
        model_data = content.iloc[data_index + 1 :]

        new_header = model_data.iloc[0]  # grab the first row for the header
        model_data = model_data[1:]  # take the data less the header row
        model_data.columns = new_header  # set the header row as the df header

        model_data.reset_index(drop=True, inplace=True)

    # cut bottom
    model_data = cut_row_nan(model_data)
    model_data = cut_column_nan(model_data)
    return model_data


def cut_row_nan(content: DataFrame) -> DataFrame:
    # cut bottom
    first_col = content.iloc[:, 0]
    data_item = first_col.loc[first_col == "nan"]
    if data_item.empty:
        # no nan data
        return content

    nan_index = data_item.index.tolist()[0]
    content = content.iloc[:nan_index]
    return content


def cut_column_nan(content: DataFrame) -> DataFrame:
    # cut right
    header_row = content.columns
    column_names = header_row.to_list()
    if "nan" not in column_names:
        return content
    nan_index = column_names.index("nan")
    content.drop(content.columns[nan_index:], axis=1, inplace=True)
    return content
