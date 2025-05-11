// ReSharper disable once CppUnusedIncludeDirective

#include "main.h"
#include <SD.h>
#include <ArduinoHttpClient.h>

#include "arduino_secrets.h"
#include "Dropbox.h"

// settings for the modem

#define SIMPLE_NB_MODEM_SARAR4
#define SIMPLE_NB_DEBUG Serial
#define SerialAT SerialSARA
#define BAUD_RATE 115200

#include <SimpleNBClient.h>

#define GPS_BAUD_RATE 38400
#define SERIAL_BAUD 9600

#define IDLE_THRESHOLD 10 //milliseconds

#define SDCard 4

#define WAIT_FOR_VALID_GPS

#define MAX_BASENAME_LEN (8+1) // FAT limit 8.3, +1 for \0 char
#define MAX_FILENAME_LEN (MAX_BASENAME_LEN + 1 + 3) // basename + dot + extension

#define DEBUG // if defined will output debug messages to Serial

#define  GPS_BUFFER_SIZE_TYPICAL 512  // typical buffer size, for pre-allocation

unsigned long bufferTime = millis();

String gpsBuffer = ""; // holds incoming NMEA sentences
char basenameOld[MAX_BASENAME_LEN];

int current_i = 0;

SimpleNB modem(SerialSARA);
SimpleNBClientSecure client(modem);

// NBSSLClient client({}, 0);
// NB nbAccess(true);
// GPRS gprs;
Dropbox* dropbox;
HttpClient httpClientApi(client, "httpbin.org", 443);
HttpClient httpClientContent(client, "content.dropboxapi.com", 443);

char dropbox_app_key[] = SECRET_DROPBOX_APP_KEY;
char dropbox_app_secret[] = SECRET_DROPBOX_APP_SECRET;

void setup() {
    //NEVER USER RESETN
    pinMode(SARA_RESETN, OUTPUT);
    digitalWrite(SARA_RESETN, LOW);
    powerOn();
    // Initialize serial and GPS serial
    Serial.begin(SERIAL_BAUD);
    Serial1.begin(GPS_BAUD_RATE);
    // This delay gives the chance to wait for a Serial Monitor without blocking if none is found
    delay(1500);

    SimpleNBBegin(SerialSARA, BAUD_RATE);
    DBG("initialising modem.");
    modem.init();
    if (!modem.waitForRegistration(6000L, true)) {
        DBG("Failed to connect");
        delay(1000000);
    }

    DBG("Activating network");
    if (!modem.gprsConnect("m2m")) {
        DBG("Failed to activate");
    }

    DBG("Connected!");

    // Setup sd card
    initSD();
    // ensure sd has been setup before Dropbox
    dropbox = new Dropbox(dropbox_app_key, dropbox_app_secret, client);

    // init led pins
    pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
    read_serial();
    bool GPSActive;
    char dateTime[6+6+1]; //yyyymmDDHHMMSS\0
    char basename[MAX_BASENAME_LEN];
    unsigned long startTime = millis();

    unsigned long idleTime = startTime - bufferTime;
    if (idleTime < IDLE_THRESHOLD || gpsBuffer.length() < 3) {return;}

    #ifdef DEBUG
        Serial.println("[DEBUG] starting SD log");
        Serial.println(gpsBuffer);
    #endif

    GPSActive = getDateTime(gpsBuffer.c_str(), dateTime);

    getBasename(basename, dateTime, GPSActive);
    datalog(basename);

    // Check if we need to change basename
    if (strcmp(basename, basenameOld) != 0) {
        // Upload the old file to dropbox
        handle_dropbox();
        // File needs to be changed
        strcpy(basenameOld, basename);
    }
    gpsBuffer = "";
    gpsBuffer.reserve(GPS_BUFFER_SIZE_TYPICAL);
}

void powerOn() {
    // Send Poweron pulse
    pinMode(SARA_PWR_ON, OUTPUT);
    digitalWrite(SARA_PWR_ON, HIGH);
    delay(150);
    digitalWrite(SARA_PWR_ON, LOW);
}


bool initSD() {
    if (!SD.begin(SDCard)) {
        Serial.println("[ERROR] Unable to init SD Card!");
        return false;
    }
    delay(500);
    return true;
}

void handle_dropbox() {
    char filename[MAX_FILENAME_LEN];
    strncpy(filename, basenameOld, MAX_BASENAME_LEN);
    strcat(filename, ".log");

    File sd_file = SD.open(filename);
    if (sd_file) {
#ifdef DEBUG
        Serial.println("[DEBUG] Uploading file to Dropbox.");
#endif
        int status = dropbox->upload(sd_file, filename);
        sd_file.close();
        if (status != 200) {
            Serial.println("[ERROR] Failed to upload file to Dropbox. Response from dropbox is above.");
            return;
        }
#ifdef DEBUG
        Serial.println("[DEBUG] Successfully uploaded to Dropbox");
#endif
    } else {
        Serial.println("[ERROR] Failed to open SD card.");
    }
}

bool getDateTime(const char stringOriginal[], char dateTime[]) {
    char strTemp[82];
    char *gnrmc_str = nullptr;
    char *gnrmc_end = nullptr;

    if (strlen(stringOriginal) == 0) {
#ifdef DEBUG
        Serial.println("[DEBUG] Empty string");
#endif
        return false;

    }
    gnrmc_str = strstr(stringOriginal, "$GNRMC");
    if (!gnrmc_str) {
#ifdef DEBUG
        Serial.println("[DEBUG] $GNRMC NMEA sentence not found!");
#endif
        return false;
    }
    if (gnrmc_str[17] != 'A') {
#ifdef DEBUG
        Serial.println("[DEBUG] GPS is not active yet!");
#endif
        return false;
    }

    gnrmc_end = strchr(gnrmc_str, '\n');
    int len = (gnrmc_end - gnrmc_str) + 1;
    strncpy(strTemp, gnrmc_str, min(len, sizeof(strTemp)-1));
    strTemp[len] = '\0';

    const char *dateIn = nth_strchr(strTemp, ',', 9) + 1;
    dateTime[0] = dateIn[4];
    dateTime[1] = dateIn[5];
    dateTime[2] = dateIn[2];
    dateTime[3] = dateIn[3];
    dateTime[4] = dateIn[0];
    dateTime[5] = dateIn[1];

    // extract time, keeping the order (hhmmss)
    const char *timeIn = &strTemp[7];
    strncpy(&dateTime[6], timeIn, 6);

    dateTime[12] = '\n';
#ifdef DEBUG
    Serial.println("[DEBUG] GPS Date Time: " + String(dateTime));
#endif
    return true;
}

void datalog(const char basename[]) {
    char filename[MAX_FILENAME_LEN];
    strncpy(filename, basename, MAX_BASENAME_LEN);
    strcat(filename, ".log");

#ifdef DEBUG
    Serial.println("[DEBUG] Filename: " + String(filename));
#endif

    File file = SD.open(filename, FILE_WRITE);

    if (!file) {
        Serial.println("[ERROR] Failed to open file for writing. Filename: " + String(filename));
        return;
    }

    // get size to check if all has been written
    const byte len1 = gpsBuffer.length();
    const byte len2 = file.println(gpsBuffer);
    file.print("\n");

    file.close();

    if (len1 == len2) {
        blink_led();
        #ifdef DEBUG
            Serial.println("[DEBUG] Written " + String(100*len2/len1) + "% of " + String(len1) + " bytes.");
        #endif
        return;
    }
    // Show anyway if error
    Serial.println("[ERROR] Written " + String(100*len2/len1) + "% of " + String(len1) + " bytes.");
}

void getBasename(char basename[], const char dateTime[], bool gps_active) {
    if (!gps_active) {
        //use default basename
        strcpy(basename, "DEFAULT");
        return;
    }

    strncpy(basename, dateTime, 8); //8 for YYMMDDhh
    basename[8] = '\0';

#ifdef DEBUG
    Serial.println("[DEBUG] Basename: " + String(basename));
#endif

}

void read_serial() {
    while (Serial1.available()) {
        char c = Serial1.read();
        gpsBuffer += c;
        bufferTime = millis();
    }
}

void blink_led() {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(10);
    digitalWrite(LED_BUILTIN, LOW);
}

const char* nth_strchr(const char* s, int c, int n)
{
    int c_count;
    char* nth_ptr;

    for (c_count=1,nth_ptr=strchr(s,c);
         nth_ptr != nullptr && c_count < n && c!=0;
         c_count++)
    {
        nth_ptr = strchr(nth_ptr+1, c);
    }

    return nth_ptr;
}