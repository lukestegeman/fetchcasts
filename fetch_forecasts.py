import argparse
import subprocess
import os.path
import datetime

import model_info
from utils import current_yearmonth, split_yearmonth

parser = argparse.ArgumentParser(
    description='Download forecast jsons from ISWA data tree'
)

parser.add_argument('model', help='model forecasts to download')
parser.add_argument('yearmonth', nargs='?', default=None,
                    help='month in YYYY/MM format')
parser.add_argument('-f', '--flavor', default=None,
                    help='Specify model flavor. All known flavors fetched by default')
parser.add_argument('-A', '--all', action='store_true', default=False,
                    help='Fetch all forecasts for all time')
parser.add_argument('-t', '--test', action='store_true', default=False,
                    help='Print wget commands, but do not execute')
args = parser.parse_args()

class ISWAget:
    def __init__(self, model, accept=None, reject=None,
                 include=None, exclude=None):
        self.model = model
        self.root = model_info.model_root[model]
        if accept is None:
            self.accept = [f"{model}*.json"]
        else:
            self.accept = accept
        if reject is None:
            self.reject = '\?' # reject query links; e.g. sorting columns
        else:
            self.reject = reject
        self.include = include
        self.exclude = exclude
        self.flags = ['--mirror', '--no-parent', '--tries=360']

    def wget(self, flavor, yearmonth=None):
        cmd = ['wget'] + self.flags
        for a in self.accept:
            cmd += ["-A", a]
        cmd += ["--reject-regex", self.reject]
        if self.include is not None:
            cmd += ["-I", self.include]
        if self.exclude is not None:
            cmd += ["-X", self.exclude]
        if yearmonth is None:
            yearmonth = current_yearmonth()
        # Build the path.  This code uses the fact that
        # '' means skip that level.  Multiple '' make one '/'
        path = os.path.join(self.root, flavor, yearmonth, '')
        cmd += [f"https://{path}"]
        if yearmonth:
            year, month = split_yearmonth(yearmonth)
            for i, c in enumerate(cmd):
                if ('{' in c) and ('}' in c):
                    cmd[i] = c.format(year=year, month=month)
        return cmd

    def run(self, flavor=None, yearmonth=None, test=False):
        if flavor is not None:
            # use the given flavor
            flavors = [flavor]
        elif self.model in model_info.flavors:
            # use all the known flavors
            flavors = model_info.flavors[self.model]
        else:
            # this model has no flavor
            flavors = ['']

        for flavor in flavors:
            wget = self.wget(flavor, yearmonth=yearmonth)
            print(*wget, flush=True) # get ahead of buffering
            if not test:
                subprocess.run(wget)


# Defaults
accept = None
reject = None
include = None
exclude = None

# Exceptions
if args.model == 'SEPMOD':
    # SEPMOD needs to be treated very differntly
    # Forecast jsons are all in a single directory not 
    # filed by month.
    # Subdirectories filed by year are in the top level,
    # so care must be taken to avoid traversing all of that
    # Profiles are stored as .txt files
    accept = ['SEPMOD.{year}{month}*.json',
              'SEPMOD.{year}-{month}*mev.txt',
              '*_geo_integral_tseries_timestamped',
              '*_geo_tseries_timestamped']
    reject = '\?|ENLIL|data|output|plots'
    yearmonth = args.yearmonth
    current_yearmonth = current_yearmonth()
    current_year, current_month = split_yearmonth(current_yearmonth)
    if yearmonth is None:
        yearmonth = current_yearmonth
    year, month = split_yearmonth(yearmonth)
    top = os.path.split(model_info.model_root['SEPMOD'])[-1]
    if year == current_year:
        # exclude = []
        # for y in range(2000, int(current_year)):
        #     if y != year:
        #         exclude.append(f'/{top}/{y}')
        # exclude = ','.join(exclude)
        exclude = f'/{top}/20*'
    else:
        include = f'/{top}/{year}'
elif args.model == 'SWPC':
    accept = ['*RSGA.txt']
elif args.model == 'SAWS_ASPECS':
    # Include profiles stored as .txt files
    accept = ["SAWS_ASPECS*.json", "SAWS_ASPECS*.txt"]

if args.all:
    args.yearmonth = ''
iswaget = ISWAget(args.model, accept=accept, reject=reject,
                  include=include, exclude=exclude)
iswaget.run(flavor=args.flavor, yearmonth=args.yearmonth, test=args.test)
