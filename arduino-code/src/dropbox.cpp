//
// Created by Ajay Quirk on 16/04/2025.
//

#include "dropbox.h"
#include <MKRNB.h>
#include <ArduinoHttpClient.h>

Dropbox::Dropbox(const char access_token[], HttpClient& client)
    : _accessToken(access_token), _http(client) {}


int Dropbox::upload(File& sdFile, const char file_name[]) const {
    String dropbox_header_args = R"({"path": "/)" + String(file_name) + R"("})";
    _http.beginRequest();
    _http.post("/2/files/upload");
    _http.sendHeader("Authorization", String("Bearer ") + _accessToken);
    _http.sendHeader(HTTP_HEADER_CONTENT_TYPE, "application/octet-stream");
    _http.sendHeader("Dropbox-API-Arg", dropbox_header_args);
    _http.sendHeader(HTTP_HEADER_CONTENT_LENGTH, sdFile.size());

    _http.beginBody();
    const size_t BUF_SZ = 512;
    uint8_t buf[BUF_SZ];
    while (sdFile.available()) {
        size_t bytes_read = sdFile.read(buf, BUF_SZ);
        _http.write(buf, bytes_read);
    }
    _http.endRequest();

    int status = _http.responseStatusCode();
    String resp = _http.responseBody();
    Serial.print("Status: ");
    Serial.println(status);
    if (status != 200) {
        Serial.println("Response: ");
        Serial.println(resp);
        return 0;
    }
    return 1;
}
