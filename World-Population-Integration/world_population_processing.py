import sys
import os
sys.path.append("../db")

from database import init_db, db_session
from models import Metadata, Output, Parameters

from shapely.geometry import Point
import geopandas as gpd
from osgeo import gdal
from osgeo import gdalconst

from datetime import datetime
from hashlib import sha256
from collections import OrderedDict
import json

def raster2gpd(InRaster,feature_name,nodataval=-9999):
    '''
    Description: 
        Takes the path of a raster (.tiff) file and produces a Geopandas Data Frame.
    Params:
        - InRaster: the path of the input raster file
        - feature_name: the name of the feature represented by the pixel values 
    '''

    # open the raster and get some properties
    ds       = gdal.OpenShared(InRaster,gdalconst.GA_ReadOnly)
    GeoTrans = ds.GetGeoTransform()
    ColRange = range(ds.RasterXSize)
    RowRange = range(ds.RasterYSize)
    rBand    = ds.GetRasterBand(1) # first band
    nData    = rBand.GetNoDataValue()
    if nData == None:
        nData = nodataval # set it to something if not set
    else:
        print("NoData value is {0}".format(nData))

    # specify the center offset (takes the point in middle of pixel)
    HalfX    = GeoTrans[1] / 2
    HalfY    = GeoTrans[5] / 2

    points = []
    for ThisRow in RowRange:
        RowData = rBand.ReadAsArray(0,ThisRow,ds.RasterXSize,1)[0]
        for ThisCol in ColRange:
            if RowData[ThisCol] != nData:
                
                # TODO: implement filters on valid pixels
                # for example, the below would ensure pixel values are between -100 and 100
                #if (RowData[ThisCol] <= 100) and (RowData[ThisCol] >= -100):

                X = GeoTrans[0] + ( ThisCol * GeoTrans[1] )
                Y = GeoTrans[3] + ( ThisRow * GeoTrans[5] ) # Y is negative so it's a minus
                # this gives the upper left of the cell, offset by half a cell to get centre
                X += HalfX
                Y += HalfY
                points.append([Point(X, Y),X,Y,RowData[ThisCol],feature_name])

    return gpd.GeoDataFrame(points, columns=['geometry','longitude','latitude','feature_value','feature_name'])


def gen_run(year):
    '''
    Take in population estimate year and generate `run_id` and a config
    '''
    model_name = 'world_population_africa'
    model_config = {
                    'config': {
                      "year": year
                    },
                    'name': model_name
                   }

    model_config =sortOD(OrderedDict(model_config))

    run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()
    return run_id, model_config


def sortOD(od):
    '''
    Sorts ordered dictionary to ensure consistency when hashing
    '''
    res = OrderedDict()
    for k, v in sorted(od.items()):
        if isinstance(v, dict):
            res[k] = sortOD(v)
        else:
            res[k] = v
    return res 

if __name__ == "__main__":

    init_db()

    # Load Admin2 shape from GADM
    admin2 = gpd.read_file('../gadm2/gadm36_2.shp')
    admin2['country'] = admin2['NAME_0']
    admin2['state'] = admin2['NAME_1']
    admin2['admin1'] = admin2['NAME_1']
    admin2['admin2'] = admin2['NAME_2']
    admin2 = admin2[['geometry','country','state','admin1','admin2']]

    # Cut down to a bounding box around Africa to save time/memory
    admin2 = admin2.cx[-28:58, -39:40]

    # Read in World Population Africa tiff files
    files = [i for i in os.listdir('Africa_1km_Population/') if '.tif' in i]

    # Specify possible parameters
    years = [2000, 2005, 2010, 2015, 2020]

    for year in years:
                    
        params = {'year': year}
        print(params)
        run_name = f"AFR_PPP_{year}_adj_v2.tif"
        run_id, model_config = gen_run(year)
                    
        # Add metadata object to DB
        meta = Metadata(run_id=run_id, 
                model=model_config['name'],
                raw_output_link= f"https://world-modelers.s3.amazonaws.com/results/world_population_africa/{run_name}",
                run_label="World Population Africa",
                point_resolution_meters=1000)
        db_session.add(meta)
        db_session.commit()
                    
        # Add parameters to DB
        for name, val in params.items():                
            param = Parameters(run_id=run_id,
                                model=model_config['name'],
                                parameter_name=name,
                                parameter_value=val,
                                parameter_type='string')
            db_session.add(param)
            db_session.commit()
                    
        # Convert Raster to GeoPandas
        InRaster = f"Africa_1km_Population/{run_name}"
        feature_name = 'population per 1km'
        gdf = raster2gpd(InRaster,feature_name)
                    
        # Spatial merge on GADM to obtain admin areas
        # Not sure if we want to do the same thing here for 
        # World Pop as for the Yield Anomalies
        gdf = gpd.sjoin(gdf, admin2, how="left", op='intersects')
                    
        # Set run fields: datetime, run_id, model
        gdf['datetime'] = datetime(year=2018, month=1, day=1)
        gdf['run_id'] = run_id
        gdf['model'] = model_config['name']
        gdf['feature_description'] = "Estimated population on 0.008333 degree (1km at equator) grid"
        del(gdf['geometry'])
        del(gdf['index_right'])

        # perform bulk insert of entire geopandas DF
        db_session.bulk_insert_mappings(Output, gdf.to_dict(orient="records"))
        db_session.commit()
