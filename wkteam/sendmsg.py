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
        url = "http://xingshenapi.com/setHttpCallbackUrl"
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

    def secondLogin(self, Authorization):
        url = "http://xingshenapi.com/secondLogin"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': Authorization
        }
        data = {
            "wcId": "wxid_4ywnfyc5o1d812",
            "type": 2
        }
        res = requests.post(url=url, headers=headers, json=data)
        result = {}
        if res.status_code == 200:
            try:
                result = res.json()
                print(result)
            except Exception as e:
                print(e)
            code = result.get("code", "")
            if str(code) == "1000":
                result_data = result.get("data", {})
                if result_data:
                    wId = result_data.get("wId", "")
                    wcId = result_data.get("wcId", "")
                    if wId and wcId:
                        rdc_local.set("wid", wId)
                        rdc_local.set("wcId", wcId)
                        print("二次登陆成功！")
                    else:
                        print("二次登陆失败！wid or wcId为none")
                else:
                    print("二次登陆失败，data为none!")
            else:
                print("二次登陆失败,code为1001")
        else:
            print("二次登陆失败！请求超时")


if __name__ == '__main__':
    rdp_local = redis.ConnectionPool(host='47.95.217.37', port=6379, db=1)  # 默认db=0，测试使用db=1
    rdc_local = redis.StrictRedis(connection_pool=rdp_local)
    Authorization = rdc_local.get("Authorization")
    pyq = Pyq()
    pyq.secondLogin(Authorization)
