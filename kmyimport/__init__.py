"""
Script for conversion of csv export files from Fio Bank to csv that is
import-able by KMyMoney.
"""

import csv
import codecs
from datetime import datetime
import itertools
from enum import IntEnum
from html.parser import HTMLParser
import pathlib
import re

import chardet

OUTDELIM = ";"
MEMO_SEP = " - "


class Columns(IntEnum):
    """Enumeration of output collumns."""
    REFNUM = 0
    DATE = 1
    PAYEE = 2
    AMOUNT = 3
    MEMO = 4


COLUMN_DESCRIPTIONS = {
    Columns.REFNUM: "Reference number",
    Columns.DATE: "Date",
    Columns.PAYEE: "Payee",
    Columns.AMOUNT: "Amount",
    Columns.MEMO: "Memo",
}

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    stripper = MLStripper()
    stripper.feed(html)
    return stripper.get_data()


def get_output_header():
    return [COLUMN_DESCRIPTIONS[c] for c in Columns.__members__.values()]


def data_sanitize(data, is_amount=False):
    """
    Returns the given contents of cell sanitized.

    Returned data is stripped of whitespaces and problematic characters get
    removed. KMyMoney's csv importer gets easily confused when delimiters
    appear in quoted strings as well.
    """
    if is_amount:
        return re.sub(',', '.', data.strip())
    if isinstance(data, datetime):
        return data.strftime('%d %m %Y')
    return re.sub('[' + OUTDELIM + ',:]', '_', strip_tags(data.strip()))


def get_memo_column(column_names,
                    row,
                    priority_columns=set(),
                    skip_columns=set(),
                    is_column_amount=None):
    """Return the contents of memo column for the given row."""
    result = []
    processed = set()
    if not is_column_amount:
        def is_column_amount(_):
            return False
    for index in itertools.chain(priority_columns, range(len(column_names))):
        if index in skip_columns or index in processed or index >= len(row):
            continue
        processed.add(index)
        name = column_names[index]
        try:
            data = data_sanitize(row[index], is_column_amount(index))
        except IndexError:
            print("failed on index={}, with row: {}".format(index, row))
            raise
        if not data:
            continue
        data = re.sub(OUTDELIM, '_', data)
        result.append("{}{}{}".format(name, MEMO_SEP, data))
    return "\n".join(result)


def get_decoded(infile, encoding=None):
    """Returns decoded file of the given file.

    The infile will be closed and reopened again.
    """
    if not encoding:
        raw = infile.read(32)
        encoding = chardet.detect(raw)['encoding']
    infile.close()
    return open(infile.name, "rt", encoding=encoding)


def get_csv_writer(output_file=None, input_file=None):
    def get_writer(handle):
        return csv.writer(handle, delimiter=OUTDELIM, quoting=csv.QUOTE_ALL)

    if isinstance(output_file, str):
        return get_writer(open(output_file, "w"))
    elif output_file and hasattr(output_file, "write"):
        return csv.writer(output_file)
    elif input_file:
        pth = pathlib.PurePosixPath(input_file.name)
        file_name = pathlib.PurePath.joinpath(
            pth.parent, pth.stem + ".kmy" + pth.suffix)
        return get_writer(open(file_name, "w"))

    raise TypeError("no supported output_file or input_file given")


def skip_header(rows):
    """Print and skip the header preceding the actual data."""
    for row in rows:
        if len(row) <= 2:
            if len(row) == 2:
                print("{:<15}\t{}".format(
                    row[0].strip().strip('"').capitalize() + ":",
                    row[1].strip()))
            else:
                return
        else:
            return
