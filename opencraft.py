# -*- coding: utf-8 -*-

import csv
import operator
import re
import subprocess

import latex


def read_data(filename):
    if filename.lower().endswith(('xls', 'xlsx')):
        csv_filename = re.sub(r'\.xlsx?$', '.csv', filename)
        p = subprocess.Popen(
            ['ssconvert', filename, csv_filename], stderr=subprocess.DEVNULL)
        p.wait()
        filename = csv_filename
    with open(filename) as f:
        return list(csv.DictReader(f))


def aggregate_data(data, hourly_rate):
    accounts = {}
    total = 0.0
    for entry in data:
        account = accounts.setdefault(
            entry['Account Key'], dict(issues={}, total=0.0))
        account['name'] = entry['Account Name']
        issue_key = entry['Issue Key']
        issue = account['issues'].setdefault(
            issue_key, dict(hours=0.0, amount=0.0))
        issue['key'] = issue_key
        issue['summary'] = latex.escape(entry['Issue summary'])
        hours = float(entry['Billed Hours'])
        issue['hours'] += hours
        amount = hours * hourly_rate
        issue['amount'] += amount
        account['total'] += amount
        total += amount
    for account in accounts.values():
        account['issues'] = sorted(account['issues'].values(),
                                   key=operator.itemgetter('key'))
    return sorted(accounts.values(), key=operator.itemgetter('name')), total


def context_processor(context):
    data = read_data(context['data_file'])
    accounts, total = aggregate_data(data, context['hourly_rate'])
    context.update(accounts=accounts, total=total)
