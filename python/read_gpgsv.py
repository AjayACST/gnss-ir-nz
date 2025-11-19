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
    prn = []
    elev = []
    az = []
    snr = []

    for i in range(len(gsv_data)):
        current = np.array(gsv_data[i])
        current[current == ''] = np.nan # any empty strings to NaN
        if "*" in current[4]:
            break
        if current[4].isdigit() and int(current[4]) <= 32: # read the first prn block
            prn.append(int(current[4]))
            elev.append(float(current[5]))
            az.append(float(current[6]))
            snr.append(float(current[7]))

        if "*" in current[8]: # stop if early checksum
            break
        if current[8].isdigit() and int(current[8]) <= 32: # read the second prn block
            prn.append(int(current[8]))
            elev.append(float(current[9]))
            az.append(float(current[10]))
            snr.append(float(current[11]))

        if "*" in current[12]: # stop if early checksum
            break
        if current[12].isdigit() and int(current[12]) <= 32: # read the third prn block
            prn.append(int(current[12]))
            elev.append(float(current[13]))
            az.append(float(current[14]))
            snr.append(float(current[15]))

        if "*" in current[16]: # stop if early checksum
            break
        if current[16].isdigit() and int(current[16]) <= 32: # read the fourth prn block
            prn.append(int(current[16]))
            elev.append(float(current[17]))
            az.append(float(current[18]))
            snr.append(float(current[19]))

    return prn, elev, az, snr

