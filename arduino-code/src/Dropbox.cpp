//
// Created by Ajay Quirk on 16/04/2025.
//

#include "Dropbox.h"
#include <ArduinoHttpClient.h>
#include <SD.h>
#include <ArduinoJson.h>

#define SIMPLE_NB_MODEM_SARAR4
#define SIMPLE_NB_DEBUG Serial
#define SerialAT SerialSARA
#define BAUD_RATE 115200

#include <SimpleNBClient.h>

Dropbox::Dropbox(const char app_key[], const char app_secret[], SimpleNBClientSecure &client)
    : _app_key(app_key), _app_secret(app_secret), client(client) {
    if (validate_creds()) {
        Serial.println("[DEBUG] Token is valid!");
    } else {
        Serial.println("[DEBUG] Renewing token!");
        renew_creds();
    }
}

/**
 * Validates dropbox credentials and gets new ones if expired.
 *
 * @return true if successfully validated or got new credentials, false otherwise
 */
bool Dropbox::validate_creds() const {
    JsonDocument doc;
    if (!read_creds(doc)) {
        return false;
    }

    if (!client.connect("api.dropboxapi.com", 443)) {
        Serial.println("[ERROR] Failed to connect!");
        return false;
    }
    String token = doc["access_token"].as<const char*>();
    String req =
        "POST /2/users/get_current_account HTTP/1.1\r\n"
        "Host: api.dropboxapi.com\r\n"
        "Authorization: Bearer " + token + "\r\n"
        "Content-Length: 0\r\n"
        "Connection: close\r\n"    // <-- last header
        "\r\n";                    // <-- blank line

    // 4) send it in chunks
    const char *p = req.c_str();
    size_t       remaining = req.length();
    while (remaining) {
        size_t chunk = remaining > 512 ? 512 : remaining;
        client.write((const uint8_t*)p, chunk);
        p         += chunk;
        remaining -= chunk;
    }

    // 5) wait for the response to start
    unsigned long deadline = millis() + 5000;
    while (!client.available() && millis() < deadline) {
        yield();
    }
    if (!client.available()) {
        Serial.println("[ERROR] No response from server");
        client.stop();
        return false;
    }

    // 6) read the status line
    String statusLine = client.readStringUntil('\n');  // e.g. "HTTP/1.1 200 OK\r"
    statusLine.trim();                                 // remove trailing \r
    Serial.println("Status Line: " + statusLine);

    // 7) parse out the numeric code
    int code = 0;
    int sp1  = statusLine.indexOf(' ');
    int sp2  = statusLine.indexOf(' ', sp1 + 1);
    if (sp1 > 0 && sp2 > sp1) {
        code = statusLine.substring(sp1 + 1, sp2).toInt();
    }
    client.stop();
    Serial.print("Parsed code = ");
    Serial.println(code);
    return code == 200;
}

bool Dropbox::renew_creds() const {
    JsonDocument doc;
    if (!read_creds(doc)) {
        return false;
    }

    if (!client.connect("api.dropboxapi.com", 443)) {
        Serial.println("[ERROR] Failed to connect!");
        return false;
    }

    String body = String("grant_type=refresh_token") +
                  "&refresh_token=" + doc["refresh_token"].as<String>() +
                  "&client_id=" + _app_key +
                  "&client_secret=" + _app_secret;

    String req =
            String("POST /oauth2/token HTTP/1.1\r\n") +
            "Host: api.dropboxapi.com\r\n" +
            "Content-Type: application/x-www-form-urlencoded\r\n" +
            "Content-Length: " + body.length() + "\r\n" +
            "Connection: close\r\n" +
            "\r\n" +
            body;

    client.print(req);
    // 4) Read status line
    String statusLine = client.readStringUntil('\n');  // e.g. "HTTP/1.1 200 OK\r"
    int status = 0;
    {
        int sp1 = statusLine.indexOf(' ');
        int sp2 = statusLine.indexOf(' ', sp1 + 1);
        if (sp1>0 && sp2>sp1) {
            status = statusLine.substring(sp1+1, sp2).toInt();
        }
    }

    if (status != 200) {
        // skip headers
        while (client.available()) {
            if (client.readStringUntil('\n') == "\r") break;
        }
        // dump body
        Serial.println("[ERROR] Response body: ");
        while (client.available()) {
            Serial.write(client.read());
        }
        client.stop();
        return false;
    }
    // Skip other headers
    while (true) {
        String h = client.readStringUntil('\n');
        if (h == "\r" || h == "") break;
    }


    JsonDocument resDoc;
    DeserializationError err = deserializeJson(resDoc, client);
    client.stop();
    if (err) {
        Serial.println("[ERROR] Failed to deserialize the response from dropbox!");
        return false;
    }
    String new_token = resDoc["access_token"];

    resDoc["refresh_token"] = doc["refresh_token"];
    String new_auth_creds;
    serializeJson(resDoc, new_auth_creds);

    SD.remove("dropbox.txt");
    File new_creds_file = SD.open("dropbox.txt", FILE_WRITE);
    if (new_creds_file) {
        new_creds_file.print(new_auth_creds);
        new_creds_file.flush();
    }
    new_creds_file.close();
    return true;
}


bool Dropbox::read_creds(JsonDocument &doc) {
    File dropbox_creds = SD.open("dropbox.txt");
    if (!dropbox_creds) {
        Serial.println("[ERROR] dropbox.json file not found!");
        return false;
    }
    DeserializationError err = deserializeJson(doc, dropbox_creds);
    if (err) {
        Serial.println("[ERROR] Failed to deserialize json from dropbox.txt");
        return false;
    }
    return true;
}


int Dropbox::upload(File &sdFile, const char file_name[]) const {
    JsonDocument doc;
    String dropbox_header_args = R"({"path": "/)" + String(file_name) + R"("})";
    if (!read_creds(doc)) {
        Serial.println("[ERROR] Failed to deseralise the dropbox object.");
        return -1;
    }
    if (validate_creds()) {
        Serial.println("[DEBUG] Token is valid!");
    } else {
        Serial.println("[DEBUG] Renewing token!");
        renew_creds();
    }

    if (!client.connect("content.dropboxapi.com", 443)) {
        Serial.println("[ERROR] Connection Failed!");
        return -1;
    }

    String token = doc["access_token"].as<const char*>();
    String req =
            String("POST /2/files/upload HTTP/1.1\r\n") +
            "Host: content.dropboxapi.com\r\n" +
            "Authorization: Bearer " + token + "\r\n"
            "Content-Type: application/octet-stream\r\n" +
            "Dropbox-API-Arg: " + dropbox_header_args + "\r\n" +
            "Content-Length: " + sdFile.size() + "\r\n" +
            "Connection: close\r\n" +
            "\r\n";

    // Serial.println(req);

    const char *p = req.c_str();
    size_t       remaining = req.length();
    while (remaining) {
        size_t chunk = remaining > 512 ? 512 : remaining;
        client.write((const uint8_t*)p, chunk);
        p         += chunk;
        remaining -= chunk;
    }
    sdFile.seek(0);
    // 5) Stream file body in chunks
    const size_t BUF_SZ = 512;
    uint8_t buf[BUF_SZ];
    size_t totalSent = 0;
    while (sdFile.available()) {
        size_t n = sdFile.read(buf, BUF_SZ);
        client.write(buf, n);
        totalSent+=n;
    }

    // 6) Read status‐line
    // wait up to 5s for server to respond
    unsigned long deadline = millis() + 5000;
    while (!client.available() && millis() < deadline) yield();
    if (!client.available()) {
        Serial.println("[ERROR] no response");
        client.stop();
        return -1;
    }

    String statusLine = client.readStringUntil('\n');
    statusLine.trim();  // strip trailing '\r'
    Serial.println("Status: " + statusLine);

    // parse code
    int sp1 = statusLine.indexOf(' ');
    int sp2 = statusLine.indexOf(' ', sp1 + 1);
    int code = (sp1>0 && sp2>sp1)
               ? statusLine.substring(sp1+1, sp2).toInt()
               : -1;
    Serial.print("HTTP code = "); Serial.println(code);


    // 8) Read response body
    String resp;
    while (client.available()) {
        resp += char(client.read());
    }
    client.stop();
    Serial.println("Body:");
    Serial.println(resp);

    return code;

}
