#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  2 11:02:09 2018

@author: jdlara

This code is used to generate a model for the optimal allocation of Standing
Dead biomass in California generated during the period 2012 - 2017 into distribution
feeders. 

"""

from __future__ import division
from pyomo import environ as pm
from pyomo.opt import SolverFactory
import site
site.addsitedir('src/')
import db_tools as db
#import pw_cost as pw

dbname = 'apl_cec'
user = 'jdlara'
passwd = 'Amadeus-2010'
engine = db.dbconfig(user, passwd, dbname)
db.add_engine_pidguard(engine)  


# tm is the name of the model as a shorthand for Transport Model
tm = pm.ConcreteModel()

##################### Define Sets ####################

# Define sets of the substations and biomass stocks and initialize them from data above.
tm.LANDINGS = pm.Set(initialize=db.getLandings, doc='Location of Biomass sources')
tm.FEEDERS = pm.Set(initialize=db.getFeeders, doc='Location of Feeders')
tm.ROUTES = pm.Set(dimen=2, doc='Allows routes from sources to sinks', initialize=db.getRoutes)


##################### Define Variables ####################

"""
This portion of the code defines the decision making variables, in general the
model will solve for the capacity installed per substation, the decision to
install or not, the amount of biomass transported per route and variable for
the total install cost resulting from the piecewise approximation
"""
#Continous variables
tm.CapInstalled = pm.Var(tm.FEEDERS, within=pm.NonNegativeReals, doc='Installed in units of 150 kW', bounds=(0,20))
tm.BiomassFlow = pm.Var(tm.ROUTES, within=pm.NonNegativeReals, doc='Biomass shipment quantities in tons over a route')
tm.Variable_Install_Cost = pm.Var(tm.FEEDERS, within=pm.NonNegativeReals, doc='Variable for PW of installation cost')

#Binary Variables
tm.InstallorNot = pm.Var(tm.FEEDERS, within=pm.Binary,
                         doc='Decision to install or not')
tm.DeveloporNot = pm.Var(tm.LANDINGS, within=pm.Binary,
                         doc='Decision to developr the landing or not')

##################### Define Parameters ####################

# Cost related parameters, most of them can be replaced with cost curves
#Fixed Costs
tm.om_cost_fix = pm.Param(initialize=0, doc='Fixed cost of operation per installed kW')
tm.om_cost_var = pm.Param(initialize=0, doc='Variable cost of operation per installed kW')
tm.transport_cost = pm.Param(initialize=0.1343, doc='Freight in dollars per BDT per km')

#Variable Costs

number_of_units = [0, 1, 2, 3, 5, 10, 20]
cost = [0, 4000, 6500, 7500, 9300, 13000, 17000]

tm.InstallCosts = pm.Piecewise(tm.FEEDERS, tm.Variable_Install_Cost, tm.CapInstalled, pw_pts=number_of_units,  f_rule = cost, pw_constr_type = 'UB')

# Capacity related parameters
# For now considers only feeder capacity, not agregate substation bank
tm.max_capacity_feeders = pm.Param(tm.FEEDERS, initialize=db.getFeedersMax, doc='Max installation per site kW') #Pending to test query

tm.max_capacity_landings = pm.Param(tm.FEEDERS, initialize=db.getLandingsMax, doc='Max biomass per landing') #Pending to write query
tm.min_capacity_landings = pm.Param(tm.FEEDERS, initialize=10, doc='Min BDT biomass per landing')


# Operational parameters
tm.unit_capacity = pm.Param(initialize=150, doc = 'Capacity of the Unit')
tm.conversion_rate = pm.Param(initialize=833.3, doc='Heat rate kWh/BDT')
tm.capacity_factor = pm.Param(initialize=0.85, doc='Gasifier capacity factor')
tm.total_hours = pm.Param(initialize=8760, doc='Total amount of hours in the analysis period')

tm.distances = pm.Param(tm.ROUTES, initialize=db.getDistances, doc='Travel distance in km') # Pending to write query
tm.times = pm.Param(tm.ROUTES, initialize=db.getTimes, doc='Travel time in hours')          # Pending to write query

# Tariff 
tm.fit_tariff = pm.Param(tm.FEEDERS, initialize=0.197, doc='Feed-in Tarrif for Biomat in $/kWh') #Pending to test query

##################### Define Constraints ####################
"""
Define contraints
Here b is the index for sources and s the index for feeders
"""
# Binary decisions constraints 

def Install_Decision_Max_rule(mdl, s):
    return mdl.CapInstalled[s] <= mdl.InstallorNot[s] * mdl.max_capacity_feeders[s]

tm.Install_Decision_Max = pm.Constraint(tm.FEEDERS, rule=Install_Decision_Max_rule, doc='Limit the maximum installed capacity and bind the continuous decision to the binary InstallorNot variable.')

def Install_Decision_Min_rule(mdl, s):
    return mdl.CapInstalled[s] >= mdl.InstallorNot[s] * tm.unit_capacity

tm.Install_Decision_Min = pm.Constraint(tm.FEEDERS, rule=Install_Decision_Min_rule, doc='Limit the mininum installed capacity and bind the continuous decision to the binary InstallorNot variable.')


def Develop_Decision_Max_rule(mdl, b):
    return mdl.CapInstalled[b] <= mdl.InstallorNot[b] * mdl.max_capacity_landings[b]

tm.Develop_Decision_Max = pm.Constraint(tm.LANDINGS, rule=Develop_Decision_Max_rule, doc='Limit the maximum installed capacity and bind the continuous decision to the binary InstallorNot variable.')

def Develop_Decision_Min_rule(mdl, b):
    return mdl.CapInstalled[b] >= mdl.DeveloporNot[b] * mdl.min_capacity_landings[b]

tm.Develop_Decision_Min = pm.Constraint(tm.LANDINGS, rule=Develop_Decision_Min_rule, doc='Limit the mininum installed capacity and bind the continuous decision to the binary InstallorNot variable.')

# Balance Constraints 

def Feeders_Balance(mdl, s):
    return mdl.CapInstalled[s] * mdl.capacity_factor * mdl.total_hours * mdl.unit_capacity == (sum(mdl.conversion_rate * mdl.BiomassTransported[b, s] for b in mdl.SOURCES))

tm.Subs_Nodal_Balance = pm.Constraint(tm.FEEDERS,rule=Feeders_Balance, doc='Energy Balance at the feeders')

def Sources_Nodal_Limit_rule(mdl, b):
    return sum(mdl.BiomassTransported[b, s] for s in tm.FEEDERS) <= (tm.max_capacity_landings[b])

tm.LANDINGS_Nodal_Limit = pm.Constraint(tm.LANDINGS, rule=Sources_Nodal_Limit_rule, doc='Limit of biomass supply from a landing')


##################### Define Objective Function ##############################
def net_revenue_rule(mdl):
    return (
        # Fixed capacity installtion costs
        sum(mdl.Variable_Install_Cost[f] for f in mdl.FEEDERS) +
        # O&M costs (variable & fixed)
        sum((mdl.om_cost_fix + mdl.capacity_factor * mdl.om_cost_var) * mdl.CapInstalled[f]
            for f in mdl.FEEDERS) +
        # Transportation costs
        sum(mdl.distances[r] * tm.BiomassTransported[r] * mdl.transport_cost
            for r in mdl.ROUTES) +
        # Biomass acquisition costs.
        sum(mdl.biomass_cost[b] * sum(mdl.BiomassTransported[b, f] for f in mdl.FEEDERS)
            for b in mdl.LANDINGS) -
        # Gross profits during the period
        sum(mdl.fit_tariff[f] * mdl.CapInstalled[f] * mdl.capacity_factor * mdl.total_hours * tm.unit_capacity
            for f in mdl.FEEDERS)
          )

tm.net_profits = pm.Objective(rule=net_revenue_rule, sense=pm.minimize,
                              doc='Define objective function')

############################ Solve Model ####################################

opt = SolverFactory("gurobi")
results = opt.solve(tm, tee=True)