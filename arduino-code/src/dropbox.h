//
// Created by Ajay Quirk on 16/04/2025.
//

#ifndef DROPBOX_H
#define DROPBOX_H
#include "MKRNB.h"


class Dropbox {
public:
    Dropbox(const char app_key[], const char app_secret[], NBSSLClient& client);
private:
    const char *app_key;
    const char *app_secret;
    NBSSLClient* client;
};

#endif //DROPBOX_H
