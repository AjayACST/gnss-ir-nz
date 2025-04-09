#include <Arduino.h>
#include <SPI.h>
#include <SD.h>

// Define GPSSerial as Serial1 so that all GPS serial operations refer to Serial1.
#define GPSSerial Serial1

// Configuration macros and constants
#define GPS_BAUD_RATE      38400
#define GPS_BUFFER_SIZE    512
#define MAX_BASNAME_LEN    (8+1)
#define MAX_FILENAME_LEN   (MAX_BASNAME_LEN-1+1+3+1) // basename-null+dot+ext+null
#define IDLE_THRESHOLD     10

// Pin assignments (ensure SD card CS pin is correct for your board/setup)
const int SDcard = 4;

// Default basename if GPS data is not valid
const char basenameDefault[] = "DEFAULT";

// Global variables
String GPSBuffer = "";
unsigned long bufferTime = 0; // Initialize in setup()
int numBlk = 0;
char basenameOld[MAX_BASNAME_LEN] = "";

// Function prototypes
bool initSD();
void getBasename(char basename[], const char dateTime[], bool GPSActive);
bool getDateTime(const char stringOriginal[], char dateTimeOut[]);
void datalog(const char basename[]);
const char* nth_strchr(const char* s, char c, int n);

void setup() {
    Serial.begin(9600);
    // Optionally wait for the serial port to be available.
    // while (!Serial);

    // Initialize SD card. Halt if the initialization fails.
    if (!initSD()) {
        Serial.println("[ERROR] SD initialization failed, halting.");
        while (1);
    }

    // Begin the Serial1 port for GPS communication.
    GPSSerial.begin(GPS_BAUD_RATE);
    
    // Reserve the buffer size and clear any incoming data
    GPSBuffer.reserve(GPS_BUFFER_SIZE);
    while (GPSSerial.available()) {
        GPSSerial.read();
    }
    
    // Initialize bufferTime with the current time.
    bufferTime = millis();
}

void loop() {
    // Read incoming GPS serial data
    while (GPSSerial.available()) {
        char c = GPSSerial.read();
        GPSBuffer += c;
        bufferTime = millis();  // update last reception time
    }
    
    unsigned long startTime = millis();
    unsigned long idleTime = startTime - bufferTime;
    
    // Process data only when no new characters are incoming and a minimum data length is reached
    if (idleTime < IDLE_THRESHOLD || GPSBuffer.length() < 3) {
        return;
    }
    
    Serial.println("[DEBUG] Starting processing...");
    Serial.print(GPSBuffer);
    
    // Try to extract date/time from the GPS string.
    char dateTime[13]; // Format: yymmddHHMMSS\0 -> 12 characters + terminating null
    bool GPSActive = getDateTime(GPSBuffer.c_str(), dateTime);
    if (!GPSActive) {
        GPSBuffer = "";
        GPSBuffer.reserve(GPS_BUFFER_SIZE);
        return;
    }
    
    // Generate a filename basename from the GPS timestamp
    char basename[MAX_BASNAME_LEN];
    getBasename(basename, dateTime, GPSActive);
    
    // Log the GPS string to the SD card with the generated filename.
    datalog(basename);
    
    // If the basename changes, reset the block counter.
    if (strcmp(basename, basenameOld) != 0) {
        strncpy(basenameOld, basename, MAX_BASNAME_LEN);
        numBlk = 0;
    }
    numBlk++;
    Serial.println("[DEBUG] number of blocks: " + String(numBlk));
    
    // Reset the buffer for the next batch of data.
    GPSBuffer = "";
    GPSBuffer.reserve(GPS_BUFFER_SIZE);
}

bool initSD() {
    if (!SD.begin(SDcard)) {
        Serial.println("[ERROR] Unable to initialise SD card");
        return false;
    }
    return true;
}

void datalog(const char basename[]) {
    char filename[MAX_FILENAME_LEN];
    // Copy the basename and ensure it is null-terminated
    strncpy(filename, basename, MAX_BASNAME_LEN);
    filename[MAX_BASNAME_LEN - 1] = '\0';
    strcat(filename, ".log");
    Serial.println("[DEBUG] filename (GPS): " + String(filename));
    
    // Open the file for appending data
    File file = SD.open(filename, FILE_WRITE);
    if (!file) {
        Serial.println("[ERROR] Unable to open file: " + String(filename));
        return;
    }
    
    // Write the GPSBuffer to the file and check the length.
    size_t len1 = GPSBuffer.length();
    size_t len2 = file.print(GPSBuffer);
    
    file.println();
    file.close();
    
    String prefix = "[DEBUG]";
    if (len1 != len2) {
        prefix = "[ERROR]";
    }
    Serial.println(prefix + " " + String(100 * len2 / len1) + "%" + " of " +
                   String(len1) + " bytes written to SD file '" + String(filename) + "'");
}

void getBasename(char basename[], const char dateTime[], bool GPSActive) {
    if (!GPSActive) {
        // Use a default filename if GPS is inactive
        strncpy(basename, basenameDefault, MAX_BASNAME_LEN);
        basename[MAX_BASNAME_LEN - 1] = '\0';
        return;
    }

    // Copy the first 6 characters of the dateTime (YYMMDD) into basename.
    strncpy(basename, dateTime, 6);
    basename[6] = '\0';

    Serial.println("[DEBUG] Using filename: " + String(basename));
}

bool getDateTime(const char stringOriginal[], char dateTimeOut[]) {
    if (strlen(stringOriginal) == 0) {
        Serial.println("[DEBUG] Empty GPS string.");
        return false;
    }
    
    // Search for the $GNRMC sentence.
    const char* limInf = strstr(stringOriginal, "$GNRMC");
    if (!limInf) {
        Serial.println("[DEBUG] $GNRMC not found!");
        return false;
    }
    
    // Check if the data indicates a valid fix.
    if (strlen(limInf) < 18 || limInf[17] != 'A') {
        Serial.println("[DEBUG] $GNRMC sentence indicates an invalid fix.");
        return false;
    }
    
    // Find the end of the line for the $GNRMC sentence.
    const char* limSup = strchr(limInf, '\n');
    int len = (limSup != NULL) ? (limSup - limInf + 1) : strlen(limInf);
    char strTemp[82];
    strncpy(strTemp, limInf, min(len, (int)sizeof(strTemp) - 1));
    strTemp[min(len, (int)sizeof(strTemp) - 1)] = '\0';
    
    // Extract the date from the sentence.
    const char* dateIn = nth_strchr(strTemp, ',', 9);
    if (dateIn == NULL || *(dateIn + 1) == '\0') {
        Serial.println("[DEBUG] Date not found in the GPS string.");
        return false;
    }
    dateIn++;  // Move past the comma

    if (strlen(dateIn) < 6) {
        Serial.println("[DEBUG] Date string too short.");
        return false;
    }
    // Reorder the date (from DDMMYY to YYMMDD)
    dateTimeOut[0] = dateIn[4];  // Year tens
    dateTimeOut[1] = dateIn[5];  // Year ones
    dateTimeOut[2] = dateIn[2];  // Month tens
    dateTimeOut[3] = dateIn[3];  // Month ones
    dateTimeOut[4] = dateIn[0];  // Day tens
    dateTimeOut[5] = dateIn[1];  // Day ones

    // Extract time (assumed to be starting at index 7 in the sentence, in hhmmss format)
    const char* timeIn = &strTemp[7];
    strncpy(&dateTimeOut[6], timeIn, 6);
    
    // Terminate the combined dateTime string.
    dateTimeOut[12] = '\0';
    Serial.println("[DEBUG] dateTime: " + String(dateTimeOut));

    return true;
}

// A helper function to return a pointer to the nth occurrence of character c in string s.
const char* nth_strchr(const char* s, char c, int n) {
    while (*s) {
        if (*s == c) {
            n--;
            if (n == 0) return s;
        }
        s++;
    }
    return NULL;
}
