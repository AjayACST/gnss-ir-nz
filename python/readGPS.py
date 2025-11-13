#!/usr/bin/env python

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

TRUE  = 1
FALSE = 0
N_PRN = 32

#=========#
# readGPS #
#=========#

def readGPS(Filename, interp=False):
    # -----------#
    # open file #
    # -----------#

    fid = open(Filename, 'r')

    # ----------------#
    # initialisation #
    # ----------------#

    hour = minute = second = UTC = doy = date = 0
    newblock = FALSE
    block_count = 0

    # -------------------------------------------------------#
    # create a structure template and array of length N_PRN #
    # -------------------------------------------------------#

    dt = np.dtype(
        [('count', int), ('time', float), ('el', float), ('az', float), ('snr', float), ('utc', float), ('date', int)])

    gps_data = [np.array([], dtype=dt) for _ in range(N_PRN)]  # creates a list of null vectors of length N_PRN
    data_to_append = np.zeros(1, dtype=dt)  # structure we will use to append to gps_data

    # ------------------------------------------#
    # step through each line of file           #
    # classify based on three packet types     #
    # populsate our gps_data lists accordingly #
    # ------------------------------------------#

    while not fid.tell() == os.fstat(fid.fileno()).st_size:

        # read first line #
        line = fid.readline().rstrip()
        if not line:
            continue

        # --------------------------------#
        # is this a GNGGA or GPGGA line? #
        # if so populate time data       #
        # --------------------------------#

        elif line.startswith('$') and ('GNGGA' in line or 'GPGGA' in line):
            newblock = TRUE
            data = line.split(',')
            utc = float(data[1])  # see the notes at end of file in the case you want to
            # extract additional location or time fields

        # --------------------------------------------------#
        # is this a GPGSV line?                            #
        # if so we will extract the prn, elev, az, and snr #
        # --------------------------------------------------#

        elif line.startswith('$') and 'GPGSV' in line and newblock == TRUE:
            gsv = []  # container for GSV data
            data = line.split(',')  # python command to create a list from comma separated varables
            num_msg = int(data[1])  # number of messages from first data line
            msg_n = int(data[2])  # message number from first data line
            gsv.append(data)  # first line append data

            # if there is more than 1 message... #
            while msg_n < num_msg:
                line = fid.readline().rstrip()  # read new line
                if line.startswith('$') and 'GPGSV' in line:  # ensure it is GPGSV
                    tmp_line = line.split(',')  # python command to create a list from comma separated varables
                    msg_n = int(tmp_line[2])  # update msg_n
                    num_msg = int(tmp_line[1])  # update num_msg
                    gsv.append(tmp_line)  # append data
                else:
                    break
            prn, elev, az, snr = read_gpgsv(gsv)  # populate the key parameters as per the read_gpgsv function

            # populate the structure based on the read_gpgsv outputs #

            for jj in range(len(prn)):
                idx = prn[jj] - 1
                data_to_append = np.zeros(1, dtype=dt)
                data_to_append[0]['count'] = block_count
                data_to_append[0]['el'] = elev[jj]
                data_to_append[0]['az'] = az[jj]
                data_to_append[0]['snr'] = snr[jj]
                data_to_append[0]['utc'] = utc  # utc comes from the preceding GNGGA or GPGGA line

                if gps_data[idx].size == 0:
                    gps_data[idx] = data_to_append
                else:
                    gps_data[idx] = np.concatenate((gps_data[idx], data_to_append))

        # =======================================#
        # is this a GNRMC or GPRMC line?        #
        # if so we extract day, month, and year #
        # =======================================#

        elif line.startswith('$') and ('GNRMC' in line or 'GPRMC' in line):
            data = line.split(',')
            day = int(data[9][:2])
            month = int(data[9][2:4])
            year = 2000 + int(data[9][4:6])
            date = year * 10000 + month * 100 + day
            if 'prn' in locals() or 'prn' in globals():
                for jj in range(len(prn)):
                    idx = prn[jj] - 1
                    gps_data[idx][-1]['date'] = date
                    gps_data[idx][-1]['utc'] = utc

                block_count += 1
                newblock = FALSE

    # --------------------#
    # cleanup and return #
    # --------------------#

    fid.close()

    # Interpolation step (NumPy-only)
    if interp:
        for prn, data in enumerate(gps_data, start=1):
            if data.size == 0:
                continue

            el = data['el']
            utc = data['utc']

            # find indices where elevation changes sharply
            ind = np.where(np.abs(np.diff(el)) > 0.1)[0]

            if len(ind) > 10:
                timeshort = utc[ind]
                elv = np.interp(utc, timeshort, el[ind])
                data['el'] = elv  # directly update elevation values



    # print(df_updated.loc[2, 'el'])
    return gps_data

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
