"""
author: Colin
@time: 2020-03-18 10:21
explain:

"""

import redis
import requests

rdp_local = redis.ConnectionPool(host='47.95.217.37', port=6379, db=1)  # 默认db=0，测试使用db=1
rdc_local = redis.StrictRedis(connection_pool=rdp_local)

def get_access_token():
    pass