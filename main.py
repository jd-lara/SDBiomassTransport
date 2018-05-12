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
tm.LANDINGS = pm.Set(initialize=db.getLandings, doc='Location of Biomass sources') # Every single landing
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
# Installed capacity = how much of the feeder's capacity we use, NOT the same as the feeder's capacity
# in units of 150 kW b/c that's APL unit size and standard size for portable gasifiers - could be changed in other runs
tm.CapInstalled = pm.Var(tm.FEEDERS, within=pm.NonNegativeReals, doc='Installed in units of 150 kW', bounds=(0,20)) # cap of 20 * 150 kW = 3,000 kW because we only care about biomat
tm.BiomassFlow = pm.Var(tm.ROUTES, within=pm.NonNegativeReals, doc='Biomass shipment quantities in tons over a route') # flow from one landing to one feeder
tm.Variable_Install_Cost = pm.Var(tm.FEEDERS, within=pm.NonNegativeReals, doc='Variable for PW of installation cost') # installation cost per gasifier - economies of scale depending on # of units at each feeder

#Binary Variables

# yes/no whether to install any gasifiers
tm.InstallorNot = pm.Var(tm.FEEDERS, within=pm.Binary,
                         doc='Decision to install or not')

# yes/no whether to harvest any biomass from a landing set on a based minimum threshold of amount of biomass being harvested per landing, which is defined later
tm.DeveloporNot = pm.Var(tm.LANDINGS, within=pm.Binary,
                         doc='Decision to developr the landing or not')

##################### Define Parameters ####################

# Cost related parameters, most of them can be replaced with cost curves
#Fixed Costs
tm.om_cost_fix = pm.Param(initialize=0, doc='Fixed cost of operation per installed kW') # define - need to figure out a reasonable cost from Kristiana's data, cite interconnection agreements, which are public. Fixed costs = costs of initial installation
tm.om_cost_var = pm.Param(initialize=0, doc='Variable cost of operation per installed kW') # costs of maintaining the units OTHER than costs of the feedstock - marginal cost of operation not including fuel
tm.transport_cost = pm.Param(initialize=0.1343, doc='Freight in dollars per BDT per km') # from Bruce Springsteen

# Variable Costs

 # define cost of installing a gasifier based on the number of gasifiers at each feeder - this is from APL estimates, but we should update it to make it more realistic
 # the true relationship is nonlinear but these breakpoints define which portions of the curve to assume are linear - one slope value per interval between 0 and 1, 1 and 2, ... 10 and 20
number_of_units = [0, 1, 2, 3, 5, 10, 20]
cost = [0, 4000, 6500, 7500, 9300, 13000, 17000]

tm.InstallCosts = pm.Piecewise(tm.FEEDERS, tm.Variable_Install_Cost, tm.CapInstalled, pw_pts=number_of_units,  f_rule = cost, pw_constr_type = 'UB')

# Capacity related parameters
# For now considers only feeder capacity, not agregate substation bank
tm.max_capacity_feeders = pm.Param(tm.FEEDERS, initialize=db.getFeedersMax, doc='Max installation per site kW') #Pending to test query - Jose will work on this in Colorado

tm.max_capacity_landings = pm.Param(tm.LANDINGS, initialize=db.getLandingsMax, doc='Max biomass per landing') #Pending to write query 
tm.min_capacity_landings = pm.Param(tm.LANDINGS, initialize=10, doc='Min BDT biomass per landing') # minimum biomass used per landing


# Operational parameters
tm.unit_capacity = pm.Param(initialize=150, doc = 'Capacity of the Unit') # change this to use a different size portable gasifier unit
tm.conversion_rate = pm.Param(initialize=833.3, doc='Heat rate kWh/BDT')
tm.capacity_factor = pm.Param(initialize=0.85, doc='Gasifier capacity factor') # how many hours the unit operates in fraction of total hours in a year
tm.total_hours = pm.Param(initialize=8760, doc='Total amount of hours in the analysis period') # hours in one year even though eventually we will consider this as a 5-year model

tm.distances = pm.Param(tm.ROUTES, initialize=db.getDistances, doc='Travel distance in km') # Pending to write query
tm.times = pm.Param(tm.ROUTES, initialize=db.getTimes, doc='Travel time in hours')          # Pending to write query - not being used right now

# Tariff 
tm.fit_tariff = pm.Param(tm.FEEDERS, initialize=0.197, doc='Feed-in Tarrif for Biomat in $/kWh') #Pending to test query - $ per kWh - same as price

##################### Define Constraints ####################
"""
Define contraints
Here b is the index for sources and s the index for feeders
"""
# Binary decisions constraints 

def Install_Decision_Max_rule(mdl, s):
    return tm.CapInstalled[s] <= tm.InstallorNot[s] * tm.max_capacity_feeders[s] # installed capacity has to be < than feeder's total capacity times binary variable of installed or not

# apply the above constraint to every feeder to a set
tm.Install_Decision_Max = pm.Constraint(tm.FEEDERS, rule=Install_Decision_Max_rule, doc='Limit the maximum installed capacity and bind the continuous decision to the binary InstallorNot variable.')

def Install_Decision_Min_rule(mdl, s):
    return tm.CapInstalled[s] >= tm.InstallorNot[s] * tm.unit_capacity # not indexed, same for every feeder (AKA no [s] for unit_capacity)

tm.Install_Decision_Min = pm.Constraint(tm.FEEDERS, rule=Install_Decision_Min_rule, doc='Limit the mininum installed capacity and bind the continuous decision to the binary InstallorNot variable.')


def Develop_Decision_Max_rule(mdl, b):
    return tm.CapInstalled[b] <= tm.DeveloporNot[b] * tm.max_capacity_landings[b]

tm.Develop_Decision_Max = pm.Constraint(tm.LANDINGS, rule=Develop_Decision_Max_rule, doc='Limit the maximum installed capacity and bind the continuous decision to the binary InstallorNot variable.')

def Develop_Decision_Min_rule(mdl, b):
    return tm.CapInstalled[b] >= tm.DeveloporNot[b] * tm.min_capacity_landings

tm.Develop_Decision_Min = pm.Constraint(tm.LANDINGS, rule=Develop_Decision_Min_rule, doc='Limit the mininum installed capacity and bind the continuous decision to the binary InstallorNot variable.')

# Balance Constraints - crux of network analysis

def Feeders_Balance(mdl, s):
    return tm.CapInstalled[s] * tm.capacity_factor * tm.total_hours * tm.unit_capacity == (sum(tm.conversion_rate * tm.BiomassTransported[b, s] for b in tm.SOURCES))

tm.Subs_Nodal_Balance = pm.Constraint(tm.FEEDERS,rule=Feeders_Balance, doc='Energy Balance at the feeders') # energy generated by gasifiers must equal energy going into feeders

def Sources_Nodal_Limit_rule(mdl, b):
    return sum(tm.BiomassTransported[b, s] for s in tm.FEEDERS) <= (tm.max_capacity_landings[b]) # for every landing, flow out across each feeder it's serving < total biomass at that landing

tm.LANDINGS_Nodal_Limit = pm.Constraint(tm.LANDINGS, rule=Sources_Nodal_Limit_rule, doc='Limit of biomass supply from a landing')


##################### Define Objective Function ##############################
def net_revenue_rule(mdl):
    return (
        # Fixed capacity installtion costs
        sum(tm.Variable_Install_Cost[f] for f in tm.FEEDERS) +
        # O&M costs (variable & fixed)
        sum((tm.om_cost_fix + tm.capacity_factor * tm.om_cost_var) * tm.CapInstalled[f]
            for f in tm.FEEDERS) +
        # Transportation costs
        sum(tm.distances[r] * tm.BiomassTransported[r] * tm.transport_cost # has some glitches
            for r in tm.ROUTES) +
        # Biomass acquisition costs.
        sum(tm.biomass_cost[b] * sum(tm.BiomassTransported[b, f] for f in tm.FEEDERS)
            for b in tm.LANDINGS) -
        # Gross profits during the period
        sum(tm.fit_tariff[f] * tm.CapInstalled[f] * tm.capacity_factor * tm.total_hours * tm.unit_capacity
            for f in tm.FEEDERS)
          )

# minimize the above value of net cost
tm.net_profits = pm.Objective(rule=net_revenue_rule, sense=pm.minimize,
                              doc='Define objective function')

############################ Solve Model ####################################

opt = SolverFactory("gurobi")
results = opt.solve(tm, tee=True)