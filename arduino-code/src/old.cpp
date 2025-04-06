// #include <Arduino.h>
// #include <SD.h>
//
// #define GPSSerial Serial1
// #define GPSSerialEvent serialEvent1
//
// #define GPS_BAUD_RATE 38400
//
// #define GPS_BUFFER_SIZE 512
//
// #define MAX_BASNAME_LEN (8+1)
// #define MAX_FILENAME_LEN (MAX_BASNAME_LEN-1+1+3+1) // basename-null+dot+ext+null
//
// #define IDLE_THRESHOLD 10
//
// const int SDcard = 4;
//
// const char basenameDefault[] = "DEFAULT";
// String GPSBuffer = "";
// unsigned long bufferTime = millis();
// const char fileDuration = 'D';
//
// int numBlk = 0;
// char basenameOld[MAX_BASNAME_LEN];
//
// bool initSD();
// void getBasename(char basename[], const char dateTime[], bool GPSActive);
// bool getDateTime(const char stringOriginal[], char dateTimeOut[]);
// void datalog(const char basename[]);
// const char* nth_strchr(const char* s, int c, int n);
//
// void setup_old() {
//     Serial.begin(9600);
// //    while (!Serial);
//     initSD();
//
//     Serial1.begin(GPS_BAUD_RATE);
//
//     GPSBuffer.reserve(GPS_BUFFER_SIZE);
//     GPSSerial.flush();
// }
//
// void loop_old() {
//     if (GPSSerial.available()) {
//         char c = GPSSerial.read();
//         GPSBuffer += c;
//         bufferTime = millis();
//     }
//     bool GPSActive;
//     char dateTime[6+6+1]; //yymmddHHMMSS\0
//     char basename[MAX_BASNAME_LEN];
//     unsigned long startTime = millis();
//
//     unsigned long idleTime = startTime - bufferTime;
//
//     // Write only when no char coming from GPS
//     if (idleTime < IDLE_THRESHOLD || GPSBuffer.length() < 3) {return;}
//
//     Serial.println("[DEBUG] Starting.");
//     Serial.print(GPSBuffer);
//
//     GPSActive = getDateTime(GPSBuffer.c_str(), dateTime);
//     if (!GPSActive) {
//         GPSBuffer = "";
//         GPSBuffer.reserve(GPS_BUFFER_SIZE);
//         return;
//     }
//
//     getBasename(basename, dateTime, GPSActive);
//
//     datalog(basename);
//
//     if (strcmp(basename, basenameOld) != 0) {
//         strncpy(basenameOld, basename, strlen(basename)+1);
//         numBlk = 0;
//     }
//     numBlk++;
//     Serial.println("[DEBUG] number of blocks: " + String(numBlk));
//
//     GPSBuffer = "";
//     GPSBuffer.reserve(GPS_BUFFER_SIZE);
//
// }
//
// bool initSD() {
//     if (!SD.begin(SDcard)) {
//         Serial.println("[ERROR] Unable to initialise SD Card");
//         return false;
//     }
//
//     return true;
// }
//
// void datalog(const char basename[]) {
//     char filename[MAX_FILENAME_LEN];
//     strncpy(filename, basename, strlen(basename)+1);
//     strcat(filename, ".log");
//     Serial.println("[DEBUG] filename (GPS): " + String(filename));
//
//     File file = SD.open(filename, FILE_WRITE);
//     if (!file) {
//         Serial.println("[ERROR] Unable to open file: " + String(filename));
//         return;
//     }
//     // Size of buffer so we can check it has all been written
//     byte len1 = GPSBuffer.length();
//
//     byte len2 = file.print(GPSBuffer);
//
//     file.println();
//     file.close();
//
//     String prefix = "[DEBUG]";
//     if (len1 != len2) {prefix = "[ERROR]";}
//
//     Serial.println(prefix + " " + (100*len2/len1) + "%" + " of " + String(len1) + " bytes written to SD file '" + String(filename) + "'");
// }
//
// void getBasename(char basename[], const char dateTime[], bool GPSActive) {
//     if (!GPSActive) {
//         // Use default filename
//         strncpy(basename, basenameDefault, strlen(basenameDefault)+1);
//         return;
//     }
//
//     // Copys the first 6 char from dateTime into basename
//     strncpy(basename, dateTime, 6);
//     basename[6]='\0';
//
//     Serial.println("[DEBUG] Using filename: " + String(basename));
// }
//
// //void GPSSerialEvent() {
// //    char c = GPSSerial.read();
// //    GPSBuffer += c;
// //    bufferTime = millis();
// //}
//
// bool getDateTime(const char stringOriginal[], char dateTimeOut[]) {
//     char strTemp[82];
//     char* limInf = NULL;
//     char* limSup = NULL;
//     const char *dateIn;
//     const char *timeIn;
//     int len;
//
//     if (strlen(stringOriginal)==0) {
//         Serial.println("[DEBUG] empty GPS string.");
//         return false;
//     }
//
//     limInf = strstr(stringOriginal, "$GNRMC");
//
//     if (!limInf) {
//         Serial.println("[DEBUG] $GNRMC not found!");
//         return false;
//     }
//
//     if ((limInf[17]!='A')) {
//         Serial.println("[DEBUG] $GNRMC not found");
//         return false;
//     }
//
//     // find end of $GPRMC sentence:
//     limSup=strchr(limInf, '\n');
//     len=(limSup-limInf)+1;
//     strncpy(strTemp, limInf, min(len, sizeof(strTemp)-1));
//     strTemp[len]='\0';
//
//     // extract date, reordering components (DDMMYY -> YYMMDD):
//     dateIn = nth_strchr(strTemp, ',', 9) + 1;
//     dateTimeOut[0] = dateIn[4];  // year
//     dateTimeOut[1] = dateIn[5];  // year
//     dateTimeOut[2] = dateIn[2];  // month
//     dateTimeOut[3] = dateIn[3];  // month
//     dateTimeOut[4] = dateIn[0];  // day
//     dateTimeOut[5] = dateIn[1];  // day
//
//     // extract time, keeping the order (hhmmss):
//     timeIn = &strTemp[7];
//     strncpy(&dateTimeOut[6], timeIn, 6);
//
//     // terminate string:
//     dateTimeOut[12]='\0';
//     Serial.println("[DEBUG] dateTime: " + String(dateTimeOut));
//
//     return true;
// }
//
// // returns a pointer to the nth character in a string:
// const char* nth_strchr(const char* s, int c, int n)
// {
//     int c_count;
//     char* nth_ptr;
//
//     for (c_count=1,nth_ptr=strchr(s,c);
//          nth_ptr != NULL && c_count < n && c!=0;
//          c_count++)
//     {
//         nth_ptr = strchr(nth_ptr+1, c);
//     }
//
//     return nth_ptr;
// }
//
// //#include <Arduino.h>
// //
// //void setup() {
// //    Serial.begin(9600);
// //    Serial1.begin(38400);
// //}
// //
// //void loop() {
// //    if (Serial1.available()) {
// //        char c = Serial1.read();
// //        Serial.write(c);
// //    }
// //
// //    if (Serial.available()) {
// //        char c = Serial.read();
// //        Serial1.write(c);
// //    }
// //}