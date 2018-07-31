# -*- coding: utf-8 -*-
"""
Created on Fri Jul 27 16:33:14 2018

@author: Carmen
"""

# helpful explanation of paths and how Python finds modules here: https://www.dummies.com/programming/python/how-to-find-path-information-in-python/
    # Python looks for packages in either the current working directory or whatever paths are listed in sys.path
    # You can add paths to sys.path by using site.addsitedir

import os
os.getcwd()
os.chdir("Documents/SDBiomassTransport/src")
os.chdir("SDBiomassTransport")
os.chdir("src")
import db_tools as db
os.chdir("../../../")


import site
site.USER_BASE
site.getuserbase() 
site.addsitedir('src/')
site.USER_SITE
site.sys.path

import sys
sys.path # this lists the search paths for modules
for p in sys.path:
    print(p)


sys.path.remove("C:\\Users\\Carmen\\Documents\\SDBiomasssTransport\\src")
