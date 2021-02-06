# -*- coding:utf-8 -*-
"""
@desc 封装调用内部接口的类，包括函数签名等
"""

import base64
import datetime
import hashlib
import hmac
import urllib
import urllib.parse
import urllib.request
from project.http_helper import HTTPHelper


class ApiKeyUtil(HTTPHelper):
    def __init__(self, host, keys):
        self.host = host
        self.access_key = str(keys[0]).strip()
        self.secret_key = str(keys[1]).strip()
        self.headers = {
            "Accept": "application/json",
            "Content-type": "application/json",
            "Accept-Language": "en-us",
        }

    def create_sign(self, params, method, host_url, request_path):
        """
        Feature: 内部函数返回签名值
        :param params: body结构体
        :param method: 方法GET,POST,PUT等等
        :param host_url: URL地址
        :param request_path: 接口地址路径
        :return: 返回签名值
        """
        sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
        encode_params = urllib.parse.urlencode(sorted_params)
        payload = [method, host_url, request_path, encode_params]
        payload = '\n'.join(payload)
        encode_type = 'utf-8'  # 'UTF8'
        payload = payload.encode(encoding=encode_type)
        secret_key = self.secret_key.encode(encoding=encode_type)
        digest = hmac.new(secret_key, payload,
                          digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        return signature

    # def create_signature(api_key, secret_key, method, url, builder):
    #     if api_key is None or secret_key is None or api_key == "" or secret_key == "":
    #         raise HuobiApiException(HuobiApiException.KEY_MISSING, "API key and secret key are required")
    #
    #     timestamp = utc_now()
    #     builder.put_url("AccessKeyId", api_key)
    #     builder.put_url("SignatureVersion", "2")
    #     builder.put_url("SignatureMethod", "HmacSHA256")
    #     builder.put_url("Timestamp", timestamp)
    #
    #     host = urllib.parse.urlparse(url).hostname
    #     path = urllib.parse.urlparse(url).path
    #
    #     # 对参数进行排序:
    #     keys = sorted(builder.param_map.keys())
    #     # 加入&
    #     qs0 = '&'.join(['%s=%s' % (key, parse.quote(builder.param_map[key], safe='')) for key in keys])
    #     # 请求方法，域名，路径，参数 后加入`\n`
    #     payload0 = '%s\n%s\n%s\n%s' % (method, host, path, qs0)
    #     dig = hmac.new(secret_key.encode('utf-8'),
    #                    msg=payload0.encode('utf-8'),
    #                    digestmod=hashlib.sha256).digest()
    #     # 进行base64编码
    #     s = base64.b64encode(dig).decode()
    #     builder.put_url("Signature", s)

    def bit_to_bytes(self, a):
        return (a + 7) // 8

    def get_sign_params(self, params, uc_sign_check=True):
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        if params is None:
            params = {}
        if uc_sign_check:
            params.update({'AWSAccessKeyId': self.access_key,
                           'SignatureMethod': 'HmacSHA256',
                           'SignatureVersion': '2',
                           'Timestamp': timestamp})
        else:
            # 签名结构体
            params.update({'AccessKeyId': self.access_key,
                           'SignatureMethod': 'HmacSHA256',
                           'SignatureVersion': '2',
                           'Timestamp': timestamp})
            # params.update({'accessKey': self.access_key,
            #                'signatureMethod': 'HmacSHA256',
            #                'signatureVersion': '2.1',
            #                'Timestamp': timestamp})
        return params

    def api_get(self, request_path, params={}, uc_sign_check=True):
        """
        Feature: 签名的GET函数
        :param params: body结构体
        :param request_path: 接口地址路径
        :return: 响应json串
        """
        method = 'GET'
        params = self.get_sign_params(params, uc_sign_check)
        host_name = urllib.parse.urlparse(self.host).hostname
        host_name = host_name.lower()
        sign = self.create_sign(params, method, host_name, request_path)
        # print("sign",sign)
        params['Signature'] = sign.decode()
        # print(params)
        # 对签名使用个人私钥签名
        # self.print_json(params)
        # url = self.host + request_path
        url = self.host + request_path
        # print("\nURL：" + url + "?" + urllib.parse.urlencode(params))
        response = self.http_get(url, params, self.headers)
        return response

    def api_post(self, request_path, params=None, uc_sign_check=True):
        """
        Feature: 签名的POST函数
        :param params: body结构体
        :param request_path: 接口地址路径
        :return: 响应json串
        """
        if params is None:
            params = dict()
        method = 'POST'
        dic = {}
        dic = self.get_sign_params(dic, uc_sign_check)
        host_url = self.host
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        sign = self.create_sign(dic, method, host_name, request_path)
        dic['Signature'] = sign.decode()
        url = host_url + request_path + "?" + urllib.parse.urlencode(dic)
        response = self.http_post(url, params, self.headers)
        return response


if __name__ == '__main__':
    params = {
        "symbol": "bccusdt",
        "accountId": 15425165,
        "userId": 1675802,
        "amount": "10000",
        "price": "1",
        "stopPrice": "6000",
        "orderType": "buy-limit",
        "type": 3
    }

    # params={"token":"Q0IdGrGbKpa7p6z3d3fGlnMpV_OSIFPvqe3Mzy5A_DoY-uOP2m0-gvjE57ad1qDF"}
    # account_id="129975"
    # account_id = "9949438"
    # ak=ApiKeyUtil("http://dawn-broker-pro.prd8.apne-1c.huobiapps.com",
    #               ["3Kk6S0G0eCH32thWCs5N","FGtXgwRTLw3ZB4ZSMIISDpHTTgoaIDzeSxw6x9qE"])
    # print(ak.api_post(request_path="/inter/users/query",params=params))
    ak = ApiKeyUtil("http://hbg-holding-limit.prd8.apne-1c.huobiapps.com",
                    ["63NBXQydWfZMDe12w89Y", "WXFEPBAkriZCJfrEYPGBrD43hRTGzt930ccPfm9b"])
    print(ak.api_post("/hbg/inter/holding/limit", params=params))
