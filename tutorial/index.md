# Build Tutorial for SNR based GNSS Reflectometry (GNSS-R) Project

## Contributors
- [Baxter Pollard](mailto:baxter.b.pollard@gmail.com)
- [Ajay Quirk](mailto:quirkajay@myvuw.ac.nz)
- [Craig Jefferies](mailto:jefferiesc@mtaspiring.school.nz)
- [Delwyn Moller](mailto:delwyn.moller@auckland.ac.nz)
- [Brain Pollard](mailto:bpollard@restorelab.co.nz)

Last updated on the 24th of January 2025

Based on Fagundes, M.A.R., Mendonça-Tinti, I., Iescheck, A.L. et al. An open-source low-cost sensor for SNR-based GNSS reflectometry: design and long-term validation towards sea-level altimetry. GPS Solut 25, 73 (2021). https://doi.org/10.1007/s10291-021-01087-1

## Table of Contents
- [Parts](#parts)
- [1. Arduino Firmware](#1-arduino-firmware)
  - [1.1 Arduino IDE Setup](#11-arduino-ide-setup)
# Parts
The parts list can be found on DigiKey here: https://www.digikey.co.nz/en/mylists/list/PICEBQ9ABU

# 1. Arduino Firmware
## 1.1 Arduino IDE Setup
Download the latest version of the Arduino IDE from here: https://www.arduino.cc/en/software

The first thing to do is install the board group from the Board Manager. To do this click the second icon in the sidebar and search for "Arduino SAMD". The board group you want to install is called "Arduino SAMD Boards (32-bits ARM Cortex-M0+)", install the latest version of this.

<img src="./images/arduino-board-install.png" height="350" alt="Arduino SAMD Board to group to install">

You can then install the library that we will need for this project. We will need the MKRNB library which handles communication between the cellular network and our device.
To do this click the library icon below the boards manager and search for MKRNB and install it.

<img src="./images/arduino-library-install.png" height="350" alt="MKRNB library to install">