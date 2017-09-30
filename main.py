#!/usr/bin/env python3

import argparse
import datetime
import importlib
import re
import os
import shutil
import subprocess
import sys
import tempfile

import dateutil.parser
import jinja2
import yaml


DEFAULTS = dict(
    context={},
    template_dir='.',
    invoice_dir='.',
    invoices_file='invoices.yaml',
)


class Config(dict):

    def __init__(self, *args, **kwargs):
        self.__dict__ = self
        self.update(DEFAULTS)
        dict.__init__(self, *args, **kwargs)

    @classmethod
    def from_yaml(cls, yaml_file):
        with open(yaml_file) as f:
            return cls(yaml.load(f.read()))


def format_currency(amount, digits=2):
    return '{:.{}f}'.format(amount, digits)


def render_invoice(config):
    context = config.context
    if 'context_processor' in config:
        module_name, function_name = config.context_processor.rsplit('.', 1)
        module = importlib.import_module(module_name)
        getattr(module, function_name)(context)
    env = jinja2.Environment(
        block_start_string='<%',
        block_end_string='%>',
        variable_start_string='<<',
        variable_end_string='>>',
        comment_start_string='<#',
        comment_end_string='<#',
        loader=jinja2.FileSystemLoader(config.template_dir),
    )
    env.filters['currency'] = format_currency
    template = env.get_template(config.template_name)
    return template.render(context)


def next_invoice_number(invoices, year):
    regex = re.compile(r'(?P<year>\d+)-(?P<number>\d+)$')
    max_num = 0
    for inv in invoices:
        y, n = regex.match(inv['number']).groups()
        if int(y) == year:
            max_num = max(max_num, int(n))
    return '{:04d}-{:04d}'.format(year, max_num + 1)


def command_new(config, args):
    invoice_context = dict(p.split('=', 1) for p in args.params)
    if 'date' in invoice_context:
        date = dateutil.parser.parse(invoice_context['date']).date()
    else:
        date = datetime.date.today()
        invoice_context.update(date=date.isoformat())
    try:
        with open(config.invoices_file) as f:
            invoices = yaml.load(f.read())
    except IOError:
        invoices = []
    invoice_number = next_invoice_number(invoices, date.year)
    invoice_context.update(number=invoice_number)
    invoices.append(invoice_context)
    with open(config.invoices_file, 'w') as f:
        f.write(yaml.dump(invoices))
    config.context.update(invoice_context)
    latex_source = render_invoice(config)
    base_name = 'invoice-{}'.format(invoice_number)
    with tempfile.TemporaryDirectory() as temp_dir:
        with open(os.path.join(temp_dir, base_name + '.tex'), 'w') as f:
            f.write(latex_source)
        p = subprocess.Popen([
            'pdflatex', '-halt-on-error', '-output-directory', temp_dir, f.name
        ])
        if p.wait():
            print('LaTeX failed -- please resolve the errors above.',
                  file=sys.stderr)
            sys.exit(1)
        shutil.move(os.path.join(temp_dir, base_name + '.pdf'),
                    os.path.join(config.invoice_dir, base_name + '.pdf'))
        

def main(argv):
    parser = argparse.ArgumentParser(
        description='Generate invoices from LaTeX templates.')
    parser.add_argument(
        '--config', metavar='FILE', default='config.yaml',
        help='path of the YAML config file')
    subparsers = parser.add_subparsers(dest='command')
    parser_new = subparsers.add_parser('new', help='create new invoice')
    parser_new.add_argument('params', metavar='PARAM=VALUE', nargs='+')
    args = parser.parse_args(argv[1:])

    config = Config.from_yaml(args.config)
    if args.command == 'new':
        command_new(config, args)
    else:
        parser.print_usage()


if __name__ == '__main__':
    main(sys.argv)
