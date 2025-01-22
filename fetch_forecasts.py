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
                 include=None, exclude=None, yearmonth_path=True):
        self.model = model
        self.root = model_info.model_root[model]
        if accept is None:
            if model in model_info.accept:
                self.accept = model_info.accept[model]
            else:
                self.accept = [f"{model}*.json"]
        else:
            self.accept = accept
        if reject is None:
            self.reject = '\?' # reject query links; e.g. sorting columns
        else:
            self.reject = reject
        self.include = include
        self.exclude = exclude
        self.flags = ['--mirror', '--no-parent']
        self.yearmonth_path = yearmonth_path



#wget --mirror --no-parent -nH --cut-dirs=1000000000 -A archive_202401*.html -P test/ --reject-regex /? ftp://ftp.swpc.noaa.gov/pub/alerts/

    def wget(self, flavor, yearmonth=None, ftp=False):
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
        if self.yearmonth_path:
            path = os.path.join(self.root, flavor, yearmonth, '')
        else:
            path = os.path.join(self.root, flavor, '')
        if ftp:
            insert = model_info.ftp_source.get(self.model).get(flavor)
            cmd += ["ftp://" + insert]
            cmd += ["-P", 'tmp']
            cmd += ["--cut-dirs=1000", "-nH"]
            cmd2 = ["source_dir='tmp'; dest_dir='" + model_info.model_root.get(self.model) + os.sep + flavor + "'; mkdir -p \"$dest_dir\"; find \"$source_dir\" -type f -name 'archive_[0-9][0-9][0-9][0-9][0-9][0-9]*.html' | while read -r file; do filename=$(basename \"$file\"); year_month=$(echo \"$filename\" | grep -oP 'archive_\\K[0-9]{6}'); year=$(echo $year_month | grep -o '^[0-9]\{4\}'); month=$(echo $year_month | grep -o '..$'); target_dir=\"$dest_dir/$year/$month\"; mkdir -p \"$target_dir\"; mv \"$file\" \"$target_dir/\"; done; rm -r \"$source_dir\";"]
        else:
            cmd += [f"https://{path}"]
            cmd2 = None
        print(yearmonth)
        if yearmonth:
            year, month = split_yearmonth(yearmonth)
            for i, c in enumerate(cmd):
                if ('{' in c) and ('}' in c):
                    cmd[i] = c.format(year=year, month=month)

        if yearmonth == '' and ftp:
            for i, c in enumerate(cmd):
                if ('{' in c) and ('}' in c):
                    cmd[i] = c.format(year='', month='')

        return cmd, cmd2

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
            # do any flavors come from an ftp source?
            if model_info.ftp_source.get(self.model) is not None:
                if model_info.ftp_source.get(self.model).get(flavor) is not None:
                    ftp = True
                else:
                    ftp = False
            else:
                ftp = False

            wget, wget2 = self.wget(flavor, yearmonth=yearmonth, ftp=ftp)
            print(*wget, flush=True) # get ahead of buffering
            if wget2 is not None:
                print(*wget2, flush=True)
            if not test:
                subprocess.run(wget, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if wget2 is not None:
                    subprocess.run(wget2, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Defaults
accept = None
reject = None
include = None
exclude = None
kwargs = {}

# Exceptions
if args.model == 'SEPMOD':
    # SEPMOD needs to be treated very differntly
    # Forecast jsons are all in a single directory not 
    # filed by month.
    # Subdirectories filed by year are in the top level,
    # so care must be taken to avoid traversing all of that
    # Profiles are stored as .txt files
    kwargs['yearmonth_path'] = False
    accept = ['SEPMOD.{year}-{month}*.json',
              'SEPMOD.{year}-{month}*mev.txt',
              'SEPMOD.{year}{month}*_geo_integral_tseries_timestamped',
              'SEPMOD.{year}{month}*_geo_tseries_timestamped']
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

if args.all:
    args.yearmonth = ''

iswaget = ISWAget(args.model, accept=accept, reject=reject,
                  include=include, exclude=exclude, **kwargs)
iswaget.run(flavor=args.flavor, yearmonth=args.yearmonth, test=args.test)
