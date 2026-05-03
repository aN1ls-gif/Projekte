# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 10:08:43 2026

@author: Nils
"""
# =============================================================================
# import os
# import sys
# 
# os.environ['PYSPARK_PYTHON'] = sys.executable
# os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable
# =============================================================================

import datetime
from dateutil.relativedelta import relativedelta

Now = datetime.datetime.now()
print(Now.date() + relativedelta(months=-6))