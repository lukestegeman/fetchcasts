#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#### PURPOSE # #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####
purpose = "Take in values and spit out a JSON (JavaScript Object Notation) object in the format needed for the CCMC SEP Scoreboard. Python 3 version."
#### END of PURPOSE #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####


#### PROLOG ## #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####
"""
program:	{0}
purpose:	{1}
author:		Joycelyn Thomson Jones
date:		2019.02.04

//=== File Prolog ============================================================
//
//	This code was developed by NASA, Goddard Space Flight Center, Code 580
//	for the Community Coordinated Modeling Center (CCMC) project.
//
//--- Notes ------------------------------------------------------------------
//  Development history follows this notice.
//
//--- Warning ----------------------------------------------------------------
//	This software is property of the National Aeronautics and Space
//	Administration. Unauthorized use or duplication of this software is
//	strictly prohibited. Authorized users are subject to the following
//	restrictions:
//	*	Neither the author, their corporation, nor NASA is responsible for
//		any consequence of the use of this software.
//	*	The origin of this software must not be misrepresented either by
//		explicit claim or by omission.
//	*	Altered versions of this software must be plainly marked as such.
//	*	This notice may not be removed or altered.
//
//=== End File Prolog ========================================================

modifications are listed at the end of the file.

""".format(__file__, purpose)
#### END of PROLOG ### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####


#### IMPORTS #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####


#### System Imports ####
import argparse
import collections
import datetime
import logging
import json
import os
import string
import sys
import traceback
#### end of IMPORTS #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####


#### FUNCTIONS #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####

def CheckAllClearThresholdVsEnergyChannel(acD, totalD):
    """ 
    Input:
        acD (dictionary) all clear data
        totalD (dictionary) the forecast's data
    Output: None.  Program exits if there is a conflict found in the values.
    Description:
        Compare the all clear threshold value against the energy channel minimum value.  
        If they don't match the expected value, explain it to the user and exit.

    """
    acthresh = acD['threshold']
    min_ = totalD['energy_channel']['min']
    max_ = totalD['energy_channel']['max']
    if max_ == -1 or max_ == '-1':
        #print('    > {0} {1}'.format(min_, totalD['energy_channel']['units']))
        if min_ in [10, "10"]:
            if acthresh not in [10, "10"]: # throw an error
                print('Energy Channel and All Clear Threshold do not match.  With a > 10 MeV energy channel, the all clear threshold should be 10 pfu.  Exiting.')
                sys.exit()
        elif min_ in [100, "100"]:
            if acthresh not in [1, "1"]: # throw an error
                print('Energy Channel and All Clear Threshold do not match.  With a > 100 MeV energy channel, the all clear threshold should be 1 pfu.  Exiting.')
                sys.exit()
    #else:
    #    #print('    {0} - {1} {2}'.format(min_, max_, totalD['energy_channel']['units']))
    #    # can't validate
    return
# end CheckAllClearThresholdVsEnergyChannel


def CheckForRequiredArgs(d, req_argsL=None, err_msg=None):
    """ 
    Input:
        d:         (dictionary) data 
        req_argsL: (list|None) a list of keys that are required to be in the data dictionary.
        err_msg:   (string|None) error message formatstring
    Output: None
    Description: Check the given (or default) list and see if we got all the required args.
        Check that the values for those required args are not None.

    """
    if req_argsL == None: # this means it is the top level required args.
        req_argsL = ['model_short_name', 'spase_id', 'issue_time', 'mode', 'energy_min', 'energy_max', 'energy_units', 'species', 'location', 'prediction_window']
    if err_msg == None:
        err_msg = 'Missing required arg: \'{}\''

    keyL = d.keys()
    for a in req_argsL:
        if a not in keyL: 
            ThrowArgError(err_msg.format(a.replace('_', '-')), d)
        DontAllowNoneValues(d[a], a.replace('_', '-'), d)
    return
# end CheckForRequiredArgs


def DontAllowNoneValues(v, field_name, d):
    """ 
    Input:
        v:          (ANY) the value, could be of any type
        field_name: (string) the field name for this value
        d:          (dictionary) the argument values given to this program.
    Output: None
    Description: Determines if the value is equal to or equivalent to None.  Throws an error if that is the case.

    """
    
    noneList = [None, 'None', 'none', ['none'], ['None'], [None]] # NOTE: 0 is not included because it is valid/needed in many fields
    if isinstance(v, list):
        #print('{} is a list? {}'.format(field_name, v))
        if v == []:
            msg = 'A \'None\' value was given for {}, but it isn\'t allowed.'.format(field_name)
            ThrowArgError(msg, d)
        else:
            for v_ in v: DontAllowNoneValues(v_, field_name, d)
    else:
        #print('{} is not a list {}'.format(field_name, v))
        if v in noneList:
            msg = 'A \'None\' value was given for {}, but it isn\'t allowed.'.format(field_name)
            ThrowArgError(msg, d)
    return
# end DontAllowNoneValues


def InitLogger(log_dir, log_file_starter, file_handler_level='warning'):
    """ 
    Input:
        log_dir:               (string) the directory the log file should be stored in
        log_file_starter:      (string) the beginning of the log file's name (the current timestamp will be added to it)
        file_handler_level:    (string) the minimum level of log messages you want to appear in the log file.  Default is 'warning'
    Output: a Python logging object
    Description:
        Initialize a Python logging object, per the user's specifications, and return it. Steps to do this include:
            Create current timestamp to make log name unique.
            Create custom logger.
            Set the desired logging level and logging format.
            Create the log directory, if needed, to store the log.
            Create the file log handler.

    """


    # Get current timestamp to put in log filename
    n = datetime.datetime.now()
    now_ts = '{}{:02d}{:02d}{:02d}{:02d}{:02d}'.format(n.year, n.month, n.day, n.hour, n.minute, n.second)

    # Create a custom logger
    custom_logger = f'{log_file_starter}.{now_ts}'
    logger = logging.getLogger(custom_logger)

    # Set the log message context format (i.e., what you want to see on each line of the log)
    #FORMAT = '%(asctime)s -%(name)s -%(levelname)s [%(funcName)s:L%(lineno)d] %(message)s'
    FORMAT = '%(asctime)s -%(levelname)s [%(funcName)s:L%(lineno)d] %(message)s'
    formatter = logging.Formatter(FORMAT)

    levels_in_order = ['debug', 'info', 'warning', 'error', 'critical']
    # set the log parent's (root) desired logging level
    # NOTE: whatever log level you set this to, this will affect what it written to stdout.
    # it will also limit the MINIMUM level that the handlers can be effectively set at
    levels = {'debug':logging.DEBUG, 'info':logging.INFO, 'warning':logging.WARNING, 'error':logging.ERROR, 'critical':logging.CRITICAL}
    # set the parent log level to be the sae as the file_handler_level.
    logging.basicConfig(level=levels[file_handler_level], format=FORMAT)

    # Validate or create log directory for file handler
    first_msg = ''
    if not os.path.exists(log_dir):
        try:
            # make the log directory (and all the necessary parent directories) 
            if major < 2:
                msg = 'sep_json_writer must be run with Python 2 or higher. Exiting.'
                print(msg)
                logger.critical(msg)
                sys.exit()
            elif major == 2:
                try:
                    os.makedirs(log_dir)
                except OSError:
                    if not os.path.isdir(log_dir):
                        raise
            else: # major == 3
                from pathlib import Path
                path = Path(log_dir)
                path.mkdir(parents=True, exist_ok=True)


            #first_msg = 'Just made new logs directory (\'{}\').'.format(log_dir)
        except Exception as e:
            first_msg = 'WARNING: can\'t make log directory. Using current directory. Error message is (\'{}\').'.format(e)
            log_dir= './'

    # Create file handler
    log_file = os.path.join(log_dir, f'{custom_logger}.log')
    fh = logging.FileHandler(log_file) # prints to log file
    #print(f'about to set the FileHandler level to {file_handler_level} or {levels[file_handler_level]}')
    fh.setLevel(levels[file_handler_level])
    #fh.setFormatter(logging.Formatter('%(asctime)s -%(name)s -%(levelname)s [%(funcName)s:L%(lineno)d] %(message)s'))
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger.propagate = False

    # If there was a problem with the initial log directory creation, go ahead and log it now
    if first_msg != '': logger.warning(first_msg)
    logger.info(f'Messages are being logged in {log_file}.')

    return (logger, fh)
# end InitLogger


def InitLoggerOld(log_dir, log_starter):
    """ 
    Input:
        log_dir:     (string) the directory the log should live in.
        log_starter: (string) the beginning of the log filename.
    Output: a python logging object.
    Description: Initialize logger for logging messages.

    """

    logger = logging.getLogger(__name__)
    first_msg = ''
    if not os.path.exists(log_dir): 
        try:   os.mkdir(log_dir)
        except:
            first_msg = 'WARNING: can\'t make logs directory. Using current directory.'
            print(first_msg)
            log_dir= './'
    n = datetime.datetime.utcnow()
    now_ts = '{}{:02d}{:02d}{:02d}{:02d}{:02d}'.format(n.year, n.month, n.day, n.hour, n.minute, n.second)
    log_file = os.path.join(log_dir, '{}.{}.log'.format(log_starter, now_ts))
    hdlr = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO) # replace INFO with DEBUG, WARNING, ERROR, or CRITICAL, as desired
    if first_msg != '': logger.warning(first_msg)
    return logger
# end InitLoggerOld


def InitParser(desc):
    """ 
    Input: desc: (string) a description of this program/script function.
    Output: argparse parser object
    Description: create the argparse parser object and then add arguments to it.

    """

    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawTextHelpFormatter)
    # Make output JSON filename an arg, otherwise give it a good default
    parser.add_argument("-o", "--output", dest="output_filename", help="JSON output filename.  Default is the <model_short_name>.<prediction_window_start_time>.<issue_time>.json")
    parser.add_argument("-d", "--output-dir", default='./', help="Full path to output directory. Default is current directory.")
    # Make logging an option
    parser.add_argument("-n", "--no-logging", dest="log_msgs", action='store_false', default=True, help="Turn off logging. It is turned on by default.")
    # Make log directory an option, otherwise make it the current directory
    parser.add_argument("-l", "--log-dir", default='./', help="Full path to log directory. Default is current directory.")
    # Make log filename an option, otherwise give it a good default
    parser.add_argument("-b", "--log-basename", dest="log_starter", default='isep_model_run', help="Beginning of the log filename (date and time will be added automatically).  Default is \'isep_model_run\'.")
    parser.add_argument('--import-data-dictionary', action='store_true', default=False, help='import the data dictionary (in the \'sep_forecast_submission_dataDict\' variable from a file named \'named input_sep.py\', OR use the --data-dictionary option to specify the full path to the file that holds the \'sep_forecast_submission_dataDict\' variable.')
    parser.add_argument('--data-dictionary', default=None, help='full path to the file holding the \'sep_forecast_submission_dataDict\'data dictionary. NOTE: this is ignored if --import-data-dictionary is not used.')

    parser.add_argument('--contact-name', nargs='*', action='append', help='DEPRECATED.  Do not use.')
    parser.add_argument('--contact-email', action='append', help='DEPRECATED.  Do not use.')
    parser.add_argument('--model-short-name', nargs='*', help='Short name (e.g. acronym) of model to appear on scoreboard. Consider including version number with acronym if distinction needed. 30 character limit.(Required)')
    parser.add_argument('--spase-id', help='Link to URL of full model description metadata in CCMC metadata registry in SPASE format (contact CCMC to register your model).(Required)')
    parser.add_argument('--issue-time', help='Forecast issue time (e.g. model run is complete and forecast is created)(Required)')
    parser.add_argument('--mode', default='forecast', help='Allowed values: forecast, historical, nowcast, simulated_realtime_forecast, simulated_realtime_nowcast.  Default is \'forecast\'. (Optional)')

    # optional Triggers/cme (>1 allowed)
    parser.add_argument('--cme-start-time', action='append', help='Provide if forecast is issued based on a CME trigger. Timestamp of 1st coronagraph image CME is visible in. (Optional)')
    parser.add_argument('--cme-liftoff-time', action='append', help='Timestamp of coronagraph image with 1st indication of CME liftoff (used by CACTUS). (Optional)')
    parser.add_argument('--cme-lat', action='append', help='CME latitude (deg). (Optional, but required with cme-lon)')
    parser.add_argument('--cme-lon', action='append', help='CME latitude (deg). (Optional, but required with cme-lat)')
    parser.add_argument('--cme-pa', action='append', help='CME plane-of-sky position angle (measured from solar north in degrees counter-clockwise ). (Optional)')
    parser.add_argument('--cme-half-width', action='append', help='CME half-width (deg). (Optional)')
    parser.add_argument('--cme-speed', action='append', help='CME speed (km/s). (Optional)')
    parser.add_argument('--cme-acceleration', action='append', help='CME acceleration (km/s^2). (Optional)')
    parser.add_argument('--cme-height', action='append', help='CME height at which the above parameters were derived (solar radii from Sun center). (Optional)')
    parser.add_argument('--cme-time-at-height-time', action='append', help='CME time at specificied height. (Optional, required with cme_time_at_height_height)')
    parser.add_argument('--cme-time-at-height-height', action='append', help='Specificied height in solar radii. (Optional, required with cme_time_at_height_time)')
    parser.add_argument('--cme-coordinates', action='append', help='Coordinate system for CME lat/lon parameters (e.g. HEEQ or Carrington) (Optional, but required with cme-lat or cme-lon)')
    parser.add_argument('--cme-catalog', action='append', help='Name of catalog where CME information was pulled from.  Allowed values: ARTEMIS, DONKI, HELCATS, JHU APL, CACTUS_NRL, CACTUS_SIDC, CORIMP, SEEDS, SOHO_CDAW, STEREO_COR1, SWPC (contact us to add a new catalog name) (Optional)')
    parser.add_argument('--cme-catalog-id', action='append', help='ID value for the catalog where CME information was pulled from. (Required if catalog value is DONKI, otherwise it is optional)')
    parser.add_argument('--cme-urls', nargs='*', action='append', help='List of urls where CME information can be found, or information was pulled from. (Optional, more than one is allowed)')

    # optional Triggers/flare (>1 allowed)
    parser.add_argument('--flare-last-data-time', action='append', help='Last time data timestamp that was used to create forecast (relevant for forecasts issued before flare end times) (Optional)')
    parser.add_argument('--flare-start-time', action='append', help='Flare start time (Optional)')
    parser.add_argument('--flare-peak-time', action='append', help='Flare peak time (Optional)')
    parser.add_argument('--flare-end-time', action='append', help='Flare end time (Optional)')
    parser.add_argument('--flare-location', action='append', help='Flare location in Stonyhurst coordinates (i.e., N00W00/S00E00 format). (Optional)')
    parser.add_argument('--flare-intensity', action='append', help='Flare intensity (W/m^2) (Optional)')
    parser.add_argument('--flare-integrated-intensity', action='append', help='Flare integrated intensity (J/m^2) (Optional)')
    parser.add_argument('--flare-noaa-region', action='append', help='Associated NOAA active region number (including the preceding 1) (Optional)')
    parser.add_argument('--flare-urls', nargs='*', action='append', help='List of urls where flare information can be found, or information was pulled from. (Optional, more than one is allowed)')

    # optional Triggers/cme_simulation (>1 allowed)
    parser.add_argument('--cme-sim-model', action='append', help='Model name (Optional)')
    parser.add_argument('--cme-sim-completion-time', action='append', help='Simulation completion time (Optional, required if cme-sim-model is used)')
    parser.add_argument('--cme-sim-urls', nargs='*', action='append', help='List of urls where simulation information can be found, or information was pulled from. (Optional, more than one is allowed)')

    # optional Triggers/particle_intensity (>1 allowed)
    parser.add_argument('--pi-observatory', action='append', help='Name of observatory/spacecraft data are from. (Optional)')
    parser.add_argument('--pi-instrument', action='append', help='Name of instrument data are from. (Optional, required if pi-observatory used)')
    parser.add_argument('--pi-last-data-time', action='append', help='Last time data timestamp used to create forecast. (Optional, required if pi-observatory used)')
    #parser.add_argument('--pi-ongoing-events', nargs='*', action='append', help='If an ongoing event triggers your forecast, list the properties you used') # start_time, threshold, energy_min, energy_max (all are required, if any)
    parser.add_argument('--pi-ongoing-events-start-time', nargs='*', action='append', help='If an ongoing event triggers your forecast, this is the start time. (Optional)')
    parser.add_argument('--pi-ongoing-events-threshold', nargs='*', action='append', help='If an ongoing event triggers your forecast, this is the threshold used to define the event in pfu. (Optional, required if pi-ongoing-events-start-time used)')
    parser.add_argument('--pi-ongoing-events-energy-min', nargs='*', action='append', help='If an ongoing event triggers your forecast, this is the min of energy channel range in MeV. (Optional, required if pi-ongoing-events-start-time used)')
    parser.add_argument('--pi-ongoing-events-energy-max', nargs='*', action='append', help='If an ongoing event triggers your forecast, this is the max of energy channel range in MeV. -1 represents an unbounded integral channel. (Optional, required if pi-ongoing-events-start-time used)')

    # optional Triggers/human_evaluation (>1 allowed)
    parser.add_argument('--human-evaluation-last-data-time', action='append', help='Last data time timestamp that was used to create forecast')

    # optional model inputs: magnetic_connectivity 
    parser.add_argument('--magcon-method', nargs='*', action='append', help='Provide if specific magnetic connectivity information was used to produce your forecast method string required, if magnetic_connectivity used. allowed values: Parker Spiral, PFSS-Parker Spiral, WSA, WSA-ENLIL, ADAPT-WSA-ENLIL (contact us to add your method to this format). (Optional, required if magnetic_connectivity was used)')
    parser.add_argument('--magcon-lat', nargs='*', action='append', help='Provide if specific magnetic connectivity information was used to produce your forecast method string required, if magnetic_connectivity used. Latitude (deg) position of magnetic field line footpoint linking the observing spacecraft to the Sun (in Stonyhurst coordinates).  (Optional)')
    parser.add_argument('--magcon-lon', nargs='*', action='append', help='Provide if specific magnetic connectivity information was used to produce your forecast method string required, if magnetic_connectivity used. Longitude (deg) position of magnetic field line footpoint linking the observing spacecraft to the Sun (in Stonyhurst coordinates).  (Optional, required, if magnetic_connectivity used)')
    parser.add_argument('--magcon-angle-great-circle', nargs='*', action='append', help='Provide if specific magnetic connectivity information was used to produce your forecast method string required, if magnetic_connectivity used. Angle (deg) between the related solar event and the foot point of the magnetic field line linking the observing spacecraft to the Sun. (Optional)')
    parser.add_argument('--magcon-angle-lat', nargs='*', action='append', help='Provide if specific magnetic connectivity information was used to produce your forecast method string required, if magnetic_connectivity used. Angle between the related solar event and the foot point of the magnetic field line linking the observing spacecraft to the Sun. connection angle lat = solar event lat - magnetic connectivity footpoint lat  (Optional)')
    parser.add_argument('--magcon-angle-lon', nargs='*', action='append', help='Provide if specific magnetic connectivity information was used to produce your forecast method string required, if magnetic_connectivity used. Angle between the related solar event and the foot point of the magnetic field line linking the observing spacecraft to the Sun. connection angle lon = solar event lon - magnetic connectivity footpoint lon (Optional, required, if connection_angle used).')
    parser.add_argument('--magcon-solar-wind-observatory', nargs='*', action='append', help='Provide if specific magnetic connectivity information was used to produce your forecast method string required, if magnetic_connectivity used. Use if a certain solar wind speed was assumed to compute the magnetic connectivity observatory string optional Name of observatory/spacecraft data are from(Optional, required, if solar_wind used )')
    parser.add_argument('--magcon-solar-wind-speed', nargs='*', action='append', help='Provide if specific magnetic connectivity information was used to produce your forecast method string required, if magnetic_connectivity used. Use if a certain solar wind speed was assumed to compute the magnetic connectivity. Assumed solar wind speed to compute magnetic connectivity.  (Optional, required, if solar_wind used)')

    # optional model inputs: magnetogram
    parser.add_argument('--magnetogram-observatory', nargs='*', action='append', help='Provide if a magnetogram was used to produce your forecast. Name of observatory/spacecraft data are from. (Optional, required if magnetogram was used.)')
    parser.add_argument('--magnetogram-instrument', nargs='*', action='append', help='Provide if a magnetogram was used to produce your forecast. Name of instrument data are from. (Optional, required if magnetogram was used.)')
    parser.add_argument('--magnetogram-product', nargs='*', action='append', help='Provide if a magnetogram was used to produce your forecast. Name of data product used. (Optional)')
    parser.add_argument('--magnetogram-product-last-data-time', nargs='*', action='append', help='Provide if a magnetogram was used to produce your forecast Last time data timestamp available at the time of forecast. (Optional, required if magnetogram was used.)')

    # required Forecast
    # required Forecast/energy_channel
    parser.add_argument('--energy-min', action='append', help='Min of energy channel range. (Required)')
    parser.add_argument('--energy-max', action='append', help='Max of energy channel range. -1 represented an unbounded integral channel. (Required)')
    parser.add_argument('--energy-units', action='append', help='Energy channel units (Required)')

    parser.add_argument('--species', action='append', help='Allowed values: electron, proton, helium, helium3, helium4, oxygen, iron, ion. (Required)')
    parser.add_argument('--location', action='append', help='Allowed values: mercury, venus, earth, mars, psp, stereoa, stereob, dawn, juno, L1, L2, L4, L5. (Required)')
    parser.add_argument('--prediction-window', nargs=2, action='append', help='Start time and end time (in that order) of the prediction window that is relevant to the given data.  Start of forecast prediction window must be within one hour of forecast issue time when in \'forecast\' mode. (Required)') # start_time, end_time (both are required)

    # optional Forecast/peak_intensity
    parser.add_argument('--peak-intensity', action='append', help='Forecast peak intensity value. (Optional)')
    parser.add_argument('--peak-intensity-units', action='append', help='Forecast peak intensity value units. (Optional, required if peak-intensity used)')
    parser.add_argument('--peak-intensity-uncertainty', action='append', help='Forecast peak intensity uncertainty value (same units as peak intensity). (Optional)')
    parser.add_argument('--peak-intensity-uncertainty-low', action='append', help='Forecast peak intensity lowest uncertainty value (same units as peak intensity). (Optional, required if peak-intensity-uncertainty-high used.  Ignored if peak-intensity-uncertainty used.)')
    parser.add_argument('--peak-intensity-uncertainty-high', action='append', help='Forecast peak intensity highest uncertainty value (same units as peak intensity). (Optional, required if peak-intensity-uncertainty-low used.  Ignored if peak-intensity-uncertainty used.)')
    parser.add_argument('--peak-intensity-time', action='append', help='Forecast time for reaching peak intensity value. (Optional)')

    # optional Forecast/peak_intensity_esp
    parser.add_argument('--peak-intensity-esp', action='append', help='Forecast peak intensity value in the vicinity of shock passage. (Optional)')
    parser.add_argument('--peak-intensity-esp-units', action='append', help='Forecast peak intensity units in the vicinity of shock passage. (Optional, required if peak-intensity-esp used)')
    parser.add_argument('--peak-intensity-esp-uncertainty', action='append', help='Forecast peak intensity in the vicinity of shock passage uncertainty value (same units as peak intensity). (Optional, cannot be used with either peak-intensity-esp-uncertainty-low or peak-intensity-esp-uncertainty-high)')
    parser.add_argument('--peak-intensity-esp-uncertainty-low', action='append', help='Forecast peak intensity in the vicinity of shock passage lowest uncertainty value (same units as peak intensity). (Optional, required if peak-intensity-esp-uncertainty-high used.  Cannot be used if peak-intensity-esp-uncertainty is used.)')
    parser.add_argument('--peak-intensity-esp-uncertainty-high', action='append', help='Forecast peak intensity in the vicinity of shock passage highest uncertainty value (same units as peak intensity). (Optional, required if peak-intensity-esp-uncertainty-low used.  Cannot be used if peak-intensity-esp-uncertainty is used.)')
    parser.add_argument('--peak-intensity-esp-time', action='append', help='Forecast time for reaching peak intensity value in the vicinity of shock passage. (Optional)')
    
    # optional Forecast/peak_intensity_max
    parser.add_argument('--peak-intensity-max', action='append', help='Forecast max peak intensity for the entire prediction window value. (Optional)')
    parser.add_argument('--peak-intensity-max-units', action='append', help='Forecast max peak intensity value units (Optional, required if peak-intensity-max used)')
    parser.add_argument('--peak-intensity-max-uncertainty', action='append', help='Forecast max peak intensity uncertainty value (same units as intensity) (for symmetric uncertainties). (Optional, cannot be used with either peak-intensity-max-uncertainty-low or peak-intensity-max-uncertainty-high)')
    parser.add_argument('--peak-intensity-max-uncertainty-low', action='append', help='Forecast max peak intensity low uncertainty value (same units as peak intensity). (Optional, required if peak-intensity-max-uncertainty-high used.  Cannot be used if peak-intensity-max-uncertainty is used.)')
    parser.add_argument('--peak-intensity-max-uncertainty-high', action='append', help='Forecast max peak intensity high uncertainty value (same units as peak intensity). (Optional, required if peak-intensity-max-uncertainty-low used.  Cannot be used if peak-intensity-max-uncertainty is used.)')
    parser.add_argument('--peak-intensity-max-time', action='append', help='Forecast time for reaching max peak intensity value. (Optional)')
    
    # optional Forecast/fluence
    parser.add_argument('--fluences', nargs='*', action='append', help='Forecast fluence value (corresponds to event length). (Optional)')
    parser.add_argument('--fluence-units', nargs='*', action='append', help='Forecast fluence units. (Optional, required if fluence used)')
    parser.add_argument('--fluence-uncertainty-low', nargs='*', action='append', help='Forecast fluence lowest uncertainty value (same units as fluence). (Optional, required if fluence-uncertainty-high used.)')
    parser.add_argument('--fluence-uncertainty-high', nargs='*', action='append', help='Forecast fluence highest uncertainty value (same units as fluence). (Optional, required if fluence-uncertainty-low used.)')
   
    # optional Forecast/event_length 
    parser.add_argument('--event-length-start-times', nargs='*', action='append', help='Event length must fall within prediction window. Forecast energetic particle event start time (\'onset\' time). (Optional)')
    parser.add_argument('--event-length-end-times', nargs='*', action='append', help='Forecast energetic particle event end time. (Optional)')
    parser.add_argument('--event-length-thresholds', nargs='*', action='append', help='Threshold used to extract start and end times. (Optional, required if event-length-start-time used)')
    parser.add_argument('--event-length-threshold-units', nargs='*', action='append', help='Units of threshold. (Optional, required if event-length-start-time used)')

    # optional Forecast/threshold_crossings (>1 allowed)
    parser.add_argument('--thresh-crossing-times', nargs='*', action='append', help='Multiple threshold_corssings can be provided for the same forecast energy channel.  Forecast threshold crossing time. (Optional, more than one is allowed)')
    parser.add_argument('--thresh-uncertainties', nargs='*', action='append', help='Forecast crossing time uncertainty in hours. (Optional, more than one is allowed)')
    parser.add_argument('--crossing-thresholds', nargs='*', action='append', help='Particle intensity threshold value crossing time refers to. (Optional, required if thresh-crossing-times used, more than one is allowed)')
    parser.add_argument('--crossing-threshold-units', nargs='*', action='append', help='Units of threshold. (Optional, required if thresh-crossing-times used, more than one is allowed)')

    # optional Forecast/probabilities (>1 allowed)
    parser.add_argument('--probabilities', nargs='*', action='append', help='Multiple probabilities can be provided for the same forecast energy channel. forecast probability value (range 0 to 1). (Optional, more than one is allowed)')
    parser.add_argument('--prob-uncertainties', nargs='*', action='append', help='Plus/minus error bar for probabilty_value (in probability_value units). (Optional, more than one is allowed)')
    parser.add_argument('--prob-thresholds', nargs='*', action='append', help='Particle intensity threshold value probability forecast refers to. (Optional, required if probabilities is used, more than one is allowed)')
    parser.add_argument('--prob-threshold-units', nargs='*', action='append', help='Units of threshold. (Optional, required if probabilities is used, more than one is allowed)')

    # optional Forecast/all_clear 
    parser.add_argument('--all-clear', action='append', help="""There are three situations for setting all_clear_boolean=false:
(1) for >10MeV energy channel, your forecast of peak intensity OR threshold crossing exceeds 10 pfu OR your probabilty forecast for a threshold of 10 pfu exceeds your custom probability_threshold;
(2) for the >100MeV energy channel, your forecast of peak intensity OR threshold crossing exceeds 1 pfu OR your probabilty forecast for a threshold of 1 pfu exceeds your custom probability_threshold;
(3) for your custom (non-integral) energy channel, your forecast peak intensity OR threshold crossing exceeds your custom threshold.
Custom cases (3) are being stored but will not be used in the all-clear scoreboard display.
    (Optional)""")
    parser.add_argument('--all-clear-threshold', action='append', help='Particle intensity threshold value all_clear_boolean refers to. Can be 10 pfu for >10MeV channel, 1 pfu for >100MeV channel, or a custom threshold value. (Optional, required if all-clear is used)')
    parser.add_argument('--all-clear-threshold-units', action='append', help='Units of threshold. (Optional, required if all-clear is used)')
    parser.add_argument('--all-clear-probability-threshold', action='append', help='Probability threshold value all_clear_boolean refers to. Must specify this threshold if setting all_clear_boolean based on probability forecast. (Optional)')

    parser.add_argument('--sep-profile', action='append', help='Text file with 2 columns: datetime string and predicted SEP intensity for this energy channel. (Optional)')
    parser.add_argument('--native-id', action='append', help='Specify only if forecast has a native id from your model run. (Optional)')

    return parser
# end InitParser


def OrganizeIntensityData(intensity_field_name, got_argL, d, i):
    """ 
    Input:
        intensity_field_name: (string) the name of the Intensity field.  One of {peak_intensity|peak_intensity_esp|peak_intensity_max}
        got_argL: (list) a list of all the arguments that were submitted to this program
        d: (dictionary) a dictionary holding all the reformatted data that will eventually be written out to the JSON file.
        i: (integer) the index number for this field's list of arguments to look at
    Output: a dictionary of data to be added to the output JSON file
    Description:
        Ensure that all required field values were received.
        Ensure that invalid values were not received.
        Reformat the data into a dictionary that will be used when writing out the JSON file.
     
    """
    ifn = intensity_field_name
    
    if '{}_units'.format(ifn) not in got_argL:
        msg = 'Got peak_intensity, but did not get required {}_units.'.format(ifn)
        ThrowArgError(msg, d) 
    else: DontAllowNoneValues(d['{}_units'.format(ifn)][i], '{}_units'.format(ifn), d)
    t2D = collections.OrderedDict() # temp dictionary
    t2D = {'intensity':d[ifn][i], 'units': d['{}_units'.format(ifn)][i]}
    for ifn_ in ['uncertainty', 'uncertainty_low', 'uncertainty_high', 'time']: # optional
        key = '{}_{}'.format(ifn, ifn_)
        if key in got_argL and d[key][i] not in noneList:
            # if key is 'peak_intensity[X]_uncertainty_low', make sure there's a corresponding 'peak_intensity[X]_uncertainty_high' value (and vice versa).
            if d[key][i] not in noneList:
                if ifn_ == 'uncertainty_low' or ifn_ == 'uncertainty_high':
                    if ifn_ == 'uncertainty_low':  ifn_opposite = 'uncertainty_high'
                    if ifn_ == 'uncertainty_high': ifn_opposite = 'uncertainty_low'
                    try:
                        key_opposite = '{}_{}'.format(ifn, ifn_opposite)
                        print('key_opposite is {0}'.format(key_opposite))
                        print('d[key_opposite] is {0}'.format(d[key_opposite]))
                        if d['{}_{}'.format(ifn, ifn_opposite)] != None:
                            if d['{}_{}'.format(ifn, ifn_opposite)][i] in noneList:
                                msg = 'Got invalid \'None\' {0}_{1} value.  If you give a {0}_{2} value, you must have a non-None {0}_{1} value.'.format(ifn, ifn_opposite, ifn_)
                                ThrowArgError(msg, d)
                    except:
                        value_ = d['{0}_{1}'.format(ifn, ifn_opposite)][i]
                        msg = 'Got invalid {0}_{1} value ({3}).  If you give a {0}_{2} value, you must have a non-None {0}_{1} value.'.format(ifn, ifn_opposite, ifn_, value_)
                        ThrowArgError(msg, d)
                t2D[ifn_] = d[key][i]

    return t2D
# end OrganizeIntensityData


def ParseArguments(parser, useargs=None):
    """ 
    Input: parser (argparse parser object)
    Output: a tuple holding: (args.output_filename, args.output_dir, args.log_msgs, args.log_dir, args.log_starter, dataDict)
    Description: Build the data dictionary based on the arguments the user included on the command line. 
    Warnings: This does NOT run if importing the input_sep dictionary!

    """

    #print('====Starting to parse arguments.===========================================')
    args = parser.parse_args(args=useargs)
    if args.import_data_dictionary:
        if args.data_dictionary != None:
            print('Loading the data you supplied.')
            #print(args.data_dictionary)
            import importlib.util
            spec = importlib.util.spec_from_file_location("sep_forecast_submission_dataDict", args.data_dictionary)
            foo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(foo)
            #print(foo.sep_forecast_submission_dataDict)
            return (args.output_filename, args.output_dir, args.log_msgs, args.log_dir, args.log_starter, foo.sep_forecast_submission_dataDict)
        else:
            try:
                from input_sep import sep_forecast_submission_dataDict
                return (args.output_filename, args.output_dir, args.log_msgs, args.log_dir, args.log_starter, sep_forecast_submission_dataDict)
            except ImportError:
                print("""
###################################################################################
#!!!! Error while trying to import the sep_forecast_submission_dataDict !!!!      #
#                                                                                 #
# You MUST name the dictionary variable sep_forecast_submission_dataDict.         #
# You can save it to a file named input_sep.py OR to any file you wish, just use  #
# the --data-dictionary arg and give it the full path to the file holding the     #
# sep_forecast_submission_dataDict.                                               #
# Make sure the user can read the input_sep.py file.                              #
# input_sep.py MUST be in the same directory as this (sep_json_writer.py) script. #
#                                                                                 #
# Then run the ./sep_json_writer.py with the --import-data-dictionary option.     #
# you can use these options as well                                               #
#    --output <desired beginning of output file name>                             #
#    --output-dir <full path to where you want the output file to be saved>       #
#    --no-logging                                                                 #
#    --log-basename <desired beginning of log file name>                          #
#    --log-dir <full path to where you want log file(s) to be saved>              #
###################################################################################
                """)
                sys.exit()
    d = vars(args)
    argsL = ['model_short_name', 'spase_id', 'issue_time', 'mode', 'cme_start_time', 'cme_liftoff_time', 'cme_lat', 'cme_lon', 'cme_pa', 'cme_half_width', 'cme_speed', 'cme_acceleration', 'cme_height', 'cme_time_at_height_time', 'cme_time_at_height_height', 'cme_coordinates', 'cme_catalog', 'cme_catalog_id', 'cme_urls', 'flare_last_data_time', 'flare_start_time', 'flare_peak_time', 'flare_end_time', 'flare_location', 'flare_intensity', 'flare_integrated_intensity', 'flare_noaa_region', 'flare_urls', 'cme_sim_model', 'cme_sim_completion_time', 'cme_sim_urls', 'pi_observatory', 'pi_instrument', 'pi_last_data_time', 'pi_ongoing_events_start_time', 'pi_ongoing_events_threshold', 'pi_ongoing_events_energy_min', 'pi_ongoing_events_energy_max', 'human_evaluation_last_data_time', 'magcon_method', 'magcon_lat', 'magcon_lon', 'magcon_angle_great_circle', 'magcon_angle_lat', 'magcon_angle_lon', 'magcon_solar_wind_observatory', 'magcon_solar_wind_speed', 'magnetogram_observatory', 'magnetogram_instrument', 'magnetogram_product', 'magnetogram_product_last_data_time', 'energy_min', 'energy_max', 'energy_units', 'species', 'location', 'prediction_window', 'peak_intensity', 'peak_intensity', 'peak_intensity_units', 'peak_intensity_uncertainty', 'peak_intensity_uncertainty_low', 'peak_intensity_uncertainty_high', 'peak_intensity_time', 'peak_intensity_esp', 'peak_intensity_esp_units', 'peak_intensity_esp_uncertainty', 'peak_intensity_esp_uncertainty_low', 'peak_intensity_esp_uncertainty_high', 'peak_intensity_esp_time', 'peak_intensity_max', 'peak_intensity_max_units', 'peak_intensity_max_uncertainty', 'peak_intensity_max_uncertainty_low', 'peak_intensity_max_uncertainty_high', 'peak_intensity_max_time', 'fluences', 'fluence_units', 'fluence_uncertainty_low', 'fluence_uncertainty_high', 'event_length_start_times', 'event_length_end_times', 'event_length_thresholds', 'event_length_threshold_units', 'thresh_crossing_times', 'thresh_uncertainties', 'crossing_thresholds', 'crossing_threshold_units', 'probabilities', 'prob_uncertainties', 'prob_thresholds', 'prob_threshold_units', 'all_clear', 'all_clear_threshold', 'all_clear_threshold_units', 'all_clear_probability_threshold', 'sep_profile', 'native_id']
    noneList = [None, 'None', 'none', ['none'], ['None'], [None]] # NOTE: 0 is not included because it is valid/needed in many fields
    dataDict = collections.OrderedDict()
    checkedL = []
    CheckForRequiredArgs(d) # if this returns, we have the required arg values
    #print d

    for a in argsL:
        if d[a] not in noneList:
            # look at each value and determine how to handle it.
            #print('working on {}.'.format(d[a]))
            if a == 'model_short_name':
                DontAllowNoneValues(d['model_short_name'], 'model-short-name', d)
                DontAllowNoneValues(d['spase_id'], 'spase-id', d)
                msn = ' '.join(d[a]) # concatenating model short name values, if needed
                msn = msn.strip()
                dataDict['model'] = {'short_name':msn, 'spase_id':d['spase_id']}
            elif a in ['issue_time', 'mode']:
                DontAllowNoneValues(d[a], a.replace('_', '-'), d)
                dataDict[a] = d[a]
            elif a == 'cme_start_time' and a in d.keys(): # this is not a required arg
                # there can be more than one cme set.
                # each arg defined with nargs and append is a list of lists
                co = len('cme_') # chop_off (how much of the arg name to chop off to convert it to a key in dataDict
                got_argL = []
                for aa in ('cme_start_time', 'cme_liftoff_time', 'cme_lat', 'cme_lon', 'cme_pa', 'cme_half_width', 'cme_speed', 'cme_acceleration', 'cme_height', 'cme_time_at_height_time', 'cme_time_at_height_height', 'cme_coordinates', 'cme_catalog', 'cme_catalog_id', 'cme_urls', ):
                    if aa in d.keys() and d[aa] not in noneList: got_argL.append(aa)
                # handle 'required' args, which there aren't many, except coordinates if lat or lon are given.
                # if lat is given, so must be lon (and vice versa)
                if 'cme_lat' in got_argL and d['cme_lat'] not in noneList:
                    CheckForRequiredArgs(d, ['cme_coordinates'], 'Missing \'cme-coordinates\', which is required if you give a \'cme-lat\' value.')
                    CheckForRequiredArgs(d, ['cme_lon'], 'Missing \'cme-lon\', which is required if you give a \'cme-lat\' value.')
                elif 'cme_lon' in got_argL and d['cme_lon'] not in noneList:
                    CheckForRequiredArgs(d, ['cme_coordinates'], 'Missing \'cme-coordinates\', which is required if you give a \'cme-lon\' value.')
                    CheckForRequiredArgs(d, ['cme_lat'], 'Missing \'cme-lat\', which is required if you give a \'cme-lon\' value.')
                # build the dictionary to go into the triggers list.
                list_length = len(d['cme_start_time'])
                #print('initial length of cme_start_time arg is {}'.format(list_length))
                for aa in got_argL:
                    if d[aa] not in noneList and len(d[aa]) != list_length:
                        ThrowArgError('mismatch on the number of values given for \'cme_start_time\' and \'{}\''.format(aa), d)
                for i in range(0, len(d['cme_start_time'])):
                    tD = collections.OrderedDict() # temp dictionary
                    for aa in got_argL:
                        if aa in ['cme_time_at_height_time', 'cme_time_at_height_height']:
                            # if you get cme_time_at_height_time, cme_time_at_height_height is required and vice versa.
                            if aa == 'cme_time_at_height_time': # we only want to do this once
                                if 'cme_time_at_height_height' not in got_argL: 
                                    msg = 'missing \'cme_time_at_height_height\' arg.  Required because you used \'cme_time_at_height_time\' arg.'
                                    ThrowArgError(msg, d)
                                if d[aa][i] not in noneList and d['cme_time_at_height_height'][i] not in noneList:
                                    tD['time_at_height'] = {'time':d[aa][i], 'height':d['cme_time_at_height_height'][i]}
                            elif aa == 'cme_time_at_height_height':
                                # Both args should have been given. Thus, 'cme_time_at_height_height' should have already been processed when
                                # 'cme_time_at_height_time' came up.  So when you get here, all you need to do is verify if 'cme_time_at_height_time'
                                # was included and throw an error if it is missing.
                                if 'cme_time_at_height_time' not in got_argL: 
                                    msg = 'missing \'cme_time_at_height_time\' arg.  Required because you used \'cme_time_at_height_height\' arg.'
                                    ThrowArgError(msg, d)
                        elif d[aa][i] not in noneList:
                            tD[aa[co:]] = d[aa][i]
                    if 'triggers' in dataDict.keys():
                        dataDict['triggers'].append({'cme':tD})
                    else: dataDict['triggers'] = [{'cme':tD}]
            elif a == 'flare_last_data_time' and a in d.keys(): # this is not a required arg
                # there can be more than one cme set.
                # each arg defined with nargs and append is a list of lists
                co = len('flare_') # chop_off (how much of the arg name to chop off to convert it to a key in dataDict
                got_argL = []
                for aa in ('flare_last_data_time', 'flare_start_time', 'flare_peak_time', 'flare_end_time', 'flare_location', 'flare_intensity', 'flare_integrated_intensity', 'flare_noaa_region', 'flare_urls'):
                    if aa in d.keys() and d[aa] not in noneList: got_argL.append(aa)
                # handle 'required' args, which is 'flare_last_data_time'
                for aa in ['flare_last_data_time']:
                    DontAllowNoneValues(d[aa], aa, d)
                list_length = len(d['flare_last_data_time'])
                #print('initial length of flare_last_data_time arg is {}'.format(list_length))
                for aa in got_argL:
                    if d[aa] not in noneList and len(d[aa]) != list_length:
                        ThrowArgError('mismatch on the number of values given for \'flare_last_data_time\' and \'{}\''.format(aa), d)
                for i in range(0, len(d['flare_last_data_time'])):
                    tD = collections.OrderedDict() # temp dictionary
                    for aa in got_argL:
                        if d[aa][i] not in noneList:
                            tD[aa[co:]] = d[aa][i]
                    if 'triggers' in dataDict.keys():
                        dataDict['triggers'].append({'flare':tD})
                    else: dataDict['triggers'] = [{'flare':tD}]
            elif a == 'cme_sim_model' and a in d.keys(): # this is not a required arg
                # there can be more than one cme set.
                # each arg defined with nargs and append is a list of lists
                co = len('cme_sim_') # chop_off (how much of the arg name to chop off to convert it to a key in dataDict
                got_argL = []
                for aa in ('cme_sim_model', 'cme_sim_completion_time', 'cme_sim_urls'):
                    if aa in d.keys() and d[aa] not in noneList: got_argL.append(aa)
                list_length = len(d['cme_sim_model'])
                #print('initial length of cme_sim_model arg is {}'.format(list_length))
                for aa in got_argL:
                    if d[aa] not in noneList and len(d[aa]) != list_length:
                        ThrowArgError('mismatch on the number of values given for \'cme_sim_model\' and \'{}\''.format(aa), d)
                for i in range(0, len(d['cme_sim_model'])):
                    tD = collections.OrderedDict() # temp dictionary
                    for aa in got_argL:
                        if aa == 'cme_sim_completion_time':
                            if d[aa][i] not in noneList:
                                tD['simulation_completion_time'] = d[aa][i]
                        elif d[aa][i] not in noneList:
                            tD[aa[co:]] = d[aa][i]
                    if 'triggers' in dataDict.keys():
                        dataDict['triggers'].append({'cme_simulation':tD})
                    else: dataDict['triggers'] = [{'cme_simulation':tD}]
            elif a == 'pi_observatory' and a in d.keys() and d[a] not in noneList: # this is not a required arg
                # there can be more than one particle_intensity set.
                # each arg defined with nargs and append is a list of lists
                got_argL = ['pi_observatory']
                possible_fieldsL = ['pi_instrument', 'pi_last_data_time', 
                    'pi_ongoing_events_start_time', 'pi_ongoing_events_threshold', 'pi_ongoing_events_energy_min', 'pi_ongoing_events_energy_max']
                for aa in possible_fieldsL:
                    if aa in d.keys() and d[aa] not in noneList: got_argL.append(aa)
                # handle 'required' (if you got here) args, which are 'pi_instrument', 'pi_last_data_time'
                req_argsL = ['pi_observatory', 'pi_instrument', 'pi_last_data_time']
                err_msg = 'Missing \'{}\', which is required if you give a \'pi-observatory\' value.'
                CheckForRequiredArgs(d, req_argsL, err_msg)
                list_length = len(d['pi_observatory'])
                for aa in got_argL:
                    if d[aa] not in noneList and len(d[aa]) != list_length:
                        ThrowArgError('mismatch on the number of values given for \'pi_observatory\' and \'{}\''.format(aa), d)
                for i in range(0, len(d['pi_observatory'])):
                    co = len('pi_') # chop_off (how much of the arg name to chop off to convert it to a key in dataDict
                    tD = collections.OrderedDict() # temp dictionary
                    for aa in got_argL:
                        if aa == 'pi_ongoing_events_start_time' and d[aa][i] not in noneList: # more than one is allowed
                            # make sure that you have all four values because all are required, if any are given
                            inner_req_argsL = ['pi_ongoing_events_threshold', 'pi_ongoing_events_energy_min', 'pi_ongoing_events_energy_max']
                            for ra in inner_req_argsL:
                                if ra not in got_argL:
                                    msg = 'Got pi-ongoing-events-start-time, but did not get required {}.'.format(ra)
                                    ThrowArgError(msg, d)
                                else: DontAllowNoneValues(d[ra][i], ra, d) # checks for an empty list if var is of type list, o/w None or 'None'
                            co2 = len('pi_ongoing_events_')
                            t2L = []
                            for j in range(0, len(d['pi_ongoing_events_start_time'][i])):
                                t2D = collections.OrderedDict()
                                for f in ['pi_ongoing_events_start_time'] + inner_req_argsL:
                                    if f in d.keys() and d[f][i][j] not in noneList:
                                        t2D[f[co2:]] = d[f][i][j]
                                    else: # throw error
                                        msg = 'Got pi-ongoing-events-start-time, but did not get required {}.'.format(f)
                                        ThrowArgError(msg, d)
                                t2L.append(t2D)
                            tD['ongoing_events'] = t2L
                        elif aa in req_argsL: 
                            if d[aa][i] not in noneList:
                                tD[aa[co:]] = d[aa][i] # this makes it so that we don't get duplicate ongoing_events values
                    if 'triggers' in dataDict.keys():
                        dataDict['triggers'].append({'particle_intensity':tD})
                    else: dataDict['triggers'] = [{'particle_intensity':tD}]
            elif a == 'human_evaluation_last_data_time' and a in d.keys(): # this is not a required arg 
                # there can be more than one cme set.
                # each arg defined with nargs and append is a list of lists
                co = len('human_evaluation_') # chop_off (how much of the arg name to chop off to convert it to a key in dataDict
                got_argL = []
                for aa in ('human_evaluation_last_data_time'):
                    if aa in d.keys() and d[aa] not in noneList: got_argL.append(aa)
                # handle 'required' args, which is 'human_evaluation_last_data_time'
                for aa in ['human_evaluation_last_data_time']:
                    DontAllowNoneValues(d[aa], aa, d)
                list_length = len(d['human_evaluation_last_data_time'])
                #print('initial length of human_evaluation_last_data_time arg is {}'.format(list_length))
                for aa in got_argL:
                    if d[aa] not in noneList and len(d[aa]) != list_length:
                        ThrowArgError('mismatch on the number of values given for \'human_evaluation_last_data_time\' and \'{}\''.format(aa), d)
                for i in range(0, len(d['human_evaluation_last_data_time'])):
                    tD = collections.OrderedDict() # temp dictionary
                    for aa in got_argL:
                        if d[aa][i] not in noneList:
                            tD[aa[co:]] = d[aa][i]
                    if 'triggers' in dataDict.keys():
                        dataDict['triggers'].append({'human_evaluation':tD})
                    else: dataDict['triggers'] = [{'human_evaluation':tD}]
            elif a == 'magcon_method': # it's optional # here is the start of a magnetic connection model input 
                # there can be more than one magnetic_connectivity set.
                # each arg is a list of lists
                got_argL = ['magcon_method']
                possible_fieldsL = [ 'magcon_lat', 'magcon_lon', 'magcon_angle_great_circle', 'magcon_angle_lat', 'magcon_angle_lon', 'magcon_solar_wind_observatory', 'magcon_solar_wind_speed',]
                for aa in possible_fieldsL:
                    if aa in d.keys() and d[aa] not in noneList: got_argL.append(aa)
                # check for all required args: 'magcon_lon'
                req_argsL = ['magcon_lon']
                err_msg = 'Missing \'{}\', which is required if you give a \'magcon_method\' value.'
                CheckForRequiredArgs(d, req_argsL, err_msg)
                list_length = len(d['magcon_method'])
                # make sure each received magcon fields have the same number of values as 'magcon_method'
                for aa in got_argL:
                    if d[aa] not in noneList and len(d[aa]) != list_length:
                        ThrowArgError('mismatch on the number of values given for \'magcon_method\' and \'{}\''.format(aa), d)      
                # if either _angle_great_circle or _angle_lat is given, then there must also be an _angle_lon value.
                if ('magcon_angle_great_circle' in got_argL or 'magcon_angle_lat' in got_argL) and ('magcon_angle_lon' not in got_argL):
                    msg = 'There must be a magcon_angle_lon value for every magcon_angle_lat or magcon_angle_great_circle value given.'
                    ThrowArgError(msg, d)
                # if _solar_wind_observatory is given, then there must also be a _solar_wind_speed value.
                if 'magcon_solar_wind_observatory' in got_argL and 'magcon_solar_wind_speed' not in got_argL:
                    msg = 'There must be a magcon_solar_wind_speed value for every magcon_solar_wind_observatory value given.'
                    ThrowArgError(msg, d)

                # now that we know we have the same number of values for each field, convert this to a list of dictionaries
                lod = list()
                print("[magcon:L514] len(d['magcon_method']): {0} d['magcon_method']: {1}".format(len(d['magcon_method']), d['magcon_method']))
                for i in range(0, len(d['magcon_method'])):
                    co = len('magcon_') # chop_off (how much of the arg name to chop off to convert it to a key in dataDict
    
                    # prep dictionary for all magnetic_connectivity data
                    tD = collections.OrderedDict() # temp dictionary
                    for aa in ['magcon_method', 'magcon_lat', 'magcon_lon']:
                        if aa in got_argL: 
                            if d[aa][i] not in noneList:
                                if type(d[aa][i]) == type(list()) and len(d[aa][i]) == 1:
                                    tD[aa[co:]] = d[aa][i][0]
                                else: tD[aa[co:]] = d[aa][i]
                    print("[magcon:L526] tD is now {0}".format(tD))

                    # prep connection_angle subdict
                    if 'magcon_angle_lon' in got_argL:
                        subdict = dict()
                        co = len('magcon_angle_') # chop_off (how much of the arg name to chop off to convert it to a key in dataDict
                        for aa in ['magcon_angle_great_circle', 'magcon_angle_lat', 'magcon_angle_lon']:
                            if d[aa][i] not in noneList:
                                if type(d[aa][i]) == type(list()) and len(d[aa][i]) == 1:
                                    subdict[aa[co:]] = d[aa][i][0]
                                else: subdict[aa[co:]] = d[aa][i]
                        tD['connection_angle'] = subdict
                    print("[magcon:L538] tD is now {0}".format(tD))

                    # prep solar_wind subdict
                    if 'magcon_solar_wind_speed' in got_argL:
                        subdict = dict()
                        co = len('magcon_solar_wind_') # chop_off (how much of the arg name to chop off to convert it to a key in dataDict
                        for aa in ['magcon_solar_wind_observatory', 'magcon_solar_wind_speed']:
                            if d[aa][i] not in noneList:
                                if type(d[aa][i]) == type(list()) and len(d[aa][i]) == 1:
                                    subdict[aa[co:]] = d[aa][i][0]
                                else: subdict[aa[co:]] = d[aa][i]
                        tD['solar_wind'] = subdict
                    print("[magcon:L550] tD is now {0}".format(tD))
                    print("tD['method'] {}".format(tD['method']))
                    print("tD['lat'] {}".format(tD['lat']))
                    print("tD['lon'] {}".format(tD['lon']))
                    print("tD['connection_angle'] {}".format(tD['connection_angle']))
                    print("tD['solar_wind'] {}".format(tD['solar_wind']))
                    
                    # save this dictionary to the list of dictionaries for magnetic_connectivity
                    lod.append(tD)

                # save the magnetic_connectivity list of dictionaries to the model inputs' list of dictionaries
                try: dataDict['inputs'].append({'magnetic_connectivity':lod})
                except KeyError: dataDict['inputs'] = [{'magnetic_connectivity':lod}]
            elif a == 'magnetogram_observatory': # it's optional # here is the start of a magnetogram model input 

                # there can be more than one magnetic_connectivity set.
                # each arg is a list of lists
                got_argL = ['magnetogram_observatory']
                possible_fieldsL = [ 'magnetogram_instrument', 'magnetogram_product', 'magnetogram_product_last_data_time', ]
                for aa in possible_fieldsL:
                    if aa in d.keys() and d[aa] not in noneList: got_argL.append(aa)
                # check for all required args: 'magnetogram_instrument'
                req_argsL = ['magnetogram_instrument']
                err_msg = 'Missing \'{}\', which is required if you give a \'magnetogram_observatory\' value.'
                CheckForRequiredArgs(d, req_argsL, err_msg)
                list_length = len(d['magnetogram_observatory'])
                # make sure each received magnetogram fields have the same number of values as 'magnetogram_observatory'
                for aa in got_argL:
                    if d[aa] not in noneList and len(d[aa]) != list_length:
                        ThrowArgError('mismatch on the number of values given for \'magnetogram_observatory\' and \'{}\''.format(aa), d)      
                # if _product is given, then there must also be a _product_last_data_time value.
                if ('magnetogram_product' in got_argL) and ('magnetogram_product_last_data_time' not in got_argL):
                    msg = 'There must be a magnetogram_product_last_data_time value for every magnetogram_product value given.'
                    ThrowArgError(msg, d)
                # now that we know we have the same number of values for each field, convert this to a list of dictionaries
                lod = list()
                for i in range(0, len(d['magnetogram_observatory'])):
                    co = len('magnetogram_') # chop_off (how much of the arg name to chop off to convert it to a key in dataDict
    
                    # prep dictionary for all magnetic_connectivity data
                    tD = collections.OrderedDict() # temp dictionary
                    for aa in ['magnetogram_observatory', 'magnetogram_instrument']:
                        if aa in got_argL: 
                            if type(d[aa][i]) == type(list()) and len(d[aa][i]) == 1:
                                tD[aa[co:]] = d[aa][i][0]
                            else: tD[aa[co:]] = d[aa][i]

                    # prep products subdict
                    if 'magnetogram_product_last_data_time' in got_argL:
                        sublod = list()
                        for j in range(0, len(d['magnetogram_product_last_data_time'][i])):
                            subdict = dict()
                            for (db_fieldname, argname) in [('product', 'magnetogram_product'), ('last_data_time', 'magnetogram_product_last_data_time')]:
                                if d[argname][i][j] not in noneList:
                                    subdict[db_fieldname] = d[argname][i][j]
                            if subdict != {}: sublod.append(subdict)
                        tD['products'] = sublod

                    # save this dictionary to the list of dictionaries for magnetogram
                    lod.append(tD)

                # save the magnetogram list of dictionaries to the model inputs' list of dictionaries
                try: dataDict['inputs'].append({'magnetogram':lod})
                except KeyError: dataDict['inputs'] = [{'magnetogram':lod}]
            elif a == 'energy_min': # it's required  # Here's the start of the forecast
                forecastLOD = [] # temp list to hold all the forecasts
                #print('Got to forecasts/energy_min.')
                fluencesT = ('fluences', 'fluence_units', 'fluence_uncertainty_low', 'fluence_uncertainty_high')
                event_lengthsT = ('event_length_start_times', 'event_length_end_times', 'event_length_thresholds', 'event_length_threshold_units', )
                threshold_crossingsT = ('thresh_crossing_times', 'thresh_uncertainties', 'crossing_thresholds', 'crossing_threshold_units', )
                probabilitiesT = ('probabilities', 'prob_uncertainties', 'prob_thresholds', 'prob_threshold_units', )
                fT = ('energy_min', 'energy_max', 'energy_units', 'species', 'location', 'prediction_window', 'peak_intensity', 'peak_intensity', 'peak_intensity_units', 'peak_intensity_uncertainty', 'peak_intensity_uncertainty_low', 'peak_intensity_uncertainty_high', 'peak_intensity_time', 'peak_intensity_esp', 'peak_intensity_esp_units', 'peak_intensity_esp_uncertainty', 'peak_intensity_esp_uncertainty_low', 'peak_intensity_esp_uncertainty_high', 'peak_intensity_esp_time', 'peak_intensity_max', 'peak_intensity_max_units', 'peak_intensity_max_uncertainty', 'peak_intensity_max_uncertainty_low', 'peak_intensity_max_uncertainty_high', 'peak_intensity_max_time', fluencesT, event_lengthsT, threshold_crossingsT, probabilitiesT, 'all_clear', 'all_clear_threshold', 'all_clear_threshold_units', 'all_clear_probability_threshold', 'sep_profile', 'native_id')
                req_argsT = ('energy_min', 'energy_max', 'energy_units', 'species', 'location', 'prediction_window')
                CheckForRequiredArgs(d, req_argsT)
                got_argL = []
                for aa in fT:
                    if aa in [fluencesT, event_lengthsT, threshold_crossingsT, probabilitiesT]: # you've got the threshold crossing tuple or probabilties tuple
                        for aaa in aa: 
                            if aaa in d.keys() and d[aaa] not in noneList: 
                                got_argL.append(aaa)
                    else:
                        if aa in d.keys() and d[aa] not in noneList: 
                            got_argL.append(aa)
                #print('Got these args: {}'.format(got_argL))
                list_length = len(d['energy_min'])
                #print('initial length of energy_min arg is {}'.format(list_length))
                for aa in got_argL:
                    if d[aa] not in noneList and len(d[aa]) != list_length:
                        ThrowArgError('mismatch on the number of values given for \'energy_min\' and \'{}\''.format(aa), d)
                for i in range(0, len(d['energy_min'])):
                    tD = collections.OrderedDict() # temp dictionary
                    for aa in got_argL:
                        if aa == 'energy_min': # required, as are energy_max and energy_units
                            t2D = collections.OrderedDict()
                            for k in ['energy_min', 'energy_max', 'energy_units']:
                                if d[k][i] in noneList: # throw error
                                    msg = 'Got invalid {} value of {} and it is a required value.'.format(k, d[k][i])
                                    ThrowArgError(msg, d)
                            t2D['min'] = d['energy_min'][i]
                            t2D['max'] = d['energy_max'][i]
                            t2D['units'] = d['energy_units'][i]
                            tD['energy_channel'] = t2D
                        elif aa in ['species', 'location']: # required
                            tD[aa] = d[aa][i]
                        elif aa == 'prediction_window': # required
                            try:
                                tD['prediction_window'] = {'start_time':d['prediction_window'][i][0], 'end_time': d['prediction_window'][i][1]}
                            except:
                                msg = 'Didn\'t get enough values in prediction_window.  There should be two values: start_time and then end_time.'
                                ThrowArgError(msg, d) 
                        elif aa == 'peak_intensity' and d['peak_intensity'][i] not in noneList: # optional
                            tD['peak_intensity'] = OrganizeIntensityData(aa, got_argL, d, i)
                        elif aa == 'peak_intensity_esp' and d['peak_intensity_esp'][i] not in noneList: # optional
                            tD['peak_intensity_esp'] = OrganizeIntensityData(aa, got_argL, d, i)
                        elif aa == 'peak_intensity_max' and d['peak_intensity_max'][i] not in noneList: # optional
                            tD['peak_intensity_max'] = OrganizeIntensityData(aa, got_argL, d, i)
                    
                        elif aa == 'fluences' and d['fluences'][i] not in noneList: # optional
                            # going to get a list of lists for these args because they are nargs=* and append 
                            if 'fluence_units' not in got_argL: # required if 'fluence' is given
                                msg = 'Got fluence, but did not get required fluence_units.'
                                ThrowArgError(msg, d) 
                            DontAllowNoneValues(d['fluences'][i], 'fluences', d)
                            DontAllowNoneValues(d['fluence_units'][i], 'fluence_units', d)
                            # check that we have the same number of fluences and fluence_units values
                            if len(d['fluences'][i]) != len(d['fluence_units'][i]):
                                msg = 'Did not get the same number of fluences and fluence_units values.  For every fluences values, you must have a corresponding fluence_units value.'
                                ThrowArgError(msg, d)
                            # make sure that either both (fluences and fluence_units) values are None, or that both values are not None.  
                            for j in range(0, len(d['fluences'][i])):
                                fluence = d['fluences'][i][j]
                                fluence_units = d['fluence_units'][i][j]
                                if fluence == None and fluence_units == None: pass # this is allowed
                                elif fluence != None and fluence_units != None: pass # this is desired
                                else:
                                    if fluence == None:
                                        msg = 'Got invalid \'None\' fluences value.  You must have either both a fluences and fluence_units value or neither.'
                                        ThrowArgError(msg, d)
                                    elif fluence_units == None:
                                        msg = 'Got invalid \'None\' fluence_units value.  You must have either both a fluences and fluence_units value or neither.'
                                        ThrowArgError(msg, d)
                            # IF uncertainty_low and uncertainty_high are used, then there must be one for every set of fluence and fluence_unit values.
                            num_of_unc_low = num_of_unc_high = 0
                            unc_low = unc_high = None
                            if 'fluence_uncertainty_low' in d.keys() and d['fluence_uncertainty_low'] != None: # not a required arg
                                num_of_unc_low = len(d['fluence_uncertainty_low'][i])
                            if 'fluence_uncertainty_high' in d.keys() and d['fluence_uncertainty_high'] != None: # not a required arg
                                num_of_unc_high = len(d['fluence_uncertainty_high'][i])
                            # but if one uncertainty value is given, the other must be given
                            if num_of_unc_low != num_of_unc_high:
                                msg = 'The number of fluence uncertainty_low and uncertainty_high values must match.'
                                ThrowArgError(msg, d)
                            # the number of uncertainty values match, 
                            elif num_of_unc_low > 0:
                                # if there are uncertainty values, make sure they match the number of fluence values
                                print("d['fluences']: {0}".format(d['fluences']))
                                print("d['fluence_uncertainty_low']: {0}".format(d['fluence_uncertainty_low']))
                                print("d['fluence_uncertainty_high']: {0}".format(d['fluence_uncertainty_high']))
                                if num_of_unc_low != len(d['fluences'][i]):
                                    msg = 'In order for fluence uncertainty_low and uncertainty_high values to be used, there must be one for every fluences given.  I was given {0} fluence uncertainty_low values, {1} fluence uncertainty_high values and {2} fluences values.'.format(num_of_unc_low, num_of_unc_high, len(d['fluences'][i]))
                                    ThrowArgError(msg, d)
                                # make sure both the uncertainty_low and uncertainty_high values are either None or not None.
                                for j in range(0, len(d['fluence_uncertainty_low'][i])):
                                    low = d['fluence_uncertainty_low'][i][j]
                                    high = d['fluence_uncertainty_high'][i][j]
                                    if low == None and high == None: pass # this is allowed
                                    elif low != None and high != None: pass # this is allowed
                                    else:
                                        if low == None:
                                            msg = 'Got invalid \'None\' fluence_uncertainty_low value.  You must have both a fluence_uncertainty_low and fluence_uncertainty_high value or neither.'
                                        elif high == None:
                                            msg = 'Got invalid \'None\' fluence_uncertainty_high value.  You must have both a fluence_uncertainty_low and fluence_uncertainty_high value or neither.'
                                        ThrowArgError(msg, d)

                            translate_arg2keyD = {
                                'fluences': 'fluence',
                                'fluence_units': 'units',
                                'fluence_uncertainty_low': 'uncertainty_low',
                                'fluence_uncertainty_high': 'uncertainty_high',
                            }
                            t2L = []
                            for j in range(0, len(d['fluences'][i])):
                                t2D = collections.OrderedDict() # temp dictionary
                                updated_dict = False
                                for f in ['fluences', 'fluence_units', 'fluence_uncertainty_low', 'fluence_uncertainty_high']:
                                    if f in got_argL and d[f] != []:
                                        try: 
                                            if d[f][i][j] not in noneList:
                                                t2D[translate_arg2keyD[f]] = d[f][i][j]
                                                updated_dict = True
                                        except:
                                            print('[L568] some error with {}.  Exiting.'.format(f))
                                            sys.exit()
                                if updated_dict: t2L.append(t2D)
                            if t2L != []: tD['fluences'] = t2L

                        elif aa == 'event_length_start_times' and d['event_length_start_times'][i] not in noneList: # optional
                            # going to get a list of lists for these args because they are nargs=* and append 
                            # checking for 'required' (if event_length given) args
                            rL = ['event_length_thresholds', 'event_length_threshold_units']
                            for ra in rL:
                                if ra not in got_argL:
                                    msg = 'Got event_length_start_times, but did not get required {}.'.format(ra)
                                    ThrowArgError(msg, d)
                                else: DontAllowNoneValues(d[ra][i], ra, d)
                            translate_arg2keyD = {
                                'event_length_start_times': 'start_time',
                                'event_length_end_times': 'end_time',
                                'event_length_thresholds': 'threshold', 
                                'event_length_threshold_units': 'threshold_units',
                            }

                            for k in ['event_length_start_times', 'event_length_thresholds', 'event_length_threshold_units']:
                                if d[k][i] in noneList: # throw error
                                    msg = 'Got invalid {} value of {} and it is a required value.'.format(k, d[k][i])
                                    ThrowArgError(msg, d)
                                else:
                                    for j in range(0, len(d['event_length_start_times'][i])):
                                        if d[k][i][j] in noneList: # throw error
                                            msg = 'Got invalid {} value of {} and it is a required value.'.format(k, d[k][i][j])
                                            ThrowArgError(msg, d)
                            
                            t2L = []
                            for j in range(0, len(d['event_length_start_times'][i])):
                                t2D = collections.OrderedDict() # temp dictionary
                                updated_dict = False
                                for f in ['event_length_start_times', 'event_length_end_times', 'event_length_thresholds', 'event_length_threshold_units', ]:
                                    if f in got_argL and d[f] != []:
                                        try: 
                                            if d[f][i][j] not in noneList:
                                                t2D[translate_arg2keyD[f]] = d[f][i][j]
                                                updated_dict = True
                                        except:
                                            print('[L568] some error with {}.  Exiting.'.format(f))
                                            sys.exit()
                                if updated_dict: t2L.append(t2D)
                            if t2L != []: tD['event_lengths'] = t2L

                        elif aa == 'thresh_crossing_times' and d['thresh_crossing_times'][i] not in noneList: # optional
                            # going to get a list of lists for these args because they are nargs=* and append 
                            req_argsL = ['crossing_thresholds', 'crossing_threshold_units']
                            for ra in req_argsL:
                                if ra not in got_argL:
                                    msg = 'Got thresh_crossing_times, but did not get required {}.'.format(ra)
                                    ThrowArgError(msg, d)
                                else: DontAllowNoneValues(d[ra][i], ra, d)
                            translate_arg2keyD = {
                                'thresh_crossing_times':'crossing_time',
                                'thresh_uncertainties':'uncertainty',
                                'crossing_thresholds':'threshold',
                                'crossing_threshold_units':'threshold_units',
                            }
                            t2L = []
                            for j in range(0, len(d['thresh_crossing_times'][i])):
                                t2D = collections.OrderedDict()
                                updated_dict = False
                                for f in ['thresh_crossing_times', 'thresh_uncertainties', 'crossing_thresholds', 'crossing_threshold_units']:
                                    if f in got_argL and d[f] != []:
                                        try: 
                                            #print('[L525] in {} d[f] is {}'.format(f, d[f]))
                                            #print('[L526] in {} d[f][i] is {}'.format(f, d[f][i]))
                                            #print('[L527] in {} d[f][i][j] is {}'.format(f, d[f][i][j]))
                                            if d[f][i][j] not in noneList:
                                                t2D[translate_arg2keyD[f]] = d[f][i][j]
                                                updated_dict = True
                                        except:
                                            print('[L608] some error with {}.  Exiting.'.format(f))
                                            sys.exit()
                                if updated_dict: t2L.append(t2D)
                            if t2L != []: tD['threshold_crossings'] = t2L
                        elif aa == 'probabilities' and d['probabilities'][i] not in noneList: # going to get a list of lists for these because they are nargs=* and append 
                            req_argsL = ['prob_thresholds', 'prob_threshold_units']
                            for ra in req_argsL:
                                #print('{}: {} testing for NULL synonyms.'.format(ra, d[ra][i]))
                                if ra not in got_argL:
                                    msg = 'Got probabilities, but did not get required {}.'.format(ra)
                                    ThrowArgError(msg, d)
                                else: DontAllowNoneValues(d[ra][i], ra, d) # checks for an empty list if var is of type list, o/w None or 'None'
                            translate_arg2keyD = {
                                'probabilities': 'probability_value',
                                'prob_uncertainties': 'uncertainty',
                                'prob_thresholds': 'threshold',
                                'prob_threshold_units': 'threshold_units',
                            }
                            t2L = []
                            for j in range(0, len(d['probabilities'][i])):
                                t2D = collections.OrderedDict()
                                for f in ['probabilities', 'prob_uncertainties', 'prob_thresholds', 'prob_threshold_units']:
                                    #print('**** **** **** **** **** **** **** **** **** **** **** **** **** **** ')
                                    #print(f)
                                    #print(f in d.keys())
                                    #print(d.keys())
                                    #print(d[f][i][j] not in noneList)
                                    if f == 'prob_uncertainties':  # 'prob_uncertainties' is optional.
                                        try:
                                            if f in d.keys() and d[f][i][j] not in noneList: 
                                                t2D[translate_arg2keyD[f]] = d[f][i][j]
                                        except: pass
                                    else:  # The rest are required (if probabiltities given)
                                        try:
                                            if f in d.keys() and d[f][i][j] not in noneList: 
                                                t2D[translate_arg2keyD[f]] = d[f][i][j]
                                        except: 
                                            # throw error
                                            msg = 'Got probabilties, but did not get required {}.'.format(f)
                                            ThrowArgError(msg, d)
                                t2L.append(t2D)
                            tD['probabilities'] = t2L
                        elif aa == 'all_clear' and d['all_clear'][i] not in noneList:
                            # checking for 'required' (if event_length given) args
                            rL = ['all_clear_threshold', 'all_clear_threshold_units']
                            for ra in rL:
                                #print('is {} in got_argL? {}'.format(ra, ra in got_argL))
                                if ra not in got_argL:
                                    msg = 'Got all_clear, but did not get required {}.'.format(ra)
                                    ThrowArgError(msg, d)
                            co = len('all_clear_')
                            t2D = collections.OrderedDict() # temp dictionary
                            for j in ['all_clear', 'all_clear_threshold', 'all_clear_threshold_units', 'all_clear_probability_threshold']:
                                if j in got_argL:
                                    if j == 'all_clear': 
                                        k = 'all_clear_boolean'
                                        v = d[j][i]
                                        if v in ['True', 'true', True]: v = True
                                        elif v in ['False', 'false', False]: v = False
                                        else: 
                                            msg = 'Invalid \'all_clear\' value given. It need to be \'True\' or \'False\'.' 
                                            ThrowArgError(msg, d)
                                        t2D[k] = v
                                    else: 
                                        k = j[co:]
                                        if d[j][i] not in noneList:
                                            t2D[k] = d[j][i]
                            CheckAllClearThresholdVsEnergyChannel(t2D, tD)
                            tD['all_clear'] = t2D
                        elif aa in ['sep_profile', 'native_id']:
                            if aa in d.keys() and d[aa][i] not in noneList: # optional
                                tD[aa] = d[aa][i]
                    #print('forcast tD going into LOD: {}'.format(tD))
                    forecastLOD.append(tD)
                dataDict['forecasts'] = forecastLOD
    #print('====Finished parsing arguments.===========================================')
    #print(dataDict)
    #print('====Finished parsing arguments.===========================================')
    return (args.output_filename, args.output_dir, args.log_msgs, args.log_dir, args.log_starter, dataDict)
# end ParseArguments
    
    
def ThrowArgError(msg, d):
    """ 
    Input:
        msg: (string) the message to be presented as an error message.
        d:   (dictionary) data for initializing the log file.
    Output: None
    Description: print the message.  if indicated, initialize logger object then log the message also.

    """

    print(msg)
    # if logging is desired, log the message
    if d['log_msgs']: 
        # initialize logger object (from parameters)
        logger = InitLogger(d['log_dir'], d['log_starter'], 'debug')
        # log the message.  It if is being called from here, it's an error message.
        logger.error(msg)
    sys.exit()
# end ThrowArgError


#### END of FUNCTIONS ## #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####


#### CLASSES # #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####
class ConvertToJSON:
    def __init__(self, dataD, output_filename, output_dir, log_msgs, log_dir, log_starter):
        """ 
        Input:
            self:            (ConvertToJSON object)
            dataD:           (dictionary) the data to write to the JSON-formatted output file
            output_filename: (string) output filename to be written
            output_dir:      (string) directory where the output file should be put
            log_msgs:        (boolean) whether or not to log the messages.
            log_dir:         (string) the directory the log should live in.
            log_starter:     (string) the beginning of the log filename.
        Output: (automatically returned) ConvertToJSON object
        Description: Convert the data to the JSON format and write the JSON file out.
    
        """

        self.dataDict = dataD
        self.forecast_or_historical_mode = 'forecast' # default data mode
        self.orderedDict = collections.OrderedDict()
        self.noneList = [None, 'None', '0', 0]
        self.now = n = datetime.datetime.utcnow() # datetime obj # used for log basename
        self.now_ts = '{}{:02d}{:02d}{:02d}{:02d}{:02d}'.format(n.year, n.month, n.day, n.hour, n.minute, n.second) # string created from datetime obj

        if output_filename in self.noneList:
            # prep model short_name to be used in default output_filename value
            msn = self.dataDict['model']['short_name']
            for (a, b) in [(' ', '_'), ('-', '_')]:
                msn = msn.replace(a, b)
            # prep issue_time to be used in default output_filename value
            t = self.dataDict['issue_time']
            
            # get the prediction_window_start_time
            pw_start_ = self.GetFirstPredictionWindowStartTime()

            self.output_filename = '{0}.{1}.{2}.json'.format(msn, pw_start_, t)
            self.output_filename = self.output_filename.replace(':', '')
        else:
            # make sure output filename has a lowercase .json extension
            if output_filename[-5:] == '.JSON':
                self.output_filename = output_filename.replace('.JSON', '.json')
            elif output_filename[-5:] == '.json':
                self.output_filename = output_filename
            else:
                print('The output filename must have a .json extension.  Adding it.')
                self.output_filename = f'{output_filename}.json'
            if ':' in self.output_filename:
                self.output_filename = self.output_filename.replace(':', '')
                print('WARNING!  A colon \':\' was found in the JSON output filename.  It has been removed because multiple operating systems do not handle that correctly.')
        self.output_dir = output_dir
        self.log_msgs = log_msgs
        self.log_dir = log_dir
        self.log_starter = log_starter

        self.WriteJSON()

        # Make sure run was successful.  So make sure self.output_filename exists and that the file is not empty
        # make sure file exists
        if os.path.exists(self.output_filename):
            # make sure filesize is != 0
            if os.stat(self.output_filename).st_size != 0:
                # give success message.
                print('Success!  Here is our definition of success: the output JSON file exists and is not empty.')
        return
    # end __init__ from ConvertToJSON class


    def ConvertDTString2DTO(self, dts):
        """ 
        Input:
            self: (ConvertToJSON object)
            dts:  (string) date time stamp
        Output: datetime object 
        Description: Convert incoming string in 'YYYY-MM-DDTHH:MMZ' format to a DateTime Object.
            This assumes that the DateTimeString validation step has already been run. 

        """

        try:
            y = int(dts[0:4])
            m = int(dts[5:7])
            d = int(dts[8:10])
            h = int(dts[11:13])
            n = int(dts[14:16]) # n --> thinking m for minute, but it's already used so bumped it to 'n'
        except: 
            logging.critical(f'\tError Type: {sys.exc_info()[0]}\n\tError Details: {sys.exc_info()[1]}\n\t{traceback.print_tb(sys.exc_info()[2])}')
            logging.critical(f'Converting the date/time string to a datetime object failed. The date/time string is {dts}')
            sys.exit()
        

        return datetime.datetime(y, m, d, h, n, 0)
    # end ConvertDTString2DTO


    def GetFirstPredictionWindowStartTime(self):
        """ 
        Input: self: (ConvertToJSON object)
        Output: (string) the earliest prediction_window.start_time from the list of forecasts.
        Description: go through all the forecasts and find the earliest prediction_window start time. 

        """

        t = self.dataDict['issue_time']
        L = list()
        for f in self.dataDict['forecasts']:
            L.append( f['prediction_window']['start_time'] )
        L.sort()
        if len(L) > 0:
            return L[0]
        return None
    # end GetFirstPredictionWindowStartTime


    def IJWError(self, m, log=False, exit=False):
        """ 
        Input:
            self: (ConvertToJSON object)
            m:    (string) the message to be logged.
            log:  (boolean) whether or not to log 
            exit: (boolean) whether or not to exit the program
        Output: None
        Description: Log the message in an appropriate manner and exit, if requested.
        Notes: IJW = ISEP JSON Writer

        """

        print("{0}: {1}".format(os.path.basename(__file__), m))
        if log and exit:
            logging.critical("{0}: {1}".format(os.path.basename(__file__), m))
            logging.critical("{0}: Exiting.".format(os.path.basename(__file__)))
            sys.exit()
        elif log:
            logging.error("{0}: {1}".format(os.path.basename(__file__), m))
        elif exit:
            logging.critical("{0}: Exiting".format(os.path.basename(__file__)))
            sys.exit()

        return
    # end IJWError
       
 
    def IJWWarning(self, m, log=False): 
        """ 
        Input:
            self: (ConvertToJSON object)
            m:    (string) the message to be logged.
            log:  (boolean) whether or not to log 
        Output: None
        Description: Print the message. Log the message, if requested.
        Notes: IJW = ISEP JSON Writer
    
        """

        # in the style of argparse.error output
        print("{0}: {1}".format(os.path.basename(__file__), m))
        if log: logging.warning("{0}: {1}".format(os.path.basename(__file__), m))

        return
    # end IJWWarning

	
    def __del__(self):
        """ 
        Input: self: (ConvertToJSON object)
        Output: None
        Description: It's supposed to delete the object, but it is actually doing nothing.
    
        """
        pass #self.cx.close()
    # end __del__


    def InitLogger(self):
        """ 
        Input: self: (ConvertToJSON object)
        Output: Python logging object
        Description: Initialize logger for logging messages.

        """

        logger = logging.getLogger(__name__)
        # need to add a temp aspect to this...
        n = datetime.datetime.utcnow()
        if os.path.exists(self.log_dir): pass
        else:  
                try:   os.mkdir(self.log_dir)
                except:
                        print('ERROR: can\'t make logs directory. Using current directory.')
                        self.log_dir= './'
        log_file = os.path.join(self.log_dir, '{}.{}.log'.format(self.log_starter, self.now_ts))
        hdlr = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(logging.INFO) # replace INFO with DEBUG, WARNING, ERROR, or CRITICAL, as desired

        return logger
    # end InitLogger

    
    def PrepForecastAllClear(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prep the Forecast's all_clear data for the ordered dictionary, from which the JSON is written.
    
        """

        stub_found = False
        pfn = 'forecasts/all_clear' # parent field name
        toD = collections.OrderedDict()
        L = [
            ('all_clear_boolean', False, True, None, None, None, True),
            ('threshold', 0, True, False, False, None, False),
            ('threshold_units', 'pfu', True, None, None, None, True), 
            ('probability_threshold', 0, False, False, False, None, True),
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    if k == 'all_clear_boolean':
                        self.ValidateBoolean(value, '{}/{}'.format(pfn, k))
                    elif s == 0:
                        # 'threshold' Can be 10 pfu, 1 pfu, or custom 
                        value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), neg_allowed=allow_neg, neg_one_allowed=allow_neg_one)
                    elif k == 'threshold_units':
                        self.ValidateAlphaNumeric(value, '{}/{}'.format(pfn, k), allow_addtl_chars=' -_+*^()/')
                    toD[k] = value
        return toD
    # end PrepForecastAllClear


    def PrepForecastEnergyChannel(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prep the Forecast's energy_channel data for the ordered dictionary, from which the JSON is written.
    
        """

        stub_found = False
        pfn = 'forecasts/energy_channel' # parent field name
        toD = collections.OrderedDict()
        L = [
            ('min', 0, True, False, False, None, False), # is allow_stub_value correct?
            ('max', 0, True, False, True, None, False), # is allow_stub_value correct?
            ('units', 'pfu', True, None, None, None, True), 
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    if k in ['min', 'max']:
                        value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), neg_allowed=allow_neg, neg_one_allowed=allow_neg_one)
                    elif k == 'units':
                        self.ValidateAlphaNumeric(value, '{}/{}'.format(pfn, k), allow_addtl_chars=' -_+*^()/')
                    toD[k] = value
        return toD
    # end PrepForecastEnergyChannel


    def PrepForecastEventLengths(self, lod, prediction_window_d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prep the Forecast's event_lengths data for the ordered dictionary, from which the JSON is written.
    
        """
        
        stub_found = False
        pfn = 'forecasts/event_lengths' # parent field name
        toD = collections.OrderedDict()
        L = [
            ('start_time', 'YYYY-MM-DDTHH:MMZ', True, None, None, False, False), 
            ('end_time', 'YYYY-MM-DDTHH:MMZ', False, None, None, False, False), 
            ('threshold', 0, True, False, False, None, False),
            ('threshold_units', 'pfu', True, None, None, None, True), 
        ]

        #for d in lod:
        #    print(d)
        #    print(type(d))
        #    print(d.keys())
        #    print('exiting prematurely from PrepForecastEventLength. --Joycelyn')
        #    sys.exit()
        newL = []
        for d in lod:
            toD = collections.OrderedDict()
            for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
                if self.VerifyKeyInDict(k, d, required=r):
                    value = d[k]
                    if not allow_stub_value:
                        stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                    if allow_stub_value or not stub_found:
                        if s == 'YYYY-MM-DDTHH:MMZ':
                            self.ValidateDateTimeStamp(value, '{}/{}'.format(pfn, k), ensure_in_past=must_be_in_past)
                        elif k  == 'threshold':
                            value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), neg_allowed=allow_neg, neg_one_allowed=allow_neg_one)
                        elif k == 'threshold_units':
                            self.ValidateAlphaNumeric(value, '{}/{}'.format(pfn, k), allow_addtl_chars=' -_+*^()/')
                        toD[k] = value
            s = d['start_time']
            e = None
            if 'end_time' in d.keys():
                e = d['end_time']
            self.ValidateForecastEventLength(s, e, prediction_window_d)
            newL.append(toD)
        return newL
    # end PrepForecastEventLengths


    def PrepForecastFluences(self, lod):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prep the Forecast's fluence data for the ordered dictionary, from which the JSON is written.
    
        """
        
        stub_found = False
        pfn = 'forecasts/fluences' # parent field name
        toD = collections.OrderedDict()
        L = [
            ('fluence', '0', True, False, False, None, True),
            ('units', 'pfu', True, None, None, None, True), 
            ('uncertainty_low', 0, False, False, False, None, True),
            ('uncertainty_high', 0, False, False, False, None, True),
        ]
        newL = []
        for d in lod:
            toD = collections.OrderedDict()
            for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
                if self.VerifyKeyInDict(k, d, required=r):
                    value = d[k]
                    if not allow_stub_value:
                        stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                    if allow_stub_value or not stub_found:
                        if k == 'units':
                            self.ValidateAlphaNumeric(value, '{}/{}'.format(pfn, k), allow_addtl_chars=' -_+*^()/')
                        else:
                            value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), neg_allowed=allow_neg, neg_one_allowed=allow_neg_one)
                        toD[k] = value
            newL.append(toD)
        return newL
    # end PrepForecastFluences


    def PrepForecastPeakIntensity(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Define the string parent field name and call PrepForecastPeakIntensityOrEspOrMax
    
        """
    
        pfn = 'forecasts/peak_intensity' # parent field name
        return self.PrepForecastPeakIntensityOrEspOrMax(d, pfn)
    # end PrepForecastPeakIntensity


    def PrepForecastPeakIntensityEsp(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Define the string parent field name and call PrepForecastPeakIntensityOrEspOrMax
    
        """
    
        pfn = 'forecasts/peak_intensity_esp' # parent field name
        return self.PrepForecastPeakIntensityOrEspOrMax(d, pfn)
    # end PrepForecastPeakIntensityEsp


    def PrepForecastPeakIntensityMax(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Define the string parent field name and call PrepForecastPeakIntensityOrEspOrMax
    
        """

        pfn = 'forecasts/peak_intensity_max' # parent field name
        return self.PrepForecastPeakIntensityOrEspOrMax(d, pfn)
    # end PrepForecastPeakIntensityMax


    def PrepForecastPeakIntensityOrEspOrMax(self, d, pfn):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
            pfn:  (string) parent field name, used for error messages
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Verify and Validate the values given
        Notes:  peak_intensity, peak_intensity_esp, and peak_intensity_max are supposed to have the exact same fields.

        """
        
        stub_found = False
        toD = collections.OrderedDict()
        L = [
            ('intensity', '0', True, False, False, None, False),
            ('units', 'pfu', True, None, None, None, True), 
            ('uncertainty', 0, False, False, False, None, True),
            ('uncertainty_low', 0, False, False, False, None, True),
            ('uncertainty_high', 0, False, False, False, None, True),
            ('time', 'YYYY-MM-DDTHH:MMZ', False, None, None, False, False),
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    if k in ['intensity', 'uncertainty', 'uncertainty_low', 'uncertainty_high']:
                        value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), neg_allowed=allow_neg, neg_one_allowed=allow_neg_one)
                    elif k == 'units':
                        self.ValidateAlphaNumeric(value, '{}/{}'.format(pfn, k), allow_addtl_chars=' -_+*^()/')
                    elif k == 'time':
                        self.ValidateDateTimeStamp(value, '{}/{}'.format(pfn, k), ensure_in_past=must_be_in_past)
                    toD[k] = value


        # make sure that if there is an 'uncertainty' value that there is not an 'uncertainty_low' or 'uncertainty_high' value
        if 'uncertainty' in d.keys():
            self.VerifyExclusive('uncertainty', 'uncertainty_low', d)
            self.VerifyExclusive('uncertainty', 'uncertainty_high', d)


        # if there is an 'uncertainty_low' value, there also needs to be an 'uncertainty_high' value (and vice versa).
        if 'uncertainty_low' in d.keys(): self.VerifyKeyInDict('uncertainty_high', d, required=True)
        if 'uncertainty_high' in d.keys(): self.VerifyKeyInDict('uncertainty_low', d, required=True)

        return toD
    # end PrepForecastPeakIntensityOrEspOrMax


    def PrepForecastPredictionWindow(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: prepare the forecast's prediction window data 
    
        """

        stub_found = False
        pfn = 'forecasts/prediction_window' # parent field name
        toD = collections.OrderedDict()
        L = [
            ('start_time', 'YYYY-MM-DDTHH:MMZ', True, None, None, False, False),
            ('end_time', 'YYYY-MM-DDTHH:MMZ', True, None, None, False, False),
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    self.ValidateDateTimeStamp(value, '{}/{}'.format(pfn, k), ensure_in_past=must_be_in_past)
                    #if k == 'start_time':
                    #    pass # TODO start of forecast prediction window (must be within one hour of forecast issue time for "forecast" mode)
                    toD[k] = value

        return toD
    # end PrepForecastPredictionWindow


    def PrepForecastProbabilities(self, lod):
        """ 
        Input:
            self: (ConvertToJSON object)
            lod:  (a list of dictionaries) data
        Output: a list of ordered dictionaries of data to be written to the JSON file
        Description: prepare the forecast's probabilities (a list of probability values)
    
        """
        
        stub_found = False
        pfn = 'forecasts/probabilities' # parent field name
        L = [
            ('probability_value', 0, True, False, False, None, False),
            ('uncertainty', 0, False, False, False, None, True),
            ('threshold', 0, True, False, False, None, False),
            ('threshold_units', 'pfu', True, None, None, None, True), 
        ]
        newL = []
        for d in lod:
            toD = collections.OrderedDict()
            for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
                if self.VerifyKeyInDict(k, d, required=r):
                    value = d[k]
                    if not allow_stub_value:
                        stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                    if allow_stub_value or not stub_found:
                        if s == 0:
                            value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), neg_allowed=allow_neg, neg_one_allowed=allow_neg_one)
                            if k == 'probability_value': self.ValidateForecastProbabilityValue(value)
                        elif k == 'units':
                            self.ValidateAlphaNumeric(value, '{}/{}'.format(pfn, k), allow_addtl_chars=' -_+*^()/')
                        toD[k] = value
            newL.append(toD)

        return newL
    # end PrepForecastProbabilities


    def PrepForecastThresholdCrossings(self, lod):
        """ 
        Input:
            self: (ConvertToJSON object)
            lod:  (a list of dictionaries) data
        Output: a list of ordered dictionaries of data to be written to the JSON file
        Description: prepare the forecast's threshold crossings (a list of threshold crossing values)
    
        """
        
        stub_found = False
        pfn = 'forecasts/threshold_crossings' # parent field name
        L = [
            ('crossing_time', 'YYYY-MM-DDTHH:MMZ', True, None, None, False, False),
            ('uncertainty', 0, False, False, False, None, True),
            ('threshold', 0, True, False, False, None, False),
            ('threshold_units', 'pfu', True, None, None, None, True), 
        ]
        #for d in lod:
        #    print(d)
        #print('Exiting prematurely from PrepForecastThresholdCrossings. --Joycelyn')
        #sys.exit()
        newL = []
        for d in lod:
            toD = collections.OrderedDict()
            for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
                if self.VerifyKeyInDict(k, d, required=r):
                    value = d[k]
                    if not allow_stub_value:
                        stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                    if allow_stub_value or not stub_found:
                        if s == 'YYYY-MM-DDTHH:MMZ':
                            self.ValidateDateTimeStamp(value, '{}/{}'.format(pfn, k), ensure_in_past=must_be_in_past)
                        elif s == 0:
                            value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), neg_allowed=allow_neg, neg_one_allowed=allow_neg_one)
                        elif k == 'units':
                            self.ValidateAlphaNumeric(value, '{}/{}'.format(pfn, k), allow_addtl_chars=' -_+*^()/')
                        toD[k] = value
            newL.append(toD)
        return newL
    # end PrepForecastThresholdCrossings


    def PrepForecast(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prep all the forecast's data, a single forecast
    
        """

        stub_found = False
        pfn = 'forecasts' # parent field name
        toD = collections.OrderedDict() # temp ordered dictionary
        leafD = {
            'species': (self.noneList, True, self.ValidateForecastSpecies),
            'location': (self.noneList, True, self.ValidateForecastLocation),
            'sep_profile': ("filename_energychannel.txt", False, self.ValidateForecastSEPProfile),
            'native_id': (self.noneList, False, self.ValidateForecastNativeID),
        }
        L = [
            ('energy_channel', True, self.PrepForecastEnergyChannel),
            ('species', True, None),
            ('location', True, None),
            ('prediction_window', True, self.PrepForecastPredictionWindow),
            ('peak_intensity', False, self.PrepForecastPeakIntensity),
            ('peak_intensity_esp', False, self.PrepForecastPeakIntensityEsp),
            ('peak_intensity_max', False, self.PrepForecastPeakIntensityMax),
            ('fluences', False, self.PrepForecastFluences),
            ('event_lengths', False, self.PrepForecastEventLengths),
            ('threshold_crossings', False, self.PrepForecastThresholdCrossings),
            ('probabilities', False, self.PrepForecastProbabilities),
            ('all_clear', False, self.PrepForecastAllClear),
            ('sep_profile', False, None),
            ('native_id', False, None),
        ]
        for (k, r, meth) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                if meth is None:
                    if k in leafD.keys():
                        value = d[k]
                        (s, r, val_meth) = leafD[k]
                        stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r)
                        if not stub_found: 
                            val_meth(value)
                            toD[k] = value
                else: 
                    #print('about to call {} with arg *{}*.'.format(str(meth), d[k]))
                    if k == 'event_lengths': toD[k] = meth(d[k], d['prediction_window'])
                    else: toD[k] = meth(d[k])
        return toD
    # end PrepForecast (NOT PrepForecasts !!!)

    def PrepForecasts(self):
        """ 
        Input:
            self: (ConvertToJSON object)
        Output: None (self.orderedDict is updated instead)
        Description: Prep all the forecasts' data 
    
        """
        
        pfn = 'forecasts'
        if self.VerifyKeyInDict(pfn, required=True):
            L = self.dataDict[pfn]
            # if L is not a list, throw an error
            if not isinstance(L, list):
                m = 'ERROR: \'{}\' is supposed to be a list, but it isn\'t. Exiting.'.format(pfn)
                self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
            newL = []
            for d in L:
                toD = self.PrepForecast(d)
                newL.append(toD)
            if newL != []: self.orderedDict[pfn] = newL
            else:
                m = 'ERROR: \'{}\' did not get any data. Exiting.'.format(pfn)
                self.IJWError(m, self.log_msgs, True) # (msg, log, exit)

        return 
    # end PrepForecasts


    def PrepIssueTime(self):
        """ 
        Input: self: (ConvertToJSON object)
        Output: None
        Description: Prep the issue_time data for the ordered dictionary, from which the JSON is written.
    
        """

        stub_found = False
        k = pfn = 'issue_time' # parent field name
        if self.VerifyKeyInDict(k, required=True): # make sure the key exists
            L = [ ('issue_time', 'YYYY-MM-DDTHH:MMZ', True, None, None, True, False), ]
            for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
                value = self.dataDict[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}'.format(k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    self.ValidateDateTimeStamp(value, '{}'.format(k), ensure_in_past=must_be_in_past) # ensure proper format 'YYYY-MM-DDTHH:MMZ'
                    self.orderedDict[k] = value

        return
    # end PrepIssueTime


    def PrepMode(self):
        """ 
        Input: self: (ConvertToJSON object)
        Output: None
        Description: Prep the mode data for the ordered dictionary, from which the JSON is written. 
    
        """

        pfn = 'mode'
        if self.VerifyKeyInDict(pfn, required=True):
            value = self.dataDict[pfn]
            # the stub value is 'forecast' and that's a legit (and likely) value, so skip the VerifyNonStubValue step
            valid_valuesL = ['forecast', 'historical', 'nowcast', 'simulated_realtime_forecast', 'simulated_realtime_nowcast']
            self.ValidateEnum(value, valid_valuesL, pfn)
            self.forecast_or_historical_mode = value
            self.orderedDict[pfn] = value

        return
    # end PrepMode


    def PrepModel(self):
        """ 
        Input: self: (ConvertToJSON object)
        Output: None
        Description: Prep the model data for the ordered dictionary, from which the JSON is written.
    
        """

        stub_found = False
        k = pfn = 'model' # parent field name
        if self.VerifyKeyInDict(k, required=True):
            d = self.dataDict[k]
            toD = collections.OrderedDict()
            L = [
                ('short_name', 'Short name for your model', True, None, None, None, False),
                ('spase_id', 'spase://CCMC/SimulationModel/MODEL_NAME/VERSION', True, None, None, None, False),
            ]
            for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
                if self.VerifyKeyInDict(k, d, required=r):
                    value = d[k]
                    if not allow_stub_value:
                        stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                    if allow_stub_value or not stub_found:
                        if k == 'short_name': self.ValidateAlphaNumeric(value, '{}/{}'.format(pfn, k), allow_addtl_chars=' -_+().') # should I allow other characters?
                        elif k == 'spase_id': self.ValidateURL(value, '{}/{}'.format(pfn, k), spase_id=True) # Validate single url value
                        toD[k] = value
        self.orderedDict[pfn] = toD

        return
    # end PrepModel

    def PrepModelInputs(self):
        """ 
        Input: self: (ConvertToJSON object)
        Output: None
        Description: Prep the model inputs data (if it exists) for the ordered dictionary, from which the JSON is written.
    
        """

        newL = list()
        if self.VerifyKeyInDict('inputs', required=False):
            print('[PrepModelInputs:L1414] type(self.dataDict[\'inputs\']) is {1} self.dataDict[\'inputs\'] is {0}'.format(self.dataDict['inputs'], type(self.dataDict['inputs'])))
            for d in self.dataDict['inputs']:
                print('[PrepModelInputs:L1416] type(d) is {1} d is {0}'.format(d, type(d)))
                newD = {}
                if self.VerifyKeyInDict('magnetic_connectivity', d, required=False):
                    # d['magnetic_connectivity'] is a list of dictionaries
                    print("[PrepModelInputs:L1437] type(d['magnetic_connectivity']) is {1} d['magnetic_connectivity'] is {0}".format(d['magnetic_connectivity'], type(d['magnetic_connectivity'])))
                    for d2 in d['magnetic_connectivity']:
                        print('the dictionary is for magnetic_connectivity. about to go to PrepModelInputsMagneticConnectivity.')
                        print('type(d2): {0}; d2: {1}'.format(type(d2), d2))
                        newD = {'magnetic_connectivity': self.PrepModelInputsMagneticConnectivity(d2)}
                        if newD != {}: newL.append(newD)
                elif self.VerifyKeyInDict('magnetogram', d, required=False):
                    # d['magnetogram'] is a list of dictionaries
                    for d2 in d['magnetogram']:
                        newD = {'magnetogram': self.PrepModelInputsMagnetogram(d2)}
                        if newD != {}: newL.append(newD)
        if newL != []: self.orderedDict['inputs'] = newL # put Inputs in ordered dictionary

        return
    # end PrepModelInputs


    def PrepModelInputsMagneticConnectivity(self, d):
        """ 
        Input: 
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prep the model inputs' magnetic connectivity data
    
        """

        stub_found = False
        pfn = 'inputs/magnetic_connectivity' # parent field names
        toD = collections.OrderedDict() # temp ordered dictionary

        # define values for validating the following magnetic_connectivity values 
        L = [
            # key name, stub value, req'd, allow_neg values, allow_neg_one values, must_be_in_past, allow_stub_value, min_value, max_value
            ('method', None, True, None, None, False, False, None, None), # allowed values: Parker Spiral, PFSS-Parker Spiral, WSA, WSA-ENLIL, ADAPT-WSA-ENLIL  (& maybe: Parker_Spiral_2.5Rs)
            ('lat', 0, False, True, True, None, True, -90, 90),
            ('lon', 0, True, True, True, None, True, -180, 180),
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value, min_v, max_v) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    if s == 0:
                        value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), allow_neg, allow_neg_one, min_v, max_v)
                if k == 'method':
                    # check that the method value is one of the allowed values
                    self.ValidateModelInputsMagneticConnectivityMethod(value, '{}/{}'.format(pfn, k))
                toD[k] = value
        # process the connection_angle values, if they exist
        k = 'connection_angle'
        if self.VerifyKeyInDict(k, d, required=False):
            toD[k] = self.PrepModelInputsMagneticConnectivityConnectionAngle(d[k])
        # process the solar_wind values, if they exist
        k = 'solar_wind'
        if self.VerifyKeyInDict(k, d, required=False):
            toD[k] = self.PrepModelInputsMagneticConnectivitySolarWind(d[k])

        return toD
    # end PrepModelInputsMagneticConnectivity


    def PrepModelInputsMagneticConnectivityConnectionAngle(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prep the model inputs' magnetic connectivity connection angle data
    
        """

        stub_found = False
        pfn = 'inputs/magnetic_connectivity/connection_angle' # parent field names
        toD = collections.OrderedDict() # temp ordered dictionary

        # define values for validating the following magnetic_connectivity values 
        L = [
            # key name, stub value, req'd, allow_neg values, allow_neg_one values, must_be_in_past, allow_stub_value, min_value, max_value
            ('great_circle', 0, False, False, False, None, True, 0, 360),
            ('lat', 0, False, True, True, None, True, -90, 90),
            ('lon', 0, True, True, True, None, True, -180, 180),
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value, min_v, max_v) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    if s == 0:
                        value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), allow_neg, allow_neg_one, min_v, max_v)
                toD[k] = value
        return toD
    # end PrepModelInputsMagneticConnectivityConnectionAngle


    def PrepModelInputsMagneticConnectivitySolarWind(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prepare the solar_wind data from inputs/magnetic_connectivity (if it exists) for the ordered dictionary, from which the JSON is written.
    
        """

        stub_found = False
        pfn = 'inputs/magnetic_connectivity/connection_angle' # parent field names
        toD = collections.OrderedDict() # temp ordered dictionary

        # define values for validating the following magnetic_connectivity values 
        L = [
            # key name, stub value, req'd, allow_neg values, allow_neg_one values, must_be_in_past, allow_stub_value, min_value, max_value
            ('observatory', None, False, None, None, None, True, None, None),
            ('speed', 0, True, False, False, None, True, 0, None),
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value, min_v, max_v) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    if s == 0:
                        value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), allow_neg, allow_neg_one, min_v, max_v)
                    if k == 'observatory': # Validate observatory (alphanumeric + some special characters?)
                        self.ValidateAlphaNumeric(value, '{}/{}'.format(pfn, k), allow_addtl_chars='-_')
                # do not bother to save the observatory value if it is None
                if k == 'observatory' and value in noneList: pass
                else: toD[k] = value

        return toD
    # end PrepModelInputsMagneticConnectivitySolarWind


    def PrepModelInputsMagnetogram(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prepare the magnetogram data from inputs (if it exists) for the ordered dictionary, from which the JSON is written.
    
        """

        stub_found = False
        pfn = 'inputs/magnetogram' # parent field names
        toD = collections.OrderedDict() # temp ordered dictionary

        # define values for validating the following magnetic_connectivity values 
        L = [
            # key name, stub value, req'd, allow_neg values, allow_neg_one values, must_be_in_past, allow_stub_value, min_value, max_value
            ('observatory', None, True, None, None, False, False, None, None),
            ('instrument', None, True, None, None, False, False, None, None),
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value, min_v, max_v) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                self.ValidateAlphaNumeric(value, '{}/{}'.format(pfn, k), allow_addtl_chars='-_')
                toD[k] = value
        # process the products values, if they exist
        k = 'products'
        if self.VerifyKeyInDict(k, d, required=False):
            lod = list()
            for d2 in d[k]:
                lod.append(self.PrepModelInputsMagnetogramProducts(d2))
            toD[k] = lod

        return toD
    # end PrepModelInputsMagnetogram

   
    def PrepModelInputsMagnetogramProducts(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prep the model inputs/magnetogram/products data (if it exists) for the ordered dictionary, from which the JSON is written.
    
        """

        stub_found = False
        pfn = 'inputs/magnetogram/products' # parent field names
        toD = collections.OrderedDict() # temp ordered dictionary

        # define values for validating the following magnetic_connectivity values 
        L = [
            # key name, stub value, req'd, allow_neg values, allow_neg_one values, must_be_in_past, allow_stub_value, min_value, max_value
            ('product',        None,                False, None, None, False, False, None, None),
            ('last_data_time', 'YYYY-MM-DDTHH:MMZ', True,  None, None, False, False, None, None), 
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value, min_v, max_v) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    if s == 'YYYY-MM-DDTHH:MMZ':
                        self.ValidateDateTimeStamp(value, '{}/{}'.format(pfn, k), ensure_in_past=must_be_in_past)
                if k == 'product': self.ValidateAlphaNumeric(value, '{}/{}'.format(pfn, k), allow_addtl_chars='-_')
                # do not bother to save the product value if it is None
                if k == 'product' and value in noneList: pass
                else: toD[k] = value

        return toD
    # end PrepModelInputsMagnetogramProducts

 
    def PrepTriggers(self):
        """ 
        Input: self: (ConvertToJSON object)
        Output: None
        Description: Prep the triggers data (if it exists) for the ordered dictionary, from which the JSON is written.
    
        """

        newL = []
        if self.VerifyKeyInDict('triggers', required=False):
            for d in self.dataDict['triggers']:
                newD = {}
                if self.VerifyKeyInDict('cme', d, required=False):
                    newD = {'cme': self.PrepTriggersCME(d['cme'])}
                if self.VerifyKeyInDict('flare', d, required=False):
                    newD = {'flare': self.PrepTriggersFlare(d['flare'])}
                if self.VerifyKeyInDict('cme_simulation', d, required=False):
                    newD = {'cme_simulation': self.PrepTriggersCMESimulation(d['cme_simulation'])}
                if self.VerifyKeyInDict('particle_intensity', d, required=False):
                    newD = {'particle_intensity': self.PrepTriggersParticleIntensity(d['particle_intensity'])}
                if newD != {}: newL.append(newD)
        if newL != []: self.orderedDict['triggers'] = newL # put Triggers in ordered dictionary

        return 
    # end PrepTriggers


    def PrepTriggersCME(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prep the triggers/cme data (if it exists) for the ordered dictionary, from which the JSON is written.
    
        """

        stub_found = False
        pfn = 'triggers/cme' # parent field names
        toD = collections.OrderedDict() # temp ordered dictionary
        L = [
            ('start_time', 'YYYY-MM-DDTHH:MMZ', True, None, None, False, False, None, None),
            ('liftoff_time', 'YYYY-MM-DDTHH:MMZ', False, None, None, False, False, None, None),
            ('lat', 0, False, True, True, None, True, -90, 90),
            ('lon', 0, False, True, True, None, True, -180, 180),
            ('pa', 0, False, True, True, None, True, 0, 360),
            ('half_width', 0, False, True, True, None, True, 0, 180),
            ('speed', 0, False, True, True, None, True, 0, 5000),
            ('acceleration', 0, False, False, False, None, True, None, None),
            ('height', 0, False, True, True, None, False, 1, 250),
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value, min_v, max_v) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    if s == 'YYYY-MM-DDTHH:MMZ':
                        self.ValidateDateTimeStamp(value, '{}/{}'.format(pfn, k), ensure_in_past=must_be_in_past)
                    elif s == 0:
                        value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), allow_neg, allow_neg_one, min_v, max_v)
                    toD[k] = value
                # If 'lat' is a non-zero/non-stub value given, make sure 'lon' is there too.
                if k == 'lat' and not self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=False): 
                    self.VerifyKeyInDict('lon', d, required=True)
                # If 'lon' is a non-zero/non-stub value given, make sure 'lat' is there too.
                if k == 'lon' and not self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=False): 
                    self.VerifyKeyInDict('lat', d, required=True)
        k = 'time_at_height'
        if self.VerifyKeyInDict(k, d, required=False):
            toD[k] = self.PrepTriggersCMETimeAtHeight(d[k])
        # coordinates and catalog
        stub_found = False
        if self.VerifyKeyInDict('lat', d, required=False) or self.VerifyKeyInDict('lon', d, required=False):
            L = [('coordinates', self.noneList, True, None, None, None, False)]
        else: L = [('coordinates', self.noneList, False, None, None, None, False)]
        L.append(('catalog', self.noneList, False, None, None, None, False))
        if 'catalog' in d and d['catalog'] == 'DONKI': 
            L.append(('catalog_id', self.noneList, True, None, None, None, True))
        else:
            L.append(('catalog_id', self.noneList, False, None, None, None, True))
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    if k == 'coordinates': self.ValidateCoordinates(value)
                    elif k == 'catalog': self.ValidateCatalog(value)
                    elif k == 'catalog_id': self.ValidateCatalogID(value, d['catalog'])
                toD[k] = value
        # urls
        k = 'urls'
        if self.VerifyKeyInDict(k, d, required=False):
            value = d[k]
            toD[k] = self.PrepTriggersURLs(value, '{}/{}'.format(pfn, k)) # verifies list, non-None, validates, returns fresh List

        return toD
    # end PrepTriggersCME


    def PrepTriggersCMESimulation(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prep the triggers/CME Simuation data (if it exists) for the ordered dictionary, from which the JSON is written.
    
        """
        
        stub_found = False
        pfn = 'triggers/cme_simulation' # parent field name
        toD = collections.OrderedDict() # temp ordered dictionary
        L = [
            ('model', self.noneList, True, None, None, None, False),
            ('simulation_completion_time', 'YYYY-MM-DDTHH:MMZ', False, None, None, True, False),
            ('urls', [], False, None, None, None, True), 
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    if k == 'model':
                        self.ValidateAlphaNumeric(value, '{}/{}'.format(pfn, k), allow_addtl_chars=' -_+')
                        toD[k] = value
                    elif s == 'YYYY-MM-DDTHH:MMZ':
                        self.ValidateDateTimeStamp(value, '{}/{}'.format(pfn, k), ensure_in_past=must_be_in_past)
                        toD[k] = value
                    elif k == 'urls': 
                        toD[k] = self.PrepTriggersURLs(value, '{}/{}'.format(pfn, k))

        return toD
    # end PrepTriggersCMESimulation


    def PrepTriggersCMETimeAtHeight(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prep the trigger CME's time at height data
    
        """
        
        stub_found = False
        pfn = 'triggers/cme/time_at_height' # parent field name
        toD = collections.OrderedDict() # temp ordered dictionary
        L = [
            ('time', 'YYYY-MM-DDTHH:MMZ', True, None, None, False, False, None, None),
            ('height', 0, True, False, False, None, False, 1, 9000),
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value, min_v, max_v) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    if s == 'YYYY-MM-DDTHH:MMZ':
                        self.ValidateDateTimeStamp(value, '{}/{}'.format(pfn, k), ensure_in_past=must_be_in_past)
                    elif s == 0:
                        value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), allow_neg, allow_neg_one, min_v, max_v)
                    toD[k] = value
        return toD
    # end PrepTriggersCMETimeAtHeight


    def PrepTriggersFlare(self, d):
        """ 
        Input:
            self: (ConvertToJSON object)
            d:    (dictionary) data
        Output: an ordered dictionary of data to be written to the JSON file
        Description: Prep the trigger CME's time at height data
    
        """
        """ """
        stub_found = False
        pfn = 'triggers/flare' # parent field name
        toD = collections.OrderedDict() # temp ordered dictionary
        L = [
            ('last_data_time', 'YYYY-MM-DDTHH:MMZ', True, None, None, False, False), 
            ('start_time', 'YYYY-MM-DDTHH:MMZ', False, None, None, False, False), 
            ('peak_time', 'YYYY-MM-DDTHH:MMZ', False, None, None, False, False), 
            ('end_time', 'YYYY-MM-DDTHH:MMZ', False, None, None, False, False),
            ('location', self.noneList, False, None, None, None, False), 
            ('intensity', 0, False, None, None, None, False),
            ('integrated_intensity', 0, False, None, None, None, False),
            ('noaa_region', self.noneList, False, None, None, None, False), 
            ('urls', [], False, None, None, None, True), 
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    if s == 'YYYY-MM-DDTHH:MMZ':
                        self.ValidateDateTimeStamp(d[k], '{}/{}'.format(pfn, k), ensure_in_past=must_be_in_past)
                        toD[k] = value
                    elif k == 'location': 
                        self.ValidateStonyhurstCoordinates(value, '{}/{}'.format(pfn, k)) # Validate Stonyhurst coordinates (N00W00/S00E00 format)
                        toD[k] = value
                    elif s == 0:
                        value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), neg_allowed=allow_neg, neg_one_allowed=allow_neg_one)
                        toD[k] = value
                    elif k == 'noaa_region': 
                        self.ValidateNOAARegion(value) # Validate noaa_region (include the preceding 1) 
                        toD[k] = value
                    elif k == 'urls': 
                        toD[k] = self.PrepTriggersURLs(value, '{}/{}'.format(pfn, k))
        return toD
    # end PrepTriggersFlare


    def PrepTriggersParticleIntensity(self, d):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ """
        stub_found = False
        toD = collections.OrderedDict() # temp ordered dictionary
        pfn = 'triggers/particle_intensity' # parent field name
        L = [
            ('observatory', self.noneList, True, None, None, None, False), 
            ('instrument', self.noneList, True, None, None, None, False),
            ('last_data_time', 'YYYY-MM-DDTHH:MMZ', True, None, None, False, False),
        ]
        for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
            if self.VerifyKeyInDict(k, d, required=r):
                value = d[k]
                if not allow_stub_value:
                    stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                if allow_stub_value or not stub_found:
                    if s == 'YYYY-MM-DDTHH:MMZ':
                        self.ValidateDateTimeStamp(value, '{}/{}'.format(pfn, k), ensure_in_past=must_be_in_past)
                    else:
                        # Validate observatory and instrument values (is that even possible?  alphanumeric + some special characters?)
                        self.ValidateAlphaNumeric(value, '{}/{}'.format(pfn, k), allow_addtl_chars='-_')
                    toD[k] = value
        k = 'ongoing_events'
        if self.VerifyKeyInDict(k, d, required=False):
             toD[k] = self.PrepTriggersParticleIntensityOngoingEvents(d[k])
        return toD
    # end PrepTriggersParticleIntensity

    def PrepTriggersParticleIntensityOngoingEvents(self, List):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ """
        stub_found = False
        pfn = 'triggers/particle_intensity/ongoing_events' # parent field name
        newL = []
        L = [
            ("start_time", "YYYY-MM-DDTHH:MMZ", True, None, None, False, False),
            ("threshold", 0, True, False, False, None, True), 
            ("energy_min", 0, True, False, False, None, True), 
            ("energy_max", 0, True, False, True, None, True), # -1 ok. o/w float
        ]
        #print('received List: {} which is of type({}).'.format(List, type(List)))
        for d in List:
            toD = collections.OrderedDict() # temp ordered dictionary
            for (k, s, r, allow_neg, allow_neg_one, must_be_in_past, allow_stub_value) in L:
                if self.VerifyKeyInDict(k, d, required=r):
                    value = d[k]
                    if not allow_stub_value:
                        stub_found = self.VerifyNonStubValue(value, s, '{}/{}'.format(pfn, k), required=r) # check for non-stub value
                    if allow_stub_value or not stub_found:
                        if s == 'YYYY-MM-DDTHH:MMZ':
                            self.ValidateDateTimeStamp(value, '{}/{}'.format(pfn, k), ensure_in_past=must_be_in_past)
                        else:
                            value = self.ValidateFloat(value, '{}/{}'.format(pfn, k), neg_allowed=allow_neg, neg_one_allowed=allow_neg_one)
                        toD[k] = value
            newL.append(toD)
        return newL
    # end PrepTriggersParticleIntensityOngoingEvents

    def PrepTriggersURLs(self, value, field_name):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """Verify that the value is a list of urls.  Don't return any urls that are in the self.noneList. Validate the URL. """
        newL = []
        self.VerifyIsInstance(value, list, field_name) # make sure it is a list
        for url in value:
            if any([self.VerifyNonStubValue(url, n, field_name, required=False) for n in self.noneList]):
                pass
            else: 
                self.ValidateURL(url, field_name) # Validate single url value
                newL.append(url)
        return newL
    # end PrepTriggersURLs

    def PrintLogMessage(self, m, t, logger=None):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """Print the message.  Log the message."""
        if logger == None:
            self.InitLogger()
        if mode == 'debug':
                #print("{0}: {1}".format(mode, msg))
                logger.debug(msg)
        elif mode == 'info':
                #print("{0}: {1}".format(mode, msg))
                logger.info(msg)
        elif mode == 'warning':
                print("{0}: {1}".format(mode, msg))
                logger.warning(msg)
        elif mode == 'error':
                print("{0}: {1}".format(mode, msg))
                logger.error(msg)
        elif mode == 'critical':
                print("{0}: {1}".format(mode, msg))
                logger.critical(msg)
        return
    # end PrintLogMessage

    def VerifyNonStubValue(self, value, stub_value, field_name, required=True):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """Compare the value and the stub value.  If they are equivalent, throw an error and quit."""
        found_stub_value = False
        if stub_value == []:
            if value == stub_value:
                found_stub_value = True
        elif stub_value == self.noneList:
            if any([self.VerifyNonStubValue(value, n, field_name, required=False) for n in self.noneList]):
                found_stub_value = True
        elif value == stub_value:
                found_stub_value = True
        if found_stub_value:
            m = "You did not replace the default \'{}\' value.".format(field_name)
            if required: 
                m = "{} Please do so. Exiting.".format(m)
                self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
            else: 
                m = "{} Either replace it or remove the key and default/stub value from the dictionary, please.".format(m)
                self.IJWWarning(m, log=self.log_msgs) 
        return found_stub_value
    # end VerifyNonStubValue

    def ValidateAlphaNumeric(self, value, field_name, allow_addtl_chars=''):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ Validate AlphaNumeric Value """

        if sys.version.split()[0][0] == '2': # if the Python version is < 3
            allowed_chars = string.letters + string.digits + allow_addtl_chars
        else:
            allowed_chars = string.ascii_letters + string.digits + allow_addtl_chars
        for c in value:
            if c not in allowed_chars: # throw error
                m = 'ERROR: An invalid character (\'{}\') was found in \'{}\'. It has to be one of these characters: \'{}\'.  Exiting.'.format(c, field_name, allowed_chars)
                self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        return
    # end ValidateAlphaNumeric

    def ValidateBoolean(self, value, field_name):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ """
        if value not in [True, False]:
            m = 'ERROR: the boolean value given in \'{}\' is not True or False. Exiting.'.format(field_name)
            self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        return
    # end ValidateBoolean

    def ValidateCatalog(self, value):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ """
        pfn = 'triggers/cme/catalog'
        valid_valuesL = ['ARTEMIS', 'DONKI', 'HELCATS', 'JHU APL', 'CACTUS_NRL', 'CACTUS_SIDC', 'CORIMP', 'SEEDS', 'SOHO_CDAW', 'STEREO_COR', 'SWPC']
        self.ValidateEnum(value, valid_valuesL, pfn)
        return
    # end ValidateCatalog

    def ValidateCatalogID(self, value, catalog_value):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ The catalog ID value can be anything, however, it must not be None if catalog_value == 'DONKI'.  """
        print('entered ValidateCatalogID.')
        pfn = 'triggers/cme/catalog_id'
        if catalog_value == 'DONKI' and value in noneList:
            m = 'ERROR: the value given in \'{}\' cannot be None if the catalog is DONKI. Exiting.'.format(pfn)
            self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        return
    # end ValidateCatalogID

    def ValidateCoordinates(self, value):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ Validate CME Coordinates Value (in triggers/cme)"""
        self.ValidateAlphaNumeric(value, 'triggers/cme/coordinates', allow_addtl_chars='._-')
        return
    # end ValidateCoordinates

    def ValidateDateTimeStamp(self, dts_value, field_name, ensure_in_past=False):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """Check that the date time stamp has the correct format.  Check that it is a valid value. 
        Need to allow datetimestamp to have seconds (e.g., '2000-07-14T10:03:00Z')
            or no seconds (e.g., '2000-07-14T10:03Z').

        """
        #print('In ValidateDateTimeStamp.  dts_value is {}'.format(dts_value))
        c_typeDict = {}
        for i in [0,1,2,3,5,6,8,9,11,12,14,15]: c_typeDict[i] = string.digits
        for i in [4,7]: c_typeDict[i] = '-'
        c_typeDict[10] = 'T'
        c_typeDict[13] = ':'
        #for (k, v) in c_typeDict.items():
        #    print("{} : {}".format(k, v))

        if len(dts_value) not in [17, 20]: # ensure you have exactly the correct length of date time string
            m = 'ERROR: the date time string given in \'{}\' is the wrong length. It is \'{}\'.  Exiting.'.format(field_name, dts_value)
            self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        elif len(dts_value) == 17:
            c_typeDict[16] = 'Z'
        elif len(dts_value) == 20:
            c_typeDict[16] = ':'
            for i in [17,18]: c_typeDict[i] = string.digits
            c_typeDict[19] = 'Z'
        for i in range(0, len(dts_value)):
            #print("dts_value[{0}] is {1} and is of type {2}.".format(i, dts_value[i], type(dts_value[i])))
            if dts_value[i] not in c_typeDict[i]: # the character I got in this position is not the correct type, throw an error
                m = 'ERROR: the character in the {0} index of the date time string given in \'{1}\' is not the correct type.  It needs to be one of these characters [{2}]. Exiting.'.format(i, field_name, c_typeDict[i])
                self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        if ensure_in_past:
            # make sure the date value is in the past
            y = int(dts_value[0:4])
            m = int(dts_value[5:7])
            d = int(dts_value[8:10])
            h = int(dts_value[11:13])
            n = int(dts_value[14:16]) # n --> thinking m for minute, but it's already used so bumped it to 'n'
            s = 0
            if len(dts_value) == 20:
                s = int(dts_value[17:19]) 
            if datetime.datetime(y, m, d, h, n, s) > datetime.datetime.utcnow(): # throw error
                m = 'ERROR: the date time string given in \'{}\' is not in the past. Exiting.'.format(field_name)
                self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        return True
    # end ValidateDateTimeStamp

    def ValidateEmail(self, value):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ Validation of email address (only characters + numbers + '_-@.' """
        # Validate that there are no illegal characters
        self.ValidateAlphaNumeric(value, 'email', allow_addtl_chars='.@_-')
        # make sure there is an '@' in the value and that it is not the first character
        # and make sure a '.' appears AFTER the '@' with something inbetween
        i = value.find('@')
        if i <= 0 or value.find('.', i) <= 0:
            # throw error
            m = 'ERROR: the email value given (\'{}\') is not valid.  Exiting.'.format(value)
            self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        return
    # end ValidateEmail

    def ValidateEnum(self, value, valid_valuesL, field_name):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ Make sure the value is in the valid values list, otherwise, throw an error and exit. """
        valid_values_loweredL = [v.lower() for v in valid_valuesL] # do this because we want these strings to be case insensitive
        if value.lower() not in valid_values_loweredL: # allow the value to be any case
            # throw error
            m = 'ERROR: the value given (\'{}\') is not valid.  It needs to be one of these values: \n{}\nExiting.'.format(value, str(valid_valuesL))
            self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        return
    # end ValidateEnum

    def ValidateFloat(self, value, field_name, neg_allowed=False, neg_one_allowed=False, min_=None, max_=None):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
            value:           (float) the value to be validataed
            field_name:      (string) the fieldname associated with this value
            neg_allowed:     (boolean) whether or not the value is allowed to be negative.
            neg_one_allowed: (boolean) whether or not the value is allowed to be 1.
            min_:            (float) the minimum value this item is allowed to be.
            max_:            (float) the maximum value this item is allowed to be.
        Output: a float value
        Description: convert the value to a float (if needed) and make sure it is within the bounds of allowed values.
            sample incoming intensity value: "8.2e-4"
   
        Modifications:
            2022.12.12, JTJ: fixed issue where the correct value was not being returned under these two conditions:
                if neg_one_allowed and value == -1:
                elif min_ is not None and max_ is not None and (if value >= min_ and value <= max_)

        """

        if isinstance(value, str):


            # strip off any whitespace from the value, if needed.
            value = value.strip()


            # make sure the string value does not have any disallowed characters in it.
            allowed = '{}e-.x'.format(string.digits)
            for c in str(value):
                if c not in allowed:
                    m = 'ERROR: the float value given in \'{}\' has an illegal character in it. Exiting.'.format(field_name)
                    self.IJWError(m, self.log_msgs, True) # (msg, log, exit)


            # convert the value from a string to a float, if needed.
            try: value = float(value)
            except TypeError as ex:
                print('TypeError Exception: {}'.format(ex))


        #print('type({}) is {}'.format(field_name, type(value)))


        # validate that the given value falls within the allowed range
        if neg_one_allowed and value == -1:
            return value
        elif min_ is not None and max_ is not None:
            if value >= min_ and value <= max_: return value
            else:
                m = 'ERROR: the float value given (\'{}\') in \'{}\' was not within the specified range of \'{}\' and \'{}\'. Exiting.'
                m = m.format(value, field_name, min_, max_)
                self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        elif not neg_allowed and value < 0.0:
            m = 'ERROR: the float value given in \'{}\' was negative and that is not allowed in this field. Exiting.'.format(field_name)
            self.IJWError(m, self.log_msgs, True) # (msg, log, exit)


        return value
    # end ValidateFloat


    def ValidateForecastEventLength(self, start, end, prediction_window_d):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """Event length must fall within the prediction window.
        end can be None.
        """
        start_dto = self.ConvertDTString2DTO(start)
        pw_start_dto = self.ConvertDTString2DTO(prediction_window_d['start_time'])
        pw_end_dto = self.ConvertDTString2DTO(prediction_window_d['end_time'])
        if start_dto < pw_start_dto or start_dto > pw_end_dto: # throw error
            m = 'ERROR: the forecast/event_length/start_time is not within the prediction window. Exiting.'
            self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        if end is not None:
            end_dto = self.ConvertDTString2DTO(end)
            if end_dto < pw_start_dto or end_dto > pw_end_dto: # throw error
                m = 'ERROR: the forecast/event_length/end_time ({}) is not within the prediction window ({} - {}). Exiting.'.format(end_dto, pw_start_dto, pw_end_dto)
                self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        return
    # end ValidateForecastEventLength

    def ValidateForecastLocation(self, v):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ """
        pfn = 'forecast/location'
        valid_valuesL = ['mercury', 'venus', 'earth', 'mars', 'psp', 'stereoa', 'stereob', 'dawn', 'juno', 'L1', 'L2', 'L4', 'L5']
        self.ValidateEnum(v, valid_valuesL, pfn)
        return True
    # end ValidateForecastLocation

    def ValidateForecastNativeID(self, v):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ """
        # make sure there are no wacko characters/scripting hacks
        self.ValidateAlphaNumeric(v, 'native_id', allow_addtl_chars='_-.')
        return
    # end ValidateForecastNativeID

    def ValidateForecastProbabilityValue(self, v):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """Probability value is a float, but it has to be between 0 and 1. """
        if isinstance(v, str):
            v = float(v)
        if v < 0.0 or v > 1.0:
            m = 'ERROR: the float value given (\'{}\') in \'forecasts/probability_value\' is invalid.  It must be between 0 and 1. Exiting.'.format(v)
            self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        return
    # end ValidateForecastProbabilityValue

    def ValidateForecastSEPProfile(self, v):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """2019.12.11, Per Leila, we do not want colons in filenames (bad for windows and macs, not great for linux). """
        # make sure there are no wacko characters/scripting hacks
        self.ValidateAlphaNumeric(v, 'sep_profile', allow_addtl_chars='-_.')
        return
    # end ValidateForecastSEPProfile

    def ValidateForecastSpecies(self, v):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ """
        pfn = 'forecast/species'
        valid_valuesL = ['electron', 'proton', 'helium', 'helium3', 'helium4', 'oxygen', 'iron', 'ion']
        self.ValidateEnum(v, valid_valuesL, pfn)
        return True
    # end ValidateForecastSpecies

    def ValidateHTTPURL(self, value, field_name):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """Validate a regular HTTP URL """
        value = value.strip() # chop off any leading or trailing spaces
        # if there's a space anywhere in the URL, return False success value
        if ' ' in value: return False
        # it must start with http or https
        if value.startswith('http'):
            if value.startswith('http'): ci = 4
            elif value.startswith('https'): ci = 5
            else: return False
            # followed by ://
            if value[ci:ci+3] == '://':
                ci = ci + 3
                # try:
                # followed by x number of alphanumeric characters, including - (hostname)... followed by .
                ei = value.find('.', ci)
                self.ValidateAlphaNumeric(value[ci:ei], field_name, allow_addtl_chars='-')
                ci = ei + 1
                # followed by x number of alphanumeric characters, including - (domain name)... followed by .
                ei = value.find('.', ci)
                self.ValidateAlphaNumeric(value[ci:ei], field_name, allow_addtl_chars='-')
                ci = ei + 1
                # followed by 2+ number of alpha characters (top-level domain)... followed by / or :
                ei = value.find(':', ci)
                if ei > -1: # there's a port number
                    # Validate the TLD
                    self.ValidateAlphaNumeric(value[ci:ei], field_name, allow_addtl_chars='')
                    ci = ei + 1
                    # Validate the port number
                    ei = value.find('/', ci)
                    self.ValidateNumeric(value[ci:ei], field_name)
                    ci = ei + 1
                else: # Validate the TLD
                    ei = value.find('/', ci)
                    if ei == -1: ei = len(value)
                    self.ValidateAlphaNumeric(value[ci:ei], field_name, allow_addtl_chars='')
                    ci = ei + 1
                ## followed by x number of alphanumeric characters, including -%=&?~/ 
                #if len(value) >= ci:
                #    ei = len(value)
                #     # Check for blacklisted characters???
                #  #self.ValidateAlphaNumeric(value[ci:ei], '{}/{}'.format(pfn, k), allow_addtl_chars='-%=&?~/') # This is going to be too strong.
                # except: return False
            else: return False
        return True
    # end ValidateHTTPURL


    def ValidateModelInputsMagneticConnectivityMethod(self, value, pfn):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ Validate that the method value given (under inputs / magnetic_connectivity) is an accepted one. 
        Here are the currently allowed values: Parker Spiral, PFSS-Parker Spiral, WSA, WSA-ENLIL, ADAPT-WSA-ENLIL (& maybe Parker_Spiral_2.5Rs...checking with Leila 2020.11.13)

        """
        allowed_values = ['Parker Spiral', 'PFSS-Parker Spiral', 'WSA', 'WSA-ENLIL', 'ADAPT-WSA-ENLIL', 'Parker_Spiral_2.5Rs']
        if value not in allowed_values:
            m = 'ERROR: \'{0} / {1}\' has to be one of these values: {2}.  Exiting.'.format(pfn, 'method', allowed_values)
            self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        return
    # end ValidateModelInputsMagneticConnectivityMethod


    def ValidateNOAARegion(self, value):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ Validate noaa_region.  The NOAA active region number is a 5-digit number and current values are > 10,000, although many people present just the last four digits.  """
        # make sure all digits.
        for c in str(value):
            if c not in string.digits:
                m = 'ERROR: \'noaa_region\' is not all numerical digits. Exiting.'
                self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        if isinstance(value, str):
            try: value = int(value)
            except TypeError as ex:
                print('TypeError Exception: {}'.format(ex))
        # make sure value is > 10000.
        if value < 10000:
            m = 'ERROR: \'noaa_region\' has to include the leading 1 in the number.  Exiting.'
            self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        if value > 100000: # it should be a 5 digit number, so if it goes over to 6 digits, throw an error
            m = 'ERROR: \'noaa_region\' is too long.  Exiting.'
            self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        return
    # end ValidateNOAARegion


    def ValidateNumeric(self, value, field_name):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """Validate that every character in the given string is a digit."""
        for c in value: # value is already a string
            if c not in string.digits:
                m = 'ERROR: the numeric value given in \'{}\' has an illegal character in it. Exiting.'.format(field_name)
                self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        return
    # end ValidateNumeric


    def ValidateSpaseURL(self, value, field_name):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ validate that URL follows this convention:
        "spase_id": "spase://CCMC/SimulationModel/MODEL_NAME/VERSION" 
        """
        if value.startswith('spase'):
            ci = 5
            # followed by ://
            if value[ci:ci+3] == '://':
                ci = ci + 3
                for i in range(0, 4): # for ['CCMC', 'SimulationModel', 'MODEL_NAME', 'VERSION']
                    try:
                        ei = value.find('/', ci)
                        self.ValidateAlphaNumeric(value[ci:ei], field_name, allow_addtl_chars='._-=')
                        ci = ei + 1
                    except: return False
            else: return False
        return True
    # end ValidateSpaseURL(value, field_name)

    def ValidateStonyhurstCoordinates(self, value, field_name):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ Validate the use of Stonyhurst coordinates (use N00W00/S00E00 format). """
        self.ValidateAlphaNumeric(value, field_name)
        c_typeDict = {}
        for i in [1,2,4,5]: c_typeDict[i] = string.digits
        c_typeDict[0] = 'NS'
        c_typeDict[3] = 'EW'
        #for (k, v) in c_typeDict.items():
        #    print("{} : {}".format(k, v))
        if len(value) != 6: # ensure you have exactly the correct length of coordinates
            m = 'ERROR: the Stonyhurst coordinate string given in \'{}\' is the wrong length. Exiting.'.format(field_name)
            self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        for i in range(0, len(value)):
            #print("value[{0}] is {1} and is of type {2}.".format(i, value[i], type(value[i])))
            if value[i] not in c_typeDict[i]: # the character I got in this position is not the correct type, throw an error
                m = 'ERROR: the character in the {0} index of the date time string given in \'{1}\' is not the correct type.  It needs to be one of these characters [{2}]. Exiting.'.format(i, field_name, c_typeDict[i])
                self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        return
    # end ValidateStonyhurstCoordinates
                        
    def ValidateURL(self, value, field_name, spase_id=False):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """ Validate the URL, at least within reason. """
        success = False
        if value.startswith('http'):
            success = self.ValidateHTTPURL(value, field_name)
        elif value.startswith('spase'):
            success = self.ValidateSpaseURL(value, field_name)
        else:
            pass # throw an error
        return
    # end ValidateURL


    def VerifyExclusive(self, key1, key2, local_dataDict=None):
        """ 
        Input:
            self: (this object)
            self:            (ConvertToJSON object)
            key1: (string) potential key value for the local_dataDict
            key2: (string) potential key value for the local_dataDict
            local_dataDict: (dictionary) data to be put in output JSON file
        Output: None
        Description:
            if both values were given and both values are not None, then throw an error and exit the program.

        """
        if local_dataDict == None: local_dataDict = self.dataDict

        # if both values were given and both values are not None, then throw an error
        if key1 in local_dataDict.keys() and key2 in local_dataDict.keys():
            if local_dataDict[key1] != None and  local_dataDict[key2] != None:
                print("===========================================================")
                print("ERROR: cannot have non-None values for both {} and {}.".format(key1, key2))
                sys.exit()
        return
    # end VerifyExclusive
        

    def VerifyIsInstance(self, v, t, field_name):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """Throw an error if the given value, v, is not of type t."""
        if not isinstance(v, t):
            m = 'ERROR: \'{}\' is supposed to be a {}, but it isn\'t. Exiting.'.format(field_name, str(t))
            self.IJWError(m, self.log_msgs, True) # (msg, log, exit)
        return
    # end VerifyIsInstance

    def VerifyKeyInDict(self, key, local_dataDict=None, required=False):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """See if the key exists in the appropriate dictionary (self.dataDict or the provided local_dataDict).      
        If it does not, throw an error if it is a required field.

        """
        if local_dataDict == None: local_dataDict = self.dataDict
        #if not isinstance(local_dataDict, dict):
        #    print("ERROR: expecting a dictionary.  Got something else in \'{}\'. Exiting.".format(key))
        #    sys.exit()
        keyexists = key in local_dataDict.keys()
        if required and not keyexists: # issue error
            print("===========================================================")
            print("ERROR: missing key \'{}\' in dictionary. Exiting.".format(key))
            print("       dictionary does have the following keys:  ".format(key))
            for k in local_dataDict.keys():
               print('       {}: {}'.format(k, local_dataDict[k]))
            sys.exit()
        return keyexists
    # end VerifyKeyInDict

    def WriteJSON(self):
        """ 
        Doc String TODO
        Input:
            self:            (ConvertToJSON object)
        Output:
        Description:
    
        """
        """This is about controlling the order of the data written to the JSON file. 
        Along the way, prep the data for the ordered dictionary, from which the JSON is written. 
        For each field, make sure to:
            1) verify that required field(s) are there.
            2) verify that the stub/default/sample data has been replaced (but allow stub values in some cases).
            3) validate the data that is there.

        """
        self.PrepModel()
        self.PrepIssueTime()
        self.PrepMode()
        self.PrepTriggers()
        self.PrepModelInputs()
        self.PrepForecasts()

        # now for the actual writing
        d = {'sep_forecast_submission' : self.orderedDict}
        with open(self.output_filename, 'w') as outfile:
            json.dump(d, outfile)
        print('\nPlease send the following file to the CCMC: {0}\n'.format(self.output_filename))

        return 


#### END of CLASSES #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####

	
#### MAIN #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####
if __name__ == '__main__':

    noneList = [None, 'None', 'none', ['none'], ['None'], [None]] # NOTE: 0 is not included because it is valid/needed in many fields
    program_desc = "This program is supposed to help the modeler to provide their model data in to the CCMC in JSON format.  Contact Joycelyn Jones at joycelyn.t.jones@nasa.gov for additional assistance."
    parser = InitParser(program_desc)
    (output_filename, output_dir, log_msgs, log_dir, log_starter, dataDict) = ParseArguments(parser)

    ConvertToJSON(dataDict, output_filename, output_dir, log_msgs, log_dir, log_starter)


#### END of MAIN ## #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####


#### MODIFICATIONS  #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####
#
# By the way, I was under an incredibly short deadline to create this product caused by being new to the project 
# and the 5-week furlough of Dec 2018/Jan 2019.  If this code is lacking documentation, I'm sorry. 
# I've been trying to fix that.  -- JTJones
#
# 2019.03.05,JTJones: found latest addition to the visual schema, 'mode' didn't make it into the final JSON output.  Added it.
# 2019.03.05,JTJones: found that 'None' or 'none' values were getting through in lists where they shouldn't.  Fixed that.
# 2019.03.06,JTJones: Improved NOAA Region value validation to check that the number is not too large.
# 2019.03.06,JTJones: added check for key in the dictionary in PrepTriggersCMESimulation.
# 2019.07.08,JTJones: Added '-_+*^()/' as allowed characters for all 'units' fields. 
# 2019.07.08,JTJones: Changed flare/start_time to be an optional field.
# 2019.07.09,JTJones: Added lon as a requirement if lat is given, and vice versa.
# 2019.12.09,JTJones: Allowed ':' in sep_profile name, per Leila.
# 2019.12.10,JTJones: Added addition of .json file extension to output file name if user does not include it.
# 2019.12.11,JTJones: Added check that all_clear threshold matches the energy channel (see CheckAllClearThresholdVsEnergyChannel).
# 2019.12.13,JTJones: Took out ':' as an allowed character in the sep_profile name, per Leila.  Made sure output filename has ':' taken out if they are there.
# 2020.02.28,JTJones: Added '.' as a valid character for model short_name.  
# 2020.02.28,JTJones: Handling seconds in a datetime stamp, if they are there.  They are not required.
# 2020.02.28,JTJones: Fixed bug in flare_last_data_time handling.
# 2020.11.12,JTJones: Removing use of contact-name and contact-email
# 2021.02.16,JTJones: Changed datetime.datetime.now() instances to datetime.datetime.utcnow() instances because some servers aren't UTC.
# 2021.03.23,JTJones: Fixed but in peak_intensity_esp_time handling.
# 2021.05.18,JTJones: Removed 0 and '0' from noneList definition in DontAllowNoneValues because 0 is a valid value for many fields.
# 2021.06.04,JTJones: Allow 'nowcast' and 'simulated_realtime_forecast' in submission.mode field
#                     adding to peak_intensity_esp: uncertainty, uncertainty_low, uncertainty_high 
#                       NOTE: can't have uncertainty and either uncertainty_low or uncertainty_high.  if you have uncertainty_low, you must have uncertainty_high also.
#                     adding new peak_intensity_max table with these fields: intensity, units, uncertainty, uncertainty_low, uncertainty_high, time
#                       NOTE: can't have uncertainty and either uncertainty_low or uncertainty_high.  if you have uncertainty_low, you must have uncertainty_high also.
# 2021.08.24,JTJones: Allow 'simulated_realtime_nowcast' in submission.mode field
# 2022.08.29,JTJones: Added a new InitLogger.  The original InitLogger was renamed to InitLoggerOld
# 2022.12.08,JTJones: <PLANNED> The keep numerical values (floats, integers) from being put in quotation marks.
# 2025.01.19,LAStegeman: Added human_evaluation trigger.
#
#### END OF MODIFICATIONS  ## #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####

