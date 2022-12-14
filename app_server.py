from datetime import date,timedelta
import json
import os
from flask import *
from flask import Flask, current_app, request, jsonify, make_response
from db import mdb
from db import CONST
from wxapi import WX_API
from predict.predict import predict

from bson.objectid import ObjectId
from pymongo import DESCENDING, ASCENDING

app = Flask(__name__)
cdb = mdb()
pred = predict()

#################################################
##插入方法
#################################################
def check_exist(data):
    if data['table'] not in CONST.SUPPORTED_TABLES.value:
        return {'status':0, 'msg': 'unsupprted type of table'}, 1
    innerdata = data['value']
    docs = cdb[data['table']].find_one({"uuid": innerdata['uuid'], "stamp":innerdata['stamp']})
    if docs:
        current_app.logger.warning('timestamp duplicated, reject request')
        return {'status':0, 'msg': 'timestamp duplicated, reject request'}
    return None, None
    

def handle_insert(data, db):
    rs = db.insert_one(data)
    rsa, post_id = rs.acknowledged, str(rs.inserted_id)
    # 按照objectid查找记得转换objectID
    if rsa:
        return {'status':1, 'msg': f'operation succeeded, object id {post_id}'}
    else:
        return {'status':0, 'msg': 'operation failed'}

def handle_person(data):
    data_, _err = cdb.p_person_attr(data)
    if _err:
        return {'status':0, 'msg': _err}
    db = cdb.person_attr
    check = db.find_one({'uuid': data_['uuid']})
    if check:
        return {'status':0, 'msg': 'person with same uuid already exists'}
    return handle_insert(data_, db)

def handle_table(data,ver=1):
    if ver==1:
        data_ , _err= cdb.p_table_v1(data)
        if _err:
            return {'status':0, 'msg': _err}
        db = cdb.table_v1
    else:
        return {'status':0, 'msg': 'unsupprted type of table'}
    return handle_insert(data_, db)

@app.route('/insert', methods=['POST'])
def handler_insert():
    ip = request.remote_addr
    current_app.logger.info(f'insert request from {ip}')
    data = request.get_data()
    dict_data = json.loads(data)
    v, err = check_exist(dict_data)
    if err:
        return jsonify(v)
    if dict_data['table'] == 'person_attr':
        res = handle_person(dict_data['value'])
    elif dict_data['table'] == 'table_v1':
        res = handle_table(dict_data['value'], ver=1)
    else:
        res = {'status':0, 'msg': 'unsupprted type of table'}

    return jsonify(res)

##############################################################




##############################################################
#请求方法
##############################################################

def handle_f_records(data, days=7):
    if 'uuid' not in data.keys():
        return {'status':0, 'msg': 'please give the uuid'}
    if 'table' not in data.keys():
        db = cdb.table_v1
    else:
        db = cdb[data['table']]
    result = dict()
    dates = list()
    #####后面要考虑下0点到4点怎么计算日期
    today = date.today()
    time_len = timedelta(days=days)
    for record in db.find({'uuid': data['uuid']}).sort('stamp', DESCENDING):
        date_ = date(*record['date'])
        if date_ in dates:
            continue
        else:
            dates.append(date_)
            record['_id']=str(record['_id'])
            result[date_.strftime(f'%Y-%m-%d')] = record
        if today - date_ >= time_len:
            break
    if result:
        # result['_id']=str(result['_id']) #_id的objectid不能被网页直接返回
        return {'status': 1, 'msg': 'query succeed', 'value': result}
    else:
        return {'status': 1, 'msg': 'query succeed but no data matched can be found', 'value': result}

def handle_predict(data):
    id = data['uuid']
    if not isinstance(id, str):
        return {'status':0, 'msg': 'uuid value illegal'}
    db = cdb.person_attr
    p_res = db.find_one({'uuid': data['uuid']})
    if p_res:
        db_t = cdb.table_v1
        # today = date.today().timetuple()
        # today = list(today)[:3]
        today = date.today()
        time_len = timedelta(days=3)
        r_res = None
        i = 0
        for record in db_t.find({'uuid': data['uuid']}).sort('stamp', DESCENDING):
            if i>0:
                break
            i += 1
            date_ = date(*record['date'])
            if today - date_ > time_len:
                continue
            r_res = record
            
        if r_res:
            result = pred.pred([r_res, p_res])  # 已经在另一个模块中实现了报错
            result['value']['record']['_id'] = str(result['value']['record']['_id'])
            return result
        else:
            return {'status':0, 'msg': 'no data in 3 days'}

def handle_qperson(data):
    db = cdb.person_attr
    res = db.find_one({'uuid': data['uuid']})
    if res:
        res['_id']=str(res['_id'])
        return {'status': 1, 'msg': 'query succeed', 'value': res}
    else:
        return {'status': 1, 'msg': 'query succeed but no data matched can be found', 'value': res}


@app.route('/query', methods=['POST'])
def handler_query():
    ip = request.remote_addr
    current_app.logger.info(f'query request from {ip}')
    data = request.get_data()
    dict_data = json.loads(data)
    ##########################
    #查询方法包括
    #type: full_records,  predict_result, by_objid, find
    #uuid:   full_records, predict_result
    #table:  full_records, find, by_objid 方法需包含该字段
    #object_id:  by_objid方法
    #limit: {//json 需满足的键值关系，等同于mongodb数据库find语句}  仅find方法
    ##########################
    if dict_data['type'] not in CONST.SUPPORTED_QUERY.value:
        res = {'status':0, 'msg': 'unsupprted type of query'}
        return jsonify(res)
    if dict_data['type'] == 'full_records':
        res = handle_f_records(dict_data)
    elif dict_data['type'] == 'predict_result':
        res = handle_predict(dict_data)
    elif dict_data['type'] == 'by_objid':
        pass
    elif dict_data['type'] == 'person':
        res = handle_qperson(dict_data)
    return jsonify(res)



@app.route('/getid', methods=['POST'])
def getid():
    data = request.get_data()
    dict_data = json.loads(data)
    code = dict_data['code']
    st, res = wxapi.code2session(code)
    if st == 1:
        return jsonify({'status': 1, 'uuid': res})
    else:
        return jsonify({'status': 0, 'msg': res})


@app.route('/')
def index():
    return "<p>You are accessing an api</p>"



if __name__ == '__main__':
    port = os.getenv('FLASK_RUN_PORT')
    if port == None:
        port = 4001
    log = 'INFO'
    secret = None
    try:
        with open('secret.json', 'r') as f:
            secret = json.load(f)
            if 'app_id' in secret.keys() and 'secret' in secret.keys():
                pass
            else:
                raise "can't load app secret file"
    except:
        raise "can't load app secret file"
    wxapi = WX_API(secret['app_id'], secret['secret'])
    # app.logger.setLevel(app.logger.level.)
    if os.path.exists('/cert/ssl.key'):
        app.run(host='0.0.0.0', port=port, ssl_context=('/cert/ssl.pem','/cert/ssl.key'))
    app.run(host='0.0.0.0', port=port)