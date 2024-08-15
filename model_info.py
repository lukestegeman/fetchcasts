from os.path import join

default_root = 'iswa_data_tree/model/heliosphere/sep_scoreboard'

model_root = {
    'MAG4':      join(default_root, 'mag4_2019'),
    'MagPy':     join(default_root, 'MagPy'),
    'RELEASE':   join(default_root, 'RELEASE'),
    'SEPSTER':   join(default_root, 'SEPSTER'),
    'SEPSTER2D': join(default_root, 'SEPSTER2D'),
    'UMASEP':    join(default_root, 'UMASEP'),
    'SEPMOD':    'enlil2.9e',
    'SWPC'  :    'iswa_data_tree/composite/coupled/noaa-swpc',
    'SAWS_ASPECS':    join(default_root, 'SAWS_ASPECS'),
    'iPATH':     join(default_root, 'iPATH'),
    'GSU':       join(default_root, 'GSU_All_Clear'),
    'SPRINTS':   join(default_root, 'SPRINTS-SEP')
}

models = sorted(model_root.keys())

flavors = {
    'MAG4':['HMI-NRT-JSON',
            'V-HMI-NRT-JSON',
            'VPLUS-HMI-NRT-JSON',
            'VWF-HMI-NRT-JSON',
            'WF-HMI-NRT-JSON'],
    'MagPy':['2.X'],
    'RELEASE':['30Min/aceepam',
               '60Min/aceepam',
               '90Min/aceepam',
               '30Min/sohoephin',
               '60Min/sohoephin',
               '90Min/sohoephin'],
    'SEPSTER':['Parker',
               'WSA-ENLIL'],
    'SEPSTER2D':['1.X'],
    'UMASEP':['v3_X/100MeV',
              'v3_X/10MeV',
              'v3_X/30MeV',
              'v3_X/500MeV',
              'v3_X/50MeV'],
    'SWPC':['RSGA'],
    'SAWS_ASPECS':['1.X/Forecasts/Intensity',
                   '1.X/Forecasts/Probability',
                   '1.X/Forecasts/Profile',
                   '1.X/Nowcasts/Intensity',
                   '1.X/Nowcasts/Probability',
                   '1.X/Nowcasts/Profile'],
    'iPATH':['2.X/CME/ZEUS/JSON',
             '2.X/CME/ZEUS/10MeV',
             '2.X/CME/ZEUS/30MeV',
             '2.X/CME/ZEUS/50MeV',
             '2.X/CME/ZEUS/100MeV',
             '2.X/flare/ZEUS/JSON',
             '2.X/flare/ZEUS/10MeV',
             '2.X/flare/ZEUS/30MeV',
             '2.X/flare/ZEUS/50MeV',
             '2.X/flare/ZEUS/100MeV'],
    'GSU':['v0_1'],
    'SPRINTS':['1.X/Post_Eruptive']
}

inactive_flavors = {
    'UMASEP':['v2_0/100MeV',
              'v2_0/10MeV',
              'v20190101/100MeV',
              'v20190101/10MeV',
              'v20190101/500MeV',
              'v2_0/30MeV',
              'v2_0/500MeV',
              'v2_0/50MeV',
              'v2_1/100MeV',
              'v2_1/10MeV',
              'v2_1/30MeV',
              'v2_1/500MeV',
              'v2_1/50MeV']
}

accept = {
    'MAG4':        ['MAG4_*.json'],
    'MagPy':       ['MagPy-*.json'],
    'RELEASE':     ['HESPERIA_REleASE_*.json'],
    'SEPSTER':     ['sepster_*.json'],
    'SEPSTER2D':   ['sepster2D_*.json'],
    'UMASEP':      ['UMASEP*.json'],
    'SEPMOD':      ['SEPMOD.{year}-{month}*.json',
                    'SEPMOD.{year}-{month}*mev.txt',
                    'SEPMOD.{year}{month}*_geo_integral_tseries_timestamped',
                    'SEPMOD.{year}{month}*_geo_tseries_timestamped'],
    'SWPC':        ['*RSGA.txt'],
    'SAWS_ASPECS': ["SAWS_ASPECS*.json", "SAWS_ASPECS*.txt"],
    'iPATH':       ['ZEUS+iPATH_*.json', 'ZEUS+iPATH_*.txt'],
    'GSU':         ['GSU_All_Clear.*.json'],
    'SPRINTS':     ['SPRINTS_Post_Eruptive_*.json']
}
