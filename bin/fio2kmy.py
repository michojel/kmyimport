#!/usr/bin/env python3
"""
Script for conversion of csv export files from Fio Bank to csv that is
import-able by KMyMoney.
"""

import argparse
import csv
from enum import Enum
import re

import kmyimport


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


INDELIM = ";"
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


def merge_columns(row, original):
    """Return row filled with data from alternative columns."""
    for dest, src in [(kmyimport.Columns.PAYEE,
                       FioColumns.PAYEEACCOUNTNAME.value)]:
        if row[dest]:
            continue
        data = kmyimport.data_sanitize(original[src], is_column_amount(src))
        if not data:
            continue
        row = row[:dest] + [data] + row[dest + 1:]
    return row


def transform(rows):
    """
    Yields modified row for each input row.

    Data is sanitized and less important columns are merged into single memo
    column.
    """
    yield kmyimport.get_output_header()
    for index, row in enumerate(rows):
        newrow = []
        for col in PRIORITY_COLUMNS:
            data = kmyimport.data_sanitize(row[col], is_column_amount(col))
            if index > 0 and col == FioColumns.DATE.value:
                data = re.sub('/', ' ', data)
            newrow.append(data)
        if index == 0:
            column_names = row
            continue
        newrow.append(kmyimport.get_memo_column(
            column_names, row,
            MEMO_PRIORITY_COLUMNS, PRIORITY_COLUMNS, is_column_amount))
        yield merge_columns(newrow, row)


def process_file(input_file):
    """Writes a new file for the given csv file with .kmy.csv suffix."""
    writer = kmyimport.get_csv_writer(input_file=input_file)
    rows = csv.reader(input_file, delimiter=INDELIM, quotechar='"')
    kmyimport.skip_header(rows)
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
