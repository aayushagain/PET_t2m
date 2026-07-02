# PET_t2m
Comparison of different potential evapotranspiration and 2m air temperature datasets for catchments. 
Summary of datasets used and results for catchments is provided in the Summary.pdf.

**0_PET_t2m_datasets_download_and_comparison**
  **1, Downloading and preparing dataset**
  A. METREF
    Based on https://gitlab.com/helpdesk.landsaf/lsasaf_data_access/-/tree/main/examples/thredds
    An issue with getting pet datasets from date x to date y was that date time stamps were assigned randomly, oscillating around the starting date. 
    Fixed here by downloading .nc for each day, then merging the dataset into single nc. 

  B. ERA5_Land
    PET accumulated for 24 hours in the downloaded dataset, which is converted to hourly dataset. 

  C. CERRA 
    CERRA forecasts were used for 3 hour gaps between reanalysis. Accumulation to forecast horizon were converted to hourly values.
    CERRA uses area preserving LCC projection. Catchments were converted to LCC to prevent data loss. 

  D. hPET dataset
    multithreading for downloading. 
    for clipping, a minor error in code (provided along with data) was fixed. 

  E. HOSTRADA and monthly PET Dataset from DWD
    Both datasets were available in similar format. Same function used for downloading both. 
    Certain website attributes are hardcoded and commented out. 
    monthly PET dataset was available only in ASCII format, which was converted into netcdf and geocoded.

  **2, Comparing the datasets** 
    Datasets were only compared after obtaining time series from 1_ts_for_catchment.
    A. pet dataset plots
      - these functions create comparative plots for all pet datasets
      - cumulative pet for year plotted 
      - cumulative pet for each month for all years are plotted
      - average pet for each hour in each month are averaged and plotted 
      - average pet for each hour and its range is plotted 
    B. t2m dataset plots
      - these functions create comparative plots for all t2m datasets
      - average t2m for year plotted 
      - averate t2m for each month for all years are plotted
      - average t2m for each hour in each month are averaged and plotted 
      - average t2m for each hour and its range is plotted 
    C. metric plots
      - creates metric matrix for each catchment for all pet datasets
      - metrices calculated by taking all data at once, summer, winter, spring and autumn months separately 
      PET:
          - PBIAS, MAE, correlation with respect to one another, violin plot for distribution of the datasets
          - cumulative monthly (ERA5, ERA5Land, hPET, CERRA, METREF, mPET), 
          - cumulative daily (ERA5, ERA5Land, hPET, CERRA, METREF), 
          - and hourly pet (ERA5, ERA5Land, hPET, CERRA)
          - correlation
              - if all datasets normal Pearson
                  - else spearman
     t2m
        - PBIAS, MAE, correlation with respect to one another, violin plot for distribution of the datasets
            - hourly (ERA5, ERA5Land, CERRA, HOSTRADA)
        - correlation
            - if all datasets normal Pearson
                - else spearman
    D. Distribution of errors
      - catchment elevation and catchment slope vs PET PBIAS, PET MAE: monthly PET taken as reference against ERA5, ERA5_Land, hPET, CERRA
      - catchment elevation and catchment slope vs t2m PBIAS, t2m MAE: HOSTRADA taken as reference against ERA5, ERA5_Land, CERRA 

**1_Timeseries_Inputparameter_cerra_pev**
  - sample script to obtain timeseries of pet from CERRA dataset at hourly interval
  - range, timesteps changed according to dataset
