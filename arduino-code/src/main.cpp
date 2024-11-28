#include <Arduino.h>
#include <Wire.h>
#include <SparkFun_u-blox_GNSS_Arduino_Library.h>
#include <SD.h>

SFE_UBLOX_GNSS gnss;


File gnssFile;
const int chipSelect = 4;

#define sdWriteSize 512
#define gnssFileBufferSize 16384

uint8_t *gnssBuffer;

unsigned long lastPrint;

int numSFRBX = 0;
int numRAWX = 0;

//void newSFRBX(UBX_RXM_SFRBX_data_t *ubxDataStruct) {
//    numSFRBX++;
//}
//
//void newRAWX(UBX_RXM_RAWX_data_t *ubxDataStuct) {
//    numRAWX++;
//}

void newNAVSAT(UBX_NAV_SAT_data_t *ubxNavSatData) {
    uint8_t numSats = ubxNavSatData->header.numSvs;
    Serial.print("Num Satalites in View");
    Serial.print(numSats);
    Serial.println();

    for (uint8_t i = 0; i < numSats && i < UBX_NAV_SAT_MAX_BLOCKS; i++) {
        UBX_NAV_SAT_block_t sat = ubxNavSatData->blocks[i];

        Serial.print("Satellite ");
        Serial.print(i + 1);
        Serial.print(": PRN=");
        Serial.print(sat.svId);
        Serial.print(", Elevation=");
        Serial.print(sat.elev);
        Serial.print("°, Azimuth=");
        Serial.print(sat.azim);
        Serial.println("°");
    }
}

void setup() {
    // write your initialization code here
    Serial.begin(9600);
    Wire.begin();
    while (!Serial) {
        ;
    }
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, LOW);

    while (Serial.available()) {
        // Make sure serial buffer is empty
        Serial.read();
    }
    Serial.println("Press any key to start logging.");
    while (!Serial.available()) {
        ;
    }
    delay(100);

    while (Serial.available()) {
        Serial.read();
    }

    // SD Card Stuff
    Serial.println("Initializing SD card...");
    if (!SD.begin(chipSelect)) {
        Serial.println("Card failed, or not present");
        while (1);
    }
    Serial.println("Card initialized.");

    gnssFile = SD.open("RXM_RAWX.UC2", FILE_WRITE);
    if (!gnssFile) {
        Serial.println("Failed to create UBX data file!");
        while (1);
    }

    gnss.disableUBX7Fcheck();

    gnss.setFileBufferSize(gnssFileBufferSize);

    if (!gnss.begin()) {
        Serial.println("u-blox GNSS not detected at default I2C address!");
        while (1);
    }

    gnss.setI2COutput(COM_TYPE_UBX);
    gnss.saveConfigSelective(VAL_CFG_SUBSEC_IOPORT);
    gnss.setNavigationFrequency(1);

//    gnss.setAutoRXMSFRBXcallbackPtr(&newSFRBX);
//    gnss.logRXMSFRBX();
//
//    gnss.setAutoRXMRAWXcallbackPtr(&newRAWX);
//    gnss.logRXMRAWX();

    gnss.setAutoNAVSATcallbackPtr(&newNAVSAT);
//    gnss.log

    gnssBuffer = new uint8_t[sdWriteSize];

    lastPrint = millis();

}

void loop() {
    gnss.checkUblox();
    gnss.checkCallbacks();
    delay(500);

//    while (gnss.fileBufferAvailable() >= sdWriteSize) {
//        digitalWrite(LED_BUILTIN, HIGH);
//
//        gnss.extractFileBufferData(gnssBuffer, sdWriteSize);
//
//        gnssFile.write(gnssBuffer, sdWriteSize);
//
//        // In case SD writing is slow or there is a lot of data to write, keep checking for arrival of new data
//        gnss.checkUblox();
//        gnss.checkCallbacks();
//        digitalWrite(LED_BUILTIN, LOW);
//    }
//
//    if (millis() > (lastPrint+1000)) {
//        Serial.print("Number of message groups received: SFRBX: ");
//        Serial.print(numSFRBX);
//        Serial.print(" RAWX: ");
//        Serial.print(numRAWX);
//
//        uint16_t maxBufferBytes = gnss.getMaxFileBufferAvail();
//
//        if (maxBufferBytes > ((gnssFileBufferSize / 5) * 4)) {
//            Serial.println("WARNING: the file buffer has been over 80% full. Some data may have been lost.");
//        }
//        lastPrint = millis();
//    }
//
//    // Check if user wants to stop logging
//    if (Serial.available()) {
//        uint16_t remBytes = gnss.fileBufferAvailable();
//
//        while (remBytes > 0) {
//            digitalWrite(LED_BUILTIN, HIGH);
//
//            uint16_t  bytesWrite = remBytes;
//            if (bytesWrite > sdWriteSize) {
//                bytesWrite = sdWriteSize;
//            }
//
//            gnss.extractFileBufferData(gnssBuffer, bytesWrite);
//
//            gnssFile.write(gnssBuffer, bytesWrite);
//
//            remBytes -= bytesWrite;
//        }
//
//        digitalWrite(LED_BUILTIN, LOW);
//
//        gnssFile.close();
//
//        Serial.println("Logging stopped.");
//        while(1);
//    }
}