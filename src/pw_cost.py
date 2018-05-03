#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  2 11:00:26 2018

@author: jdlara
"""



def pwModel():
"""
The data for the piecewise cost of installation is given in # of gasifiers per
substation. This is why the sizes are integers. The cost is the total cost in $
of installing the amount N of gasifiers. Given that the gasifiers can only be
installed in integer number, this is a better approximation of the costs than
using a cost per kw. This explicit calculation needs to be replaced with a file.
"""



def calculate_lines(x, y):
    """
    Calculate lines to connect a series of points. This is used for the PW approximations. Given matching vectors of x,y coordinates. This only makes sense for monotolically increasing values.

    This function does not perform a data integrity check.
    """
    slope_list = {}
    intercept_list = {}
    for i in range(0, len(x) - 1):
        slope_list[i + 1] = (y[i] - y[i + 1]) / (x[i] - x[i + 1])
        intercept_list[i + 1] = y[i + 1] - slope_list[i + 1] * x[i + 1]
    return slope_list, intercept_list



"""
Each piecewise approximation requires and independent set for each one of the lines in the approximation. In this case, this is the piecewise approximation for the installations costs, and more maybe required soon.
"""
model.Pw_Install_Cost = Set(initialize=range(1, len(number_of_containers)),
                            doc='Set for the Piecewise approx of the installation cost')

"""