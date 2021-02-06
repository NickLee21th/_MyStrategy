# -*- coding: utf-8 -*-
"""
简单封装requests库，并声明service包中常用的成员变量
所有service包中的其他类都需继承HTTPHelper类，成员变量统一放在init方法中声明，子类直接引用
"""
import hashlib
import requests
# from Crypto.Cipher import AES
# from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
# from Crypto.PublicKey import RSA
import json
import base64

import time
import logging
from project.get_config import *


class HTTPHelper:
    def __init__(self, environment=None):
        if environment is None:
            environment = "online"  # get_runtime_env(key_path_str="base/env_name")
        self.hadax_host = "http://huobi-hadax-service.%s.huobiapps.com/hadax/v2/open" % environment
        self.redirect_uri = "http://www-tt-hbcloud.hbcloud.%s.huobiapps.com/register/activate/" % environment
        self.finger_print = "d2d5e662aebf7266409802ff7d8d47cd"
        self.client_id = "328db0e75a584954b66fbedecedc4344"
        self.quotes_host = "http://pro-api.%s.huobiapps.com" % environment
        logging.basicConfig(filename='HTTPHelper.log', level=logging.INFO)

    # 输出LOG
    def log_print(self, log, log_level='info'):
        if log is not None:
            print(str(log))
            logging.info(str(log))

    def http_get(self, url=None, params=None, headers=None, keys=None, values=None):
        c = 0
        while c <= 3:
            try:
                # if keys is not None and values is not None:
                #     params = self.build_params(keys, values)
                #     with allure.step("请求参数是：{}".format(params)):
                #         pass
                # print('url = ' + str(url))
                # self.log_print("http_get URL: %s" % url)
                response = requests.get(url=url, params=params, headers=headers, timeout=10)
                if response.status_code == 200 \
                        and response.text is not None \
                        and response.text != "null\n"\
                        and response.text != "null":
                    pass
                    # print("\nGET: " + url + "\n", flush=True)
                if response.status_code in (200, 401) and response.text is not None:
                    # with allure.step("返回结果是：{}".format(response.json())):
                    #     pass
                    return response.json()
                else:
                    # print("\nGET: " + url + "\n", flush=True)
                    # print(response)
                    self.log_print("response.status_code= " + str(response.status_code) + "\n", log_level='error')
                    self.log_print("response.reason= " + str(response.reason), log_level='error')
                    self.log_print("response.text= " + str(response.text), log_level='error')
                    raise Exception("request failed!")
            except Exception as e:
                self.log_print(str(e), log_level='error')
                c = c + 1
                time.sleep(1)

    def http_post(self, url=None, jsons=None, headers=None, files=None, data=None, keys=None, values=None):
        c = 0
        while c <= 3:
            try:
                if keys is not None and values is not None:
                    jsons = self.build_params(keys, values)
                    # with allure.step("请求参数是：{}".format(jsons)):
                    #     pass
                # self.log_print("http_post URL: %s" % url)
                response = requests.post(url=url, json=jsons, headers=headers, data=data, files=files, timeout=15)
                # if response.status_code in (200, 401) and response.text is not None:
                #     # with allure.step("返回结果是：{}".format(response.json())):
                #     #     pass
                if response.status_code in (200, 401) \
                        and response.text is not None \
                        and response.text != "null\n"\
                        and response.text != "null":
                    # print("\nPOST: " + url + "\n", flush=True)
                    return response.json()
                else:
                    # print("\nPOST: " + url + "\n", flush=True)
                    # print(response)
                    self.log_print("response.status_code= " + str(response.status_code) + "\n", log_level='error')
                    self.log_print("response.reason= " + str(response.reason), log_level='error')
                    self.log_print("response.text= " + str(response.text), log_level='error')
                    raise Exception("request failed!")
            except Exception as e:
                self.log_print(str(e), log_level='error')
                c = c + 1
                time.sleep(1)

    @staticmethod
    def build_params(keys, values):
        params = {}
        if isinstance(keys, list):
            for i in range(len(keys)):
                if values[i] is not None:
                    params[keys[i]] = values[i]
        elif values is not None:
            params[keys] = values
        return params

    # def build_params_rsa(self, keys, values):
    #     params = {}
    #     for i in range(len(keys)):
    #         if values[i] is not None:
    #             params[keys[i]] = self.js_encrypt(values[i])
    #     return params

    def md5(self, str, salt='ThisIsSalt'):
        str = str + salt
        md = hashlib.md5()
        md.update(str.encode())
        res = md.hexdigest()
        return res

    @staticmethod
    def print_json(json_str):
        print(json.dumps(json_str, indent=4, sort_keys=True, ensure_ascii=False))

    def encrypt_base64(self, src):
        '''
        对密钥key进行加密，生成base64字符串
        '''
        return base64.urlsafe_b64decode(src)

    # def encrypt_aes(self, params):
    #     """
    #     生成AES密文
    #     :param params: 明文P
    #     :param key: 密钥K
    #     :param iv:
    #     :return: 密文C
    #     """
    #     key = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC+dR1pKz0YchrCU0oj7xIrW/9cS85BRxmes2eN1j+ZeBgGXQ+dyGdK4lr2GQKXQTLbYtRclCzGMwj8ecHjHRQxkec4fDkwdT1K66Q55bdKJS8LKX82eYg4vH73vAisAOoOOyn7RhXMpfWl2O95080RSwU28L/cIZJ2ZslIm9W0OQIDAQAB"
    #     params = json.dumps(params)
    #     bs = AES.block_size
    #     cryptor = AES.new(key)
    #     pad = lambda s: s + (bs - len(s) % bs) * chr(bs - len(s) % bs)
    #     src_str = pad(params)
    #     src_byte = src_str.encode('utf-8')
    #     ciphertext = cryptor.encrypt(src_byte)  # AES加密
    #     aes_base64 = self.encrypt_base64(ciphertext)  # 生成base64
    #     print(aes_base64)
    #     return aes_base64

    # def js_encrypt(self, text):
    #     # 通过拿到js中的RSA公钥，构造完整的公钥部分
    #     key = """-----BEGIN PUBLIC KEY-----
    # MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC+dR1pKz0YchrCU0oj7xIrW/9cS85BRxmes2eN1j+ZeBgGXQ+dyGdK4lr2GQKXQTLbYtRclCzGMwj8ecHjHRQxkec4fDkwdT1K66Q55bdKJS8LKX82eYg4vH73vAisAOoOOyn7RhXMpfWl2O95080RSwU28L/cIZJ2ZslIm9W0OQIDAQAB
    # -----END PUBLIC KEY-----"""
    #     rsakey = RSA.importKey(key)
    #     cipher = Cipher_pkcs1_v1_5.new(rsakey)  # 生成对象
    #     print(text)
    #     text = {"mac": "test"}
    #     cipher_text = base64.b64encode(cipher.encrypt(bytes(json.dumps(text).encode())))  # 对传递进来的用户名或密码字符串加密
    #     value = cipher_text.decode('utf8')  # 将加密获取到的bytes类型密文解码成str类型
    #     return str(value)