import swpc_proton
import sep_json_writer
import model_info
from utils import current_yearmonth, split_yearmonth

import argparse
import datetime
import logging
import os.path

parser = argparse.ArgumentParser(
    description='Download forecast jsons from ISWA data tree'
)
parser.add_argument('yearmonth', nargs='?', default=current_yearmonth(),
                    help='month in YYYY/MM format')
parser.add_argument('--all', action='store_true')
args = parser.parse_args()
# TODO: implemnt --clobber argument, default is not to clobber

# Instantiate the SWPC proton probability forecast parser object
# and parse all forecasts in the given time range
year, month = split_yearmonth(args.yearmonth, asint=True)
start = datetime.datetime(year, month, 1)
try:
    end = start.replace(month=month+1)
except ValueError:
    if start.month == 12:
        end = start.replace(year=year+1, month=1)
    else:
        raise

mode = 'reload'
dbo = None
verbose = True
logger = logging.getLogger()
lfh = None
cfg = dict(archive_dir=model_info.model_root['SWPC'])
p = swpc_proton.Proton(start, end, mode, dbo, verbose, logger, lfh, cfg)
forecasts = p.ParseAll(datefilter=(not args.all))

# Constant list of JSON data for this type of forecast
all_clear_probability_threshold = 0.01
json_args = ['--model-short-name', 'SWPC Day 1',
             '--spase-id', 'spase://CCMC/SimulationModel/SWPC/v20090103',
             '--mode', 'forecast', 
             '--energy-min', '10',
             '--energy-max', '-1',
             '--energy-units', 'MeV',
             '--species', 'proton',
             '--location', 'earth',
             '--prob-thresholds', '10',
             '--prob-threshold-units', 'pfu',
             '--all-clear-threshold', '10', 
             '--all-clear-threshold-units', 'pfu',
             '--all-clear-probability-threshold', str(all_clear_probability_threshold)
]

# To fill: issue_time, prediction_window, probabilities, all_clear
program_desc = "Convert directory of SWPC RSGA.txt files to CCMC JSON"
json_parser = sep_json_writer.InitParser(program_desc)

for filepath, (issue, day1, day2, day3) in forecasts.items():
    filedir, filename = os.path.split(filepath)
    # The Day-1 prediction window begins at 00:00 UTC on the 
    # day following the day the forecast was issued,
    # and has a duration of 1 day
    nextday = issue + (datetime.timedelta(days=1) 
                       - datetime.timedelta(hours=issue.hour, minutes=issue.minute))
    window = (nextday, nextday+datetime.timedelta(days=1))

    # Evaluate all clear boolean
    all_clear = day1 <= all_clear_probability_threshold

    # Make the JSON by calling sep_json_writer and providing a list of 
    # command-line arguments. Merge constant arguments from list above with
    # the forecast-specific arguments we iterate through here
    print('===')
    print('Making JSON from', filename)
    useargs = [*json_args,
               '--output', filepath.replace('.txt', '.json'),
               '--issue-time', issue.isoformat()+'Z',
               '--prediction-window', window[0].isoformat()+'Z',
                                      window[1].isoformat()+'Z',
               '--probabilities', str(day1),
               '--all-clear', str(all_clear).lower()]
    (output_filename, output_dir, log_msgs, log_dir, log_starter, dataDict) = sep_json_writer.ParseArguments(json_parser, useargs)
    sep_json_writer.ConvertToJSON(dataDict, output_filename, output_dir, log_msgs, log_dir, log_starter)
