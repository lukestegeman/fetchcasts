import sys
import os
import datetime
import glob
import re
import collections

def CreateMonToIntDict():
    return dict(zip(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    [x for x in range(1, 12+1)]))
                     

class DataFormat():
    def __init__(self, start, end, dbo, verbose, logger, lfh, cfg):
        """
        Input:
            self:    (object) this DataFormat object
            start:   (datetime object) indicates the start date to download/reload data
            end:     (datetime object) indicates the end date to download/reload data
            dbo:     (MySQL DB connection object) connection to the database
            logger:  (python logging object) log handle
            lfh:     (file handle object) the log file file handle
            cfg:     (dictionary) all the program configuration options, as designated by the user.
        Output: a DataFormat Object (automatically returned)
        Description: Initialize DataFormat object variables. 

        """
        self.start_date = start
        self.end_date = end
        self.dbo = dbo
        self.verbose = verbose
        self.logger = logger
        self.lfh = lfh
        self.cfg = cfg
        self.threshold = 10 # all of our data sources are for the >10 MeV EC, therefore, threshold is 10 pfu for all of them
    # end DataFormat.__init__


    def AlreadyInDatabase(self, f):
        """
        Input:
            self: (object) this DataFormat object
            f:    (string) full path to data file
        Output: None
        Description:
            Parse the data file and see if the data is already in the database.
            If the data is already in the database, log it and do nothing.
            If the data is not already in the database, add it.

        """

        self.logger.debug('[DataFormat] Entered AlreadyInDatabase.')

        t = self.ParseDataFile(f) # pT has the format of: (issue_time, day1, day2, day3) 
        self.logger.debug('[DataFormat] Parsed data file.')

        # Issue Time
        issue_time = t[0] # NOTE: issue_time is a datetime object

        # get the model IDs for the SWPC forecast days
        model_ids = self.GetModelIds()
        self.logger.debug(f'[DataFormat] Got model IDs: {model_ids}')

        for i in range(1, len(t)):  # Loop through just the dayX forecasts
            # Is this Forecast already in the database?

            (pwst, pwet) = self.GetPredictionWindow(i, issue_time)
            self.logger.debug(f'[DataFormat] SWPC day {i}:\n\tpw start: {pwst}\n\tpw end:   {pwet}')

            # See if there is a forecast for this prediction window time for this model and energy channel
            forecast_id = self.GetForecastID(10, pwst, pwet, model_ids[i], issue_time)
            self.logger.debug(f'[DataFormat] Forecast ID returned from GetForecastID is {forecast_id}')

            if forecast_id == 0: 
                # there's no forecast for this prediction window/model/energy channel combination, so add the forecast
                self.InsertForecast(i, model_ids[i], issue_time, 10, t[i], pwst, pwet) # SWPC day {1|2|3}, model_id, issue_time, ec_min, probability value, pwst, pwet
                self.logger.debug('[DataFormat] Inserted forecast.')
            else: 
                # there is a forecast for this prediction window/model/energy channel combination
                self.logger.debug('[DataFormat] The forecast is already in the database.')

        self.logger.debug('[DataFormat] Exiting AlreadyInDatabase.')
        return
    # end DataFormat.AlreadyInDatabase


    def EmailErrorToResponsiblePerson(self, line_num, msg):
        """
        Input:
            self:     (object) this DataFormat object
            line_num: (integer) the number indicating the code line number that called EmailErrorToResponsiblePerson
            msg:      (string) message to be emailed to the SEP lead programmer.  NOTE: used as the email subject as well as the main part of the email body.
        Output: None
        Description:
            Email a formatted message to the SEP lead programmer indicating what line num of code 
            triggered this message.

        """
        subj = msg
        msg = '{0}\n\nError Code L{1}\n\n'.format(msg, line_num)
        SendSMTPEmail(subj, msg, self.cfg['sep_lead_email'], self.cfg['sep_lead_email'], False)
        return
    # end DataFormat.EmailErrorToResponsiblePerson


    def ExitGracefully(self):
        """
        Input: self: (object) this Source object
        Output: None
        Description: Exit the program gracefully: roll back any SQL actions and close the database connection, then shut down the logger.

        """

        # Roll back any SQL actions and close the databse connection.
        if self.dbo != None:
            self.dbo.Rollback()
            self.logger.warning('Rolled back the SQL for this ingestation, just in case.')
            self.dbo.Close()

        # Shut down logger.
        ShutdownLogger(self.logger, self.lfh)  # from lib_shared
        sys.exit()
    # end DataFormat.ExitGracefully


    def GetForecastID(self, ec, pwst, pwet, model_id, issue_time):
        """
        Input:
            self:     (object) this DataFormat object
            ec:       (integer) the minimum value for this integral energy channel.  the expected value is 10.
            pwst:     (datetime object) the date/time that marks the start of the prediction window.
            pwet:     (datetime object) the date/time that marks the end of the prediction window.
            model_id: (integer) the ID for this model in the database.model table
            issue_time: (datetime object) the date/time that the forecast was issued.
        Output: the ID for a forecast that matches this energy channel and prediction window from this model, if any.
        Description: See if there's a forecast in the database table for this model with the same energy channel and prediction window.

        """
        
        # Assume the Model ID exists
        # See if there is a forecast for this prediction window time for this model and energy channel
        sql = """SELECT id FROM forecast 
                  WHERE energy_min = %s AND energy_max = -1 
                    AND prediction_window_start_time = %s AND prediction_window_end_time = %s 
                    AND submission_id in (SELECT id FROM submission WHERE model_id = %s AND issue_time = %s); 
        """
        args = [10, pwst, pwet, model_id, issue_time]

        forecast_id = 0
        self.dbo.SQLExec(sql, args, logger=self.logger)
        for (forecast_id, ) in self.dbo.GetCursor().fetchall(): 
            pass

        return forecast_id
    # end DataFormat.GetForecastID


    def GetFTPConnection(self, ftp_domain):
        """
        Input: 
            self:       (object) this DataFormat object
            ftp_domain: (string) the domain name for the FTP server
        Output: FTP object that holds a connection to the FTP server
        Description:
             Try getting an FTP connection
             NOTE: Added 10 retries because connecting to the SWPC FTP server tends to fail a lot due to a maximum number of connections.
                   Trying just a few seconds later makes a difference.

        """

        self.logger.debug('[DataFormat] Entered FTPConnection.')

        # Initializing variables needed for the loop
        ftp = None
        count = 0

        while count <= 10 and ftp == None:
            try:
                count += 1
                ftp = FTP(ftp_domain) # connect to host, default port
            except ftplib.all_errors:
                self.logger.critical('SWPC FTP Server is refusing the connection.')
                self.ExitGracefully()
            except:
                if count < 10:
                    self.logger.debug('Cannot connect to the SWPC FTP server.  Will try again in a few seconds.')
                    time.sleep(2)
                else:
                    self.logger.critical('You cannot connect to the SWPC FTP server.  Tried 10 times.')
                    self.ExitGracefully()

        return ftp
    # end DataFormat.GetFTPConnection


    def GetModelIds(self):
        """
        Input: self: (object) this DataFormat object
        Output:  a list of the model IDs for the three SWPC day forecasts
        Description: look up the model ID values for SWPC Day 1, SWPC Day 2, SWPC Day 3, respectively.           
            If they don't exist in the database, add them.

        """

        # get a list of the model IDs for easy future reference
        model_ids = [None] # this is so the day number can be used as the index into the list
        for i in [1, 2, 3]:
            model_id = 0
            sql = 'SELECT id FROM model WHERE short_name = "SWPC Day {0}";'.format(i)
            self.dbo.SQLExec(sql, [])
            for (model_id, ) in self.dbo.GetCursor().fetchall(): 
                if model_id != None and model_id != 0:
                    model_ids.append(model_id)

        if model_ids == [None]:
            # this means the models do not exist.  Add them.
            # SWPC Day 1       | spase://CCMC/SimulationModel/SWPC/v20080103
            for i in [1, 2, 3]:
                sql = 'INSERT INTO model VALUES (NULL, "SWPC Day {0}", "spase://CCMC/SimulationModel/SWPC/v20080103");'.format(i)
                self.dbo.SQLExec(sql, [])
                model_ids.append( self.dbo.GetLastInsertID() )
            
        return model_ids
    # end DataFormat.GetModelIds


    def InsertAllClearTable(self, forecast_id, probability, threshold):
        """
        Input:
            self:        (object) this DataFormat object
            forecast_id: (integer) ID number for this forecast, as indicated in the forecast.id field.
            probability: (float) probability value given by SWPC forecast.
            threshold:   (integer) threshold value, given the energy channel
        Output: None
        Description: Insert the needed data into the all_clear table. 

        """

        # Determine the all clear boolean value given the probabiility forecast
        probability_threshold = 0.01 # threshold for all clear (1%) 
        all_clear = False
        if probability <= probability_threshold: all_clear = True 
                 
        sql = 'INSERT INTO all_clear VALUES (%s, %s, %s, %s, %s);'
        args = [forecast_id, all_clear, threshold, 'pfu', probability_threshold]
        self.dbo.SQLExec(sql, args)

        return
    # end DataFormat.InsertAllClearTable 


    def InsertForecast(self, swpc_day, model_id, issue_time, ec_min, probability, pwst, pwet):
        """
        Input:
            self:        (object) this DataFormat object
            swpc_day:    (integer) the forecast day {1, 2, 3}
            model_id:    (integer) ID number for this model, as indicated in the model.id field
            issue_time:  (datetime object) date and time when this forecast was issued.
            ec_min:      (integer) minimum energy channel value.
            probability: (float) probability value given by SWPC forecast.
            pwst:        (datetime object) prediction window start date and time.
            pwet:        (datetime object) prediction window end date and time.
        Output: None
        Description:
            Insert all the data for this forecast into the database.
            Approach the tables in this order:
                submission (add to model first, if needed) (return submission ID to be used in populating the forecast table)
                forecast (return forecast ID to be used in populating the probability and all_clear tables)
                probability
                all_clear
            
        """
    
        submission_id = self.InsertSubmissionTable(swpc_day, model_id, issue_time, 'forecast')
        forecast_id = self.InsertForecastTable(submission_id, ec_min, pwst, pwet)
        self.logger.debug(f'forecast ID is {forecast_id}')
        self.InsertProbabilityTable(forecast_id, probability, self.threshold)
        self.InsertAllClearTable(forecast_id, probability, self.threshold)

        return
    # end DataFormat.InsertForecast

    
    def InsertForecastTable(self, submission_id, ec_min, pwst, pwet):
        """
        Input:
            self:          (object) this DataFormat object
            submission_id: (integer) ID number for this submission, as indicated in the submission.id field
            ec_min:        (integer) minimum energy channel value.
            pwst:          (datetime object) prediction window start date and time.
            pwet:          (datetime object) prediction window end date and time.
        Output: the forecast.id value once the data has been inserted into the database.
        Description: Insert the SWPC forecast into the forecast table.   

        """
        sql = 'INSERT INTO forecast VALUES (NULL, %s, %s, -1, "MeV", "proton", "earth", %s, %s, NULL);'
        args = [submission_id, ec_min, pwst, pwet]
        self.dbo.SQLExec(sql, args, logger=self.logger)

        # Fetch the forecast ID value from the forecast that was just inserted.
        forecast_id = self.dbo.GetLastInsertID()

        return forecast_id
    # end DataFormat.InsertForecastTable


    def InsertModelTable(self, swpc_day):
        """ 
        Input:
            self:     (object) this DataFormat object
            swpc_day: (integer) the forecast day {1, 2, 3}
        Output: the model.id value 
        Description:
            Fetch from/Insert into the SWPC model (for that given day) the model table.
            Return the model's ID value.

        """

        # If the model is already in the database, get the existing model ID.
        # Otherwise, insert the model into the model table
        spase_id = 'spase://CCMC/SimulationModel/SWPC/v20080103'
        short_name = 'SWPC Day {0}'.format(swpc_day)

        # See if the model is already in the database
        model_id = None
        sql = "SELECT id FROM model WHERE short_name = %s AND spase_id = %s;"
        args = [short_name, spase_id]
        self.dbo.SQLExec(sql, args)
        for (model_id, ) in self.dbo.GetCursor().fetchall():
            pass

        # If the model is not already in the database, add it.
        if model_id == None:
            sql = "INSERT INTO model VALUES (NULL, %s, %s);" # id, short_name, spase_id
            self.dbo.SQLExec(sql, args) # use the same args as above
            # Fetch the model ID value from the model that was just inserted.
            model_id = self.dbo.GetLastInsertID()

        self.logger(f'Just added SWPC Day {swpc_day} and it is model_id {model_id}')
        return model_id
    # end DataFormat.InsertModelTable


    def InsertProbabilityTable(self, forecast_id, probability, threshold):
        """ 
        Input:
            self:        (object) this DataFormat object
            forecast_id: (integer) ID number for this forecast, as indicated in the forecast.id field
            probability: (float) the SEP probability value forecasted by SWPC.
            threshold:   (float) the SEP probability threshold value used by SWPC.
        Output: None
        Description: Insert the forecast's probability value into the probability table. 

        """

        sql = 'INSERT INTO probability VALUES (NULL, %s, %s, NULL, %s, "pfu");'
        args = [forecast_id, probability, threshold]
        self.dbo.SQLExec(sql, args)

        return
    # end DataFormat.InsertProbabilityTable


    def InsertSubmissionTable(self, swpc_day, model_id, issue_time, mode):
        """ 
        Input:
            self:       (object) this DataFormat object
            swpc_day:   (integer) the forecast day {1, 2, 3}
            model_id:   (integer) ID number for this model, as indicated in the model.id field
            issue_time: (datetime object) date and time when this forecast was issued.
            mode:       (string) Valid mode values are {'historical' | 'forecast'}, however, for SWPC forecasts, this value will always be 'foreccast'.  
        Output: the submission.id value 
        Description:
            Insert the forecast's data into the submission table.
            Return the submission ID value.

        """

        self.logger.debug(f'Entered InsertSubmissionTable.  model_id is {model_id}')
        if model_id == None:
            self.logger.debug('Going into InsertModelTable.')
            model_id = self.InsertModelTable(swpc_day)

        sql = "INSERT INTO submission (id, model_id, issue_time, mode) VALUES (NULL, %s, %s, %s);"
        args = [model_id, issue_time, mode]
        self.logger.info(f'sql: {sql}')
        self.logger.info(f'args: {args}')
        self.dbo.SQLExec(sql, args)

        # Fetch the submission ID value from the submission that was just inserted.
        submission_id = self.dbo.GetLastInsertID()
        self.logger.debug(f'submission ID is {submission_id}')
        if submission_id == 0: sys.exit()

        return submission_id
    # end DataFormat.InsertSubmissionTable


    def ParseSWPCProbabilitiesLine(self, line, header, delimiter):
        """
        Input:
            self:      (object) this DataFormat object
            line:      (string) line of data text to be parsed
            header:    (string) the header of the line to ignore
            delimiter: (string) the delimiter used to split the probability values apart
        Output: a list of the SEP probabilities for Day 1, 2, and 3, respectively, as integer values.
        Description:
            Parse the SWPC SEP forecast data line and return just the values, as integers.

        """

        line_type = header.split()[0]
        self.logger.debug(f'[DataFormat] Entered ParseSWPCProbabilitiesLine. Type {line_type}')

        line = line[len(header):]  # Chop off the line header
        line = line.strip()
        probabilities = line.split(delimiter) # split the line on the delimiter
        
        self.logger.debug(f'[DataFormat] ParseSWPCProbabilitiesLine (split) line is: {probabilities}.  Type {line_type}')
        try:
            # convert number to a percentage
            probabilities = [ int(p.strip())/100. for p in probabilities if p.strip() != '' ]
        except ValueError as e:
            self.logger.error(f'ValueError: {e}')
            self.logger.error(f'value sent to ParseSWPCProbabilitiesLine was {line}.  Type {line_type}.')
            #self.ExitGracefully()
            raise
        self.logger.debug(f'[DataFormat] Exiting ParseSWPCProbabilitiesLine. Type {line_type}')
        return probabilities
    # end DataFormat.ParseSWPCProbabilitiesLine


    def ParseSWPCIssuedLine(self, line):
        """ 
        Input:
            self:   (object) this DataFormat object
            line:   (string) line of data text to be parsed
        Output: a datetime object representing the issue_time of the forecast.
        Description:
            Parse line with issued date/time to get year, month, day, hour, minutes.
            Sample line:
                :Issued: 2019 Jun 10 2200 UTC

        """
        
        line = line[len(':Issued:'):]
        lineL = line.split()
        if len(lineL) < 4: 
            subj = 'Problem with SWPC file'
            msg = 'Problem with SWPC file issued at {0}.  Cannot get issue time.'
            sender = recipients = self.cfg['sep_lead_email']
            SendSMTPEmail(subj, msg, sender, recipients, False)
            sys.exit()
        # Get year out
        year = int(lineL[0])
        # Get month out and translate it from abbreviation to number
        month = lineL[1]
        mon2IntD = CreateMonToIntDict()
        month = mon2IntD[month]
        # get day out
        day = int(lineL[2])
        # Get hour and minutes out
        time_ = int(lineL[3])
        hour = int(time_ / 100)
        minute = time_ % 100
    
        issued_dto = datetime.datetime(year, month, day, hour, minute)
        return issued_dto
    # end DataFormat.ParseSWPCIssuedLine
# end class DataFormat 

class Proton(DataFormat):
    """
    Data Source #4
    The NOAA SWPC Proton Forecast issued every 24 hours
    ftp://ftp.swpc.noaa.gov/pub/warehouse/2019/RSGA/
    """

    def __init__(self, start, end, mode, dbo, verbose, logger, lfh, cfg):
        """
        Input:
            self:    (object) this Proton object
            start:   (datetime object) indicates the start date to download/reload data
            end:     (datetime object) indicates the end date to download/reload data
            mode:    (string) {'download'|'reload'} it tells the code whether to download data from SWPC or reload local data files.
            dbo:     (MySQL DB connection object) connection to the database
            logger:  (python logging object) log handle
            lfh:     (file handle object) the log file file handle
            cfg:     (dictionary) all the program configuration options, as designated by the user.
        Output: a Proton Object (automatically returned)
        Description:
            Download the latest file (or all the files since a given date).
            If data is not already in the database, add the data.

        """

        # Get inheritance of all the properties and methods from parent
        if sys.version_info[0] == 2:
            DataFormat.__init__(self, start, end, dbo, verbose, logger, lfh, cfg) # Makes the child class inherit all the properties and methods from its parent
        elif sys.version_info[0] == 3: # Python 3 
            super().__init__(start, end, dbo, verbose, logger, lfh, cfg) 

        self.logger.info('[DS#4] Initializing Proton object.')

        # NOTE: this data source has been limited to 1996 - 2012.11.13, per Leila on 2020.02.27
        if start < datetime.datetime(1996, 1, 1, 0, 0, 0) or end >= datetime.datetime(2012, 11, 14, 0, 0, 0):
            pass
            #self.logger.critical('Data Source #4, Proton data via FTP, is only usable from January 1, 1996, through November 13, 2012.  You asked for data outside of that range.  Exiting.')
            #sys.exit()

        # Initialize class variables
        self.output_file_template = 'noaa.swpc.proton.{}.txt'
        self.output_directory_template = os.path.join(self.cfg['archive_dir'], '{}')
        self.output_file_full_path_template = os.path.join(self.output_directory_template, self.output_file_template)
        self.downloaded_files = list()
        self.got_good_files = False

        if mode == 'download': self.Download()
        elif mode == 'reload': self.Reload()
        self.logger.info(f'[DS#4] Proton {mode} completed.')

        if len(self.downloaded_files) > 0: 
            self.got_good_files = True

        self.logger.debug('[DS#4] Completed Proton object.')
    # end Proton.__init__


    def Download(self):
        """ 
        Input: self: (object) this Proton object
        Output: None
        Description:
            Download the three-day RSGA forecast file(s) from SWPC's FTP site.
            The URL used is ftp://ftp.swpc.noaa.gov/pub/warehouse/2019/RSGA/
            NOTE: You can download historical data from this location as well, going back to 2018.01.01.  
    
        """

        self.logger.debug('[DS#4/Proton] Entered Download.')

        # Initializing needed variables
        ftp_domain = 'ftp.swpc.noaa.gov'
        curr_year = None
        ftp = None
        count = 0

        ftp = self.GetFTPConnection(ftp_domain)
        self.logger.debug('[DS#4/Proton] Got a connection to the FTP server.')

        # Now that you have the FTP connection, log in anonymously
        ftp.login()               # user anonymous, passwd anonymous@
        self.logger.debug('[DS#4/Proton] Logged in to the FTP server.')

        # Loop through all the days you need to get the forecast for and download the forecast
        for d in DateRange(self.start_date, self.end_date+datetime.timedelta(days=1)): # Adding a day because DateRange does not include the ending date given

            # change the directory you are in on the FTP server, based on the year value for the data you are trying to download.
            if curr_year != d.year:
                curr_year = d.year
                file_path = '/pub/warehouse/{0}/RSGA/'.format(curr_year) 
                ftp.cwd(file_path)        # change directory

                # Make sure the output directory exists
                f_out_dir = os.path.join(self.cfg['archive_dir'], 'RSGA', str(d.year))
                if not os.path.exists(f_out_dir): os.mkdir(f_out_dir)

            # Format the input and output filenames/paths
            date_ = '{0}{1:02d}{2:02d}'.format(d.year, d.month, d.day) # example: '20190609'
            f_in = '{0}RSGA.txt'.format(date_) # example: '20190609RSGA.txt'
            f_out = 'noaa.swpc.rsga.10mev.{0}.txt'.format(date_) # example: 'noaa.swpc.rsga.10mev.20190609.txt'
            f_out_full_path = os.path.join(f_out_dir, f_out) 

            # Try to actually download the file from the FTP server, if the file does not already exist.
            try:
                if not os.path.exists(f_out_full_path):
                    ftp.retrbinary('RETR {0}'.format(f_in), open('{0}'.format(f_out_full_path), 'wb').write)
                    self.logger.debug(f'[DS#4/Proton] Just dumped Proton/RSGA data to file ({f_out})')
            except:
                self.logger.warning(f'[DS#4/Proton] Failed at retrieving SWPC file {f_in}')


            # Determine success/failure of download
            if not os.path.exists(f_out_full_path) or (os.path.exists(f_out_full_path) and os.stat(f_out_full_path).st_size == 0):
                # If it fails to download, you'll get a file named properly, but it will be an empty file.
                try: os.remove(f_out_full_path) # remove the empty file so it doesn't cause problems later
                except OSError: pass
                self.logger.warning(f'[DS#4/Proton] Downloaded empty SWPC file ({f_out}) from FTP site')
                # Do NOT e-mail anyone because this is going to happen EVERY time the new file is slightly late, which is frequently.
                #self.EmailErrorToResponsiblePerson(802, subj)
            elif os.path.exists(f_out_full_path):
                # If it downloads successfully, put it in the list of files to be ingested into the database
                self.downloaded_files.append(f_out_full_path)
                self.logger.info('[DS#4/Proton] Successfully downloaded SWPC 3-Day Forecast RSGA file from FTP site.')
                self.got_good_files = False
                
        ftp.quit()
        self.logger.debug('[DS#4/Proton] Exiting Download.')
        return
    # end Proton.Download


    def GetPredictionWindow(self, day, issue_time):
        """ 
        Input: 
            self: (object) this S1 object
            day:  (integer) the day number for this SWPC forecast (e.g., Day 1, Day 2, Day 3)
            issue_time: (datetime object) the forecast issue date/time
        Output: (tuple) prediction window start time and prediction window end time
        Description:
            Determine the prediction window based on this type of object and the issue time.

        """

        # NOTE: **For Day 1 Forecasts**, the PW start time is set to the next day because the issue time is typically 2200 of the day before the PW starts.
        # The day 2 and day 3 forecasts move forward by the appropriate number of days.
        pwst = datetime.datetime(issue_time.year, issue_time.month, issue_time.day, 0, 0) + datetime.timedelta(days=day) 
        pwet = datetime.datetime(pwst.year, pwst.month, pwst.day, 23, 59)

        return (pwst, pwet)
    # end Proton.GetPredictionWindow


    def GotDataFilesSuccessfully(self):
        """ 
        Input: self: (object) this S1 object
        Output: (boolean) the value of self.got_good_files
        Description:
            Return self.got_good_files, which tracks if the download of the SWPC 3-Day forecast S1 data via HTTP was successful.
            'Success' is defined as answering 'Yes' to the following two questions:
                Was there an ':Issued:' line in the downloaded data?
                Did a data file get downloaded and saved?
                Is the new data file approximately the correct size (i.e., within 10% of the expected size)?

        """
        return self.got_good_files
    # end Proton.GotDataFilesSuccessfully


    def ParseDataFile(self, f):
        """ 
        Input:
            self: (object) this Proton object
            f:    (string) full path to data file
        Output: a tuple with:
            issue date/time
            SEP forecasts for day 1, 2, and 3, respectively.
        Description:
            Parse the data file.
            When you find the line with with issued date/time, send it to ParseSWPCIssuedLine to get parsed.
                Sample issued date/time line:
                    :Issued: 2020 Jan 01 0030 UTC
            When you find a line with the SWPC forecast values, send it to ParseSWPCProtonLine to get parsed.
                Sample forecast values lines:
                    Proton     01/01/01 
                        --or--
                    PROTON     01/01/01 

        """

        self.logger.debug('[DS#4/Proton] Entered ParseDataFile.')

        # Initialize needed variables
        issue = day1 = day2 = day3 = None

        with open(f) as ifh:
            self.logger.debug(f'[DS#4/Proton] ==== Inside {f} ===============================================')

            for line in ifh.readlines(): 
                line = line.strip()
                if ':Issued:' in line:
                    issue = self.ParseSWPCIssuedLine(line) # issue is a datetime object
                    self.logger.debug(f'[DS#4/Proton] Got issue time: {issue}')

                elif line.startswith('Proton') or line.startswith('PROTON'):
                    if line.startswith('Proton'):   p = re.compile('Proton[ ]+[0-9]+/[0-9]+/[0-9]+')
                    elif line.startswith('PROTON'): p = re.compile('PROTON[ ]+[0-9]+/[0-9]+/[0-9]+')
                    m = p.match(line)
                    if m != None:
                        self.logger.debug(f'[DS#4/Proton] Found \'Proton\' line:\n\t{line}')
                        [day1, day2, day3] = self.ParseSWPCProbabilitiesLine(line, 'Proton', '/')
                        self.logger.debug(f'[DS#4/Proton] Returned from ParseSWPCProbabilitiesLine.  Proton probabilities are {day1}, {day2}, {day3}')

        if any([ True if d == None else False for d in [day1, day2, day3] ]):
            msg = f'[DS#4/Proton] Problem reading data file ({f})'
            self.logger.error(msg)
            #self.ExitGracefully()
            raise Exception(msg)

        self.logger.debug('[DS#4/Proton] Exiting ParseDataFile.')
        return (issue, day1, day2, day3)
    # end Proton.ParseDataFile


    def Reload(self):
        """ 
        Input: self: (object) this Proton object
        Output: None
        Description:
            Get a list of all the RSGA files already downloaded and stored in the local data archive.
            Sort the list and store it in self.downloaded_files.

            NOTE: this data source has been limited to 1996 - 2012.11.13, per Leila on 2020.02.27

        """

        self.logger.debug('[DS#4/Proton] Entered Reload.')


        # Get a list of all the >10 MeV RSGA files in the archive.
        # The filename pattern for the archived files is <archive_dir_from_config.json>/RSGA/YYYY/MM/YYYYMMDDRSGA*.txt
        fp1 = os.path.join(self.cfg['archive_dir'], 'RSGA', '*', '*', '*RSGA.txt')

        # Loop through all the filename patterns and get a list of the files that match each one
        for fp in [fp1]:
            # Get the list of file paths that match that filename pattern
            for f in glob.glob(fp):
                self.downloaded_files.append(f)
        self.logger.debug('[DS#4/Proton] Got list of RSGA files in the data archive.')


        # sort the file list
        self.downloaded_files.sort()
        self.logger.debug('[DS#4/Proton] Sorted the list of RSGA files in the data archive.')


        self.logger.debug('[DS#4/Proton] Exiting Reload.')
        return 
    # end Proton.Reload

    def ParseAll(self, datefilter=True):
        forecasts = collections.OrderedDict()
        for filepath in self.downloaded_files:
            filedir, filename = os.path.split(filepath)
            if datefilter:
                match = re.search('(\d{4})(\d{2})(\d{2})RSGA.txt', filename)
                if match:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
                    date = datetime.datetime(year, month, day, 0, 0)
                else:
                    continue
                if not ((date >= self.start_date) and (date < self.end_date)):
                    continue
            try:
                forecasts[filepath] = self.ParseDataFile(filepath)
            except:
                # logging should have been done upstream; just move on
                continue
                
        return forecasts
    # end Proton.ParseAll

# end class Proton
