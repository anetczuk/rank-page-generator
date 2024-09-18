#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause license found in the
# LICENSE file in the root directory of this source tree.
#

import logging
import json


_LOGGER = logging.getLogger(__name__)


def load_transaltion(translation_path):
    if not translation_path:
        return {}
    with open(translation_path, "r", encoding="utf8") as fp:
        return json.load(fp)


def get_translation(translation_dict, key):
    value = translation_dict.get(key)
    if value is not None:
        return value
    _LOGGER.info("translation not found for '%s'", key)
    return key
