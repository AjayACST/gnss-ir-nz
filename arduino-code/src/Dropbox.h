//
// Created by Ajay Quirk on 16/04/2025.
//

#ifndef DROPBOX_H
#define DROPBOX_H
#include <ArduinoHttpClient.h>
#include <SD.h>
#include <ArduinoJson.h>

#define SIMPLE_NB_MODEM_SARAR4
#define SIMPLE_NB_DEBUG Serial
#define SerialAT SerialSARA
#define BAUD_RATE 115200

#include "SimpleNBClient.h"


class Dropbox {
public:
    Dropbox(const char app_key[], const char app_secret[], SimpleNBClientSecure& http_api_client);
    int upload(File& sdFile, const char file_name[]);
private:
    static bool read_creds(JsonDocument& doc);
    bool validate_creds();
    bool renew_creds();
    const char* _app_key;
    const char* _app_secret;
    void logPrintln(const String& message);
    File logFile;
    SimpleNBClientSecure& client;
};

#endif //DROPBOX_H
