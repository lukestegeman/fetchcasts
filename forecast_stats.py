import pathlib
import os.path
import pickle

import model_info

# TODO remove hardcoded years
#year_range = (2017,2017+1)
year_range = (2019,2023+1)
stats = {}

for model in model_info.models:
    stats[(model,)] = 0
    if model in model_info.flavors:
        flavors = model_info.flavors[model]
        if model in model_info.inactive_flavors:
            flavors += model_info.inactive_flavors[model]
    else:
        flavors = ['']
    for flavor in sorted(flavors):
        p = pathlib.Path(os.path.join(model_info.model_root[model], flavor))
        stats[(model, flavor)] = 0
        if not p.is_dir():
            raise Exception(p, "does not exist")
        print(p)
        for year in range(*year_range):
            for month in range(1,12+1):
                yearmonth = f"{year:04d}/{month:02d}"
                pym = p / yearmonth
                if pym.is_dir():
                    n = sum(1 for json in pym.glob('*.json'))
                    print(f"  {yearmonth}: {n}")
                elif flavor == '':
                    # case that works for SEPMOD
                    ym_glob = yearmonth.replace('/', '-')
                    n = sum(1 for json in p.glob(f'**/*{ym_glob}*.json'))
                    print(f"  {yearmonth}: {n}")                    
                else:
                    n = 0
                    print(f"  {yearmonth}: -")
                stats[(model, flavor, yearmonth)] = n
                stats[(model, flavor)] += n
                stats[(model,)] += n

print("Aggregate stats:")
for k in stats:
    if len(k) < 3:
        print(k, ':', stats[k])

pickle.dump(stats, open('forecast_stats.pickle', 'wb'))
