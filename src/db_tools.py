#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  2 10:58:20 2018

@author: jdlara
"""

from sqlalchemy import create_engine, pool
from sqlalchemy import event
from sqlalchemy import exc
import warnings
import pandas as pd
import os


######################Engine creation and database ############################

def add_engine_pidguard(engine):
    """Add multiprocessing guards.

    Forces a connection to be reconnected if it is detected
    as having been shared to a sub-process.

    """

    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        connection_record.info['pid'] = os.getpid()

    @event.listens_for(engine, "checkout")
    def checkout(dbapi_connection, connection_record, connection_proxy):
        pid = os.getpid()
        if connection_record.info['pid'] != pid:
            # substitute log.debug() or similar here as desired
            warnings.warn(
                "Parent process %(orig)s forked (%(newproc)s) with an open "
                "database connection, "
                "which is being discarded and recreated." %
                {"newproc": pid, "orig": connection_record.info['pid']})
            connection_record.connection = connection_proxy.connection = None
            raise exc.DisconnectionError(
                "Connection record belongs to pid %s, "
                "attempting to check out in pid %s" %
                (connection_record.info['pid'], pid)
            )

def dbconfig(user,passwd,dbname, echo_i=False):
    global engine
    """
    returns a database engine object for querys and inserts
    -------------

    name = name of the PostgreSQL database
    echoCmd = True/False wheather sqlalchemy echos commands
    """    
    str1 = ('postgresql+psycopg2://'+user+':'+ passwd + '@switch-db2.erg.berkeley.edu:5433/'+dbname) 
    
    engine = create_engine(str1, connect_args={'sslmode':'require'},echo=echo_i, isolation_level="AUTOCOMMIT", poolclass=pool.NullPool)
    return engine

######################Information retrieval queries############################


def getRoutes(model):
    e = engine
    df_routes = pd.read_sql_query('select landing_no, feeder_no from lemmav2.substation_routes where api_distance > 0 and api_distance is not null and center_ok is NULL;', e)
    route_list = list(zip(df_routes.landing_no, df_routes.feeder_no))
    return route_list

# Some landings are on roads that don't have legitimate google routes because road data used to create landings != road data used by google
    # but very few road routes have that error
    # creates a 99 instead of a real distance
    # Jose will fix errors in landings due to distance = 0 or distnace = 99
    # For purposes of Working with Chris, we can manually go through landing location errors rather than hard fixing it

def getFeeders(model):
    e = engine
    df_routes = pd.read_sql_query('select feeder_no from lemmav2.substation_routes where api_distance > 0 and api_distance is not null and center_ok is NULL;', e)
    feeder_list = df_routes["feeder_no"].unique()
    return feeder_list

def getLandings(model):
    e = engine
    # df_routes is a data frame of routes from the databse stored locally in memory
    df_routes = pd.read_sql_query('select landing_no from lemmav2.substation_routes where api_distance > 0 and api_distance is not null and center_ok is NULL;', e)
    biomass_temp = df_routes["landing_no"].unique()
    biomass_list = [ int(b) for b in biomass_temp]
    return biomass_list

# Landing ID numbers are not sequential, don't worry about what they actually are


def getFeedersMax(model, s):
    temp = pd.read_sql_query(('select uniform_generation_feederlimit_machine from "PGE".feeders_limits_data where feeder_no = '+ str(s) + ';'), engine)
    if temp.values.tolist()[0][0] < 0:
        return 1
    else:
        return temp.values.tolist()[0][0]
    
def getLandingsMax(model, b):
    temp = pd.read_sql_query((' '+ str(b) + ';'), engine)
    if temp.values.tolist()[0][0] < 0:
        return 1
    else:
        return temp.values.tolist()[0][0]    

def getDistances(model, l, f):
    temp = pd.read_sql_query((' '+ str(s) + ';'), engine)
    if temp.values.tolist()[0][0] < 0:
        return 1
    else:
        return temp.values.tolist()[0][0]  
    
def getTimes(model, l, f):
    temp = pd.read_sql_query((''+ str(s) + ';'), engine)
    if temp.values.tolist()[0][0] < 0:
        return 1
    else:
        return temp.values.tolist()[0][0]      