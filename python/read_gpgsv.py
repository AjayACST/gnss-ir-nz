#!/usr/bin/env python

import numpy as np

#============#
# read_gpgsv #
#============#

# purpose - function to read GPS GPGSV data and populate prn, elevation angle, azimuth angle, snr
#
# authors - Delwyn Moller & Brian Pollard
#           dkmoller@restorelab.co.nz
#           bpollard@restorelab.co.nz
#
# date    - v1 release 2024.04.11
#
# usage   - returns variables in the order (prn, elev, az, snr)
#
# license - released freely under the Gnu Public License WITHOUT ANY WARRANTY; without even the implied warranty of
#           MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#           https://www.gnu.org/licenses/gpl-3.0.en.html

#============#
# read_gpgsv #
#============#

def read_gpgsv(gsv_data):

    # null declarations #

    prn = []
    elev = []
    az = []
    snr = []

    #---------------------------------------#
    # loop over length of the gsv data list #
    #---------------------------------------#
    
    for ii in range(len(gsv_data)):


        # first block is cells 4 through 7 #
        # data is prn, elev, az, snr       #
        print(gsv_data[ii])
        if ("*" in gsv_data[ii][4]): # if we have an early checksum, abort the next group of four
            break
            
        if ((gsv_data[ii][5] != '' and gsv_data[ii][6] != '' and gsv_data[ii][7] != '') and (not np.isnan(int(gsv_data[ii][4])) and int(gsv_data[ii][4]) <= 32)):
            prn.append(int(gsv_data[ii][4])) 
            elev.append(float(gsv_data[ii][5]))
            az.append(float(gsv_data[ii][6]))
            snr.append(float(gsv_data[ii][7]))

        # second block is cells 8 through 11 #

        if ("*" in gsv_data[ii][8]):  # if we have an early checksum, abort the next group of four
            break

        if ((gsv_data[ii][9] != '' and gsv_data[ii][10] != '' and gsv_data[ii][11] != '') and (not np.isnan(int(gsv_data[ii][8])) and int(gsv_data[ii][8]) <= 32)):
            prn.append(int(gsv_data[ii][8]))
            elev.append(float(gsv_data[ii][9]))
            az.append(float(gsv_data[ii][10]))
            snr.append(float(gsv_data[ii][11]))
            
        # third block is cells 12 through 15 #

        if ("*" in gsv_data[ii][12]): # if we have an early checksum, abort the next group of four
            break
        
        if ((gsv_data[ii][13] != '' and gsv_data[ii][14] != '' and gsv_data[ii][15] != '') and (not np.isnan(int(gsv_data[ii][12])) and int(gsv_data[ii][12]) <= 32)):
            prn.append(int(gsv_data[ii][12]))
            elev.append(float(gsv_data[ii][13]))
            az.append(float(gsv_data[ii][14]))
            snr.append(float(gsv_data[ii][15]))

        # fourth block is cells 16 through 19 #
        if ("*" in gsv_data[ii][16]): break
        # gsv_data[ii][19] = gsv_data[ii][19].split("*")[0] # deals with checksum
        # Not needed with UBlox data as we have an extra signal ID parameter after the CNO
        
        if ((gsv_data[ii][17] != '' and gsv_data[ii][18] != '' and gsv_data[ii][19] != '') and (not np.isnan(int(gsv_data[ii][16])) and int(gsv_data[ii][16]) <= 32)):
            prn.append(int(gsv_data[ii][16]))
            elev.append(float(gsv_data[ii][17]))
            az.append(float(gsv_data[ii][18]))
            snr.append(float(gsv_data[ii][19]))

    return prn, elev, az, snr

