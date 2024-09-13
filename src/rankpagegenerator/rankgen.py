#!/usr/bin/python3
#
# MIT License
#
# Copyright (c) 2024 Arkadiusz Netczuk <dev.arnet@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

try:
    ## following import success only when file is directly executed from command line
    ## otherwise will throw exception when executing as parameter for "python -m"
    # pylint: disable=W0611
    import __init__
except ImportError:
    ## when import fails then it means that the script was executed indirectly
    ## in this case __init__ is already loaded
    pass

import os
import logging

import pandas
from pandas.core.frame import DataFrame

from rankpagegenerator.utils import write_data


_LOGGER = logging.getLogger(__name__)


def print_info(model_path):
    model: DataFrame = Generator.load(model_path)
    Generator.print_info(model)


def generate_pages(model_path, output_path):
    gen = Generator()
    gen.generate(model_path, output_path)


class Generator:
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
        self._generate_submodel(model)

    def _generate_submodel(self, model):
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
            values_set = set(model[char_name].tolist())
            values_set = sorted(values_set)
            for value in values_set:
                submodel = model[model[char_name] == value]
                result_column = submodel[result_name]
                result_set = set(result_column.tolist())
                resilt_str = " ".join(result_set)
                content += f"""<tr> <td>{value}</td> <td>{resilt_str}</td> </tr>\n"""
            content += """</table>\n"""

        else:
            content += """<table>\n"""
            content += f"""<tr> <th>{self.label_characteristic}:</th> <th>{self.label_value}:</th> </tr>\n"""
            for char_name in char_names:
                values_set = set(model[char_name].tolist())
                values_set = sorted(values_set)
                links_list = []
                for value in values_set:
                    submodel = model[model[char_name] == value]
                    submodel = submodel.drop(char_name, axis=1)
                    subpage_path = self._generate_submodel(submodel)
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
        _LOGGER.debug("%f%% writing page: %s", progress, page_path)
        write_data(page_path, content)
        return page_path

    @staticmethod
    def load(model_path) -> DataFrame:
        model: DataFrame = pandas.read_excel(model_path)
        model = model.astype(str)

        # data_desc: DataFrame = pandas.read_excel(model_path, sheet_name=1)
        # print(data_desc)

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
            values_set = set(model[char_name].tolist())
            length = len(values_set)
            total_count *= length
        return total_count

    @staticmethod
    def print_info(model):
        column_names = list(model.columns)
        char_names = column_names[1:]
        for char_name in char_names:
            values_set = set(model[char_name].tolist())
            length = len(values_set)
            print(f"{char_name}: {length} {values_set}")
        total_count = Generator.get_total_count(model)
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
