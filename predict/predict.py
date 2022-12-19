import lightgbm as lgb
from numpy import ndarray
from typing import List, Dict

class predict():
    def __init__(self):
        self.model = lgb.Booster(model_file='./predict/lgbm_model_all_features.txt')
        self.key_list = ['ks','temp','yt','qc','tt','age','sex']

    def pre_data(self, dict_data, attr):
        x = list()
        try:
            for key in self.key_list:
                if key == 'temp':
                    if dict_data[key]>36.7:
                        x.append(1)
                    else:
                        x.append(0)
                elif key in ['age', 'sex']:
                    if key == 'age':
                        x.append(1) if attr[key] > 3 else x.append(0) #69岁
                    if key == 'sex':
                        x.append(1) if attr[key] == 'male' else x.append(0)
                else:
                    x.append(1) if dict_data['symptom'][key] else x.append(0)
        except:
            return None, 'load key error'
        if len(x) == 7:
            x.append(0)
            return [x], None
        else:
            return None, 'get sample failed, lenth not equal to 7'
    
    @staticmethod
    def weighted(pred, temp):
        w = 5
        b = 2
        risk = min(max(4*(pred-.1),0), 0.99)
        risk = 0.01(w*((max(min(temp,40), 37.3)-37.3) + b)*(1 if temp>37.3 else 0)) + risk
        if risk < 0.19:
            risk = 0.01
        return risk
        

    def pred(self, data):
        x, err =  self.pre_data(*data)
        print(x, err)
        if not err:
            risk = self.model.predict(x)
            # risk = min(max(4*(risk-.1),0), 0.95)
            risk = predict.weighted(risk[0], x['temp'])
            # return {'status':1, 'value':{'record':data[0],'result': round(risk[0],2)}}
            return {'status':1, 'value':{'record':data[0],'result': round(risk, 2)}}
        else:
            # print(x)
            return {'status':0, 'msg': f'erroe occurred on preprocessing data : {err}'}
