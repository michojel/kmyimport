#!/usr/bin/env python3

"""
Script for conversion of csv export files from RoklenFX to csv that is
import-able by KMyMoney.
"""

import argparse
from collections import defaultdict
import csv
from datetime import datetime
from enum import IntEnum
import itertools
import pathlib
import re

import chardet


class TransColumns(IntEnum):
    """Enumeration of columns of input transactions csv file."""
    STATUS = 0
    DATE = 1
    REFNUM = 2
    SOLD_AMOUNT = 3
    SOLD_CURRENCY = 4
    RATIO = 5
    BOUGHT_AMOUNT = 6
    BOUGHT_CURRENCY = 7
    PAYEE = 8
    AMOUNT = 9
    VARIABLE_SYMBOL = 10
    TYPE = 11


class PayColumns(IntEnum):
    """Enumeration of columns of payments csv file."""
    DATE = 0
    AMOUNT = 1
    CURRENCY = 2
    PAYEE = 3
    REFNUM = 4
    TRANSACTION_REFNUM = 5


class DataColumns(IntEnum):
    """Enumeration of internal data columns."""
    REFNUM = 0
    DATE = 1
    PAYEE = 2
    AMOUNT = 3
    RATIO = 5
    BOUGHT_AMOUNT = 6
    BOUGHT_CURRENCY = 7
    SOLD_CURRENCY = 8
    VARIABLE_SYMBOL = 9
    TYPE = 10
    STATUS = 11
    TRANSACTION_REFNUM = 12


class KMyColumns(IntEnum):
    """Enumeration of output collumns."""
    REFNUM = 0
    DATE = 1
    PAYEE = 2
    AMOUNT = 3
    MEMO = 4


COLUMN_DESCRIPTIONS = {
    KMyColumns.REFNUM: "Reference number",
    KMyColumns.DATE: "Date",
    KMyColumns.PAYEE: "Payee",
    KMyColumns.AMOUNT: "Amount",
    KMyColumns.MEMO: "Memo",
}

DATACOL_NAMES = {
    DataColumns.RATIO: "Rate",
    DataColumns.BOUGHT_AMOUNT: "Amount bought",
    DataColumns.BOUGHT_CURRENCY: "Bought currency",
    DataColumns.SOLD_CURRENCY: "Sold currency",
    DataColumns.VARIABLE_SYMBOL: "Variable symbol",
    DataColumns.TYPE: "Type",
    DataColumns.STATUS: "Status",
    DataColumns.TRANSACTION_REFNUM: "Reference number of transaction",
}


INDELIM = ";"
OUTDELIM = ";"
MEMO_SEP = " - "
PRIORITY_COLUMNS = (DataColumns.REFNUM, DataColumns.DATE,
                    DataColumns.PAYEE, DataColumns.AMOUNT)
MEMO_PRIORITY_COLUMNS = (DataColumns.BOUGHT_AMOUNT,
                         DataColumns.BOUGHT_CURRENCY,
                         DataColumns.SOLD_CURRENCY,
                         DataColumns.RATIO, DataColumns.TRANSACTION_REFNUM)
AMOUNT_COLUMNS = (DataColumns.AMOUNT, DataColumns.BOUGHT_AMOUNT)

APP_DESC = """
Convert RoklenFX exports to csv file import-able by KMyMoney.

For each currency present in the given transactions or payments files an export
file is created named RoklenFX-${date}-${currency}.kmy.csv. Each of such
exported file should be imported in its own KMyMoney account of the same
currency.
"""


def parse_args():
    """Return parsed arguments of the script."""
    parser = argparse.ArgumentParser(description=APP_DESC)
    parser.add_argument(
        'transactions',
        type=argparse.FileType('rb'),
        help='Transactions file.')
    parser.add_argument(
        'payments',
        type=argparse.FileType('rb'),
        help='Payments file.')
    return parser.parse_args()


def is_column_amount(index):
    """Returns true if the given index belongs to column containing amount."""
    return index in AMOUNT_COLUMNS


def data_sanitize(data, column_index=None):
    """
    Returns the given contents of cell sanitized.

    Returned data is stripped of whitespaces and problematic characters get
    removed. KMyMoney's csv importer gets easily confused when delimiters
    appear in quoted strings as well.
    """
    if column_index is not None and is_column_amount(column_index):
        data = re.sub(',', '.', data)
    if isinstance(data, datetime):
        return data.strftime('%d %m %Y')
    return re.sub('[' + OUTDELIM + ',:]', '_', data.strip())


def get_memo_column(transaction):
    """Returns the contents of memo column for the given transaction.

    Parameters
    ----------
    transaction : dict(int -> obj)

    Returns
    -------
    list of strings
        Row for CSV writer.
    """
    result = []
    processed = set()
    for col in itertools.chain(
            MEMO_PRIORITY_COLUMNS, DataColumns.__members__.values()):
        if col in PRIORITY_COLUMNS or \
                col in processed or col not in transaction:
            continue
        processed.add(col)
        name = DATACOL_NAMES[col]
        data = data_sanitize(transaction[col], col)
        if not data:
            continue
        data = re.sub(OUTDELIM, '_', data)
        result.append("{}{}{}".format(name, MEMO_SEP, data))
    return "\n".join(result)


def transform(transactions):
    """Yields rows for each transaction.

    The data is sanitized (turned into strings).
    """
    yield [COLUMN_DESCRIPTIONS[c] for c in KMyColumns.__members__.values()]
    for transaction in transactions:
        newrow = []
        for col in PRIORITY_COLUMNS:
            newrow.append(data_sanitize(transaction[col], col))
        newrow.append(get_memo_column(transaction))
        yield newrow


def read_transactions(currencies, reader):
    """Creates internal transactions for the given transactions input.

    Parameters
    ----------
    currencies : dict(str -> list of dictionaries)
                 The dictionary will be updated for new transactions.
    reader : CSV reader for transactions file.
    """
    for index, row in enumerate(reader):
        if index == 0:  # skip header
            continue

        sold_currency = row[TransColumns.SOLD_CURRENCY].lower()
        transaction = {
            DataColumns.REFNUM: row[TransColumns.REFNUM],
            DataColumns.DATE: datetime.strptime(
                row[TransColumns.DATE], '%Y/%m/%d'),
            DataColumns.AMOUNT: "-" + row[TransColumns.SOLD_AMOUNT],
            DataColumns.RATIO: row[TransColumns.RATIO],
            DataColumns.BOUGHT_AMOUNT: row[TransColumns.BOUGHT_AMOUNT],
            DataColumns.BOUGHT_CURRENCY: row[TransColumns.BOUGHT_CURRENCY],
            DataColumns.STATUS: row[TransColumns.STATUS],
        }

        for attr in ["PAYEE", "VARIABLE_SYMBOL", "TYPE"]:
            if row[TransColumns.__members__[attr]]:
                transaction[DataColumns.__members__[attr]] = row[
                    TransColumns.__members__[attr]]
        currencies[sold_currency].append(transaction)

        bought_currency = row[TransColumns.BOUGHT_CURRENCY].lower()
        transaction = {
            DataColumns.REFNUM: row[TransColumns.REFNUM],
            DataColumns.DATE: datetime.strptime(
                row[TransColumns.DATE], '%Y/%m/%d'),
            DataColumns.AMOUNT: row[TransColumns.BOUGHT_AMOUNT],
            DataColumns.SOLD_CURRENCY: row[TransColumns.SOLD_CURRENCY],
            DataColumns.RATIO: row[TransColumns.RATIO],
            DataColumns.STATUS: row[TransColumns.STATUS],
        }

        for attr in ["PAYEE", "VARIABLE_SYMBOL", "TYPE"]:
            if row[TransColumns.__members__[attr]]:
                transaction[DataColumns.__members__[attr]] = row[
                    TransColumns.__members__[attr]]
        currencies[bought_currency].append(transaction)


def read_payments(currencies, reader):
    """Creates internal transactions for the given payments input.

    Parameters
    ----------
    currencies : dict(str -> list of dictionaries)
                 The dictionary will be updated for new transactions made out
                 of payments.
    reader : CSV reader for payments file.
    """
    for index, row in enumerate(reader):
        if index == 0:  # skip header
            continue
        currency = row[PayColumns.CURRENCY].lower()
        transaction = {
            DataColumns.REFNUM: row[PayColumns.REFNUM],
            DataColumns.DATE: datetime.strptime(
                row[PayColumns.DATE], '%d.%m.%Y'),
            DataColumns.AMOUNT: "-" + row[PayColumns.AMOUNT],
            DataColumns.PAYEE: row[PayColumns.PAYEE],
            DataColumns.TRANSACTION_REFNUM:
                row[PayColumns.TRANSACTION_REFNUM],
        }
        currencies[currency].append(transaction)


def write_currency_file(currency, transactions):
    """Writes a csv file for particular currency.

    Parameters
    ----------
    currency : str
               Abbreviation of currency.
    transactions : list of dictionaries
                   Contains transactions relating to the given currency.
    """
    transordered = sorted(transactions, key=lambda t: t[DataColumns.DATE])
    pth = pathlib.PurePosixPath(
        "RoklenFX-{}-{}.kmy.csv".format(
            transordered[0][DataColumns.DATE].strftime("%Y-%m-%d"),
            currency))
    with open(pth, "w") as output_file:
        writer = csv.writer(
            output_file, delimiter=OUTDELIM, quoting=csv.QUOTE_ALL)
        for row in transform(transordered):
            writer.writerow(row)


def process_files(transreader, payreader):
    """Writes a new file for each currency in the given input readers."""
    currencies = defaultdict(list)
    read_transactions(currencies, transreader)
    read_payments(currencies, payreader)

    for cur, trans in currencies.items():
        write_currency_file(cur, trans)


def get_decoded(infile):
    """Returns decoded file of the given file.

    The infile will be closed and reopened again.
    """
    raw = infile.read(32)
    encoding = chardet.detect(raw)['encoding']
    infile.close()
    return open(infile.name, "rt", encoding=encoding)


def main():
    """Binds all the functionality together."""
    args = parse_args()
    transreader = csv.reader(get_decoded(args.transactions),
                             delimiter=INDELIM, quotechar='"')
    payreader = csv.reader(get_decoded(args.payments),
                           delimiter=INDELIM, quotechar='"')
    process_files(transreader, payreader)


if __name__ == '__main__':
    main()
