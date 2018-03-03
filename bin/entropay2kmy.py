#!/usr/bin/env python3
"""
Script for conversion of csv export files from Entropay to csv that is
import-able by KMyMoney.
"""

import argparse
import csv
from datetime import datetime
from enum import Enum
import re

import kmyimport


class EntropayColumns(Enum):
    """Enumeration of interesting columns of input csv file."""
    DATE = 0
    PAYEE = 1
    AMOUNT = 4
    ORIGINALCURRENCY = 5
    ORIGINALAMOUNT = 6
    FOREXRATE = 7
    FEECURRENCY = 8
    FEEAMOUNT = 9
    NETAMOUNT = 11


INDELIM = ","
PRIORITY_COLUMNS = (EntropayColumns.DATE.value,
                    EntropayColumns.PAYEE.value,
                    EntropayColumns.NETAMOUNT.value)
MEMO_PRIORITY_COLUMNS = (EntropayColumns.ORIGINALCURRENCY.value,
                         EntropayColumns.ORIGINALAMOUNT.value,
                         EntropayColumns.FEECURRENCY.value,
                         EntropayColumns.FEEAMOUNT.value)
AMOUNT_COLUMNS = (EntropayColumns.AMOUNT.value,
                  EntropayColumns.ORIGINALAMOUNT.value,
                  EntropayColumns.FOREXRATE.value,
                  EntropayColumns.FEEAMOUNT.value,
                  EntropayColumns.NETAMOUNT.value)

APP_DESC = 'Convert Entropay exports to csv file import-able by KMyMoney.'


def parse_args():
    """Return parsed arguments of the script."""
    parser = argparse.ArgumentParser(description=APP_DESC)
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
    for dest, src in []:
        if row[dest]:
            continue
        data = kmyimport.data_sanitize(original[src], is_column_amount(src))
        if not data:
            continue
        row = row[:dest] + [data] + row[dest + 1:]
    return row


def transform_date(value):
    """Parse the given data value and return string expected by KMyMoney."""
    # zero pad the day of month number
    value = re.sub(r'^\d-', r'0\g<0>', value)
    return datetime.strptime(value, "%d-%b-%Y").strftime("%d %m %Y")


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
            if index > 0 and col == EntropayColumns.DATE.value:
                data = transform_date(data)
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


# main is the main function
def main():
    """Binds all the functionality together."""
    args = parse_args()
    for input_file in args.files:
        process_file(input_file)


if __name__ == '__main__':
    main()
