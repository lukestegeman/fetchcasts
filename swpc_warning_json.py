import sep_json_writer
import model_info
from utils import current_yearmonth, split_yearmonth

import argparse
import datetime
import glob
import logging
import os.path
import pandas as pd
import re

def get_submessages(filename):
    a = open(filename, 'r', encoding='latin-1')
    lines = a.readlines()
    a.close()
    start_flag = False
    for i in range(0, len(lines)):
        line = lines[i]
        if ('new Array(' in line) and (not 'new Array()' in line):
            start_index = i + 0
            start_flag = True
        if ';\n' in line and start_flag:
            end_index = i + 0
            break
    if not start_flag:
        return []
    messages = lines[start_index:end_index]
    submessage_dict_list = []
    for message in messages:
        if '"' in message:
            message = message.split('"')[1]
            submessages = message.split('<br>')
            if '' in submessages:
                submessages = [submessage for submessage in submessages if submessage != '']
            submessage_dict = {}
            for submessage in submessages: 
                if submessage.count(':') == 1:
                    key, value = submessage.split(':')
                    key = key.strip()
                    value = value.strip()
                    submessage_dict[key] = value
            submessage_dict_list.append(submessage_dict)
    return submessage_dict_list

def get_warnings(submessages):
    warning_messages = []
    warning_labels = ['WARNING', 'EXTENDED WARNING', 'CANCEL WARNING']
    for submessage in submessages:
        keys = list(submessage.keys())
        for label in warning_labels:
            if label in keys:
                warning_messages.append(submessage)
                continue
    return warning_messages

def extract_keyword_from_string(string, key):
    if key in string:
        start_index = string.index(key)
        end_index = start_index + len(key)
        return string[start_index : end_index]
    else:
        return None

def extract_connected_substring(input_string, search_chars):
    pattern = r'\w*' + re.escape(search_chars) + r'\w*'
    match = re.search(pattern, input_string) 
    if match:
        return match.group(0)
    else:
        return None

def construct_df_part(filename):
    submessages = get_submessages(filename)
    warning_messages = get_warnings(submessages)
    # MAKE DATAFRAME FROM WARNING MESSAGES
    df = pd.DataFrame()
    for message in warning_messages:
        message_df = pd.DataFrame([message])
        df = pd.concat([df, message_df])
    if 'Space Weather Message Code' in df.columns:
        df = df[df['Space Weather Message Code'].str.startswith('WARP')] 
    datetime_format = '%Y %b %d %H%M UTC'
    if 'Issue Time' in df.columns:
        df['Issue Time'] = pd.to_datetime(df['Issue Time'], format=datetime_format)
    if 'Valid From' in df.columns:
        df['Valid From'] = pd.to_datetime(df['Valid From'], format=datetime_format)
    if 'Valid To' in df.columns:
        df['Valid To'] = pd.to_datetime(df['Valid To'], format=datetime_format)
    if 'Now Valid Until' in df.columns:
        df['Now Valid Until'] = pd.to_datetime(df['Now Valid Until'], format=datetime_format)
    if 'Issue Time' in df.columns:
        df = df.sort_values('Issue Time')
    return df

def get_json_parameters(df, prefiltering=False): 
    jsons_warning = []
    jsons_extended_warning = []
    # THERE IS ONLY ONE TYPE OF WARNING
    warning = df['WARNING'].iloc[0]
    energy_low = extract_connected_substring(warning, 'MeV').replace('MeV', '')
    energy_high = str(-1)
    threshold = extract_connected_substring(warning, 'pfu').replace('pfu', '')
    json_warning_counter = -1
    json_extended_warning_counter = -1
    last_changed = None
    for index, row in df.iterrows():
        # MAKE A NEW JSON
        if not pd.isna(row['WARNING']):
            json_warning_counter += 1
            jsons_warning.append({})
            jsons_warning[json_warning_counter]['issue_time'] = row['Issue Time'].strftime('%Y-%m-%dT%H:%M:%SZ')
            jsons_warning[json_warning_counter]['energy_low'] = energy_low
            jsons_warning[json_warning_counter]['energy_high'] = energy_high
            jsons_warning[json_warning_counter]['threshold'] = threshold
            jsons_warning[json_warning_counter]['prediction_window_start'] = row['Valid From'].strftime('%Y-%m-%dT%H:%M:%SZ')
            jsons_warning[json_warning_counter]['prediction_window_end'] = row['Valid To'].strftime('%Y-%m-%dT%H:%M:%SZ')
            last_changed = 'WARNING'
            if prefiltering:
                if jsons_warning[json_warning_counter]['prediction_window_start'] > jsons_warning[json_warning_counter]['prediction_window_end']:
                    jsons_warning = jsons_warning[:-1]
                    json_warning_counter -= 1
        elif (not pd.isna(row['EXTENDED WARNING'])) and (not pd.isna(row['Now Valid Until'])):
            json_extended_warning_counter += 1
            jsons_extended_warning.append({})
            jsons_extended_warning[json_extended_warning_counter]['issue_time'] = row['Issue Time'].strftime('%Y-%m-%dT%H:%M:%SZ')
            jsons_extended_warning[json_extended_warning_counter]['energy_low'] = energy_low
            jsons_extended_warning[json_extended_warning_counter]['energy_high'] = energy_high
            jsons_extended_warning[json_extended_warning_counter]['threshold'] = threshold
            jsons_extended_warning[json_extended_warning_counter]['prediction_window_start'] = max(row['Issue Time'], row['Valid From']).strftime('%Y-%m-%dT%H:%M:%SZ')
            jsons_extended_warning[json_extended_warning_counter]['prediction_window_end'] = row['Now Valid Until'].strftime('%Y-%m-%dT%H:%M:%SZ')
            last_changed = 'EXTENDED WARNING'
            if prefiltering:
                if jsons_extended_warning[json_extended_warning_counter]['prediction_window_start'] > jsons_extended_warning[json_extended_warning_counter]['prediction_window_end']:
                    jsons_extended_warning = jsons_extended_warning[:-1]
                    json_extended_warning_counter -= 1
        else:
            if last_changed == 'WARNING':
                jsons_warning[json_warning_counter]['prediction_window_end'] = row['Issue Time'].strftime('%Y-%m-%dT%H:%M:%SZ')
            elif last_changed == 'EXTENDED WARNING':
                jsons_extended_warning[json_extended_warning_counter]['prediction_window_end'] = row['Issue Time'].strftime('%Y-%m-%dT%H:%M:%SZ')

    for i in range(0, len(jsons_warning)):
        jsons_warning[i]['last_data_time'] = jsons_warning[i]['issue_time']
    
    for i in range(0, len(jsons_extended_warning)):
        jsons_extended_warning[i]['last_data_time'] = jsons_extended_warning[i]['issue_time']
    
    return jsons_warning, jsons_extended_warning

def get_forecast_data_files(yearmonth, all_forecasts=False):    
    forecast_data_directory = os.path.join(model_info.model_root['SWPC'], 'Warning')
    forecast_data_filepaths = []
    year, month = split_yearmonth(yearmonth, asint=True)
    if all_forecasts:
        forecast_data_filepaths = glob.glob(forecast_data_directory + os.sep + '**' + os.sep + '*', recursive=True)
        forecast_data_filepaths_ = []
        for f in forecast_data_filepaths:
            if not os.path.isdir(f):
                forecast_data_filepaths_.append(f)
        forecast_data_filepaths = forecast_data_filepaths_
    else:
        # This inherently assumes that a SWPC cannot persist for more than a month.
        forecast_data_filepaths += glob.glob(os.path.join(forecast_data_directory, str(year), '{:02d}'.format(month)) + os.sep + '*')
        if month == 12:
            forecast_data_filepaths += glob.glob(os.path.join(forecast_data_directory, str(year + 1), '01') + os.sep + '*')
        else:
            forecast_data_filepaths += glob.glob(os.path.join(forecast_data_directory, str(year), '{:02d}'.format(month + 1)) + os.sep + '*')
    return forecast_data_filepaths, year, month

# TEMPORARY -- CHECKER

def get_next_element(lst, element):
    try:
        index = lst.index(element)  # Find the index of the given element
        return lst[index + 1]  # Return the next element
    except (ValueError, IndexError):
        return None  # Return None if the element is not found or it's the last element


def get_output_name(prediction_window_start, prediction_window_end, issue_time, extended=False):
    string = 'swpc_warning_' + prediction_window_start.replace(':', '') + 'Z' + '_' + prediction_window_end.replace(':', '') + 'Z' + '_' + issue_time.replace(':', '') + 'Z'
    if extended:
        string += '_extended'
    string += '.json'
    return string

def get_entry_year_month(entry):
    dt = datetime.datetime.strptime(entry['prediction_window_start'], '%Y-%m-%dT%H:%M:%SZ')
    year_str = str(dt.year)
    month_str = '{:02d}'.format(dt.month)
    return year_str, month_str

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Download SWPC warnings from SWPC FTP site; generate SWPC warning forecast JSONs.')
    parser.add_argument('yearmonth', nargs='?', default=current_yearmonth(), help='month in YYYY/MM format')
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()

    # Get forecasts for appropriate time range
    forecast_data_filepaths, year, month = get_forecast_data_files(args.yearmonth, args.all)

    # Constant list of JSON data for this type of forecast
    json_args = ['--model-short-name', 'SWPC Warning',
                 '--spase-id', '{TBD}',
                 '--mode', 'forecast',
                 '--energy-units', 'MeV',
                 '--all-clear-threshold-units' , 'pfu',
                 '--species', 'proton',
                 '--location', 'earth',
                 ]
    if get_next_element(json_args, 'spase_id') == '{TBD}':
        print('WARNING: SPASE ID is not set.')
    program_desc = 'Convert directory of files that contain SWPC SPE and ESPE warnings (archive_*.html) to CCMC JSON.'
    json_parser = sep_json_writer.InitParser(program_desc)
    
    forecasts_df = pd.DataFrame()
    for filepath in forecast_data_filepaths:
        forecasts_df_temp = construct_df_part(filepath)
        forecasts_df = pd.concat([forecasts_df, forecasts_df_temp])
        forecasts_df = forecasts_df.sort_values('Issue Time')
    forecasts_df = forecasts_df.drop_duplicates()
    if not args.all:
        condition = (forecasts_df['Valid From'].dt.year == year) & (forecasts_df['Valid From'].dt.month == month)
        forecasts_df = forecasts_df[condition]
    json_warning, json_extended_warning = get_json_parameters(forecasts_df)
    for entry in json_warning:
        year_str, month_str = get_entry_year_month(entry)
        output_dir = os.path.join(model_info.model_root['SWPC'], 'Warning', year_str, month_str)
        useargs = [*json_args,
                   '--output', os.path.join(output_dir, get_output_name(entry['prediction_window_start'], entry['prediction_window_end'], entry['issue_time'])),
                   '--issue-time', entry['issue_time'],
                   '--energy-min', entry['energy_low'],
                   '--energy-max', entry['energy_high'],
                   '--all-clear', False,
                   '--all-clear-threshold' , entry['threshold'],
                   '--prediction-window', entry['prediction_window_start'], entry['prediction_window_start'],
                   '--human-evaluation-last-data-time', entry['last_data_time']
                   ]
        (output_filename, output_dir, log_msgs, log_dir, log_starter, data_dict) = sep_json_writer.ParseArguments(json_parser, useargs)
        sep_json_writer.ConvertToJSON(data_dict, output_filename, output_dir, log_msgs, log_dir, log_starter)

    for entry in json_extended_warning: 
        year_str, month_str = get_entry_year_month(entry)
        output_dir = os.path.join(model_info.model_root['SWPC'], 'Warning', year_str, month_str)
        useargs = [*json_args,
                   '--output', os.path.join(output_dir, get_output_name(entry['prediction_window_start'], entry['prediction_window_end'], entry['issue_time'], extended=True)),
                   '--issue-time', entry['issue_time'],
                   '--energy-min', entry['energy_low'],
                   '--energy-max', entry['energy_high'],
                   '--all-clear-threshold' , entry['threshold'],
                   '--prediction-window', entry['prediction_window_start'], entry['prediction_window_start'],
                   '--human-evaluation-last-data-time', entry['last_data_time']
                   ]
        (output_filename, output_dir, log_msgs, log_dir, log_starter, data_dict) = sep_json_writer.ParseArguments(json_parser, useargs)
        sep_json_writer.ConvertToJSON(data_dict, output_filename, output_dir, log_msgs, log_dir, log_starter)

        # NOTE: OUTPUT DIR DOES NOTHING AS AN ARGUMENT TO sep_json_writer.ConvertToJSON(...)


