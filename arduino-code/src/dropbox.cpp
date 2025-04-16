//
// Created by Ajay Quirk on 16/04/2025.
//

#include "dropbox.h"
#include <MKRNB.h>

Dropbox::Dropbox(const char app_key[], const char app_secret[], NBSSLClient& client) {
    this->app_key = app_key;
    this->app_secret = app_secret;
    this->client = &client;

    // testing
    char server[] = "arduino.tips";
    char path[] = "/asciilogo.txt";
    int port = 443;
    if (client.connect(server, port)) {
        Serial.println("Connected to server");
        client.print("GET ");
        client.print(path);
        client.println(" HTTP/1.1");
        client.print("Host: ");
        client.println(server);
        client.println("Connection: close");
        client.println();
    } else {
        Serial.println("Failed to connect to server");
    }
}
