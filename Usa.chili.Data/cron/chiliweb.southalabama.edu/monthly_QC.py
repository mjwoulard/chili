# (MJW) I did not include all comments. This is designed for Python 2.7.5 with numpy 1.7 and matplotlib 1.2.0
# Some comments may still be in Python 3 syntax or for more up-to-date versions of modules
# Currently only runs plots for 1 buddy/station pair. This can be modified at the bottom of the code to run all.

# Newer version of Py 2 cuts the time from 177s to 133s (on my laptop, MJW)
# Py 3 speed is 100s on my laptop.

# time used solely for execution-time metric
import time
start_time = time.time()

# Used just for testing. Would need to split code into functions/modules
#import cProfile

# The following import and .use are required on display-less server
#import matplotlib # Needs to be installed
#matplotlib.use('Agg')

from csv import reader as csv
import os
from datetime import datetime
import mysql.connector # Needs to be installed
import matplotlib.pyplot as plt # Needs to be installed
import numpy as np # Needs to be installed

# Directory for plot PNG file output. Currently uses the directory where this script is housed. May not work in all OS.
dir_path = os.path.dirname(__file__)

# MySQL connection parameters
config = {
  'user': 'chilistudent',
  'password': 'chilistudent',
  'host': 'localhost',
  'port': '3306',
  'database': 'chili',
  'raise_on_warnings': True
}

# Create connection and cursor that can accept parameters
cnx = mysql.connector.connect(**config) # Connect
cursor = cnx.cursor(prepared = True)

# Query QC metrics
query = ("SELECT "
            "YEAR(TS), "
            "MONTH(TS), "
            "DAY(TS), "
            "HOUR(TS), "
            "MINUTE(TS), "
            "AirT_2m, "
            "AirT_1pt5m, "
            "AirT_10m, "
            "AirT_9pt5m, "
            "RH_2m, "
            "RH_10m, "
            "Precip_TB3_Tot, "
            "Precip_TX_Tot, "         
            "WndSpd_10m_WVc_2, "
            "WndSpd_2m_WVc_2, "
            "WndSpd_10m_WVc_3, "
            "WndSpd_2m_WVc_3, "
            "Pressure_1, "
            "Pressure_2, "
            "TotalRadn, "
            "QuantRadn, "
            "Temp_C, " # Hydroprobe
            "SoilT_100cm, " # Thermocouple
            "SoilSfcT, "
            "SoilT_5cm, "
            "SoilT_10cm, "
            "SoilT_5cm, "
            "SoilT_50cm, "
            "SoilT_20cm, "
            "WndSpd_Vert, " 
            "WndSpd_10m_WVc_4, "
            "Batt, "
            "ObsInSumm_Tot, "
            "Door, "
            "PTemp "
         "FROM chili.station_data "
         "INNER JOIN chili.station ON chili.station.id = chili.station_data.StationID "
         "WHERE DATE(TS) BETWEEN %s AND LAST_DAY(%s) "
            "AND StationKey = %s "
         "ORDER BY TS;"
        )

# Primary station/Buddy station pairs
stationDict = {'ashford' : 'geneva', 
               'geneva' : 'kinston', 
               'kinston' : 'florala', 
               'florala' : 'andalusia', 
               'andalusia' : 'dixie', 
               'dixie' : 'castleberry', 
               'castleberry' : 'jay', 
               'jay' : 'atmore', 
               'atmore' : 'poarch', 
               'poarch' : 'mtvernon', 
               'mtvernon' : 'leakesville', 
               'leakesville' : 'agricola', 
               'agricola' : 'mobileusaw', 
               'mobileusaw' : 'mobiledr', 
               'mobiledr' : 'grandbay', 
               'grandbay' : 'pascagoula', 
               'pascagoula' : 'gasque', 
               'gasque' : 'foley', 
               'foley' : 'elberta', 
               'elberta' : 'fairhope', 
               'fairhope' : 'robertsdale',
               'robertsdale' : 'loxley', 
               'loxley' : 'bayminette', 
               'bayminette' : 'saraland', 
               'saraland' : 'mobileusaw'}

def main(inputStations):
    StationNames = inputStations # Assigning this to another variable may be superfluous
    PlotMonths = []

    # Calendar
    MonthName = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    DaysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # Get final month for plot (one month prior to when script is run)
    # Comment out and define custom finalMonth for a specific last month.
    if datetime.today().month == 1:
        finalMonth = 12
    else:
        finalMonth = datetime.today().month - 1

    # Create a list of the past 6 month names.
    for i in range(1, 7):
        PlotMonths.append(MonthName[finalMonth - i])
    #print(PlotMonths)

    LeapYears = ['2004', '2008', '2012', '2016', '2020', '2024', '2028', '2032'] # Current leap years. Could be modified to calculate them rather than having to update this list
    
    # Metric names (variable and then a like-sensor to compare against) and commetns describing some variable names
    VariableNames = ['2m Temperature', '10m Temperature', '2m RH', 'TB3 Rainfall', '10m Windspeed', '10m Wind direction', 'Pressure1',
                    'Total Radiation', 'Hydraprobe', 'Surface Temp', '10cm Soil Temp', '50cm Soil Temp', 'Vertical Windspeed']
    VariableComment = ['', '', '', '', '(1-min vector mean)', '(1-min vector mean)', '', '', '1m Soil Temperature',
                    '', 'Thermocouples', 'Thermocouples', '(both parameters indicate turbulence at 10m)']             
    LikeSensorNames = ['1.5m Temperature', '9.5m Temperature', '10m RH', 'TE Rainfall', '2m Windspeed', '2m Wind direction', 'Pressure2',
                    'Quantum Radiation', 'Thermocouple', '5cm Soil Temp', '5cm Soil Temp', '20cm Soil Temp', '10m Wind St.Dev.']

    # Encoding below is for symbols like m/s^2, degrees, exponents, etc.
    VariableUnits = ['$^{o}$C', '$^{o}$C', '%', 'mm', 'ms$^{-1}$', 'degrees', 'mb', 'Wm$^{-2}$', '$^{o}$C', '$^{o}$C', '$^{o}$C', '$^{o}$C', 'ms$^{-1}$']

    # Set y-axis ranges and increments for plotting
    # plot1 and plot3
    MinValues = [-10.0, -10.0,   0.0, 0.0,  0.0,   0, 1000,    0, -5, -10, -5, -5, -4]
    MaxValues = [ 40.0,  40.0, 110.0, 2.5, 15.0, 360, 1040, 2000, 40,  55, 40, 40,  4]
    IncValues = [  5.0,   5.0,  10.0, 0.5,  5.0,  45,   10,  200,  5,   5,  5,  5,  1] # What is Inc? Incoming?

    # plot1 secondary yaxis
    SecMinValues = [-10.0, -10.0,   0.0, 0.0,  0.0,   0, 1000,    0, -5, -10, -5, -5,   0]
    SecMaxValues = [ 40.0,  40.0, 110.0, 2.5, 15.0, 360, 1040, 2000, 40,  55, 40, 40, 100]
    SecIncValues = [  5.0,   5.0,  10.0, 0.5,  5.0,  45,   10,  200,  5,   5,  5,  5,  10]

    # plot2
    MinDiffValues = [-2.0, -2.0, -10.0, -2.5, -5.0, -180, -2, -500, -10, -10, -10, -10, -100]
    MaxDiffValues = [ 2.0,  2.0,  10.0,  2.5,  5.0,  180,  2,  500,  10,  10,  10,  10,   10]
    IncDiffValues = [ 0.5,  0.5,   1.0,  0.5,  1.0,   90,  1,   50,   2,   2,   2,   2,   10]

    # plot3
    MinDiffBuddy = [-4.0, -4.0, -15.0, -2.5, -5.0, -180, -4, -500, -10, -10, -10, -10, -10]
    MaxDiffBuddy = [ 4.0,  4.0,  15.0,  2.5,  5.0,  180,  4,  500,  10,  10,  10,  10,  10]
    IncDiffBuddy = [ 0.5,  0.5,   5.0,  0.5,  1.0,   90,  1,   50,   2,   2,   2,   2,   2]

    # Main station and its buddy makes 2 stations
    stations = 2
    station = 0
    buddy = 1
    
    # Loop over the months.
    for mo in PlotMonths:
        # Calculate the actual number of minutes in this month, allow for leap years. Prepare basic label info.
        if mo in MonthName[0:5]: # Jan through May MUST be in the current year if doing 6 months worth of plots.
            plotyear = str(datetime.today().year)
        else:
            plotyear = str(datetime.today().year - 1)

        monthNum = MonthName.index(mo)
        if monthNum == 1 and (plotyear in LeapYears):
            days = 29
        else:
            days = DaysInMonth[monthNum]
        #print(MonthName[monthNum], plotyear, days)

        delx = 24 * 60 # minutes in a day
        plotmins = days * delx # minutes in a month

        timelabel = ['' for i in range(plotmins)]
        xlabel = ['' for i in range((plotmins // delx) + 1)] # Changed integer division to match Py3 syntax

        # zeroline
        #zeroline = np.full((plotmins), 0.0, dtype = float)
        zeroline = np.zeros(plotmins) # In order to make this work using numpy 1.7
        #print(zeroline)
        #print(zeroline.shape)

        ## Weather Station Data
        # Initialize the full array with NaN to account for missing data

        # Initializations for newer version of numpy
        #Variables = np.full((len(VariableNames), stations, plotmins), np.nan, dtype = float) # This gives a np array with a shape of (for example) 13x2x43200. (large number is minues in month)
                                                                                              # Last dimension size will vary based on what month it is.
        #LikeVars = np.full((len(VariableNames), stations, plotmins), np.nan, dtype = float)
        #BatVolt = np.full((stations, plotmins), np.nan, dtype = float) # 2 x numMinsInMonth
        #DoorOpen = np.full((stations, plotmins), np.nan, dtype = float) # Same
        #Observations = np.full((stations , plotmins), np.nan, dtype = float) # Same
        #PanelTemp = np.full((stations, plotmins), np.nan, dtype = float) # Same

        # Initializations for older version of numpy on dev server without np.full()
        Variables = np.empty((len(VariableNames), stations, plotmins))
        Variables[:] = np.nan
        LikeVars = np.empty((len(VariableNames), stations, plotmins))
        LikeVars[:] = np.nan
        BatVolt = np.empty((stations, plotmins))
        BatVolt[:] = np.nan
        DoorOpen = np.empty((stations, plotmins))
        DoorOpen[:] = np.nan
        Observations = np.empty((stations, plotmins))
        Observations[:] = np.nan
        PanelTemp = np.empty((stations, plotmins))
        PanelTemp[:] = np.nan

        #print(LikeVars.shape)

        batmins = 0
        doormins = 0
        obsmins = 0

        date = mo + plotyear
        #print(date)
        
        # Read in the data for the station and its buddy
        for s in range(len(StationNames)):
            dateVar = plotyear + '-' + '{:02d}'.format(monthNum + 1) + '-' + '01' # Format to use in query
            #print(dateVar)
            params = (dateVar, dateVar, StationNames[s])
            cursor.execute(query, params)
            #print(cursor.statement)

            # Only fetch if rows were returned. Rows may still contain NULL data.
            if cursor.with_rows:
                #print(True)
                result = cursor.fetchall()
                #print(result)
        
            # Convert rows to lists. Perhaps this would be better as numpy arrays?
            for row in range(len(result)):
                result[row] = list(result[row])

            # Replace NULLs, None, etc., with 'nan'.
            for row in result:
                for i in range(len(row)):
                    if row[i] in ('', 'NAN', '"NAN"', 'NULL' ) or row[i] is None: # originally as length = 0
                        row[i] = 'nan' # if field is null, make "nan"
                #print(row)
                # Start storing the data when it coincides with the iMET observing period.  
                year = row[0]
                month = row[1]
                day = row[2]
                hour = row[3]
                minute = row[4]
                index = ((day - 1) * delx) + (hour * 60) + minute # Refers to the particular minute of a month accounting for minutes
                                                                  # that have already been processed.

                # Each variable contains information for each station. s = index of one of the stations that had info pulled
                # index refers to the particular minute of the day being processed
                if (index < plotmins):   
                    timelabel[index] = str(day)
                    # 2m Temperature
                    Variables[0, s, index] = float(row[5]) 
                    # 1.5m Temperature
                    LikeVars[0, s, index] = float(row[6])  
                    # 10m Temperature
                    Variables[1, s, index] = float(row[7]) 
                    # 9.5m Temperature
                    LikeVars[1, s, index] = float(row[8]) 
                    # 2m RH
                    Variables[2, s, index] = float(row[9])
                    # 10m RH            
                    LikeVars[2, s, index] = float(row[10])
                    # TB3 Rainfall
                    Variables[3, s, index] = float(row[11])
                    # TE Rainfall            
                    LikeVars[3, s, index] = float(row[12])
                    # 10m vector mean wind speed over 1 min
                    Variables[4, s, index] = float(row[13])
                    # 2m vector mean wind speed over 1 min          
                    LikeVars[4, s, index] = float(row[14])
                    # 10m vector mean wind direction over 1 min
                    Variables[5, s, index] = float(row[15])
                    # 2m vector mean wind direction over 1 min
                    LikeVars[5, s, index] = float(row[16])
                    # Pressure 1
                    Variables[6, s, index] = float(row[17])
                    # Pressure 2
                    LikeVars[6, s, index] = float(row[18])
                    # Total Radiation
                    Variables[7, s, index] = float(row[19])
                    # Quantum Radiation
                    LikeVars[7, s, index] = float(row[20])
                    # Hydraprobe soil temp at 1m
                    Variables[8, s, index] = float(row[21])
                    # Thermocouple soil temp at 1m
                    LikeVars[8, s, index] = float(row[22])  
                    # Soil surface temp
                    Variables[9, s, index] = float(row[23])
                    # Soil Temp at 5 cm
                    LikeVars[9, s, index] = float(row[24])               
                    # Soil Temp at 10 cm
                    Variables[10, s, index] = float(row[25])
                    # Soil Temp at 5 cm
                    LikeVars[10, s, index] = float(row[26])      
                    # Soil Temp at 50 cm
                    Variables[11, s, index] = float(row[27])
                    # Soil Temp at 20 cm
                    LikeVars[11, s, index] = float(row[28]) 
                    # Verical Wind speed at 10m
                    Variables[12, s, index] = float(row[29])
                    # 10m Horizontal wind speed standard deviation - subtract maximum axis value to line up the 2 variables.
                    LikeVars[12, s, index] = float(row[30])                                              
                    # Battery voltage
                    BatVolt[s, index] = float(row[31])
                    if (s == 0 and BatVolt[s, index] < 12.0):
                        batmins += 1
                    # Number of obs per minute
                    Observations[s, index] = float(row[32])
                    if (s == 0 and Observations[s, index] < 10.0):
                        obsmins += 1
                    # Door Open indicator
                    DoorOpen[s, index] = float(row[33])
                    if (s == 0 and DoorOpen[s, index] == 1.0):
                        doormins += 1
                    # Data logger panel temperature
                    PanelTemp[s, index] = float(row[34])
                
            # To test if data is being readin correctly
            #for station in Variables[0]:
            #    for reading in station:
            #        if not np.isnan(reading):
            #            print(reading)

        #print(PanelTemp[station,0])\

        # Get differences between variable and like-sensor metrics
        Diff = Variables - LikeVars

        # For older version of numpy where if nansum, etc. not available:
        # Creates a mask over np.nan, carries out operation, then refills True ('np.nan') values with np.nan
        meanvar = np.mean(np.ma.masked_array(Variables, np.isnan(Variables)), axis = 2)
        meanvar = np.ma.filled(meanvar, fill_value = np.nan)
        sumvar = np.sum(np.ma.masked_array(Variables, np.isnan(Variables)), axis = 2)
        sumvar = np.ma.filled(sumvar, fill_value = np.nan)
        minvar = np.min(np.ma.masked_array(Variables, np.isnan(Variables)), axis = 2)
        minvar = np.ma.filled(minvar, fill_value = np.nan)
        maxvar = np.max(np.ma.masked_array(Variables, np.isnan(Variables)), axis = 2)
        maxvar = np.ma.filled(maxvar, fill_value = np.nan)
        stdvar = np.std(np.ma.masked_array(Variables, np.isnan(Variables)), axis = 2)
        stdvar = np.ma.filled(stdvar, fill_value = np.nan)

        # For older version of numpy where if nansum, etc. not available:
        # Creates a mask over np.nan, carries out operation, then refills True ('np.nan') values with np.nan
        meandiff = np.mean(np.ma.masked_array(Diff, np.isnan(Diff)), axis = 2)
        meandiff = np.ma.filled(meandiff, fill_value = np.nan)
        mindiff = np.min(np.ma.masked_array(Diff, np.isnan(Diff)), axis = 2)
        mindiff = np.ma.filled(mindiff, fill_value = np.nan)
        maxdiff = np.max(np.ma.masked_array(Diff, np.isnan(Diff)), axis = 2)
        maxdiff = np.ma.filled(maxdiff, fill_value = np.nan)
        stddiff = np.std(np.ma.masked_array(Diff, np.isnan(Diff)), axis = 2)
        stddiff = np.ma.filled(stddiff, fill_value = np.nan)

        ## The plot creation and printing section of the program. This could be a logical place to split the program.
        ## Much of this could probably be defined as classes in order to reduce duplicate coding.
        ## For instance, many plots have the same base property values and could be created from a template class
        print('Plots for ' + date)  # Needs to be converted to Py 2 syntax for better output.
        print('==================')
            
        for var in range(len(VariableNames)):
            #print(VariableNames[var])
            #print(Variables[var,station])
            
            print ('Plotting ' + VariableNames[var])  # Conver to Py 2 syntax for better output

            ## Get axes statistics

            # Will show warnings if entire fields are NULL in data. Can probably be surpressed.
            # Below is for more up-to-date versions of numpy
            #meanvar = np.nanmean(Variables, axis=2) # Compute mean along axis, ignoring nans            
            #sumvar = np.nansum(Variables, axis=2) # Compute sum along axis, ignore nans
            #minvar = np.nanmin(Variables, axis=2) # Compute minimum along axis, ignore nans
            #maxvar = np.nanmax(Variables, axis=2) # Compute max along axis, ignore nans
            #stdvar = np.nanstd(Variables, axis=2) # Compute standard deviation along axis, ignore nans

            # I don't think this needs to happen for each and every variable loop. Original position
            # For older version of numpy where if nansum, etc. not available:
            # Creates a mask over np.nan, carries out operation, then refills True ('np.nan') values with np.nan
            #meanvar = np.mean(np.ma.masked_array(Variables, np.isnan(Variables)), axis = 2)
            #meanvar = np.ma.filled(meanvar, fill_value = np.nan)
            #sumvar = np.sum(np.ma.masked_array(Variables, np.isnan(Variables)), axis = 2)
            #sumvar = np.ma.filled(sumvar, fill_value = np.nan)
            #minvar = np.min(np.ma.masked_array(Variables, np.isnan(Variables)), axis = 2)
            #minvar = np.ma.filled(minvar, fill_value = np.nan)
            #maxvar = np.max(np.ma.masked_array(Variables, np.isnan(Variables)), axis = 2)
            #maxvar = np.ma.filled(maxvar, fill_value = np.nan)
            #stdvar = np.std(np.ma.masked_array(Variables, np.isnan(Variables)), axis = 2)
            #stdvar = np.ma.filled(stdvar, fill_value = np.nan)
            
            # I don't think below is required to happen for each and every variable. Original position
            # Get differences between variable and like-sensor metrics
            #Diff = Variables - LikeVars

            # Will show warnings if entire fields are NULL in data
            # For newer versions of numpy
            #meandiff = np.nanmean(Diff, axis = 2)
            #mindiff = np.nanmin(Diff, axis = 2)
            #maxdiff = np.nanmax(Diff, axis = 2)     
            #stddiff = np.nanstd(Diff, axis = 2) # unused?

            # I don't think this needs to happen for every variable loop. Original position.
            # For older version of numpy where if nansum, etc. not available:
            # Creates a mask over np.nan, carries out operation, then refills True ('np.nan') values with np.nan
            #meandiff = np.mean(np.ma.masked_array(Diff, np.isnan(Diff)), axis = 2)
            #meandiff = np.ma.filled(meandiff, fill_value = np.nan)
            #mindiff = np.min(np.ma.masked_array(Diff, np.isnan(Diff)), axis = 2)
            #mindiff = np.ma.filled(mindiff, fill_value = np.nan)
            #maxdiff = np.max(np.ma.masked_array(Diff, np.isnan(Diff)), axis = 2)
            #maxdiff = np.ma.filled(maxdiff, fill_value = np.nan)
            #stddiff = np.std(np.ma.masked_array(Diff, np.isnan(Diff)), axis = 2)
            #stddiff = np.ma.filled(stddiff, fill_value = np.nan)
            
            missing = 0 # Used to keep count of missing readings

            # Find number of missing minutes (data entries)
            for index in range(plotmins):
                if np.isnan(Variables[var, station, index]):
                    missing += 1

            #print(missing)
            #print(plotmins)

            misspercent = (float(missing) / plotmins) * 100 # Need to convert one or both to floats in Python2. 
            #print(misspercent)

            # Start figure/plot creation
            figure1 = plt.figure(figsize = (25, 20))

            # Add some space between the panels on the plot
            figure1.subplots_adjust(hspace=0.5)

            # Add subplots
            plot1 = figure1.add_subplot(4,1,1)
            plot2 = figure1.add_subplot(4,1,2)
            plot3 = figure1.add_subplot(4,1,3)
            plot4 = figure1.add_subplot(4,1,4)

            # Plot variable and like-sensor for station
            # This works because order of Variables and VariableNames matches. Assignment of variables from DB pull need to match.
            # The order of VariableUnits also relies on the above. Assignment of variables from DB pull need to match.
            # LikeVariableNames follow the same rules. Order matters.
            if (VariableNames[var] == '10m Wind direction'): 
                plot1.scatter(range(plotmins), Variables[var,station], linewidth = 0, marker = '.', 
                    color = 'royalblue', label = '%s %s' % (VariableNames[var], StationNames[station]))      
                # alpha makes the line transparent; a smaller value is more transparent
                # plot1.scatter(range(plotmins), LikeVars[var,station], linewidth=0, marker='.', color='red', alpha=0.4, label='%s %s' %(LikeSensorNames[var],StationNames[station]))
            else:
                plot1.plot(range(plotmins), Variables[var,station], linewidth = 2, color = 'royalblue', 
                    label = '%s %s' % (VariableNames[var], StationNames[station]))      
                # alpha makes the line transparent; a smaller value is more transparent
                # plot1.twinx().plot(range(plotmins), LikeVars[var,station], linewidth=1.2, linestyle='--', color='red', alpha=0.4, label='%s %s' %(LikeSensorNames[var],StationNames[station]))

            # 'pad' is the padding space between the tick marks and the number, 'direction' determines which way the tick marks point, 'size' sets the length of the tick marks
            plot1.set_xlim([0, plotmins])

            # Set time (x) axis increment in minutes
            plot1.tick_params(axis = 'x', colors = 'black', direction = 'out', pad = 0, size = 10)

            # Minor tick marks
            #plot1.minorticks_on()

            #plot1.xaxis.set_minor_locator(MultipleLocator(60*12))
            plot1.set_xticks(np.linspace(0, plotmins, (plotmins // delx) + 1)) # Changed integer division syntax to work with Py3
            for i in range((plotmins // delx)): # Changed integer division syntax to work with Py3
                xlabel[i] = timelabel[i * delx]
            plot1.set_xticklabels(xlabel, rotation = 90, ha = 'center', fontsize = 14)

            #Set ticks and labels on primary y-axis
            plot1.set_ylim(MinValues[var], MaxValues[var])
            plot1.set_yticks(np.arange(MinValues[var], MaxValues[var] + 0.1, IncValues[var]))
            plot1.set_ylabel(r"%s (%s)" % (VariableNames[var], VariableUnits[var]), fontsize = 14, color = 'royalblue')

            # Make the y labels bigger.
            for label in plot1.get_yticklabels():
                label.set_color('royalblue')
                label.set_size(14)

            # Add title, grid, legend etc.
            # transform=plot1.transAxes makes the x and y coordinates run from 0 to 1 with (0,0) being the lower left and (1,1) the upper left corner of the plot panel.
            plot1.text(0, 1.5, "Station: %s     Buddy: %s     Date: %s " % (StationNames[station], StationNames[buddy], date), 
                transform = plot1.transAxes, fontsize = 28, fontweight = 'bold')
            plot1.text(0, 1.3, "Variable: %s %s" % (VariableNames[var], VariableComment[var]), 
                transform = plot1.transAxes, fontsize = 28, fontweight = 'bold')
            if(VariableNames[var] == 'TB3 Rainfall'):
                plot1.text(0, 1.1, "Total = %5.2f %s" % (sumvar[var, station], VariableUnits[var]), 
                    transform = plot1.transAxes, horizontalalignment = 'left', fontsize = 22, fontweight = 'bold')
            else:
                plot1.text(0, 1.1, "Mean = %5.2f %s" % (meanvar[var, station], VariableUnits[var]), 
                    transform = plot1.transAxes, horizontalalignment = 'left', fontsize = 22, fontweight ='bold')

            # minvalue=minvar[var,station]
            plot1.text(0.25, 1.1, "Minimum = %5.2f %s" % (minvar[var, station], VariableUnits[var]), 
                transform = plot1.transAxes, horizontalalignment = 'left', fontsize = 22, fontweight = 'bold')
            # maxvalue=maxvar[var,station]
            plot1.text(0.5, 1.1, "Maximum = %5.2f %s" % (maxvar[var, station], VariableUnits[var]), 
                transform = plot1.transAxes, horizontalalignment = 'left', fontsize = 22, fontweight = 'bold')
            # tsdvalue=stdvar[var,station]
            plot1.text(0.75, 1.1, "St. Deviation = %5.2f %s" % (stdvar[var, station], VariableUnits[var]), 
                transform = plot1.transAxes, horizontalalignment = 'left', fontsize = 22, fontweight = 'bold')
            unit = "%"
            plot1.text(0.75, 1.5, "Missing minutes = %6i (%6.2f %s)" % (missing, misspercent, unit), 
                transform = plot1.transAxes, horizontalalignment = 'left', fontsize = 22, fontweight = 'bold')
                        
            plot1.grid(which = 'major', axis = 'both', color = 'LightGrey', linestyle = 'dotted')
            plot1.grid(which = 'minor', axis = 'x', color = 'LightGrey', linestyle = 'dotted')

            ## Secondary y-axis for like-sensor
            plot5 = plot1.twinx()
            if (VariableNames[var] == '10m Wind direction'):
                plot5.scatter(range(plotmins), LikeVars[var, station], linewidth = 0, marker = '.', color = 'red', 
                    alpha = 0.3, label = '%s %s' % (LikeSensorNames[var],StationNames[station]))
            else:
                plot5.plot(range(plotmins), LikeVars[var, station], linewidth = 1.2, linestyle = '--', color = 'red', 
                    alpha = 0.4, label = '%s %s' % (LikeSensorNames[var],StationNames[station]))
            plot5.set_xlim([0,plotmins])

            # Set Secondary axis y labels and tick marks.
            plot5.set_ylim(SecMinValues[var], SecMaxValues[var])
            plot5.set_yticks(np.arange(SecMinValues[var], SecMaxValues[var] + 0.1, SecIncValues[var]))
            for label in plot5.get_yticklabels():
                label.set_color('red')
                label.set_size(14)
            # plot1.twinx().set_ylabel(r"%s %s" %(VariableNames[var],VariableUnits[var]),fontsize = 14, color ='red')
            # plot1.twinx().get_yaxis().get_major_formatter().set_useOffset(False)
            
            # Draw legends
            # ncol alows you to place the legend labels side by side; set it to n if you have n labels, so it creates n columns for you.
            # bbox_to_anchor allows you to place the legend relative to the plot area with the first number being the x dimension and the second the y dimensions, 
            # x and y values ranging from 0 to 1 define the plot area with bottom left being (0,0) and top right (1,1).
            # Throughout, legend and frame coding was changed because the API is different for the version of matplotlib on the server
            # The original code has been left in, just commented out.

            #plot5.legend(loc = 2, ncol = 1, fontsize = 14, framealpha = 1.0, bbox_to_anchor = (0.8, 1.04))
            #plot1.legend(loc = 2, ncol = 1, fontsize = 14, framealpha = 1.0, bbox_to_anchor = (0.4, 1.04))
            legend5 = plot5.legend(loc = 2, ncol = 1, fontsize = 14, bbox_to_anchor = (0.8, 1.04))
            frame5 = legend5.get_frame()
            frame5.set_alpha(1.0) # May need to be '1.0' for older module?
            legend1 = plot1.legend(loc = 2, ncol = 1, fontsize = 14, bbox_to_anchor = (0.8, 1.04))
            frame1 = legend1.get_frame()
            frame1.set_alpha(1.0)

            # Plot difference between variable and like-sensor for station
            if (VariableNames[var] == '10m Wind direction'):
                plot2.scatter(range(plotmins), Variables[var, station] - LikeVars[var, station], 
                    linewidth = 0.0, marker = '.', color = 'royalblue', label = '%s-%s %s' % (VariableNames[var], LikeSensorNames[var], StationNames[station]))      
            else:
                plot2.plot(range(plotmins), Variables[var, station] - LikeVars[var, station], 
                    linewidth = 1.2, color = 'royalblue', label = '%s-%s %s' % (VariableNames[var], LikeSensorNames[var], StationNames[station]))

            plot2.plot(range(plotmins), zeroline, linewidth = 1.0, color = 'black')     
            plot2.set_xlim([0, plotmins])

            # Set time (x) axis increment in minutes
            plot2.tick_params(axis = 'x', colors = 'black', direction = 'out', pad = 0, size = 10)

            # Minor tick marks
            #plot2.minorticks_on()
            #plot2.xaxis.set_minor_locator(MultipleLocator(60*12))
            plot2.set_xticks(np.linspace(0, plotmins, (plotmins // delx) + 1)) # Changed integer division syntax to work with Py3
            for i in range((plotmins // delx)): # Changed integer division syntax to work with Py3
                xlabel[i] = timelabel[i * delx]

            plot2.set_xticklabels(xlabel, rotation = 90, ha = 'center', fontsize = 14)
            #plot2.set_xlabel("Midnight/Day of the month", fontsize= 14)
            plot2.set_ylim(MinDiffValues[var], MaxDiffValues[var])
            plot2.set_yticks(np.arange(MinDiffValues[var], MaxDiffValues[var] + 0.1, IncDiffValues[var]))
            plot2.set_ylabel(r"%s (%s)" % (VariableNames[var], VariableUnits[var]), fontsize = 14, color = 'black')

            # Make the y labels bigger and blue.
            for label in plot1.get_yticklabels():
                label.set_size(14)
                label.set_color('black')

            #plot2.text(-60,MaxDiffValues[var]+IncDiffValues[var],"Station: %s   Buddy: %s   Date: %s" % (StationNames[station],StationNames[buddy],date),fontsize=22,fontweight='bold')
            plot2.grid(which = 'major', axis = 'both', color = 'LightGrey', linestyle = 'dotted')
            plot2.grid(which = 'minor', axis = 'x', color = 'LightGrey', linestyle = 'dotted')
            #plot2.legend(loc = 2, fontsize = 14, framealpha = 1.0, bbox_to_anchor = (0.4, 1.08))
            legend2 = plot2.legend(loc = 2, fontsize = 14, bbox_to_anchor = (0.4, 1.08))
            frame2 = legend2.get_frame()
            frame2.set_alpha(1.0)
            plot2.text(0, 1.1 ,"MeanDiff = %5.2f %s" % (meandiff[var, station],VariableUnits[var]), 
                transform = plot2.transAxes, horizontalalignment = 'left', fontsize = 22, fontweight = 'bold')
            plot2.text(0.25, 1.1, "MinDiff = %5.2f %s" % (mindiff[var, station],VariableUnits[var]), 
                transform = plot2.transAxes, horizontalalignment = 'left', fontsize = 22, fontweight = 'bold')
            plot2.text(0.5, 1.1, "MaxDiff = %5.2f %s" % (maxdiff[var, station],VariableUnits[var]), 
                transform = plot2.transAxes, horizontalalignment = 'left', fontsize = 22, fontweight = 'bold')             
            plot2.text(0.75, 1.1, "StDevDiff = %5.2f %s" % (stddiff[var, station],VariableUnits[var]), 
                transform = plot2.transAxes, horizontalalignment = 'left', fontsize = 22, fontweight = 'bold')

            # Plot variable for station and buddy 
            if (VariableNames[var] == '10m Wind direction'):
                # Should 'royalblue' be 'RoyalBlue' or 'SeaGreen' be 'seagreen'?
                plot3.scatter(range(plotmins), Variables[var, station], linewidth = 0, marker = '.', color = 'royalblue', 
                    label = '%s %s' % (VariableNames[var], StationNames[station]))      
                plot3.scatter(range(plotmins), Variables[var, buddy], linewidth = 0, marker = '.', color = 'SeaGreen', 
                    alpha = 0.3, label = '%s %s' % (VariableNames[var], StationNames[buddy]))  
            else:
                plot3.plot(range(plotmins), Variables[var, station], linewidth = 2, color = 'royalblue', 
                    label = '%s %s' % (VariableNames[var], StationNames[station]))      
                plot3.plot(range(plotmins), Variables[var, buddy], linewidth = 2, linestyle = '--', color = 'SeaGreen', 
                    alpha = 0.4, label = '%s %s' % (VariableNames[var], StationNames[buddy]))

            # 'pad' is the padding space between the tick marks and the number, 'direction' determines which way the tick marks point, 'size' sets the length of the tick marks
            plot3.set_xlim([0, plotmins])

            # Set time (x) axis increment in minutes
            plot3.tick_params(axis = 'x', colors = 'black', direction = 'out', pad = 0, size = 10)

            # Minor tick marks
            #plot3.minorticks_on()
            #plot3.xaxis.set_minor_locator(MultipleLocator(60*12))
            plot3.set_xticks(np.linspace(0, plotmins, (plotmins // delx) + 1)) # Changed integer division syntax to work with Py3
            for i in range((plotmins // delx)): # Changed integer division syntax to work with Py3
                xlabel[i] = timelabel[i * delx]

            plot3.set_xticklabels(xlabel, rotation = 90, ha = 'center', fontsize = 14)
            #plot3.set_xlabel("Midnight/Day of the month", fontsize= 14)
            plot3.set_ylim(MinValues[var], MaxValues[var])
            plot3.set_yticks(np.arange(MinValues[var], MaxValues[var] + 0.1, IncValues[var]))
            plot3.set_ylabel(r"%s (%s)" % (VariableNames[var], VariableUnits[var]), fontsize = 14, color = 'black')

            # Make the y labels bigger.
            for label in plot3.get_yticklabels():
                label.set_size(14)
                label.set_color('black')

            plot3.grid(which = 'major', axis = 'both', color = 'LightGrey', linestyle = 'dotted')
            plot3.grid(which = 'minor', axis = 'x', color = 'LightGrey', linestyle = 'dotted')
            # ncol alows you to place the legend labels side by side; set it to n if you have n labels, so it creates n columns for you.
            #plot3.legend(loc = 2, ncol = 2, fontsize = 14, framealpha = 1.0, bbox_to_anchor = (0.4, 1.08))
            legend3 = plot3.legend(loc = 2, ncol = 2, fontsize = 14, bbox_to_anchor = (0.4, 1.08))
            frame3 = legend3.get_frame()
            frame3.set_alpha(1.0)

            # Plot variable difference between buddies.
            if (VariableNames[var] == '10m Wind direction'):
                plot4.scatter(range(plotmins), Variables[var, station] - Variables[var, buddy], linewidth = 0, marker = '.', color = 'seagreen', 
                    label = '%s %s - %s %s' % (VariableNames[var], StationNames[station], VariableNames[var], StationNames[buddy]))      
            else:
                plot4.plot(range(plotmins), Variables[var, station] - Variables[var, buddy], linewidth = 1.2, color = 'seagreen', 
                    label = '%s %s - %s %s' % (VariableNames[var], StationNames[station], VariableNames[var], StationNames[buddy]))      
            plot4.plot(range(plotmins), zeroline, linewidth = 1.0, color = 'black')    

            # 'pad' is the padding space between the tick marks and the number, 'direction' determines which way the tick marks point, 'size' sets the length of the tick marks
            plot4.set_xlim([0, plotmins])

            # Set time (x) axis increment in minutes
            plot4.tick_params(axis = 'x', colors = 'black', direction = 'out', pad = 0, size = 10)

            # Minor tick marks
            #plot4.minorticks_on()
            #plot4.xaxis.set_minor_locator(MultipleLocator(60*12))
            plot4.set_xticks(np.linspace(0, plotmins, (plotmins // delx) + 1)) # Changed integer division syntax to work with Py3
            for i in range((plotmins // delx)): # Changed integer division syntax to work with Py3
                xlabel[i] = timelabel[i * delx]

            plot4.set_xticklabels(xlabel, rotation = 90, ha = 'center', fontsize = 14)
            plot4.set_xlabel("Midnight/Day of the month", fontsize = 14)

            plot4.set_ylim(MinDiffBuddy[var], MaxDiffBuddy[var])
            plot4.set_yticks(np.arange(MinDiffBuddy[var], MaxDiffBuddy[var] + 0.1, IncDiffBuddy[var]))
            plot4.set_ylabel(r"%s (%s)" % (VariableNames[var], VariableUnits[var]), fontsize = 14, color = 'black')

            # Make the y labels bigger and blue.
            for label in plot1.get_yticklabels():
                label.set_size(14)
                label.set_color('black')

            #plot4.text(-60,MaxDiffValues[var]+IncDiffValues[var],"Station: %s   Buddy: %s   Date: %s" % (StationNames[station],StationNames[buddy],date),fontsize=22,fontweight='bold')
            plot4.grid(which = 'major', axis = 'both', color = 'LightGrey', linestyle = 'dotted')
            plot4.grid(which = 'minor', axis = 'x', color = 'LightGrey', linestyle = 'dotted')
            #plot4.legend(loc = 2, fontsize = 14, framealpha = 1.0, bbox_to_anchor = (0.4, 1.08))
            legend4 = plot4.legend(loc = 2, fontsize = 14, bbox_to_anchor = (0.4, 1.08))
            frame4 = legend4.get_frame()
            frame4.set_alpha(1.0)

            ### Write the plot to a file 
            #Variable = '2mTemperature' # I'm unsure what this was for as the variable was never used.
            # Added dir_path and the forward-slash to save files to current working directory. Windows may need to flip the slash?
            figure1.savefig(dir_path + "/plots/1moQCplot-%s-%s-%s.png" % (StationNames[station], VariableNames[var], date), format='png')
            plt.close(figure1)

        # Plot DL Status parameters
        print('Plotting Status Parameters\n')

        figure1 = plt.figure(figsize = (25, 16))
        plot1 = figure1.add_subplot(4, 1, 1)
        plot2 = figure1.add_subplot(4, 1, 2)
        plot3 = figure1.add_subplot(4, 1, 3)
        plot4 = figure1.add_subplot(4, 1, 4)
            
        minrange = 10
        maxrange = 14
        incrange = 1 # What is incrange?

        plot1.plot(range(plotmins), BatVolt[station], linewidth = 2, color = 'royalblue', label = 'Battery Voltage')      
        plot1.set_xlim([0, plotmins])
        # Set time (x) axis increment in minutes
        plot1.tick_params(axis = 'x', colors = 'black', direction = 'out', pad = 0, size = 10)
        plot1.set_xticks(np.linspace(0, plotmins, (plotmins // delx) + 1)) # Changed integer division syntax to work with Py3
        for i in range((plotmins // delx)): # Changed integer division syntax to work with Py3
            xlabel[i] = timelabel[i * delx]

        plot1.set_xticklabels(xlabel, rotation = 90, ha = 'center', fontsize = 14)
        #plot1.set_xlabel("Midnight/Day of the month", fontsize= 14)

        plot1.set_ylim(minrange, maxrange)
        plot1.set_yticks(np.arange(minrange, maxrange + 0.1, incrange))
        plot1.set_ylabel(r"Battery Voltage (V)",fontsize = 14, color = 'black')

        # Make the y labels bigger.
        for label in plot1.get_yticklabels():
            label.set_size(14)
            label.set_color('black')

        plot1.text(-60, maxrange + incrange, "Station: %s     Date: %s     Status Parameters" % (StationNames[station], date), 
            fontsize = 22,fontweight = 'bold')
        plot1.grid(which = 'major', axis = 'both', color = 'LightGrey', linestyle = 'dotted')
        plot1.grid(which = 'minor', axis = 'x', color = 'LightGrey', linestyle = 'dotted')
        # ncol alows you to place the legend labels side by side; set it to n if you have n labels, so it creates n columns for you.
        # bbox_to_anchor allows you to place the legend relative to the plot area with the first number being the x dimension and the second the y dimensions, 
        # x and y values ranging from 0 to 1 define the plot area with bottom left being (0,0) and top right (1,1).

        #plot1.legend(loc = 2, ncol = 2, fontsize = 14, framealpha = 1.0, bbox_to_anchor = (0.4, 1.08))
        legend1 = plot1.legend(loc = 2, ncol = 2, fontsize = 14, bbox_to_anchor = (0.4, 1.08))
        frame1 = legend1.get_frame()
        frame1.set_alpha(1.0)
        unit = "%"
        plot1.text(0.75, 1.5, "Missing minutes = %6i (%6.2f %s)" % (missing,misspercent,unit), 
            transform = plot1.transAxes, horizontalalignment = 'left', fontsize = 22, fontweight = 'bold')
        plot1.text(0.01, 0.9, "Number of minutes below 12V = %6i " % (batmins), 
            transform = plot1.transAxes, horizontalalignment = 'left', fontsize = 22)

        minrange = -1
        maxrange = 2
        incrange = 1

        plot2.plot(range(plotmins), DoorOpen[station], linewidth = 2, color = 'red', label = 'Door Open')      
        plot2.set_xlim([0, plotmins])

        # Set time (x) axis increment in minutes
        plot2.tick_params(axis = 'x', colors = 'black', direction = 'out', pad = 0, size = 10)
        plot2.set_xticks(np.linspace(0, plotmins, (plotmins // delx) + 1)) # Changed integer division syntax to work with Py3
        for i in range((plotmins // delx)): # Changed integer division syntax to work with Py3
            xlabel[i] = timelabel[i * delx]

        plot2.set_xticklabels(xlabel, rotation = 90, ha = 'center', fontsize = 14)
        #plot2.set_xlabel("Midnight/Day of the month", fontsize= 14)

        plot2.set_ylim(minrange, maxrange)
        plot2.set_yticks(np.arange(minrange, maxrange + 0.1, incrange))
        plot2.set_ylabel(r"Door Open",fontsize = 14, color = 'black')

        # Make the y labels bigger.
        for label in plot2.get_yticklabels():
            label.set_size(14)
            label.set_color('black')

        plot2.grid(which = 'major', axis = 'both', color = 'LightGrey', linestyle = 'dotted')
        plot2.grid(which = 'minor', axis = 'x', color = 'LightGrey', linestyle = 'dotted')
        # ncol alows you to place the legend labels side by side; set it to n if you have n labels, so it creates n columns for you.
        # bbox_to_anchor allows you to place the legend relative to the plot area with the first number being the x dimension and the second the y dimensions, 
        # x and y values ranging from 0 to 1 define the plot area with bottom left being (0,0) and top right (1,1).

        #plot2.legend(loc = 2, ncol = 2, fontsize = 14, framealpha = 1.0, bbox_to_anchor = (0.4, 1.08))
        legend2 = plot2.legend(loc = 2, ncol = 2, fontsize = 14, bbox_to_anchor = (0.4, 1.08))
        frame2 = legend2.get_frame()
        frame2.set_alpha(1.0)
        plot2.text(0.01, 0.9, "Number of minutes with door open = %6i " % (doormins), 
            transform = plot2.transAxes, horizontalalignment = 'left', fontsize = 22)
        
        minrange = 0
        maxrange = 30
        incrange = 5
        plot3.plot(range(plotmins), Observations[station], linewidth = 2, color = 'seagreen', label = 'Observations in Minute')      
        plot3.set_xlim([0, plotmins])

        # Set time (x) axis increment in minutes
        plot3.tick_params(axis = 'x', colors = 'black', direction = 'out', pad = 0, size = 10)
        plot3.set_xticks(np.linspace(0, plotmins, (plotmins // delx) + 1)) # Changed integer division syntax to work with Py3
        for i in range((plotmins // delx)): # Changed integer division syntax to work with Py3
            xlabel[i] = timelabel[i * delx]

        plot3.set_xticklabels(xlabel, rotation = 90, ha = 'center', fontsize = 14)
        #plot3.set_xlabel("Midnight/Day of the month", fontsize= 14)

        plot3.set_ylim(minrange, maxrange)
        plot3.set_yticks(np.arange(minrange, maxrange + 0.1, incrange))
        plot3.set_ylabel(r"Observations", fontsize = 14, color = 'black')

        # Make the y labels bigger.
        for label in plot3.get_yticklabels():
            label.set_size(14)
            label.set_color('black')

        plot3.grid(which = 'major', axis = 'both', color = 'LightGrey', linestyle = 'dotted')
        plot3.grid(which = 'minor', axis = 'x', color = 'LightGrey', linestyle = 'dotted')
        # ncol alows you to place the legend labels side by side; set it to n if you have n labels, so it creates n columns for you.
        # bbox_to_anchor allows you to place the legend relative to the plot area with the first number being the x dimension and the second the y dimensions, 
        # x and y values ranging from 0 to 1 define the plot area with bottom left being (0,0) and top right (1,1).

        #plot3.legend(loc = 2, ncol = 2, fontsize = 14, framealpha = 1.0, bbox_to_anchor = (0.4, 1.08))
        legend3 = plot3.legend(loc = 2, ncol = 2, fontsize = 14, bbox_to_anchor = (0.4, 1.08))
        frame3 = legend3.get_frame()
        frame3.set_alpha(1.0)
        plot3.text(0.01, 0.9, "Number of minutes with less than 10 obs = %6i " % (obsmins), 
            transform = plot3.transAxes, horizontalalignment = 'left', fontsize = 22)

        minrange = -10
        maxrange = 45
        incrange = 5
        
        plot4.plot(range(plotmins), PanelTemp[station], linewidth = 2, color = 'indigo', label = 'Panel Temperature')      
        plot4.set_xlim([0, plotmins])

        # Set time (x) axis increment in minutes
        plot4.tick_params(axis = 'x', colors = 'black', direction = 'out', pad = 0, size = 10)
        plot4.set_xticks(np.linspace(0, plotmins, (plotmins // delx) + 1)) # Changed integer division syntax to work with Py3
        for i in range((plotmins // delx)): # Changed integer division syntax to work with Py3
            xlabel[i] = timelabel[i * delx]

        plot4.set_xticklabels(xlabel, rotation = 90, ha = 'center', fontsize = 14)
        #plot4.set_xlabel("Midnight/Day of the month", fontsize= 14)

        plot4.set_ylim(minrange, maxrange)
        plot4.set_yticks(np.arange(minrange, maxrange + 0.1, incrange))
        plot4.set_ylabel(r"Temperature ($^{o}$C)", fontsize = 14, color = 'black')

        # Make the y labels bigger.
        for label in plot4.get_yticklabels():
            label.set_size(14)
            label.set_color('black')

        plot4.grid(which = 'major', axis = 'both', color = 'LightGrey', linestyle = 'dotted')
        plot4.grid(which = 'minor', axis = 'x', color = 'LightGrey', linestyle = 'dotted')
        # ncol alows you to place the legend labels side by side; set it to n if you have n labels, so it creates n columns for you.
        # bbox_to_anchor allows you to place the legend relative to the plot area with the first number being the x dimension and the second the y dimensions, 
        # x and y values ranging from 0 to 1 define the plot area with bottom left being (0,0) and top right (1,1).

        #plot4.legend(loc = 2, ncol = 2, fontsize = 14, framealpha = 1.0, bbox_to_anchor = (0.4, 1.08))
        legend4 = plot4.legend(loc = 2, ncol = 2, fontsize = 14, bbox_to_anchor = (0.4, 1.08))
        frame4 = legend4.get_frame()
        frame4.set_alpha(1.0)
        # Plot4 doesn't have text? Should probably be something about panel temperature.
        
        figure1.savefig(dir_path + "/plots/1moQCplot-%s-StatusParameters-%s.png" % (StationNames[station], date), format='png') #format kw is redundant but used for testing
        plt.close(figure1)

# Uncomment to run on all station/buddy pairs.
#for k,v in stationDict.items():   
#    main([k, v])

# Comment out if running all station/buddy pairs.
main(['agricola', 'mobileusaw'])

cursor.close()
cnx.close()

elapsed_time = time.time() - start_time
print('Execution time: ' + str(elapsed_time))