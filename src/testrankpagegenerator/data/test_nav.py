#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause license found in the
# LICENSE file in the root directory of this source tree.
#

import unittest

import os
from nodejs import node
from rankpagegenerator.data import DATA_DIR


SCRIPT_DIR = os.path.dirname(__file__)


class NavTest(unittest.TestCase):
    def test_nav(self):
        nav_path = os.path.join(SCRIPT_DIR, "test_nav.js")
        os.environ["NODE_PATH"] = DATA_DIR
        returncode = node.call([nav_path])
        self.assertEqual(returncode, 0)

        # output = node.run([nav_path])
        # print(output.returncode)
        # print(output.stdout)
        # print(output.stderr)
