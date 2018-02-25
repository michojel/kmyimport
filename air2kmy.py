#!/usr/bin/env python3
"""
Script for conversion of csv export files from Air Bank to csv that is
import-able by KMyMoney.
"""

import argparse
import csv
from enum import Enum
import itertools
import pathlib
import re


class AirColumns(Enum):
    """Enumeration of interesting columns of input csv file."""
    DATE = 0
    AMOUNT = 5
    FEE = 6
    ORIGINALAMOUNT = 8
    PAYEE = 9
    PAYEEACCOUNTNAME = 11
    MYNOTE = 17
    RECEIVERNOTE = 18
    NOTE = 19
    EXCHANGERATE = 25
    POSTDATE = 31
    REFNUM = 32


class KMyColumns(Enum):
    """Enumeration of output collumns."""
    REFNUM = 0
    DATE = 1
    PAYEE = 2
    AMOUNT = 3
    MEMO = 4


INDELIM = ";"
OUTDELIM = ";"
MEMO_SEP = " - "
PRIORITY_COLUMNS = (AirColumns.REFNUM.value, AirColumns.DATE.value,
                    AirColumns.PAYEE.value, AirColumns.AMOUNT.value)
MEMO_PRIORITY_COLUMNS = (AirColumns.POSTDATE.value, AirColumns.MYNOTE.value,
                         AirColumns.NOTE.value, AirColumns.RECEIVERNOTE.value)
AMOUNT_COLUMNS = (AirColumns.AMOUNT.value, AirColumns.FEE.value,
                  AirColumns.ORIGINALAMOUNT.value,
                  AirColumns.EXCHANGERATE.value)

APP_DESC = 'Convert Airbank exports to csv file import-able by KMyMoney.'


def parse_args():
    """Return parsed arguments of the script."""
    parser = argparse.ArgumentParser(description=APP_DESC)
    parser.add_argument(
        'files',
        type=argparse.FileType('rt'),
        nargs="+",
        help='Files to process.')
    return parser.parse_args()


def is_column_amount(index):
    """Returns true if the given index belongs to column containing amount."""
    return index in AMOUNT_COLUMNS


def data_sanitize(data, column_index=None):
    """
    Return the given contents of cell sanitized.

    Returned data is stripped of whitespaces and problematic characters get
    removed. KMyMoney's csv importer gets easily confused when delimiters
    appear in quoted strings as well.
    """
    if column_index is not None and is_column_amount(column_index):
        data = re.sub(',', '.', data)
    return re.sub('[' + OUTDELIM + ',:]', '_', data.strip())


def merge_columns(row, original):
    """Return row filled with data from alternative columns."""
    for dest, src in [(KMyColumns.AMOUNT.value, AirColumns.FEE.value),
                      (KMyColumns.PAYEE.value,
                       AirColumns.PAYEEACCOUNTNAME.value)]:
        if row[dest]:
            continue
        data = data_sanitize(original[src], src)
        if not data:
            continue
        row = row[:dest] + [data] + row[dest + 1:]
    return row


def get_memo_column(column_names, row):
    """Return the contents of memo column for the given row."""
    result = []
    processed = set()
    for index in itertools.chain(MEMO_PRIORITY_COLUMNS, range(
            len(column_names))):
        if index in PRIORITY_COLUMNS or index in processed:
            continue
        processed.add(index)
        name = column_names[index]
        data = data_sanitize(row[index], index)
        if not data:
            continue
        data = re.sub(OUTDELIM, '_', data)
        result.append("{}{}{}".format(name, MEMO_SEP, data))
    return "\n".join(result)


def transform(rows):
    """
    Yields modified row for each input row.

    Data is sanitized and less important columns are merged into single memo
    column.
    """
    for index, row in enumerate(rows):
        newrow = []
        for col in PRIORITY_COLUMNS:
            data = data_sanitize(row[col], col)
            if index > 0 and col == AirColumns.DATE.value:
                data = re.sub('/', ' ', data)
            data = re.sub(OUTDELIM, '_', data)
            newrow.append(data)
        if index == 0:
            column_names = row
            newrow.append("Memo")
        else:
            newrow.append(get_memo_column(column_names, row))
        yield merge_columns(newrow, row)


def process_file(input_file):
    """Writes a new file for the given csv file with .kmy.csv suffix."""
    pth = pathlib.PurePosixPath(input_file.name)
    with open(pathlib.PurePath.joinpath(
            pth.parent, pth.stem + ".kmy" + pth.suffix), "w") as output_file:
        rows = csv.reader(input_file, delimiter=INDELIM, quotechar='"')
        writer = csv.writer(
            output_file, delimiter=OUTDELIM, quoting=csv.QUOTE_ALL)
        for row in transform(rows):
            writer.writerow(row)


def main():
    """Binds all the functionality together."""
    args = parse_args()
    for input_file in args.files:
        process_file(input_file)


if __name__ == '__main__':
    main()
