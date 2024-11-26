

satlist = 1:32; % use all GPS satellites
pvf = 2; % polynomial order used to remove the direct signal.
% this can be smaller, especially for short elevation angle ranges.

% the avg_maxRH variable will store  a crude median reflector height 
% for a single day/site
avg_maxRH = [];

freqtype=1;

% rule of thumb, you should not think you are correctly estimating
% RH when it is less than 2*lambda, which is 40-50 cm, depending on
% the wavelength (l1 vs l2).

minRH   = 0.4; % meters
maxArcTime = 4; % one hour 
% 
% Mininum number of points. This value could be used as QC
minPoints = 100; %it is totally arbitrary for now.

emin = 5; emax = 30;

ediff = 10;

% get wavelength (right now just L1 GPS) 
cf  = 0.1902936; 
w=4*pi/cf;


% checking azimuths in 45 degree bins  %will want to constrain this more
% for Snowfarm
azrange = 45; %
%azrng = [215 240; 270 315; 315 360] 
naz = round(360/azrange);

%naz =1;

for a=1:1  %just testing in one loop but 
 
    % window by these azimuths
        % azim1 = (a-1)*azrange;
        % azim2 = azim1 + azrange;
     azim1 = 225;
     azim2 = 360-45;
    %  window by satellite
    length(prn)
    for kk = 1:length(prn)
      sat=prn(kk)
        
      el = gps_snr_data(sat).el;
      az = gps_snr_data(sat).az;
      snr = gps_snr_data(sat).snr;

      i=find(el>emin&el<emax&az>azim1&az<azim2&~isnan(az)&~isnan(el))
      if(max(i)>length(el))
          i=find(el>emin&el<emax&az'>azim1&az'<azim2);
      end

      % in some cases you have both ascending and descending arcs
      % in one azimuth bin that will fulfill this find statement,
      % but for cryosphere applications
      % it probably won't hurt you too much

      elevAngles =gps_snr_data(sat).el(i);
      dt = time(gps_snr_data(sat).cnt(end)) - time(gps_snr_data(sat).cnt(1))
      %keyboard
      if((max(elevAngles)-min(elevAngles))>ediff & length(i) > minPoints);% & dt/3600 < maxArcTime )

          %%%%%%%%%%%%%%%%%%%%%
          %% convert to linear from dB
          data = 10.^(gps_snr_data(sat).snr(i)/20);
          %
         % time = GPS_data(gps_snr_data(sat).cnt(i),1)+GPS_data(gps_snr_data(sat).cnt(i),2)/60+GPS_data(gps_snr_data(sat).cnt(i),3)/3600;
          meanUTC = mean(time);
          % time span of track in hours
          
          %    average azimuth for a track, in degrees
          azm = mean(gps_snr_data(sat).az(i));
          %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
          % detrend data
          p=polyfit(elevAngles, data,pvf);
          pv = polyval(p, elevAngles);

          
          saveSNR = smooth(data-pv)'; %remove the direct signal with a polynomial
          
          %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
          %we do the fft on the sine of the elevation angles 
          sineE = sind(elevAngles);

          [sortedX,j] = unique(sineE');
          %sortedX=sind(elevAngles)';
          % sort the data so all tracks are rising
          % this is our spatial frequency sampling size
          es = sind(0.01);
          Fs = 1/es;
          sortedY = saveSNR(j);
          sortedXint = min(sortedX):es:max(sortedX);
          %make the spacing uniform in sin(elev) space so we can fft
          sortedYint = interp1(sortedX, sortedY, sortedXint);
          L=max(sortedXint)-min(sortedXint);
          freq = fft(sortedYint);
          figure(a)
          hsolve = abs(fftshift(freq));
          plot(Fs/L*(-L/2:es:L/2)*cf/2,hsolve/max(hsolve));
          xlim([-10 10])
          keyboard
          hold on
        kk

       end
  end
end
