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

import sys
import argparse
import logging

from rankpagegenerator import logger
from rankpagegenerator.rankgen import generate_pages, print_info


_LOGGER = logging.getLogger(__name__)


# =======================================================================


def process_generate(args):
    _LOGGER.info("starting generator")
    _LOGGER.debug("logging to file: %s", logger.log_file)
    model_path = args.data
    output_path = args.outdir
    generate_pages(model_path, output_path)
    return 0


def process_info(args):
    _LOGGER.debug("logging to file: %s", logger.log_file)
    model_path = args.data
    print_info(model_path)
    return 0


# =======================================================================


def main():
    parser = argparse.ArgumentParser(description="rank-page-generator", prog="rankpagegenerator.main")
    parser.add_argument("-la", "--logall", action="store_true", help="Log all messages")
    # have to be implemented as parameter instead of command (because access to 'subparsers' object)
    parser.add_argument("--listtools", action="store_true", help="List tools")
    parser.set_defaults(func=None)

    subparsers = parser.add_subparsers(help="one of tools", description="use one of tools", dest="tool", required=False)

    ## =================================================

    description = "generate rank static pages"
    subparser = subparsers.add_parser("generate", help=description)
    subparser.description = description
    subparser.set_defaults(func=process_generate)
    subparser.add_argument("-d", "--data", action="store", required=False, help="Path to data file with model")
    subparser.add_argument("--outdir", action="store", required=True, help="Path to output directory")

    ## =================================================

    description = "print model info"
    subparser = subparsers.add_parser("info", help=description)
    subparser.description = description
    subparser.set_defaults(func=process_info)
    subparser.add_argument("-d", "--data", action="store", required=False, help="Path to data file with model")

    ## =================================================

    args = parser.parse_args()

    if args.listtools is True:
        tools_list = list(subparsers.choices.keys())
        print(", ".join(tools_list))
        return 0

    if args.logall is True:
        logger.configure(logLevel=logging.DEBUG)
    else:
        logger.configure(logLevel=logging.INFO)

    if "func" not in args or args.func is None:
        ## no command given -- print help message
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    code = main()
    sys.exit(code)
