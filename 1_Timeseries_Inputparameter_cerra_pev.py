# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 18:42:30 2026

@author: Adhikari 
based on era5_Adina
changes made to work properly with lambert conical projection
"""
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import mapping
from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap
from shapely.geometry import Point
import xarray as xr
import rioxarray
import numpy as np
from pyproj import Transformer
import pyproj
import datetime as dt
import numpy as np
import time
from tqdm import tqdm
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import xarray as xr
from matplotlib.colors import LinearSegmentedColormap
import skimage
import multiprocessing as mp 
import os

def geocode_ds(ds):
    resolution = 5500 #resolution of cerra dataset
    geo_string = f"+proj=longlat +a={6371229} +b={6371229} +no_defs"#sphere used in lambert
    proj_string = (
        "+proj=lcc +lat_1=50 +lat_2=50 +lat_0=50 +lon_0=8 "
        "+x_0=0 +y_0=0 +a=6371229 +b=6371229 +units=m +no_defs"
        )   #projection metadata from cerra; contains sphere radius, northing easting origin 
    
    ds.rio.write_crs(proj_string, inplace=True)
    # lcp = pyproj.CRS(proj_string)
    trans_geo_to_lcc = Transformer.from_crs(geo_string, proj_string, always_xy=True, accuracy=0.0) #transformer object
    
    easting0, northing0 = trans_geo_to_lcc.transform(ds.longitude.values[0,0], ds.latitude.values[0,0]) #northing easting of first point
    # easting0, northing0
    ds['x'] = [easting0+i*resolution for i      #all grids are equidistant, so added resolution to the easting of the origin
            in range(ds.x.shape[0])]            #whil
    ds['y'] = [northing0+i*resolution for i 
            in range(ds.y.shape[0])]
    ds = ds.rio.set_spatial_dims(x_dim="x", y_dim="y")   #dataset is geocoded now
    
    return ds



def calc_mean(mask, yr):
    ''' 
    First, the x,y in the datasets have to be given lambert easting northing.
    This function crops the precipitation accoprding to the shapefile.
    
    Parameter:
        file_path -path of the netcdf-file
        precip - the precipitation data as three dimensional array for each 
                    relevant timestep
    '''
    
   
    try:
        netcdf_path = r".\pet\cerra\monthly\annual_lagged"
        
        ds = xr.open_dataset(os.path.join(netcdf_path, f"{yr}.nc"))  
        ds = geocode_ds(ds)
        rr = ds['eva']
        mask_3d = np.broadcast_to(mask, rr.shape)
        mask_array = xr.DataArray(mask_3d, coords=rr.coords, dims=rr.dims)
        rr = rr.where(mask_array, np.nan, drop = True)
        rr = rr.where(rr != -9999, np.nan)
        rr_numpy = rr.values
        import skimage.measure
        rr_catch = skimage.measure.block_reduce(rr_numpy, 
                    block_size=(1, rr_numpy.shape[1], rr_numpy.shape[2]), 
                    func=np.nanmean)
        rr_catch = rr_catch.reshape(-1)*1000/1000*(-1) #pet already in mm/day and positive
        rr_catch[rr_catch < 0] = 0
        rr_catch = rr_catch.round(3)
        
        times = ds['valid_time'].values
        date = pd.to_datetime(times)
        
        ds.close()
        
    except Exception as e:
        print("Error: " + str(e) + str(yr))
    except TimeoutError as f:
        print('TimeoutError: ' + str(f) + str(yr))
    
    return rr_catch, date




netcdf_path = r".\pet\cerra\monthly\annual_lagged"
# shapefile_path = "D:\\Daten\\GIS\\Study_Area\\EZG_use_WGS84.shp"

out_Path = r".\pet\cerra\catchment_results\eto"
out_trend =r".\pet\cerra\catchment_results\trend_plots" 
out_Path_Plot = r".\pet\cerra\catchment_results\grids"
shapefile_path = r".\pet\cerra\catchments_all.shp"

years = np.arange(2001,2023,1)

if __name__ == '__main__':
    
    # Starting the multiprocessing
    pool = mp.Pool(processes=4)#mp.Pool(processes=mp.cpu_count()-4)
    proj_string = (
        "+proj=lcc +lat_1=50 +lat_2=50 +lat_0=50 +lon_0=8 "
        "+x_0=0 +y_0=0 +a=6371229 +b=6371229 +units=m +no_defs"
        )
    catchments = gpd.read_file(shapefile_path)
    catchments = catchments.to_crs(proj_string)
    # catchments = catchments.iloc[74:77]
    ds = xr.open_dataset(os.path.join(netcdf_path,"2001.nc"))
    ds = geocode_ds(ds)
    lon = ds['x'].values
    lat = ds['y'].values
    param = ds['eva']
        
    geometry = [Point(lon[i], lat[j]) for i in range(lon.shape[0]) for j 
                                                    in range(lat.shape[0])]
    netcdf_gdf = gpd.GeoDataFrame(geometry=geometry, crs = catchments.crs)
    start = dt.datetime.now()
    print("Preparation is in progress!")
    for num in np.arange(0,catchments.shape[0],1):
        # num = 107
        # EZG_ID = catchments.Field2.iloc[num]
        # catchment = catchments[catchments.Field2 == EZG_ID]
        EZG_ID = catchments.Pegel_ID.iloc[num]
        
        catchment = catchments[catchments.Pegel_ID == EZG_ID]
        if not os.path.exists(os.path.join(out_Path, f'{int(EZG_ID)}_cerra.eto')):
            try:
                points_in_shapefile = gpd.sjoin(netcdf_gdf, 
                                                catchment, 
                                                how="inner",
                                                predicate='intersects')
                
                if len(points_in_shapefile) == 0:
                    points_in_shapefile = gpd.sjoin_nearest(netcdf_gdf, 
                                                            catchment,
                                                            how="inner", 
                                                            distance_col="distance",
                                                            max_distance=5500+1) # +1 for floating point precision
                    
                    points_in_shapefile = points_in_shapefile[points_in_shapefile['distance']
                                                              == points_in_shapefile['distance'].min()]
                # points_in_shapefile.shape
                mask = np.zeros_like(ds.eva[0], dtype=bool)
                catchment_lon = points_in_shapefile['geometry'].x
                catchment_lat = points_in_shapefile['geometry'].y
                
                x_indices = [np.argmin(np.abs(lon - coord)) for coord in catchment_lon]
                y_indices = [np.argmin(np.abs(lat - coord)) for coord in catchment_lat]
                
                mask[y_indices,x_indices] = True
                ds.close()
                
                # rr = ds['eva'][0]
                # mask_array = xr.DataArray(mask, coords=rr.coords, dims=rr.dims)
                # rr = rr.where(mask_array, np.nan, drop = True)
                # print(rr)
            
                EZG_ID = int(EZG_ID)
                print(EZG_ID)    
                fig, ax = plt.subplots(figsize=(8,5.5))
                x_grid, y_grid = np.meshgrid(lon, lat)
                colors = [(0/256, 255/256, 0/256), (0, 205/256, 205/256)]
                cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=256)
                pcm = ax.pcolormesh(x_grid, y_grid, mask, cmap=cmap)
                catchments.boundary.plot(ax=ax, linewidth=1, color='black')
                catchment.boundary.plot(ax=ax, linewidth=1, color='red')
                ax.set_xlim([catchment.bounds.values[0][0]-5500*8, 
                             catchment.bounds.values[0][2]+5500*8])
                ax.set_ylim([catchment.bounds.values[0][1]-5500*8, 
                             catchment.bounds.values[0][3]+5500*8])
                ax.set_title('EZG ' + str(EZG_ID))
                plt.savefig(os.path.join(out_Path_Plot, f'{EZG_ID}_eto_cerra.png'))
                plt.show()
                plt.close()
                
                
                print('Preparation is done!', dt.datetime.now() - start)
                time.sleep(1)
                
                
                start = dt.datetime.now()
                print("Calculating mean precipitation for catchment " + str(EZG_ID) + 
                      " is in process")
            
                
                i = years.shape[0]
                result = pool.starmap(calc_mean, tqdm(zip([mask]*i, years), 
                                                total=i))
                
                mean_param = [tupel[0] for tupel in result]
                mean_param = [wert for array in mean_param for wert in array]
                dates = [tupel[1] for tupel in result]
                dates = [wert for array in dates for wert in array]
                  
                
                df = pd.DataFrame({'datetime': dates, 'pev': mean_param})
                
                # Add missing values
                idx = pd.date_range(start=str(years[0])+'-01-01 00:00:00',  #this changed to 1-20 to match with dataset
                                    end=str(years[-1])+'-12-31 01:55:00', freq='1h') #change this to 23:55:00
                df.set_index(df.columns[0], inplace=True)
                df = df.reindex(idx, fill_value=pd.NA)
                df.reset_index(inplace=True)
                df.columns = ['datetime', 'pev']
                    
                print('Calculating mean precipitation is done!', dt.datetime.now() - 
                      start)
                time.sleep(1)
                
                   
                start = dt.datetime.now()
                print("starting to save in txt-file")
                
                df['year'] = df['datetime'].dt.year
                df['month'] = df['datetime'].dt.month
                df['day'] = df['datetime'].dt.day
                df['hour'] = df['datetime'].dt.hour
                df['minute'] = df['datetime'].dt.minute
                df['pev'] = df['pev'].round(3)
                # df['pev'] = np.nan_to_num(df['pev'], nan=-9999)
                
                # df = df[['year', 'month', 'day', 'hour', 'minute', 'pev']]
                df = df[['year', 'month', 'day', 'hour', 'pev']]
                
                df.to_csv(os.path.join(out_Path, f'{EZG_ID}_cerra.eto'),
                          sep='\t', index=False, header=False)
                
                
                print("Saving for catchment " + str(EZG_ID) + " took:", 
                      dt.datetime.now() - start)
                
            except:
                print(f'Error in catchment {EZG_ID}')
            # break
        # break
        # if num > 115+45:
        #     break