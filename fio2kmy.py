#!/usr/bin/env python3
"""
Script for conversion of csv export files from Fio Bank to csv that is
import-able by KMyMoney.
"""

import argparse
import csv
from enum import Enum
import itertools
import pathlib
import re


class FioColumns(Enum):
    """Enumeration of interesting columns of input csv file."""
    REFNUM = 0
    DATE = 1
    AMOUNT = 2
    PAYEE = 4
    PAYEEACCOUNTNAME = 5
    NOTE = 11
    RECEIVERNOTE = 12
    MYNOTE = 16


class KMyColumns(Enum):
    """Enumeration of output collumns."""
    REFNUM = 0
    DATE = 1
    PAYEE = 2
    AMOUNT = 3
    MEMO = 4


INDELIM = ";"
OUTDELIM = ";"
PRIORITY_COLUMNS = (FioColumns.REFNUM.value, FioColumns.DATE.value,
                    FioColumns.PAYEE.value, FioColumns.AMOUNT.value)
MEMO_PRIORITY_COLUMNS = (FioColumns.MYNOTE.value, FioColumns.NOTE.value,
                         FioColumns.RECEIVERNOTE.value)
AMOUNT_COLUMNS = (FioColumns.AMOUNT.value, )


def parse_args():
    """Return parsed arguments of the script."""
    parser = argparse.ArgumentParser(
        description='Convert Fiobank exports to csv importable by KMyMoney')
    parser.add_argument(
        'files',
        type=argparse.FileType('r'),
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
    for dest, src in [(KMyColumns.PAYEE.value,
                       FioColumns.PAYEEACCOUNTNAME.value)]:
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
        result.append("{} - {}".format(name, data))
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
            if index > 0 and col == FioColumns.DATE.value:
                data = re.sub('/', ' ', data)
            data = re.sub(OUTDELIM, '_', data)
            newrow.append(data)
        if index == 0:
            column_names = row
            newrow.append("Memo")
        else:
            newrow.append(get_memo_column(column_names, row))
        yield merge_columns(newrow, row)


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


def process_file(input_file):
    """Writes a new file for the given csv file with .kmy.csv suffix."""
    pth = pathlib.PurePosixPath(input_file.name)
    with open(
            pathlib.PurePath.joinpath(pth.parent,
                                      pth.stem + ".kmy" + pth.suffix),
            "w") as output_file:
        rows = csv.reader(input_file, delimiter=INDELIM, quotechar='"')
        skip_header(rows)
        writer = csv.writer(
            output_file, delimiter=OUTDELIM, quoting=csv.QUOTE_ALL)
        for row in transform(rows):
            writer.writerow(row)


# main is the main function
def main():
    """Binds all the functionality together."""
    args = parse_args()
    for input_file in args.files:
        process_file(input_file)


if __name__ == '__main__':
    main()
