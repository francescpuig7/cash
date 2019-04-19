from datetime import datetime
import pandas as pd
from os import path

class Utils(object):

    def __init__(self):
        pass

    def check_license(self, code, dt):
        print(code)
        if datetime.now() <= datetime.strptime(dt, '%Y/%m/%d'):
            return True
        else:
            return False

    def check_code(self, code):
        filename = path.join(path.dirname(path.realpath(__file__)), 'keys.csv')
        df_keys = pd.read_csv(filename)
        codes = list(df_keys['code'])
        if code in codes:
            return True
        else:
            return False
