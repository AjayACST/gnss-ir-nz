%% List NMEA GPS Data for GNSS-IR
% GPSdaten=readGPS(filename)
% Probably don't need the numsats, height, lat_decimal, long_decimal,
% quality but keeping for now since might be interesting to see how it
% varies
%
% Definition: http://de.wikipedia.org/wiki/NMEA_0183
doInterp=1;
fid = fopen("25052200.LOG",'r');
TRUE = 1;
FALSE=0;

%look for the line feeds, 10 is the ASCII code for a line feed
dateilange = nnz(fread(fid)==10);


%Pointer wieder auf Beginn setzen
fseek(fid,0,'bof');

%Preallocate data
zeile = 1;
GPS_data=zeros(dateilange,12);
hour = 0;
minute = 0;
second = 0;
UTC = 0;
lat_degree = 0;
lat_decimal = 0;
long_decimal = 0;
doy = 0;
lat_A = '0';
long_A = '0';
velocity = 0;
course = 0;
numsats = 0;
height=0;
lat_decimal=0;
long_decimal=0;
quality = 0;
gpgga_strt =0;

gps_snr_data=struct('cnt',{},'el',{},'az',{},'snr',{});
gps_snr_data
newblock =FALSE;
block_count =1;

for ii = 1:32
  gps_snr_data(ii).prn = ii;
end
while ~feof(fid) %
    line = fgetl(fid); % get next line
    if isempty(line) % if empty
        continue     % continue
    elseif strncmp(line,'$GNGGA',6)|strncmp(line,'$GPGGA',6) % when line is $GPGGA
        newblock=TRUE;
        data = textscan(line,'%s%f%f%c%f%c%f%f%f%f',1,'delimiter',',');
        % compute UTC(HHMMSS.SSS), Universal Time Coordinated
        hour = floor(data{2}/10000);
        minute = floor((data{2}-hour*10000)/100);
        second = round(data{2}-floor(data{2}/100)*100);
        %UTC = strcat(num2str(hour),':',num2str(minute),':',num2str(second));


        %compute latitude(DDMM.MMM) and longitude(DDDMM.MMMM)
        lat_degree = floor(data{3}/100);
        lat_decimal = round((data{3}-lat_degree*100)/60*10^6)/10^6;
        lat_A = strcat(num2str(lat_degree+lat_decimal),data{4});

        long_degree= floor(data{5}/100);
        long_decimal = round((data{5}-long_degree*100)/60*10^6)/10^6;
        long_A = strcat(num2str(long_degree+long_decimal),data{6});

        numsats = data{8};

        %GPS-Quality:

        quality = data{7};

        %height of antenna above MSL (mean sea level)
        height = data{10};
        GPS_data(block_count,1:9)=[hour, minute, second, velocity, numsats, height, lat_decimal, long_decimal, quality];

     elseif strncmp(line,'$GPGSV',6)&&newblock==TRUE % when line is $GPGSV


         gsv(1).data = textscan(line,'%s%d%d%d%d%f%f%f%d%f%f%f%d%f%f%f%d%f%f%f*%c%c',1,'delimiter',',');
         num_msg=gsv(1).data{2};
         msg_n = gsv(1).data{3};
        
         if(msg_n==1)


             while(msg_n<num_msg)  %read all the GPGSV messages in the block
                 line = fgetl(fid); % get next line
                 %keyboard
                 if(strncmp(line,'$GPGSV',6))
                     tmp_line = textscan(line,'%s%d%d%d%d%f%f%f%d%f%f%f%d%f%f%f%d%f%f%f*%c%c',1,'delimiter',',');
                     msg_n = tmp_line{3};
                     num_msg=tmp_line{2};
                     gsv(msg_n).data = tmp_line;
                 else
                     break;
                 end
             end

             [prn, elev, az, snr]= read_gpgsv(gsv);
             elev

             for(jj=1:length(prn)) %there are up to 32 GPS satellites


                 if isempty(gps_snr_data(prn(jj)))
                     gps_snr_data(prn(jj)).cnt =  block_count;
                     gps_snr_data(prn(jj)).el=elev(jj);
                     gps_snr_data(prn(jj)).az=az(jj);
                     gps_snr_data(prn(jj)).snr=snr(jj);
                 else
                     gps_snr_data(prn(jj)).cnt = [gps_snr_data(prn(jj)).cnt block_count];
                     gps_snr_data(prn(jj)).el=[gps_snr_data(prn(jj)).el elev(jj)];
                     gps_snr_data(prn(jj)).az=[gps_snr_data(prn(jj)).az az(jj)];
                     gps_snr_data(prn(jj)).snr=[gps_snr_data(prn(jj)).snr snr(jj)];

                 end
             end
         end

    elseif strncmp(line,'$GNRMC',6)|strncmp(line,'$GPRMC',6) % when line is $GNRMC - end of block
        data = textscan(line,'%s%f%c%f%c%f%c%f%f%f%f%f%s',1,'delimiter',',');
        day = floor(data{10}/10^4);
        month = floor((data{10}-day*10^4)/100);
        year = 2000+data{10}-(day*10^4+month*100);
        GPS_data(block_count,10:12)=[day, month, year];
        


        block_count = block_count+1
        newblock=FALSE;
    else
        continue;
    end


end

time = GPS_data(1:block_count,1)*3600+GPS_data(1:block_count,2)*60+GPS_data(1:block_count,3);

if(doInterp ==1)
%%%%%%%%%%%%%%%%%%%%%%%This part below is new and deals with the
%%%%%%%%%%%%%%%%%%%%%%%quantization
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    for(ii=1:length(prn))
        prnnum = prn(ii);
        ind = find(abs(diff(gps_snr_data(prnnum).el))>.1);
        if(length(ind)>10)
            timeshort= time(gps_snr_data(prnnum).cnt(ind));
            elev=interp1(timeshort, gps_snr_data(prnnum).el(ind), time(gps_snr_data(prnnum).cnt));
            gps_snr_data(prnnum).el = elev';
          
        end
        % nice idea but doesn't work...
        % ind = find(abs(diff(gps_snr_data(prnnum).snr))>.1);
        % if(~isempty(ind))  % now reinterpolate SNR onto new time grid
        %     [snrshort,IA,IC] = unique(gps_snr_data(prnnum).snr(ind)+(gps_snr_data(prnnum).snr(ind+1)-gps_snr_data(prnnum).snr(ind))/2);
        %     timeinterpshort = time(gps_snr_data(prnnum).cnt(ind(IA)))
        %     snr=interp1(timeinterpshort,  snrshort , time(gps_snr_data(prnnum).cnt));
        %     gps_snr_data(prnnum).snr=snr';
        % 
        % end
    end

    
end



fclose(fid);


%
