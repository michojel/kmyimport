#!/usr/bin/env python3
"""
Script for conversion of csv export files from MailboxDE.cz to csv that is
import-able by KMyMoney.
"""

import argparse
import csv
from enum import IntEnum
import re

import kmyimport


class MBDColumns(IntEnum):
    """Enumeration of interesting columns of input csv file."""
    KREDIT = 0
    DATE = 1
    AMOUNT = 2
    VARIABLE_SYMBOL = 3
    PACKAGE_NUMBER = 4
    FROM = 5
    DESTINATION = 6
    TRACKING_NUMBER = 7


class KMyColumns(IntEnum):
    """Enumeration of output collumns."""
    DATE = 0
    AMOUNT = 1
    MEMO = 2


INDELIM = ";"
PRIORITY_COLUMNS = (MBDColumns.DATE, MBDColumns.AMOUNT, MBDColumns.KREDIT)
KMY2MBD = {
    kmyimport.Columns.DATE: MBDColumns.DATE,
    kmyimport.Columns.AMOUNT: MBDColumns.AMOUNT,
}
MEMO_PRIORITY_COLUMNS = (MBDColumns.FROM, MBDColumns.DESTINATION)
AMOUNT_COLUMNS = (MBDColumns.AMOUNT, MBDColumns.KREDIT)
APP_DESC = 'Convert MailboxDE.cz exports to csv importable by KMyMoney'


def parse_args():
    """Return parsed arguments of the script."""
    parser = argparse.ArgumentParser(description=APP_DESC)
    parser.add_argument(
        'files',
        type=argparse.FileType('rb'),
        nargs="+",
        help='Files to process.')
    return parser.parse_args()


def is_column_amount(index):
    """Returns true if the given index belongs to column containing amount."""
    return index in AMOUNT_COLUMNS


def merge_columns(row, original):
    """Return row filled with data from alternative columns."""
    for dest, src in [(kmyimport.Columns.AMOUNT.value, MBDColumns.KREDIT)]:
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
        for col in range(len(kmyimport.Columns) - 1):
            if col in KMY2MBD:
                mbdcol = KMY2MBD[col]
                data = kmyimport.data_sanitize(row[mbdcol],
                                               is_column_amount(mbdcol))
                if index > 0 and col == MBDColumns.DATE.value:
                    data = re.sub(r'\.', ' ', data)
            else:
                data = ""
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
    rows = csv.reader(kmyimport.get_decoded(input_file, 'iso-8859-2'),
                      delimiter=INDELIM, quotechar='"')
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
