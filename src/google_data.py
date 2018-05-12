#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  3 17:01:16 2017

@author: jdlara
"""

# ALready done, don't re-run without Jose, interacts directly with google

import googlemaps
#from sqlalchemy import Table, Column, String, MetaData
from joblib import Parallel, delayed
import pandas as pd
       
def read_db(engine2):
    with engine2.connect() as conn:
        try:
            df_routes = pd.read_sql_query('select  ST_Y(ST_Transform(landing_geom,4326)) as source_lat, ST_X(ST_Transform(landing_geom,4326)) as source_lon, landing_no as source_id, ST_Y(ST_Transform(feeder_geom,4326)) as dest_lat, ST_X(ST_Transform(feeder_geom,4326)) as dest_lon, feeder_no as dest_id FROM lemmav2.substation_routes where api_distance is NULL and center_ok is NULL and linear_distance < 70000 order by RANDOM() limit 1;', conn)
            biomass_coord = df_routes.source_lat.astype(str).str.cat(df_routes.source_lon.astype(str), sep=',')
            biomass_coord = biomass_coord.values.tolist()
            biomass_coord = list(zip(list(set(biomass_coord)),df_routes.source_id.tolist()))
            
            substation_coord = df_routes.dest_lat.astype(str).str.cat(df_routes.dest_lon.astype(str), sep=',')
            substation_coord = substation_coord.values.tolist()
            substation_coord = list(zip(list(set(substation_coord)),df_routes.dest_id.tolist()))
        except:
            print('db_read_error')
            pass  
    conn.close()
    engine2.dispose()
    
    return biomass_coord,  substation_coord

def matching(biomass_coord, substation_coord, engine, APIkey='AIzaSyBZgFHHKf7cD3ZmZVHBOpItNImAlYSJ364'):
    gmaps = googlemaps.Client(key=APIkey)
    try:        
        matrx_distance = gmaps.distance_matrix(biomass_coord[0][0], substation_coord[0][0], mode="driving", departure_time="now", traffic_model="pessimistic")
        error = matrx_distance['rows'][0]['elements'][0]['status']
        if error != 'OK':
            db_str = ('UPDATE lemmav2.substation_routes set api_distance = -99, api_time = -99 where landing_no =' + str(biomass_coord[0][1]) +' and '+ 'feeder_no =' + str(substation_coord[0][1]) +';') 
        else:
            distance = (matrx_distance['rows'][0]['elements'][0]['distance']['value'])
            try:
                time = (1 / 3600) * (matrx_distance['rows'][0]['elements'][0]['duration_in_traffic']['value'])
            except KeyError:
                time = (1 / 3600) * (matrx_distance['rows'][0]['elements'][0]['duration']['value'])
                print("KeyError")
                pass
            db_str = ('UPDATE lemmav2.substation_routes set api_distance =' + str(distance)+','+ 'api_time = '+ str(time) + ' where landing_no =' + str(biomass_coord[0][1]) +' and '+ 'feeder_no =' + str(substation_coord[0][1]) +';') 
    except:
        print('Api error')
        pass
    
    with engine.connect() as conn:
        conn.execute(db_str)
        conn.close()
    engine.dispose()  

def task():
   x, y = read_db()
   #print(x,y)
   matching(x,y)     
   
#tm.sleep(6*3600)   
Parallel(n_jobs = 4)(delayed(task)() for i in range(25000))

