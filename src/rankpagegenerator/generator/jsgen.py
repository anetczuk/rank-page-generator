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

    details_page_dict = generate_details_pages(data_loader, nophotos, output_path)

    category_page_dict = generate_category_pages(data_loader, details_page_dict, dest_photos_dict, output_path)

    script_data_content = f"""\
const ANSWER_COLUMN = "{answer_column_id}";
const VALUES_DICT = {data_loader.get_possible_values_dict()};
const CATEGORY_PAGE = {category_page_dict};
const DETAILS_PAGE = {details_page_dict};
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
    <a href='?'>{data_loader.get_translation("Reset filters")}</a>
</div>

<div id="container"></div>

</body>
</html>
"""

    out_index_path = os.path.join(output_path, "index.html")
    _LOGGER.info("writing index page to %s", out_index_path)
    write_data(out_index_path, content)


## ============================================


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
        data_dict = row_dict.copy()

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
            photos_content = generate_details_photos_content(data_loader, answer_value, out_pages_path)

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
        page_name = f"match_{answer_counter}.html"
        out_answer_path = os.path.join(out_pages_path, page_name)
        _LOGGER.info("writing page to %s", out_answer_path)
        write_data(out_answer_path, content)
        answer_counter += 1

        rel_path = os.path.join(pages_dir, page_name)
        ret_dict[answer_value] = rel_path

    return ret_dict


def generate_details_photos_content(data_loader: DataLoader, answer_value, out_pages_path):
    photos_data = data_loader.photos_dict
    if photos_data is None:
        return ""
    img_list = photos_data.get(answer_value)
    if img_list is None:
        return ""
    content = ""
    content += """<div class="photogallery bottomspace">\n"""
    content += f"""<div class="photostitle">{data_loader.get_translation("Photos")}:</div>\n"""
    for img_src, img_dest in img_list:
        img_rel_path = os.path.relpath(img_dest, out_pages_path)
        license_path = img_src + ".lic"
        license_content = ""
        if os.path.isfile(license_path):
            license_content = read_data(license_path)
            license_content = (
                f"""<div class="license"><div>{data_loader.get_translation("License")}:</div>{license_content}</div>"""
            )
        else:
            _LOGGER.warning("unable to find license file for image %s", img_src)
        content += """<div class="imgtile">\n"""
        content += f"""    <a href="{img_rel_path}"><img src="{img_rel_path}"></a>\n"""
        content += f"""    {license_content}\n"""
        content += """</div>\n"""
    content += "</div>"
    return content


# ==================================================================


def generate_category_pages(data_loader: DataLoader, details_page_dict, dest_photos_dict, output_path):
    ret_dict = {}

    answer_col_name = data_loader.get_answer_column_name()
    columns_list = list(data_loader.model_data.columns)
    pages_dir = data_loader.config_dict.get("subpage_dir", "pages")
    out_pages_path = os.path.join(output_path, pages_dir)
    os.makedirs(out_pages_path, exist_ok=True)

    answer_counter = 0
    # iteate through column names - for each generate separate page
    for column_name in columns_list:
        if column_name == answer_col_name:
            continue

        page_name = f"category_{answer_counter}.html"
        out_answer_path = os.path.join(out_pages_path, page_name)
        generate_category_single_page(data_loader, details_page_dict, dest_photos_dict, column_name, out_answer_path)

        answer_counter += 1
        rel_path = os.path.join(pages_dir, page_name)
        ret_dict[column_name] = rel_path
    return ret_dict


def generate_category_single_page(
    data_loader: DataLoader, details_page_dict, dest_photos_dict, column_name, out_answer_path
):
    page_title = data_loader.get_page_title()
    answer_col_name = data_loader.get_answer_column_name()
    values_dict = data_loader.get_possible_values_dict()

    curr_page_title = page_title
    if curr_page_title:
        curr_page_title = f"""<title>{column_name} - {curr_page_title}</title>"""

    # generate categories table
    categories_content = """<table cellspacing="0" class="categoriestable">\n"""
    categories_content += f"""<tr> <th>{column_name}:</th> </tr>\n"""
    col_values_list = values_dict.get(column_name)
    for col_val_index, col_value in enumerate(col_values_list):
        # get answers matching column value
        found_items = []
        model_dict_list = data_loader.get_model_json()
        for data_row in model_dict_list:
            data_values = data_row.get(column_name)
            if data_values is None:
                continue
            if col_value in data_values:
                answer_values = data_row.get(answer_col_name)
                found_items.extend(answer_values)

        for answer_index, answer_value in enumerate(found_items):
            answer_item = details_page_dict.get(answer_value)
            if answer_item is None:
                answer_item = answer_value
            else:
                answer_item = f"""<a href="../{answer_item}">{answer_value}</a>"""

            gallery = ""
            answer_images = dest_photos_dict.get(answer_value)
            if answer_images:
                gallery += """<div class='minigallery'>"""
                for image in answer_images:
                    img_path = f"../{image}"
                    gallery += f"""<a href="{img_path}"><img src="{img_path}"></a>"""
                gallery += """</div>"""

            if answer_index == 0:
                answer_num = len(found_items)
                first_column = f"""<td rowspan='{answer_num}'>{col_value}</td>"""
            else:
                first_column = ""

            row_class = ""
            if (col_val_index + answer_index) % 2 == 0:
                row_class = "roweven"
            else:
                row_class = "rowodd"
            categories_content += (
                f"""<tr class="{row_class}"> {first_column} <td>{answer_item}</td> <td>{gallery}</td> </tr>\n"""
            )

        if len(found_items) < 1:
            # no results for given value
            first_column = f"""<td rowspan='1'>{col_value}</td>"""
            row_class = ""
            if (col_val_index) % 2 == 0:
                row_class = "roweven"
            else:
                row_class = "rowodd"
            categories_content += f"""<tr class="{row_class}"> {first_column} <td></td> <td></td> </tr>\n"""
    categories_content += """</table>\n"""

    content = ""
    content += f"""<html>
<head>
{curr_page_title}
<link rel="stylesheet" type="text/css" href="../styles.css">
</head>
<body>
<div class="bottomspace">
<a href="../index.html">{data_loader.get_translation("Back to Filters")}</a>
</div>
<div class="categories bottomspace">
{categories_content}
</div>
</body>
</html>
"""

    _LOGGER.info("writing page to %s", out_answer_path)
    write_data(out_answer_path, content)
