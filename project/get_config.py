# -*- coding:utf-8 -*-
"""
读取配置文件yaml
"""
import codecs
import os
import yaml


root_path = os.path.abspath(os.path.dirname(__file__))
conf_path = root_path.split("utils")[0] + "conf/"


def read_yaml(filename):
    fb = codecs.open(filename, "r", "utf-8")
    content = yaml.safe_load(fb)
    fb.close()
    return content


def get_user(key):
    return read_yaml(conf_path + "user_info.yaml").get(key)


# 从运行时环境的通用配置文件中读取数据
def get_runtime_common_config(key_path_str=None):
    """
    从运行时环境的通用配置文件中读取数据
    入参 key_path_str 有效值 示例： "api_keys/hbg_inter_rule"
    """
    config_data = read_yaml(conf_path + "runtime_common.yaml")
    if key_path_str is not None:
        key_path = key_path_str.split("/")
        for item in key_path:
            if isinstance(config_data, dict):
                if item in config_data.keys():
                    config_data = config_data[item]
                else:
                    print("IN get_runtime_common_config, 找不到对应入参的配置值 key_path_str = %s" % key_path_str)
                    config_data = ""
                    break
            else:
                print("IN get_runtime_common_config, 找不到对应入参的配置值 key_path_str = %s" % key_path_str)
                config_data = ""
                break
    return config_data


# 从运行时环境配置文件中读取数据
def get_runtime_env(key_path_str=None):
    """
    从运行时环境配置文件中读取数据
    入参 key_path_str 有效值 示例： "base/env_name"
    """
    config_data = read_yaml(conf_path + "runtime_env.yaml")
    if key_path_str is not None:
        key_path = key_path_str.split("/")
        for item in key_path:
            if isinstance(config_data, dict):
                if item in config_data.keys():
                    config_data = config_data[item]
                else:
                    config_data = ""
                    break
            else:
                config_data = ""
                break
        if config_data == "":
            config_data = get_runtime_common_config(key_path_str)
    if config_data == "":
        print("IN get_runtime_env, 找不到对应入参的配置值 key_path_str = %s" % key_path_str)
    return config_data

def get_url(env, key=None):
    datas = read_yaml(conf_path + "url.yaml")
    if str(env).startswith('test'):
        return str(datas['test'][key]).replace('${env}', env)
    elif env == 'stg':
        return datas['stg'][key]
    return datas


def get_keys(key=None, var='app'):
    datas = read_yaml(conf_path + "keys.yaml").get(var)
    value = datas[key]
    return value.split(',')


def get_database(key):
    return read_yaml(conf_path + "database.yaml").get(key)


def get_all_user(key=None):
    users = read_yaml(conf_path + "user_info.yaml")
    if key is not None:
        all_user = []
        for u in users:
            if str(u).startswith('fee'):
                all_user.append(u)
        return all_user
    return users
