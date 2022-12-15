import json
import requests
import time
import threading

base_url = "https://api.weixin.qq.com/"
##app_id 和 secret由调用传参


class WX_API():
    def __init__(self, app_id, secret, auto_refresh=True):
        self.app_id = app_id
        self.secret = secret
        self.auto_refresh = auto_refresh
        self.failed_times = 0
        self.expire = 7200
        self.token = dict()
        self.check_token()

    def get_token(self):
        t0 = time.time()
        x = requests.get(base_url+f'cgi-bin/token?grant_type=client_credential&appid={self.app_id}&secret={self.secret}')
        if 'access_token' in x.json().keys():
            self.token['token'] = x.json()['access_token']
            self.token['expire'] = t0+x.json()['expires_in']
            self.expire = x.json()['expires_in']
            self.failed_times = 0
            if self.auto_refresh:
                threading.Timer(self.expire-10, self.get_token)   # 自动刷新
            return 1, None
        else:
            self.failed_times += 1
            return 0, 'get access token failed'


    def check_token(self):
        t = time.time()
        if self.failed_times > 9:
            return -1, 'up to limited retry times, shutdown'  # 错误码10 停止获取token
        if self.token:
            if t > self.token['expire']:  # 超时更新token
                st, err = self.get_token()
                if st:
                    self.check_token()
                else:  # 如果执行get_token失败
                    return st, err
            else:
                return 1, None
        else:
            st, err = self.get_token()
            if st:
                self.check_token()
            else:
                return st, err

    def code2session(self, data):
        if isinstance(data, dict):
            try:
                code = data['code']
            except:
                return 0, "can't find the key 'code'"
        else:
            code = data
        if not isinstance(code, str):
            return 0, "code2session expected to receive a str"
        st, err = self.check_token()
        if st>0:
            x = requests.get(base_url+f'sns/jscode2session?appid={self.app_id}&secret={self.secret}&js_code={code}&grant_type=authorization_code')
            resp = x.json()
            if ('errcode' in resp.keys()) and ('openid' not in resp.keys()):
                return resp['errcode'], resp['errmsg']
            else:
                return 1, resp['openid']
        else:
            return st, err