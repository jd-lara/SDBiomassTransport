# -*- coding: utf-8 -*-
"""
Created on Mon Jul 30 17:00:35 2018

@author: Carmen
"""

# TO JUST PULL FROM DATABASE

from sqlalchemy import create_engine, pool
from sqlalchemy import event
from sqlalchemy import exc
import warnings
import pandas as pd
import os


from __future__ import division
from pyomo import environ as pm
from pyomo.opt import SolverFactory
import site
site.addsitedir('Documents/SDBiomassTransport/src/')
import db_tools as db
#import pw_cost as pw

dbname = 'apl_cec'
user = 'jdlara'
passwd = 'Amadeus-2010'
engine = db.dbconfig(user, passwd, dbname)
db.add_engine_pidguard(engine)  

e = engine

df_routes = pd.read_sql_query('select feeder_no from lemmav2.substation_routes where api_distance > 0 and api_distance is not null and center_ok is NULL;', e)
feeder_list = df_routes["feeder_no"].unique()
df_landings = pd.read_sql_query('select landing_no from lemmav2.substation_routes where api_distance > 0 and api_distance is not null and center_ok is NULL;', e)
df_landings = df_landings["landing_no"].unique()
# figure out how to export as .csv
biomass_list = [ int(b) for b in biomass_temp]
   
# Go to Variable Explorer in Spyder to look at it as a table
# Always have to define lemmav2 as the schema and then .<table>