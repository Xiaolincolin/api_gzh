"""
author: Colin
@time: 2020-03-17 16:57
explain:

"""
import redis
import requests


class Pyq:
    def set_http_address(self):
        Authorization = rdc_local.get("Authorization")
        url = "http://134.175.73.113:8080/setHttpCallbackUrl"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': Authorization
        }
        data = {
            "httpUrl": "http://wxapi.adinsights.cn/api/wechat"
        }
        res = requests.post(url=url, headers=headers, json=data)
        if res.status_code == 200:
            print(res.json())


if __name__ == '__main__':
    rdp_local = redis.ConnectionPool(host='47.95.217.37', port=6379, db=1)  # 默认db=0，测试使用db=1
    rdc_local = redis.StrictRedis(connection_pool=rdp_local)
    pyq = Pyq()
    pyq.set_http_address()
