from datetime import datetime
from os import path
import csv

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
        reader = csv.reader(open(filename, 'r'))
        codes = []
        for index, row in enumerate(reader):
            codes.append(row[0])
        if code in codes:
            return True
        else:
            return False
