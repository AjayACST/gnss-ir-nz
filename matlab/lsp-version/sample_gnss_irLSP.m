


pvf = 2; % polynomial order used to remove the direct signal.
% this can be smaller, especially for short elevation angle ranges.

% get wavelength (right now just L1 GPS) Might want to add other
% constellations

cf  = 0.1902936; 
w=2*pi/cf;

LW=1;

freqtype=1;
maxHeight = 8; % (i.e. exclude reflector heights beyond this value)
desiredPrecision = 0.005; % 5mm is a reasonable level for now. 
frange = [0 8];

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% the params in this block we will want to have students change/set (gui or
% otherwise)

% rule of thumb, you should not think you are correctly estimating
% RH when it is less than 2*lambda, which is 40-50 cm, depending on
% the wavelength (l1 vs l2).

MinHt   = 1.5; % meters

% Mininum number of points. This value could be used as QC
minPoints = 50; %it is totally arbitrary for now.

emin = 6; emax =30;  %have found that the higher elevations are doing better

ediff = 10;
maxazdiff=8;

psllthresh=0.9;
dcthresh = 0.35;
snr_thresh=36;
sampling_interval =5;  %could get this from the data itself but just lazy
Avtime = 60;  %smoothing time in seconds
coeffMA = ones(1, Avtime/sampling_interval)*sampling_interval/Avtime;
% azim1 = 235;
% azim2 = 90;
azim =[270 315 360 0 45 90];
MaxHeight = 6;
minRH   = 0.4; % meters
maxdt = 30; %max jump in time/dropped data
prn = [1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20]
%end user parameters
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
for a=1:length(azim)-1  %just testing in one loop but that was for

    % window by these azimuths
    azim1=azim(a)

    azim2=azim(a+1)
    %  window by satellite
    for kk = 1:length(prn)

        sat=prn(kk);

        el = gps_snr_data(sat).el;
        segnum = zeros(size(el));
        maxseg=0;
        seglength=length(el);
        az = gps_snr_data(sat).az;
        snr = gps_snr_data(sat).snr;

        %find the contiguous arcs for each prn
        tm= time(gps_snr_data(sat).cnt);
        difft = diff(tm);
        ind = find(difft>maxdt); %(just fingd the max contiguous)
        
      
        if(~isempty(ind))
            segnum(1:ind(1)) = 0;

            if(length(ind)>1)
                for(zz=2:length(ind))
                    segnum(ind(zz-1):ind(zz))=zz-1;
                    maxseg = zz;
                end
                segnum(ind(end):end)=zz;
                maxseg = zz+1;

            else
                segnum(ind(1)+1:end)=1;
                maxseg = 1;
            end
        else
            maxseg = 1;
            segnum(:)=1;
        end


        maxseg;

        for ll = 0:maxseg
   
            
            %i=find(segnum==ll&el>emin&el<emax&az>azim1&az<azim2&~isnan(az)&~isnan(el)&~isnan(snr));  %%% added a condition here
            indel=find(segnum==ll&el>emin&el<emax&~isnan(az)&~isnan(el)&~isnan(snr));  %%% added a condition here
            azm = mean(gps_snr_data(sat).az(indel));
            indaz=find(gps_snr_data(sat).az(indel)>azim1&gps_snr_data(sat).az(indel)<azim2);
            mm=indel(indaz);
            if(length(mm)>minPoints)
               
            
                if((max(el(mm))-min(el(mm)))>ediff&&(max(az(mm))-min(az(mm)))<maxazdiff&&min(el(mm))<20)% & dt/3600 < maxArcTime )
                    disp("found a valid track")
                    [minAmp,pknoiseCrit,frange ] = quicky_QC(freqtype, maxHeight, ...
                        desiredPrecision, ediff,frange);

                    tmp=filter(coeffMA, 1, gps_snr_data(sat).snr(mm));  %
                    ind = find(tmp>snr_thresh);
                    snr_data=tmp(ind);
                    elevAngles =gps_snr_data(sat).el(mm(ind));
                    azm=mean(az(mm))
                    figure(8)
                    
                    polarscatter(az(mm)*pi/180, el(mm), 5,tmp)
                    hold on
                    %tmp= gps_snr_data(sat).snr(i);
                    %elevAngles=elevAnglesSM(ind);

                    figure(6)
                    hold off
                    plot(elevAngles, gps_snr_data(sat).snr(mm(ind)));
                    hold on
                    plot(elevAngles, snr_data);

                    %%%%%%%%%%%%%%%%%%%%%
                    %% convert to linear from dB
                   
                    data = 10.^(snr_data/20);
                    %
                    meanUTC = mean(time);

                    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                    % detrend data
                    p=polyfit(elevAngles, data,pvf);
                    pv = polyval(p, elevAngles);

                    tmp = smooth(data-pv)'; %remove the direct signal with a polynomial
                    %tmp = data-pv;
                    saveSNR= tmp(round(length(coeffMA)/2):end);
                    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                    %we do the fft on the sine of the elevation angles
                    sineE = sind(elevAngles(round(length(coeffMA)/2):end));
                    %sineE = sind(elevAngles);%(round(length(coeffMA)/2):end));

                    % sort the data so all tracks are rising
                    [sortedX,j] = unique(sineE');
                    %sortedX=sind(elevAngles)';

                    % this is our spatial frequency sampling size
                   
                    sortedY = saveSNR(j);

                    sortedX=sortedX(2:end-1);
                    sortedY=sortedY(2:end-1);

                    %make the spacing uniform in sin(elev) space so we can fft
                    % sortedXint = min(sortedX):es:max(sortedX);
                    % sortedYint = interp1(sortedX, sortedY, sortedXint);
                    % 
                    [ofac,hifac] = get_ofac_hifac( elevAngles,cf/2, maxHeight, desiredPrecision);
      
                    % call the lomb scargle code.  Input data have been scaled so that
                    % f comes out in units of reflector heights    (meters)
                    [f,p,dd,dd2]=lomb(sortedX/(cf/2), sortedY, ofac,hifac);
                    [ maxRH, maxRHAmp, pknoise ] = peak2noise(f,p,frange);
                    %  maxRH should be more than 2*lambda, or ~40-50 cm
                    % here i am restricting arcs to be < one hour.  long dt usually means
                    % you have a track that goes over midnite
                    maxObsE = max(elevAngles);
                    minObsE = min(elevAngles);%pknoise > pknoiseCrit & 
                   
                    if maxRHAmp > minAmp & maxRH > minRH  &  pknoise > pknoiseCrit & ...
                            (maxObsE-minObsE) > ediff;
                         figure(2)
                        subplot(2,1,1) % raw SNR data
                        plot(asind(sineE), saveSNR, '-','linewidth',LW);  hold on;
                        subplot(2,1,2) % periodogram
                        plot(f,p,'linewidth',LW) ; hold on;
                        axis([0 6 0 20])
                    end
                   
                  
                end
            end

        end
    end
end
