
function [prn, elev, az, snr]= read_gpgsv(gsv_data)

jj=1;

   for ii=1:length(gsv_data)
       if((~isempty(gsv_data(ii).data{6})&&~isempty(gsv_data(ii).data{7})&&~isempty(gsv_data(ii).data{8}))&&(~isnan(gsv_data(ii).data{5})&&gsv_data(ii).data{5}<=32))
           prn(jj)=gsv_data(ii).data{5};
           elev(jj) = cell2mat(gsv_data(ii).data(6));
           az(jj) = cell2mat(gsv_data(ii).data(7));
           snr(jj) = cell2mat(gsv_data(ii).data(8));
           jj=jj+1;

       end
       if((~isempty(gsv_data(ii).data{10})&&~isempty(gsv_data(ii).data{11})&&~isempty(gsv_data(ii).data{12}))&&(~isnan(gsv_data(ii).data{9})&&gsv_data(ii).data{9}<=32))
           prn(jj)=gsv_data(ii).data{9};
           elev(jj) = cell2mat(gsv_data(ii).data(10));
           az(jj) = cell2mat(gsv_data(ii).data(11));
           snr(jj) = cell2mat(gsv_data(ii).data(12));
           jj=jj+1;

       end
       if((~isempty(gsv_data(ii).data{14})&&~isempty(gsv_data(ii).data{15})&&~isempty(gsv_data(ii).data{16}))&&(~isnan(gsv_data(ii).data{13})&&gsv_data(ii).data{13}<=32))
           prn(jj)=gsv_data(ii).data{13};

           elev(jj) = cell2mat(gsv_data(ii).data(14));
           az(jj) = cell2mat(gsv_data(ii).data(15));
           snr(jj) = cell2mat(gsv_data(ii).data(16));
           jj=jj+1;

       end
       if((~isempty(gsv_data(ii).data{18})&&~isempty(gsv_data(ii).data{19})&&~isempty(gsv_data(ii).data{20}))&&(~isnan(gsv_data(ii).data{17})&&gsv_data(ii).data{17}<=32))
           prn(jj)=gsv_data(ii).data{17};

           elev(jj) = gsv_data(ii).data{18};
           az(jj) = cell2mat(gsv_data(ii).data(19));
           snr(jj) = cell2mat(gsv_data(ii).data(20));

           jj=jj+1;
       end
    
    
   end

%   info.num_sys = 1;
%   info.sys_unique = 'G';
%   info.num_obs_types = 1;
% end
