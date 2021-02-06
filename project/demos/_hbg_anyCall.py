# -*- coding:utf-8 -*-
# 基于 应用的host 和 接口路径 调用相关的接口
import logging

from project.http_helper import HTTPHelper
from project.internal_helper import ApiKeyUtil
from project.get_config import *


class HbgAnyCall(HTTPHelper):
    def __init__(self):
        self.env_name = "online"  # get_runtime_env(key_path_str="base/env_name")
        super().__init__()
        logging.basicConfig(filename='hbg_any_call_logger.log', level=logging.INFO)

    def log_print(self, log, log_level='info', ignore=True):
        if ignore:
            log = None
        if log is not None:
            logging.log(msg=str(log), level=1)
            print(str(log))

    # 基于 应用的host 和 接口路径 调用相关的 Web 接口
    def callWebMethod(
            self, host_path=None,
            interface_path=None, method_type="GET",
            headers=None, params=None,
            log_print=False
    ):
        response = -1
        try:
            if host_path is None:
                if log_print:
                    self.log_print("In callWebMethod, host_path is None!")
                return False
            if interface_path is None:
                if log_print:
                    self.log_print("In callWebMethod, interface_path is None!")
                return False
            if method_type not in ("GET", "POST"):
                if log_print:
                    self.log_print("In callWebMethod, method_type should be 'GET' or 'POST'!")
                return False
            if log_print:
                self.log_print("\n *** IN callWebMethod ***")
                # 入参
                self.log_print("入参 host_path = %s" % host_path)
                self.log_print("入参 interface_path = %s" % interface_path)
                self.log_print("入参 method_type = %s" % method_type)
            if headers is not None:
                if log_print:
                    self.log_print("入参 headers = %s" % headers)
            if params is not None:
                if log_print:
                    self.log_print("入参 params = %s" % params)
            # 调用 Web 方法
            hbg_host = host_path
            if self.env_name not in ("stg", "online"):
                hbg_host = hbg_host % self.env_name
            if log_print:
                self.log_print("hbg_host = %s" % hbg_host)
            url = hbg_host + interface_path
            if log_print:
                self.log_print("web_url = %s" % url)
            response = None
            if method_type == "GET":
                response = self.http_get(url, params=params, headers=headers)
            elif method_type == "POST":
                response = self.http_post(url, jsons=params, headers=headers)
        except Exception as ex:
            print("Exception in callWebMethod")
            self.log_print(ex)
        return response

    # 基于 应用的host 和 接口路径 调用相关的 API 接口
    def callApiMethod(
            self, host_path=None,
            interface_path=None, method_type="GET",
            access_key=None, secret_key=None,
            headers=None, params=None, isInterApi=False,
            log_print=False
    ):
        response = -1
        try:
            if host_path is None:
                if log_print:
                    self.log_print("In callApiMethod, host_path is None!")
                return False
            if interface_path is None:
                if log_print:
                    self.log_print("In callApiMethod, interface_path is None!")
                return False
            if method_type not in ("GET", "POST"):
                if log_print:
                    self.log_print("In callApiMethod, method_type should be 'GET' or 'POST'!")
                return False
            if isInterApi not in (True, False):
                if log_print:
                    self.log_print("In callApiMethod, isInterApi should be 'True' or 'False'!")
                return False
            if access_key is None:
                if log_print:
                    self.log_print("In callApiMethod, access_key is None!")
                return False
            if secret_key is None:
                if log_print:
                    self.log_print("In callApiMethod, secret_key is None!")
                return False
            self.log_print("\n### IN callApiMethod ###")
            # 入参
            if log_print:
                self.log_print("入参 host_path = %s" % host_path)
                self.log_print("入参 interface_path = %s" % interface_path)
                self.log_print("入参 method_type = %s" % method_type)
            if headers is not None:
                if log_print:
                    self.log_print("入参 headers = %s" % headers)
            if params is not None:
                if log_print:
                    self.log_print("入参 params = %s" % params)
            if access_key is not None:
                if log_print:
                    self.log_print("入参 access_key = %s" % access_key)
            if secret_key is not None:
                if log_print:
                    self.log_print("入参 secret_key = %s" % secret_key)
            api_keys = [str(access_key), str(secret_key)]
            # 调用 Api 方法
            hbg_host = host_path
            if log_print:
                self.log_print("hbg_host = %s" % hbg_host)
            url = interface_path
            if log_print:
                self.log_print("api_url = %s" % url)
            apiKeyUtil = ApiKeyUtil(hbg_host, api_keys)
            response = None
            if method_type == "GET":
                response = apiKeyUtil.api_get(url, params, isInterApi)
            elif method_type == "POST":
                response = apiKeyUtil.api_post(url, params, isInterApi)
        except Exception as ex:
            print("Exception in callApiMethod")
            self.log_print(ex)
        return response


