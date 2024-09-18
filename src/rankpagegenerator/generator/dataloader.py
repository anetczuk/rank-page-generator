#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause license found in the
# LICENSE file in the root directory of this source tree.
#

import logging
from typing import Dict
import math
import json

from pandas.core.frame import DataFrame

from rankpagegenerator.generator.dataframe import (
    load_table_from_excel,
    to_dict_from_2col,
    to_dict_col_vals,
    to_flat_list,
)


_LOGGER = logging.getLogger(__name__)


class DataLoader:
    def __init__(self, model_path, translation_path=None):
        self.model_path = model_path
        self.translation_path = translation_path

        self.config_dict = None
        self.data_type_dict = None
        self.order_dict = None
        self.model_data: DataFrame = None
        self.details_dict = None

        self.weights_dict = None
        self.translation_dict = None

        # load data
        self.config_dict = self._load_config()
        self.data_type_dict = self._load_data_types()
        self.order_dict = self._load_order()
        self.model_data = self._load_data()
        self.details_dict = self._load_details()

        self.weights_dict = self._load_weights()
        self.translation_dict = self._load_transaltion()

    def _load_config(self) -> Dict[str, str]:
        config_data: DataFrame = load_table_from_excel(self.model_path, "Config:", assume_default=False)
        config_dict = to_dict_from_2col(config_data)
        if config_dict is None:
            config_dict = {}
        return config_dict

    def _load_data_types(self):
        data_types: DataFrame = load_table_from_excel(self.model_path, "Data type:")
        data_type_dict = to_dict_from_2col(data_types)
        return data_type_dict

    def _load_order(self):
        order_data: DataFrame = load_table_from_excel(self.model_path, "Order:", assume_default=False)
        if order_data is None:
            return {}

        if self.data_type_dict:
            for row in order_data.iterrows():
                row_data = row[1]
                column_id = row_data.iloc[0]
                data_type = self.data_type_dict.get(column_id)
                if data_type:
                    # found type
                    value = row_data.iloc[1]
                    value = convert_value(value, data_type, sort_list=False)
                    row_data.iloc[1] = value
                else:
                    # convert to string list
                    value = row_data.iloc[1]
                    value = convert_value(value, "str list", sort_list=False)
                    row_data.iloc[1] = value
        order_dict = to_dict_from_2col(order_data)
        if order_dict is None:
            order_dict = {}
        return order_dict

    def _load_data(self) -> DataFrame:
        model_data: DataFrame = load_table_from_excel(self.model_path, "Data:", assume_default=True)
        apply_data_types(model_data, self.data_type_dict)
        return model_data

    def _load_details(self):
        details_data: DataFrame = load_table_from_excel(self.model_path, "Details:", assume_default=False)
        apply_data_types(details_data, self.data_type_dict)
        details_data = to_json(details_data)
        if details_data is None:
            details_data = {}
        return details_data

    def _load_weights(self):
        ## returns multi dict: [answer, category, cat_value, weight_value]
        order_dict = self.order_dict
        model_data: DataFrame = self.model_data
        weights_dict = {}

        header_row = model_data.columns
        column_names = header_row.to_list()
        for _index, row_data in model_data.iterrows():
            answer_id = row_data.iloc[0]
            weights_dict[answer_id] = {}
            row_length = len(row_data)
            for row_index in range(1, row_length):
                col_name = column_names[row_index]
                order_values = order_dict.get(col_name)
                if order_values is None:
                    # order not specified for given category - use binary rule
                    values_list = model_data[col_name].tolist()
                    values_list = to_flat_list(values_list)
                    cat_values_set = set(values_list)
                    cat_values_set = sorted(cat_values_set)

                    row_values = row_data.iloc[row_index]
                    col_weights_dict = calculate_weights_binary(row_values, cat_values_set)
                    weights_dict[answer_id][col_name] = col_weights_dict
                    continue

                try:
                    row_values = row_data.iloc[row_index]
                    col_weights_dict = calculate_weights(row_values, order_values)
                    weights_dict[answer_id][col_name] = col_weights_dict
                except ValueError:
                    _LOGGER.exception("unable to find row value in order list '%s' (%s)", col_name, order_values)
                    raise

        return weights_dict

    def _load_transaltion(self) -> Dict[str, str]:
        if not self.translation_path:
            return {}
        with open(self.translation_path, "r", encoding="utf8") as fp:
            return json.load(fp)

    def get_model_json(self):
        return to_json(self.model_data)

    def get_possible_values_dict(self):
        options_dict = to_dict_col_vals(self.model_data)
        options_dict.update(self.order_dict)
        return options_dict

    def get_page_title(self):
        return self.config_dict.get("page_title", "")

    def get_answer_column(self):
        answer_column_id = self.config_dict.get("answer_column")
        if answer_column_id is not None:
            return answer_column_id
        columns = list(self.model_data.columns)
        return columns[0]

    def get_translation(self, key: str) -> str:
        return get_translation(self.translation_dict, key)

    def get_total_count(self) -> int:
        return get_total_count(self.model_data)

    def print_info(self):
        print_data_info(self.model_data)


# ===================================================


def get_translation(translation_dict: Dict[str, str], key: str) -> str:
    value = translation_dict.get(key)
    if value is not None:
        return value
    _LOGGER.info("translation not found for '%s'", key)
    return key


def get_total_count(model: DataFrame):
    total_count = 1
    model_values = to_dict_col_vals(model)
    cols_list = list(model_values.keys())[1:]
    for char_name in cols_list:
        values_set = model_values[char_name]
        # if "" in values_set:
        #     values_set.remove("")
        length = len(values_set)
        total_count *= length
    col_len = len(cols_list)
    total_count *= math.factorial(col_len)
    # total_count *= col_len
    return total_count


def print_data_info(model):
    print(model)
    model_values = to_dict_col_vals(model)
    cols_list = list(model_values.keys())[1:]
    for char_name in cols_list:
        values_set = model_values[char_name]
        # if "" in values_set:
        #     values_set.remove("")
        length = len(values_set)
        print(f"{char_name}: {length} {values_set}")
    total_count = get_total_count(model)
    print("total_count:", total_count)


# ================================================================


def apply_data_types(data_frame: DataFrame, data_types: dict):
    if data_frame is None:
        return
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


def convert_value(value, data_type: str, sort_list=None):
    if data_type == "int":
        return int(value)
    if data_type == "int range":
        return convert_int_range(value)
    if data_type == "str list":
        sort_content = sort_list if sort_list is not None else True
        return convert_str_list(value, sort_list=sort_content)
    if data_type == "link list":
        sort_content = sort_list if sort_list is not None else False
        return convert_str_list(value, sort_list=sort_content)
    raise RuntimeError(f"unknown data type '{data_type}'")


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


# =========================================


def calculate_weights_binary(row_values, possible_values):
    if not isinstance(row_values, list):
        row_values = [row_values]
    weight_dict = {}
    for poss_item in possible_values:
        weight = 0.0
        if poss_item in row_values:
            weight = 1.0
        weight_dict[poss_item] = weight
    return weight_dict


def calculate_weights(row_values, order_values):
    if not isinstance(row_values, list):
        row_values = [row_values]
    weight_dict = {}
    for order_item in order_values:
        weight_dict[order_item] = calculate_single_weight(order_item, row_values, order_values)
    return weight_dict


def calculate_single_weight(order_item, row_values, order_values):
    if order_item in row_values:
        return 1.0
    item_indexes = get_indexes([order_item], order_values)
    row_indexes = get_indexes(row_values, order_values)
    item_index = item_indexes[0]
    distance = min([abs(item_index - row_index) for row_index in row_indexes])
    order_len = len(order_values)
    return 1.0 - distance / order_len


def get_indexes(row_values, order_values):
    index_list = []
    for row_item in row_values:
        item_index = order_values.index(row_item)
        # try:
        #     item_index = order_values.index(row_item)
        # except ValueError:
        #     _LOGGER.exception("unable to find value '%s' in list '%s'", row_item, order_values)
        #     raise
        index_list.append(item_index)
    return index_list


def to_json(content: DataFrame):
    ## converts dataframe to list of dicts
    ## where each list item contains single dataframe row
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
