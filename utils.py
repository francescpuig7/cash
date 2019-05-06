from dateutil.relativedelta import relativedelta
from datetime import datetime
from os import path
import csv


class Utils(object):

    def __init__(self):
        pass

    @staticmethod
    def check_license(code, dt):
        if datetime.now() <= datetime.strptime(dt, '%Y/%m/%d'):
            return True
        else:
            return False

    @staticmethod
    def check_code(code):
        filename = path.join('.', 'configs', 'keys.csv')
        reader = csv.reader(open(filename, 'r'))
        codes = []
        for index, row in enumerate(reader):
            codes.append(row[0])
        if code in codes:
            return True
        else:
            return False

    @staticmethod
    def three_days_warning(dt):
        three_days_date = datetime.now() + relativedelta(days=3)
        if three_days_date >= datetime.strptime(dt, '%Y/%m/%d'):
            return True
        else:
            return False
