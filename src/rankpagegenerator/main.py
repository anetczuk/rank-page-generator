#!/usr/bin/python3
#
# Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
# All rights reserved.
#
# This source code is licensed under the BSD 3-Clause license found in the
# LICENSE file in the root directory of this source tree.
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
from rankpagegenerator.generator.dataloader import DataLoader
from rankpagegenerator.generator.jsgen import generate_pages
from rankpagegenerator.generator.photogen import parse_license_file


_LOGGER = logging.getLogger(__name__)


# =======================================================================


def process_generate(args):
    _LOGGER.info("starting generator")
    _LOGGER.debug("logging to file: %s", logger.log_file)
    model_path = args.data
    translation_path = args.translation
    embed = str(args.embedscripts).lower() != "false"
    nophotos = str(args.nophotos).lower() != "false"
    output_path = args.outdir

    generate_pages(model_path, translation_path, embed, nophotos, output_path)
    return 0


def process_info(args):
    _LOGGER.debug("logging to file: %s", logger.log_file)
    model_path = args.data

    data_loader = DataLoader(model_path)
    data_loader.print_info()
    return 0


def process_photos(args):
    _LOGGER.debug("logging to file: %s", logger.log_file)
    license_path = args.licensefile
    output_path = args.outdir

    parse_license_file(license_path, output_path)
    return 0


# =======================================================================


def main():
    parser = argparse.ArgumentParser(
        prog="python3 -m rankpagegenerator.main",
        description="generate static pages containing rank search based on defined model",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-la", "--logall", action="store_true", help="Log all messages")
    # have to be implemented as parameter instead of command (because access to 'subparsers' object)
    parser.add_argument("--listtools", action="store_true", help="List tools")
    parser.set_defaults(func=None)

    subparsers = parser.add_subparsers(help="one of tools", description="use one of tools", dest="tool", required=False)

    ## =================================================

    description = "generate rank static pages"
    subparser = subparsers.add_parser(
        "generate", help=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparser.description = description
    subparser.set_defaults(func=process_generate)
    subparser.add_argument("-d", "--data", action="store", required=False, help="Path to data file with model")
    subparser.add_argument("-t", "--translation", action="store", required=False, help="Path to translation file")
    subparser.add_argument("--embedscripts", action="store", default=False, help="Embed scripts into one file")
    subparser.add_argument("--nophotos", action="store", default=False, help="Do not generate image galleries")
    subparser.add_argument("--outdir", action="store", required=True, help="Path to output directory")

    ## =================================================

    description = "print model info"
    subparser = subparsers.add_parser("info", help=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    subparser.description = description
    subparser.set_defaults(func=process_info)
    subparser.add_argument("-d", "--data", action="store", required=False, help="Path to data file with model")

    ## =================================================

    description = "parse license file and prepare photos"
    subparser = subparsers.add_parser(
        "preparephotos", help=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparser.description = description
    subparser.set_defaults(func=process_photos)
    subparser.add_argument("-lf", "--licensefile", action="store", required=True, help="Path to license file")
    subparser.add_argument("--outdir", action="store", required=True, help="Path to output directory")

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
