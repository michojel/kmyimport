#!/usr/bin/env python3
"""
Script for conversion of csv export files from Air Bank to csv that is
import-able by KMyMoney.
"""

import argparse
import csv
from enum import Enum
import re

import kmyimport


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


def merge_columns(row, original):
    """Return row filled with data from alternative columns."""
    for dest, src in [(kmyimport.Columns.AMOUNT, AirColumns.FEE.value),
                      (kmyimport.Columns.PAYEE,
                       AirColumns.PAYEEACCOUNTNAME.value)]:
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
            if index > 0 and col == AirColumns.DATE.value:
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
    for row in transform(rows):
        writer.writerow(row)


def main():
    """Binds all the functionality together."""
    args = parse_args()
    for input_file in args.files:
        process_file(input_file)


if __name__ == '__main__':
    main()
