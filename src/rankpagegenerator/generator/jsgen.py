#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause license found in the
# LICENSE file in the root directory of this source tree.
#

import os
import logging

import shutil

from rankpagegenerator.utils import write_data, read_data
from rankpagegenerator.generator.utils import HTML_LICENSE, dict_to_html_table
from rankpagegenerator.generator.dataloader import DataLoader
from rankpagegenerator.data import DATA_DIR


SCRIPT_DIR = os.path.dirname(__file__)

_LOGGER = logging.getLogger(__name__)


def generate_pages(model_path, translation_path, embed, nophotos, output_path):
    data_loader = DataLoader(model_path, translation_path)
    generate_javascript(data_loader, embed, nophotos, output_path)


## ============================================


def generate_javascript(data_loader: DataLoader, embed, nophotos, output_path):
    os.makedirs(output_path, exist_ok=True)

    navigation_script_path = os.path.join(DATA_DIR, "navigate.js")
    css_styles_path = os.path.join(DATA_DIR, "styles.css")

    answer_column_id = data_loader.get_answer_column_name()

    _LOGGER.info("answer column id: %s", answer_column_id)

    page_title = data_loader.get_page_title()
    if page_title:
        page_title = f"""<title>{page_title}</title>"""

    dest_photos_dict = {}
    if not nophotos:
        data_loader.copy_photos(output_path)
        for answer, photos_list in data_loader.photos_dict.items():
            dest_list = []
            for _img_src, img_dest in photos_list:
                img_rel_path = os.path.relpath(img_dest, output_path)
                dest_list.append(img_rel_path)
            dest_photos_dict[answer] = dest_list

    details_page_dir = generate_details_pages(data_loader, nophotos, output_path)

    script_data_content = f"""\
const ANSWER_COLUMN = "{answer_column_id}";
const VALUES_DICT = {data_loader.get_possible_values_dict()};
const DETAILS_PAGE = {details_page_dir};
const WEIGHTS_DICT = {data_loader.weights_dict};
const TRANSLATION_DICT = {data_loader.translation_dict};
const PHOTOS_DICT = {dest_photos_dict};"""

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
    <a href='?'>{data_loader.get_translation("Reset")}</a>
</div>

<div id="container"></div>

</body>
</html>
"""

    out_index_path = os.path.join(output_path, "index.html")
    _LOGGER.info("writing index page to %s", out_index_path)
    write_data(out_index_path, content)


# model_json - list of dicts (key is column name)
def generate_details_pages(data_loader: DataLoader, nophotos, output_path):
    model_json = data_loader.get_model_json()
    translation_dict = data_loader.translation_dict
    answer_column_id = data_loader.get_answer_column_name()

    ## generate answer pages
    page_title = data_loader.get_page_title()

    ret_dict = {}
    pages_dir = data_loader.config_dict.get("subpage_dir", "pages")
    out_pages_path = os.path.join(output_path, pages_dir)
    os.makedirs(out_pages_path, exist_ok=True)
    answer_counter = 0
    rows_num = len(model_json)
    for row_dict in model_json:
        data_dict = dict(zip(row_dict.keys(), row_dict.values()))

        answer_value = row_dict[answer_column_id][0]
        for item in data_loader.details_dict:
            item_detail = list(item.values())  # list of lists
            if item_detail[0][0] == answer_value:
                details_dict = item
                details_dict.pop(next(iter(details_dict)))  # remove first key
                data_dict.update(details_dict)
                break

        for key, val in data_dict.items():
            data_dict[key] = sorted(val)

        characteristics_content = dict_to_html_table(data_dict, translation_dict)

        curr_page_title = page_title
        if curr_page_title:
            curr_page_title = f"""<title>{answer_value} - {curr_page_title}</title>"""

        prev_link = data_loader.get_translation("Prev")
        if answer_counter > 0:
            prev_href = f"{answer_counter - 1}.html"
            prev_link = f"""<a href="{prev_href}">{prev_link}</a>"""
        next_link = data_loader.get_translation("Next")
        if answer_counter < rows_num - 1:
            next_href = f"{answer_counter + 1}.html"
            next_link = f"""<a href="{next_href}">{next_link}</a>"""

        photos_content = ""
        if not nophotos:
            photos_content = generate_details_photos_content(data_loader, answer_value)

        content = f"""<html>
{HTML_LICENSE}
<head>
{curr_page_title}
<link rel="stylesheet" type="text/css" href="../styles.css">
</head>
<body>
<div>
<a href="../index.html">{data_loader.get_translation("Back to Filters")}</a>
</div>
<div class="bottomspace">
<span>{prev_link}</span> <span>{next_link}</span>
</div>
<div class="characteristics bottomspace">
{characteristics_content}
</div>
{photos_content}
</body>
</html>
"""
        page_name = f"{answer_counter}.html"
        out_answer_path = os.path.join(out_pages_path, page_name)
        _LOGGER.info("writing page to %s", out_answer_path)
        write_data(out_answer_path, content)
        answer_counter += 1

        rel_path = os.path.join(pages_dir, page_name)
        ret_dict[answer_value] = rel_path

    return ret_dict


def generate_details_photos_content(data_loader: DataLoader, answer_value):
    photos_data = data_loader.photos_dict
    if photos_data is None:
        return ""
    img_list = photos_data.get(answer_value)
    if img_list is None:
        return ""
    content = ""
    content += """<div class="photosgallery">\n"""
    content += """<div class="photostitle">Photos:</div>\n"""
    for img_src, img_dest in img_list:
        license_path = img_src + ".lic"
        license_content = ""
        if os.path.isfile(license_path):
            license_content = read_data(license_path)
            license_content = f"""<div class="license"><div>License:</div>{license_content}</div>"""
        else:
            _LOGGER.warning("unable to find license file for image %s", img_src)
        content += """<div class="imgtile">\n"""
        content += f"""    <img src="{img_dest}">\n"""
        content += f"""    {license_content}\n"""
        content += """</div>\n"""
    content += "</div>"
    return content
