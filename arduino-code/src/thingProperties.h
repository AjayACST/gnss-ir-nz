//
// Created by Ajay Quirk on 31/03/2025.
//

#ifndef THINGPROPERTIES_H
#define THINGPROPERTIES_H

#include <ArduinoIoTCloud.h>
#include <Arduino_ConnectionHandler.h>

const char GPRS_APN[]      = SECRET_OPTIONAL_APN;
const char PINNUMBER[]     = SECRET_OPTIONAL_PIN;
const char GPRS_LOGIN[]    = SECRET_OPTIONAL_USERNAME;
const char GPRS_PASSWORD[] = SECRET_OPTIONAL_PASSWORD;

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

void initProperties(){

    ArduinoCloud.addProperty(nMEAStrings, READWRITE, ON_CHANGE, onNMEAStringsChange);
}

NBConnectionHandler ArduinoIoTPreferredConnection(PINNUMBER, GPRS_APN, GPRS_LOGIN, GPRS_PASSWORD);

#endif //THINGPROPERTIES_H