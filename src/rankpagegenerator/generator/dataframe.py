#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause license found in the
# LICENSE file in the root directory of this source tree.
#

import logging

import json
import pandas
from pandas.core.frame import DataFrame


_LOGGER = logging.getLogger(__name__)


def load_table_from_excel(data_path, marker, assume_default=False, sheet_index=0) -> DataFrame:
    xl = pandas.ExcelFile(data_path)
    try:
        sheets_num = len(xl.sheet_names)
        if sheet_index >= sheets_num:
            return None

        content: DataFrame = pandas.read_excel(io=xl, sheet_name=sheet_index)
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
        model = model_data.replace("nan", "")
        return model

    finally:
        xl.close()


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


def to_dict_from_2col(content: DataFrame):
    if content is None:
        return None
    field_list = content.iloc[:, 0].to_list()
    value_list = content.iloc[:, 1].to_list()
    config_dict = dict(zip(field_list, value_list))
    return config_dict


def to_dict_col_vals(content: DataFrame):
    ret_dict = {}
    header_row = content.columns
    column_names = header_row.to_list()
    for col_name in column_names:
        values_list = content[col_name].tolist()
        values_list = to_flat_list(values_list)
        cat_values_set = set(values_list)
        cat_values_list = sorted(cat_values_set)
        ret_dict[col_name] = cat_values_list
    return ret_dict


def to_dict_list(content: DataFrame):
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


def to_flat_list(data_list):
    ret_list = []
    for item in data_list:
        if isinstance(item, list):
            ret_list.extend(item)
        else:
            ret_list.append(item)
    ret_list = sorted(ret_list)
    return ret_list
