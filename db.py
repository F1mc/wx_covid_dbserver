import os
from enum import Enum, unique
import pytz
import pymongo
from pymongo import MongoClient
import datetime
import time
import json
import bson

@unique
class CONST(Enum):
    SUPPORTED_TABLES = ('table_v1','person_attr')
    SUPPORTED_QUERY = ('full_records', 'person','predict_result', 'by_objid', 'find')


connString = os.environ['MONGODB_CONNSTRING']
tz = os.environ['TZ'] #Asia/Shanghai
# tz = 'Asia/Shanghai'
tzinfo = pytz.timezone(tz)
client = MongoClient(connString, tz_aware=True, tzinfo=tzinfo)


def get():
    pass

def date_list():
    return list(datetime.date.today().timetuple()[:3])

class mdb():
    def __init__(self):
        self.db = client.covid_app
        self.person_attr = self.db.person_attr
        self.table_v1 = self.db.table_v1

    def __getitem__(self, key):
        return self.__dict__[key]

    def update(self, db, ):
        pass

    # 接收传入json，转换为存储格式
    @staticmethod
    def p_table_v1(data):
        try:
            for key, value in data['symptom'].items():
                if value not in [True, False, None]:
                    return None, 'symptom value illegal'
            if not isinstance(data['temp'],(int, float)):
                return None, 'temp value illegal'
            elif not isinstance(data['days_symp'],int):
                return None, 'days_symp value illegal'
        except:
            return None, 'unkonw main keys'
        ts = time.time()
        data['stamp'] = ts
        return data, None
    
    @staticmethod
    def p_person_attr(data):
        try:
            if not isinstance(data['age'],(int, float, None)):
                return None, 'age value illegal'
            elif data['sex'] not in ['male', 'female']:
                return None, 'sex value illegal'
        except:
            return None, 'unkonw main keys'
        ts = time.time()
        data['stamp'] = ts
        return data, None
        


