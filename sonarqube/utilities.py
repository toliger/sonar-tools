#
# sonar-tools
# Copyright (C) 2019-2022 Olivier Korach
# mailto:olivier.korach AT gmail DOT com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
'''

    Utilities for SonarQube API

'''
import sys
import os
import re
import logging
import argparse
import json
import datetime

OPT_VERBOSE = 'verbosity'
OPT_MODE = 'mode'
DRY_RUN = 'dryrun'
CONFIRM = 'confirm'
BATCH = 'batch'
RUN_MODE = DRY_RUN
ISO_DATE_FORMAT = "%04d-%02d-%02d"
SQ_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
SQ_DATE_FORMAT = "%Y-%m-%d"
SQ_TIME_FORMAT = "%H:%M:%S"

CSV_SEPARATOR = ','

logger = logging.getLogger('sonarqube-tools')
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)-7s | %(message)s')
fh = logging.FileHandler('sonarqube-tools.log')
ch = logging.StreamHandler()
logger.addHandler(fh)
logger.addHandler(ch)
fh.setFormatter(formatter)
ch.setFormatter(formatter)


def set_logger(name):
    global logger
    logger = logging.getLogger(name)
    new_fh = logging.FileHandler(name + '.log')
    new_ch = logging.StreamHandler()
    logger.addHandler(new_fh)
    logger.addHandler(new_ch)
    new_fh.setFormatter(formatter)
    new_ch.setFormatter(formatter)


def set_common_args(desc):
    """Parses options common to all sonarqube-tools scripts"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '-t', '--token', required=False,
        default=os.getenv('SONAR_TOKEN', None),
        help='''Token to authenticate to the source SonarQube, default is environment variable $SONAR_TOKEN
        - Unauthenticated usage is not possible''')
    parser.add_argument(
        '-u', '--url', required=False,
        default=os.getenv('SONAR_HOST_URL', 'http://localhost:9000'),
        help='''Root URL of the source SonarQube server,
        default is environment variable $SONAR_HOST_URL or http://localhost:9000 if not set''')
    parser.add_argument('-v', '--' + OPT_VERBOSE, required=False, choices=['WARN', 'INFO', 'DEBUG'],
                        default='INFO', help='Logging verbosity level')
    return parser


def set_component_args(parser):
    parser.add_argument('-k', '--componentKeys', '--projectKey', '--projectKeys', required=False,
                        help='Commas separated key of the components')
    return parser


def set_target_args(parser):
    parser.add_argument('-U', '--urlTarget', required=False, help='Root URL of the target SonarQube server')
    parser.add_argument('-T', '--tokenTarget', required=False,
                        help='Token to authenticate to target SonarQube - Unauthenticated usage is not possible')
    return parser


def get_logging_level(level):
    if level == 'DEBUG':
        lvl = logging.DEBUG
    elif level == 'WARN' or level == 'WARNING':
        lvl = logging.WARNING
    elif level == 'ERROR':
        lvl = logging.ERROR
    elif level == 'CRITICAL':
        lvl = logging.CRITICAL
    else:
        lvl = logging.INFO
    return lvl


def set_debug_level(level):
    logger.setLevel(get_logging_level(level))
    logger.info("Set debug level to %s", level)


def check_environment(kwargs):
    set_debug_level(kwargs.pop(OPT_VERBOSE))


def parse_and_check_token(parser):
    args = parser.parse_args()
    if args.token is None:
        logger.critical("Token is missing (Argument -t/--token)")
        sys.exit(4)
    return args


def json_dump_debug(json_data, pre_string=''):
    logger.debug("%s%s", pre_string, json_dump(json_data))


def format_date_ymd(year, month, day):
    return ISO_DATE_FORMAT % (year, month, day)


def format_date(somedate):
    return ISO_DATE_FORMAT % (somedate.year, somedate.month, somedate.day)


def string_to_date(string):
    return datetime.datetime.strptime(string, SQ_DATETIME_FORMAT)

def date_to_string(date, with_time=True):
    fmt = SQ_DATETIME_FORMAT
    if not with_time:
        fmt = SQ_DATE_FORMAT
    return date.strftime(fmt)

def get_setting(settings, key, default):
    if settings is None:
        return default
    return settings.get(key, default)

def redacted_token(token):
    if token is None:
        return '-'
    return re.sub(r'(...).*(...)', r'\1***\2', token)

def convert_to_type(value):
    try:
        newval = int(value)
        return newval
    except ValueError:
        pass
    try:
        newval = float(value)
        return newval
    except ValueError:
        pass
    return value

def unique_dict_field(data, field):
    item_list = []
    for d in data:
        element = d.get(field, None)
        if element is not None and element not in item_list:
            item_list.append(element)
    return item_list


def remove_nones(d):
    if isinstance(d, dict):
        return {k: v for k, v in d.items() if v is not None}
    else:
        return d


def json_dump(jsondata):
    return json.dumps(remove_nones(jsondata), indent=3, sort_keys=True, separators=(',', ': '))


def str_none(v):
    if v is None:
        return ''
    else:
        return str(v)
