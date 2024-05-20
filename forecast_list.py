import pathlib
import sys
import os.path
import pickle
import argparse
import warnings

import model_info
import utils

parser = argparse.ArgumentParser(
    description='Generate lists of forecast jsons from ISWA data tree'
)
parser.add_argument('model', nargs='*', help='model forecasts list')
parser.add_argument('-f', '--flavor', default=None,
                    help='Specify model flavor. All known flavors fetched by default')
parser.add_argument('--start', default='2019/01',
                    help='starting month in YYYY/MM format')
parser.add_argument('--end', default=utils.current_yearmonth(),
                    help='ending month in YYYY/MM format')
parser.add_argument('--month', default=None,
                    help='single  month in YYYY/MM format.  Ignores --start and --end.')
parser.add_argument('-P', '--print-stats', action='store_true', default=False,
                    help='Only print forecast statistics, not file names')
parser.add_argument('-S', '--save-stats', action='store_true', default=False,
                    help='Save forecast statistics')
parser.add_argument('-X', '--exclude',
                    help='Do not print/count files appearing in this list')
args = parser.parse_args()

stats = {}

exclude = []
if args.exclude:
    with open(args.exclude) as fh:
        for line in fh:
            exclude.append(line.rstrip())
exclude = set(exclude) # change to set for efficient lookups

print_files = True
if args.print_stats:
    print_files = False

if args.month is not None:
    args.start = args.month
    args.end = args.month

if args.model:
    model_list = args.model
else:
    model_list = model_info.models

for model in model_list:
    stats[(model,)] = 0

    # Check which flavors to process
    if args.flavor:
        if args.flavor in model_info.flavors[model]:
            flavors = [args.flavor]
        else:
            print("ERROR: flavor", args.flavor, "not valid for model", model)
            exit(1)
    elif model in model_info.flavors:
        flavors = model_info.flavors[model]
        if model in model_info.inactive_flavors:
            flavors += model_info.inactive_flavors[model]
    else:
        flavors = ['']

    # Iterate through selected flavors
    for flavor in sorted(flavors):
        p = pathlib.Path(os.path.join(model_info.model_root[model], flavor))
        stats[(model, flavor)] = 0
        if not p.is_dir():
            warnings.warn(str(p) + " does not exist")
            continue

        for year, month in utils.yearmonth_iter(args.start, args.end):
            yearmonth = f"{year:04d}/{month:02d}"
            pym = p / yearmonth
            if pym.is_dir():
                glob = pym.glob('*.json')
            elif flavor == '':
                # case that works for SEPMOD
                ym_glob = yearmonth.replace('/', '-')
                glob = p.glob(f'**/*{ym_glob}*.json')
            else:
                glob = None

            n = 0 # number of files in this month
            if glob:
                for json in glob:
                    if str(json) not in exclude:
                        if print_files: print(json)
                        n += 1
                stats[(model, flavor, yearmonth)] = n
            else:
                # None in stats means no directory found
                stats[(model, flavor, yearmonth)] = None
            stats[(model, flavor)] += n
            stats[(model,)] += n

def write_stats(fh):
    print("Monthly stats:", file=fh)
    for k in stats:
        if len(k) == 3:
            print(k, ':', stats[k], file=fh)

    print("Aggregate stats:", file=fh)
    for k in stats:
        if len(k) < 3:
            print(k, ':', stats[k], file=fh)

    N_all = 0
    for k in stats:
        if (len(k) == 1):
            N_all += stats[k]
    print("Total forecasts:", N_all, file=fh)

if args.print_stats:
    write_stats(sys.stdout)
if args.save_stats:
    txtfile = 'forecast_stats.txt'
    pklfile = 'forecast_stats.pkl'
    fh = open(txtfile, 'w')
    write_stats(fh)
    fh.close()
    pickle.dump(stats, open(pklfile, 'wb'))
    if args.print_stats:
        for f in txtfile, pklfile:
            print('Wrote', f)
