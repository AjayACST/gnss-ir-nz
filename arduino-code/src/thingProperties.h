//
// Created by Ajay Quirk on 31/03/2025.
//

#ifndef THINGPROPERTIES_H
#define THINGPROPERTIES_H

#include <Arduino.h>

void onNMEAStringsChange();

void configGPS();
bool initSD();
void datalog(const char basename[]);
void getBasename(char basename[], const char dateTime[], bool GPSActive);
bool getDateTime(const char stringOriginal[], char dateTime[]);
const char* nth_strchr(const char*s, int c, int n);
void read_serial();
void blink_led();
void push_iot(const char *basename);

String nMEAStrings;


#endif //THINGPROPERTIES_H