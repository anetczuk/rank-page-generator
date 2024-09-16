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
from typing import Dict

from pandas.core.frame import DataFrame

from rankpagegenerator.utils import write_data
from rankpagegenerator.generator.utils import HTML_LICENSE, convert_str_list, convert_int_range
from rankpagegenerator.generator.dataframe import load_table_from_excel, to_dict_from_2col


SCRIPT_DIR = os.path.dirname(__file__)

_LOGGER = logging.getLogger(__name__)


def print_info(model_path):
    model: DataFrame = StaticGenerator.load(model_path)
    StaticGenerator.print_info(model)


def generate_pages(model_path, _embed, output_path):
    gen = StaticGenerator()
    gen.generate(model_path, output_path)


## ============================================


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
{HTML_LICENSE}
<head>
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
        data_types: DataFrame = load_table_from_excel(model_path, "Data type:")
        data_type_dict = to_dict_from_2col(data_types)
        apply_data_types(model_data, data_type_dict)
        return model_data

    @staticmethod
    def load_details(model_path) -> DataFrame:
        details_data: DataFrame = load_table_from_excel(model_path, "Details:", assume_default=False)
        data_types: DataFrame = load_table_from_excel(model_path, "Data type:")
        data_type_dict = to_dict_from_2col(data_types)
        apply_data_types(details_data, data_type_dict)
        return details_data

    @staticmethod
    def load_config(model_path) -> Dict[str, str]:
        config_data: DataFrame = load_table_from_excel(model_path, "Config:", assume_default=False)
        if config_data is None:
            return None
        return to_dict_from_2col(config_data)

    @staticmethod
    def load_order(model_path):
        order_data: DataFrame = load_table_from_excel(model_path, "Order:", assume_default=False)
        data_types: DataFrame = load_table_from_excel(model_path, "Data type:")
        data_type_dict = to_dict_from_2col(data_types)

        if data_type_dict:
            for row in order_data.iterrows():
                row_data = row[1]
                column_id = row_data.iloc[0]
                data_type = data_type_dict.get(column_id)
                if data_type:
                    # found type
                    value = row_data.iloc[1]
                    value = convert_value(value, data_type)
                    row_data.iloc[1] = value
                else:
                    # convert to string list
                    value = row_data.iloc[1]
                    value = convert_value(value, "str list")
                    row_data.iloc[1] = value
        return order_data

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


def apply_data_types(data_frame: DataFrame, data_types: dict):
    if data_types is None:
        return

    for col_id, data_type in data_types.items():
        if col_id not in data_frame:
            # column not exists
            continue
        convert_column(data_frame, col_id, data_type)


def convert_column(data_frame: DataFrame, col_id: str, data_type: str):
    model_column = data_frame[col_id]
    for index, val in enumerate(model_column):
        model_column[index] = convert_value(val, data_type)


def convert_value(value, data_type: str):
    if data_type == "int":
        return int(value)
    if data_type == "int range":
        return convert_int_range(value)
    if data_type == "str list":
        return convert_str_list(value)
    if data_type == "link list":
        return convert_str_list(value, sort_list=False)
    raise RuntimeError(f"unknown data type '{data_type}'")


def to_flat_list(data_list):
    ret_list = []
    for item in data_list:
        if isinstance(item, list):
            ret_list.extend(item)
        else:
            ret_list.append(item)
    ret_list = sorted(ret_list)
    return ret_list
