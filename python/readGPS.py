#!/usr/bin/env python
import math
from numpy.lib import recfunctions as rfn

#=========#
# readGPS #
#=========#

# purpose - simple GPS log reader for the Mt Aspiring College 2024 pilot GNSR project
#
# authors - Delwyn Moller & Brian Pollard
#           dkmoller@restorelab.co.nz
#           bpollard@restorelab.co.nz
#
# date    - v1 release 2024.04.11
#         - v2 release 2024.06.10 - added line 144 that checks for existence of 'prn' in case of a G*RMC with no GPGSV
#
# usage   - within a python interpretor you can obtain an output structure as
#         >>> gps_data = readGPS("./FILENAME.LOG")
#
# license - released freely under the Gnu Public License WITHOUT ANY WARRANTY; without even the implied warranty of
#           MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#           https://www.gnu.org/licenses/gpl-3.0.en.html


#========#
# import #
#========#

import numpy as np
import os

from read_gpgsv import *

#===========#
# constants #
#===========#

# TRUE  = 1
# FALSE = 0
N_PRN = 32

#=========#
# readGPS #
#=========#

def readGPS(Filename, interp=False):
    # -----------#
    # open file #
    # -----------#

    # ----------------#
    # initialisation #
    # ----------------#
    #
    # hour = minute = second = UTC = doy = date = 0
    # new_block = False
    block_count = 0

    # -------------------------------------------------------#
    # create a structure template and array of length N_PRN #
    # -------------------------------------------------------#

    dt = np.dtype(
        [('count', int), ('el', float), ('az', float), ('snr', float), ('utc', float), ('date', int)])
    gps_dt = np.dtype(
        [('hour', int), ('minute', int), ('second', int), ('date', int), ('timestamp', int)]
    )

    gnss_data = [np.array([], dtype=dt) for _ in range(N_PRN)]  # creates a list of null vectors of length N_PRN
    # gps_data = []
    data_to_append = np.zeros(1, dtype=dt)  # structure we will use to append to gps_data

    # ------------------------------------------#
    # step through each line of file           #
    # classify based on three packet types     #
    # populsate our gps_data lists accordingly #
    # ------------------------------------------#

    with open(Filename, 'r') as fid:
        file = fid.read()
        line_feed_count = file.count('\n\n')
        # gps_data = [np.array([], dtype=gps_dt) for _ in range(line_feed_count)]
        gps_data = np.zeros(line_feed_count+1, dtype=gps_dt)
        fid.seek(0)
        for line in fid:
            line = line.rstrip()
            if not line:
                continue
            if line.startswith("$GNGGA") or line.startswith("$GPGGA"):
                new_block = True
                data = line.split(',')
                time_float = float(data[1])
                hour = math.floor(time_float/10000)
                minute = math.floor((time_float - hour * 10000)/100)
                second = round(time_float - math.floor(time_float/100)*100)
                gps_data[block_count]['hour'] = hour
                gps_data[block_count]['minute'] = minute
                gps_data[block_count]['second'] = second

            elif line.startswith("$GPGSV") and new_block:
                gsv = []
                data = line.split(',')
                gsv.append(data)
                num_messages = int(data[1])
                message_number = int(data[2])
                if message_number == 1:
                    while message_number < num_messages:
                        line = fid.readline().rstrip()
                        if line.startswith("$GPGSV"):
                            temp_data = line.split(',')
                            message_number = int(temp_data[2])
                            num_messages = int(temp_data[1])
                            gsv.append(temp_data)
                        else:
                            break

                    prn, elev, az, snr = read_gpgsv(gsv)
                    for jj in range(len(prn)):
                        idx = prn[jj] - 1
                        data_to_append = np.zeros(1, dtype=dt)
                        data_to_append[0]['count'] = block_count
                        data_to_append[0]['el'] = elev[jj]
                        data_to_append[0]['az'] = az[jj]
                        data_to_append[0]['snr'] = snr[jj]
                        data_to_append[0]['utc'] = time_float

                        if gnss_data[idx].size == 0:
                            gnss_data[idx] = data_to_append
                        else:
                            gnss_data[idx] = np.concatenate((gnss_data[idx], data_to_append))

            elif line.startswith("$GNRMC") or line.startswith("$GPRMC"):
                data = line.split(',')
                day = int(data[9][:2])
                month = int(data[9][2:4])
                year = 2000 + int(data[9][4:6])
                date = year * 10000 + month * 100 + day
                gps_data[block_count]['date'] = date
                block_count += 1
                new_block = False


    if interp:
        for prn, data in enumerate(gnss_data, start=1):
            if data.size == 0:
                continue

            # first join in utc and date
            idx = data['count'].astype(int) # get indices to gps_data
            utc_vals = (
                gps_data['hour'][idx] * 3600
                + gps_data['minute'][idx] * 60
                + gps_data['second'][idx]
            )
            # set utc time and date
            data['utc'] = utc_vals
            data['date'] = gps_data['date'][idx]


            el = data['el']
            utc = data['utc']

            # find indices where elevation changes sharply
            ind = np.where(np.abs(np.diff(el)) > 0.1)[0]

            if len(ind) > 10:
                timeshort = utc[ind]
                elv = np.interp(utc, timeshort, el[ind])
                data['el'] = elv  # directly update elevation values

    return gnss_data

# readGPS('../data/240531.LOG', True)

##==================##
## more information ##
##==================##
#
# you can find lists of what is in each of the fields here in the case that you want more information.
#
# GPGGA: https://docs.novatel.com/OEM7/Content/Logs/GPGGA.htm
# GPGSV: https://docs.novatel.com/OEM7/Content/Logs/GPGSV.htm
# GPRMC: https://docs.novatel.com/OEM7/Content/Logs/GPRMC.htm
#
##=================##
## runtime example ##
##=================##
# >>> from readGPS import *
# >>> gps_data = readGPS("190110.LOG")
#
## here "190110.LOG" is the filename
## readGPS returns an array "gps_data" of length 32 corresponding to the PRNs
## we can see the length of each as
#
#>>> for i in range(N_PRN):
#...     print(len(gps_data[i]))
#
## for the filename listed above these ranges are from 0 to ~33000
## if we have matplotlib installed you can make a simple plot of one of the data products of interest:
#
# >>> import matplotlib.pyplot as plt
# >>> plt.plot(gps_data[0]['el'],gps_data[0]['snr'],linestyle='None',marker='o')
# >>> plt.xlabel("elevation")
# >>> plt.ylabel("snr [dB]")
# >>> plt.show()
