import sys
import os
import warnings
sys.path.append("../db")

if not sys.warnoptions:
    warnings.simplefilter("ignore")

from database import init_db, db_session
from models import Metadata, Output, Parameters

import pandas as pd
import geopandas as gpd
import numpy as np
import shapely.geometry
import json
import yaml
import configparser
import redis
import boto3
from datetime import datetime
from collections import OrderedDict
from hashlib import sha256
import urllib.request

import random
from shapely.ops import cascaded_union
from shapely.geometry import Point

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


def gen_run(model_name, params):
    
    params.pop('scenario')
    params.pop('description')
    
    model_config = {
                    'config': params,
                    'name': model_name
                   }

    model_config = sortOD(OrderedDict(model_config))
    run_id = sha256(json.dumps(model_config, cls=NpEncoder).encode('utf-8')).hexdigest()

    # Add to model set in Redis
    r.sadd(model_name, run_id)
    
    run_obj = {'status': 'SUCCESS',
     'name': model_name,
     'config': model_config["config"],
     'bucket': bucket,
     'key': f"results/{model_name}_results/{run_id}.csv"
    }

    run_obj['config']['run_id'] = run_id
    run_obj['config'] = json.dumps(run_obj['config'], cls=NpEncoder)
    
    # Create Redis object
    r.hmset(run_id, run_obj)
    
    return run_id, model_config, run_obj
      

def sortOD(od):
    res = OrderedDict()
    for k, v in sorted(od.items()):
        if isinstance(v, dict):
            res[k] = sortOD(v)
        else:
            res[k] = v
    return res                                

def process_herbage(herbage, scen, scenarios, grange):
    """
    Primary function for processing grange
    """

    # subset for the correct scenario
    herbage = herbage[herbage['scenario'] == scen]

    herbage['geometry'] = herbage.apply(lambda x: Point(x.longitude, x.latitude), axis=1)

    # obtain scenario parameters
    params = scenarios[scenarios['scenario']==scen].iloc[0].to_dict()

    run_id, model_config, run_obj = gen_run(model_name, params)

    # generate temp CSV and push it to S3
    herbage.to_csv("tmp.csv", index=False)
    s3_bucket.upload_file("tmp.csv", run_obj['key'], ExtraArgs={'ACL':'public-read'})

    # Add metadata object to DB
    meta = Metadata(run_id=run_id, 
                    model=model_name,
                    raw_output_link= f"https://model-service.worldmodelers.com/results/{model_name}_results/{run_id}.csv",
                    run_label=herbage.description.iloc[0],
                    point_resolution_meters=25000)
    db_session.add(meta)
    db_session.commit()

    # Add parameters to DB
    for param in grange['parameters']:
        # ensure that no null parameters are stored
        if not pd.isna(params[param['name']]):
            if param['metadata']['type'] == 'ChoiceParameter':
                p_type = 'string'
                p_value = params[param['name']]
            elif param['name'] == 'temperature':
                p_type = 'float'
                p_value = float(params[param['name']])
            else:
                p_type = 'integer'
                p_value = int(params[param['name']])

            param = Parameters(run_id=run_id,
                              model=model_name,
                              parameter_name=param['name'],
                              parameter_value=p_value,
                              parameter_type=p_type
                              )
            db_session.add(param)
            db_session.commit()
        
    gdf = gpd.GeoDataFrame(herbage)
    gdf = gpd.sjoin(gdf, admin2, how="left", op='intersects')
    gdf['run_id'] = run_id
    gdf['model'] = model_name
    if 'geometry' in gdf:
        del(gdf['geometry'])
        del(gdf['index_right'])
        
    return gdf, run_id


##################################################
#### DATA PREPARATION AND PREPROCESSING STEPS ####
##################################################

config = configparser.ConfigParser()
config.read('../REST-Server/config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

profile = "wmuser"
bucket = "world-modelers"

session = boto3.Session(profile_name=profile)
s3 = session.resource("s3")
s3_client = session.client("s3")
s3_bucket= s3.Bucket(bucket)

scenarios = pd.read_csv('Scenarios.csv')
grids = pd.read_csv('Experiment 2020-01 - Gridcell Centre Points.csv')

with open('../metadata/models/G-Range-model-metadata.yaml', 'r') as stream:
    grange = yaml.safe_load(stream)    

admin2 = gpd.read_file("gadm36_ETH_shp/gadm36_ETH_2.shp")
admin2['country'] = admin2['NAME_0']
admin2['state'] = admin2['NAME_1']
admin2['admin1'] = admin2['NAME_1']
admin2['admin2'] = admin2['NAME_2']
admin2['GID_2'] = admin2['GID_2'].apply(lambda x: x.split("_")[0])
admin2['GID_1'] = admin2['GID_1'].apply(lambda x: x.split("_")[0])

eth = cascaded_union(admin2.geometry)

# download APSIM files
print("Downloading G-Range files...")
urllib.request.urlretrieve("https://world-modelers.s3.amazonaws.com/data/CSIRO/G_Range_Backcast.csv", "G_Range_Backcast.csv")
print("Download complete!")

herbage = pd.read_csv('G_Range_Backcast.csv')

# obtain lat/lon from grid file
herbage = herbage.merge(grids, how='left', left_on='gridcell_id', right_on='CellId')

# Set up datetime field
herbage['datetime'] = herbage.month.apply(lambda x: datetime(year=int(x.split('-')[0]),month=int(x.split('-')[1]),day=1))

# add in parameters from scenarios dataframe
herbage = herbage.merge(scenarios, on='scenario', how='left', suffixes=(False, False))

model_name = grange['id']

outputs = {}
for o in grange['outputs']:
    outputs[o['name']] = o
    
scenario_list = herbage.scenario.unique()

param_cols = list(scenarios.columns)
base_cols = list(herbage.columns)

##################################################
##################################################

if __name__ == "__main__":
# process G-Range backcast results
    for scen in scenario_list:

        # subset for the correct scenario
        herbage_ = herbage[herbage['scenario'] == scen]

        # drop rows where yield fields are NA
        # herbage = herbage.dropna(subset=['yield','rel_anomaly_yield'])

        gdf, run_id = process_herbage(herbage_, scen, scenarios, grange)

        print(f"Processing G-Range with run_id {run_id}")

        for feature in [i['name'] for i in grange['outputs']]:
            gdf_ = gdf
            gdf_['feature_name'] = feature
            gdf_['feature_value'] = gdf_[feature]
            gdf_['feature_description'] = outputs[feature]['description']

            db_session.bulk_insert_mappings(Output, gdf_.to_dict(orient="records"))
            db_session.commit()    