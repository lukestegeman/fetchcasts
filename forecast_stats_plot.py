import pickle
import model_info
import re

#import numpy as np
#from matplotlib import pyplot as plt

series = [('mag4_2019', '.*', 'MAG4'),
          ('UMASEP', '.*/10MeV', 'UMASEP-10'),
          ('UMASEP', '.*/30MeV', 'UMASEP-30'),
          ('UMASEP', '.*/50MeV', 'UMASEP-50'),
          ('UMASEP', '.*/100MeV', 'UMASEP-100'),
          ('UMASEP', '.*/500MeV', 'UMASEP-500'),
          ('SEPSTER', '.*', 'SEPSTER'),
          ('SEPSTER2D', '.*', 'SEPSTER2D')]

ym = set()

# First pass just to get the date axis
stats = pickle.load(open('iswa_stats.pickle', 'rb'))
for k in stats.keys():
    if len(k) == 3:
        model, flavor, yearmonth = k
        ym.add(yearmonth)
ym = np.array(sorted(ym))

# Now grab the data
data = np.zeroes((len(ym), len(series)))
for k in stats.keys():
    if len(k) != 3:
        continue
    model, flavor, yearmonth = k
    ym_ix = np.argwhere(ym == yearmonth)[0]
    for series_ix, series_model, flavor_regex, label in enumerate(series):
        if model == series_model and re.match(flavor_regex, flavor):
            data[ym_ix][series_ix] += stats[k]
