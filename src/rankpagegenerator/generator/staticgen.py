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

from rankpagegenerator.utils import write_data
from rankpagegenerator.generator.dataframe import to_dict_col_vals
from rankpagegenerator.generator.dataloader import DataLoader
from rankpagegenerator.generator.utils import HTML_LICENSE


SCRIPT_DIR = os.path.dirname(__file__)

_LOGGER = logging.getLogger(__name__)


def generate_pages(model_path, translation_path, _embed, output_path):
    gen = StaticGenerator()
    data_loader = DataLoader(model_path, translation_path)
    gen.generate(data_loader, output_path)


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

    def generate(self, data_loader: DataLoader, output_path):
        self.page_counter = 0

        self.out_root_dir = output_path
        os.makedirs(self.out_root_dir, exist_ok=True)

        self.out_index_path = os.path.join(self.out_root_dir, "index.html")
        gen_index_page(self.out_index_path)

        self.out_rank_dir = os.path.join(self.out_root_dir, "rank")
        os.makedirs(self.out_rank_dir, exist_ok=True)

        self.total_count = data_loader.get_total_count()
        self._generate_submodel(data_loader, [])

    def _generate_submodel(self, data_loader: DataLoader, curr_state):
        model = data_loader.model_data
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

        model_values = to_dict_col_vals(model)
        column_names = list(model.columns)
        char_names = column_names[1:]

        if len(char_names) == 1:
            # bottom page
            result_name = column_names[0]
            char_name = char_names[0]
            content += """<table>\n"""
            content += f"""<tr> <th>{char_name}</th> <th></th> </tr>\n"""

            model_column = model[char_name]
            values_set = model_values[char_name]

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
                values_set = model_values[char_name]
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
