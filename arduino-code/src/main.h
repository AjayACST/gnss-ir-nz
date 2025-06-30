//
// Created by Ajay Quirk on 31/03/2025.
//

#ifndef MAIN_H
#define MAIN_H

#include <Arduino.h>

void configGPS();
bool initSD();
void datalog(const char basename[]);
void getBasename(char basename[], const char dateTime[], bool GPSActive);
bool getDateTime(const char stringOriginal[], char dateTime[]);
const char* nth_strchr(const char*s, int c, int n);
void read_serial();
void blink_led();
void handle_dropbox();
void powerOn();
void logPrintln(const String& message);
#endif
//MAIN_H