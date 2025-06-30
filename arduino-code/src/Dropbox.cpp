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
    // if (!validate_creds()) {
    //     renew_creds();
    // }
}

/**
 * Validates dropbox credentials.
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
        "Connection: close\r\n"
        "\r\n";

    const char *p = req.c_str();
    size_t       remaining = req.length();
    while (remaining) {
        size_t chunk = remaining > 512 ? 512 : remaining;
        client.write((const uint8_t*)p, chunk);
        p         += chunk;
        remaining -= chunk;
    }

    unsigned long deadline = millis() + 5000;
    while (!client.available() && millis() < deadline) {
        yield();
    }
    if (!client.available()) {
        Serial.println("[ERROR] No response from server");
        client.stop();
        return false;
    }

    String statusLine = client.readStringUntil('\n');
    statusLine.trim();

    int code = 0;
    int sp1  = statusLine.indexOf(' ');
    int sp2  = statusLine.indexOf(' ', sp1 + 1);
    if (sp1 > 0 && sp2 > sp1) {
        code = statusLine.substring(sp1 + 1, sp2).toInt();
    }
    client.stop();
    // Serial.print("Parsed code = ");
    // Serial.println(code);
    return code == 200;
}

/**
 * Exchanges the refresh_token inside of dropbox.txt for a new access_token if it has expired.
 *
 * @return true if succesfully exchange refresh token for new access_token
 */
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

/**
 * Reads the dropbox.txt file and attempts to deserialize the contents
 *
 * @param doc JsonDocument to store dropbox credentials in
 * @return True if successfully read and deserialize, false otherwise
 */
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
/**
 * Uploads a file to Dropbox using the Dropbox API.
 *
 * @param sdFile The opened file from SD library
 * @param file_name The name of the file that is being uploaded
 * @return -1 if failure in credentials, -2 if failure in connecting, otherwise status code from Dropbox is returned.
 */
int Dropbox::upload(File &sdFile, const char file_name[]) {
    digitalWrite(LED_BUILTIN, HIGH);
    JsonDocument doc;
    String dropbox_header_args = R"({"path": "/)" + String(file_name) + R"(", "mode": "overwrite")" + "}";

    if (!validate_creds()) {
        if (!renew_creds()) {
            digitalWrite(LED_BUILTIN, LOW);
            return -1;
        }
    }

    if (!read_creds(doc)) {
        Serial.println("[ERROR] Failed to deserialize the dropbox object.");
        digitalWrite(LED_BUILTIN, LOW);
        return -1;
    }

    if (!client.connect("content.dropboxapi.com", 443)) {
        Serial.println("[ERROR] Connection Failed!");
        digitalWrite(LED_BUILTIN, LOW);
        return -2;
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

    const char *p = req.c_str();
    size_t       remaining = req.length();
    while (remaining) {
        size_t chunk = remaining > 512 ? 512 : remaining;
        client.write((const uint8_t*)p, chunk);
        p         += chunk;
        remaining -= chunk;
    }
    // 5) Stream file body in chunks
    const size_t BUF_SZ = 512;
    uint8_t buf[BUF_SZ];
    while (sdFile.available()) {
        size_t n = sdFile.read(buf, BUF_SZ);
        client.write(buf, n);
    }
    // wait up to 5s for server to respond
    unsigned long deadline = millis() + 5000;
    while (!client.available() && millis() < deadline) yield();
    if (!client.available()) {
        Serial.println("[ERROR] no response");
        client.stop();
        digitalWrite(LED_BUILTIN, LOW);
        return -1;
    }

    String statusLine = client.readStringUntil('\n');
    statusLine.trim();

    // parse code
    int sp1 = statusLine.indexOf(' ');
    int sp2 = statusLine.indexOf(' ', sp1 + 1);
    int code = (sp1>0 && sp2>sp1)
               ? statusLine.substring(sp1+1, sp2).toInt()
               : -1;
    if (code != 200) {
        Serial.print("HTTP code = "); Serial.println(String(code));
        // skip headers
        while (client.available()) {
            if (client.readStringUntil('\n') == "\r") break;
        }
        // dump body
        Serial.println("[ERROR] Response body: ");

        while (client.available()) {
            Serial.write(client.read());
        }
    }
    client.stop();
    digitalWrite(LED_BUILTIN, LOW);

    return code;
}