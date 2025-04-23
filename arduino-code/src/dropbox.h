//
// Created by Ajay Quirk on 16/04/2025.
//

#ifndef DROPBOX_H
#define DROPBOX_H
#include <ArduinoHttpClient.h>
#include <SD.h>


class Dropbox {
public:
    Dropbox(const char access_token[], HttpClient& httpClient);
    int upload(File& sdFile, const char file_name[]) const;
private:
    const char* _accessToken;
    HttpClient& _http;
};

#endif //DROPBOX_H
