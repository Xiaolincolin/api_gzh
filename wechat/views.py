import hashlib
import json
import time

import requests
import xmltodict
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.generic import View
# Create your views here.
import redis
import hashlib

rdp_local = redis.ConnectionPool(host='47.95.217.37', port=6379, db=1)  # 默认db=0，测试使用db=1
rdc_local = redis.StrictRedis(connection_pool=rdp_local)
redis_conn = redis.Redis(connection_pool=redis.ConnectionPool(host='47.95.217.37', port=6379, db=2))
from django.db import connection


class Wechat(View):
    def get(self, request):
        try:
            signature = request.GET.get("signature")  # 先获取加密签名
            timestamp = request.GET.get("timestamp")  # 获取时间戳
            nonce = request.GET.get("nonce")  # 获取随机数
            echostr = request.GET.get("echostr")  # 获取随机字符串
            code = request.GET.get("code")  # 获取随机字符串
            token = "sldmlsmlm"  # 自己设置的token
            # 使用字典序排序（按照字母或数字的大小顺序进行排序）

            if not code:
                # 没有code是验证，有code是授权获得openid
                list = [token, timestamp, nonce]
                list.sort()

                # 进行sha1加密
                temp = ''.join(list)
                sha1 = hashlib.sha1(temp.encode('utf-8'))
                hashcode = sha1.hexdigest()

                # 将加密后的字符串和signatrue对比，如果相同返回echostr,表示验证成功
                if hashcode == signature:
                    print("成功")
                    if echostr:
                        return JsonResponse(int(echostr), safe=False)
                    else:
                        return JsonResponse({"msg": "fail"})
                else:
                    return JsonResponse({"msg": "fail"})
            else:
                url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid=wx96f147a2125ebb3a&secret=a063a2cfbdbe0a948b2af3cbaa62e45d&code={code}&grant_type=authorization_code".format(
                    code=code)
                res = requests.get(url)
                if res.status_code == 200:
                    json_data = res.json()
                    if json_data:
                        access_token = json_data.get("access_token", "")
                        expires_in = json_data.get("expires_in", "")
                        refresh_token = json_data.get("refresh_token", "")
                        openid = json_data.get("openid", "")
                        scope = json_data.get("scope", "")
                        print([access_token, expires_in, refresh_token, openid, scope])
                        return render(request, "index.html", {
                            "openid": openid
                        })
        except Exception as e:
            print(e)
            return JsonResponse({"msg": "fail"})

    def post(self, request):
        try:
            signature = request.GET.get("signature")  # 先获取加密签名
            timestamp = request.GET.get("timestamp")  # 获取时间戳
            nonce = request.GET.get("nonce")  # 获取随机数
            echostr = request.GET.get("echostr")  # 获取随机字符串
            token = "sldmlsmlm"  # 自己设置的token
            # 使用字典序排序（按照字母或数字的大小顺序进行排序）
            list = [token, timestamp, nonce]
            list.sort()

            # 进行sha1加密
            temp = ''.join(list)
            sha1 = hashlib.sha1(temp.encode('utf-8'))
            hashcode = sha1.hexdigest()

            # 将加密后的字符串和signatrue对比，如果相同返回echostr,表示验证成功
            if hashcode == signature:
                print("成功")
                # 请求来自微信服务器, 获取消息, 根据微信公众平台提示, 微信用户发送消息到公众号之后, 不管该消息
                # 是否是我们需要处理的, 都要在5秒内进行处理并回复, 否则微信将会给用户发送错误提示, 并且重新进行
                # 校验上述服务器URL是否可用, 所以对于我们不需要处理的消息, 可以直接回复 "success"(微信推荐) 或者 "",
                # 这样微信服务器将不会发送错误提示到微信, 也不会去重新校验服务器URL

                msg_xml_str = request.body
                if not msg_xml_str:
                    return HttpResponse("success")
                else:
                    msg_xml_str = str(msg_xml_str, encoding="utf-8")
                # 解析消息
                msg_xml_dict_all = xmltodict.parse(msg_xml_str)
                print(msg_xml_dict_all)
                msg_xml_dict = msg_xml_dict_all["xml"]
                # 获取消息类型, 消息内容等信息
                msg_type = msg_xml_dict["MsgType"]
                user_open_id = msg_xml_dict["FromUserName"]
                # 需要回复的信息
                response_dict = {
                    "xml": {
                        "ToUserName": msg_xml_dict["FromUserName"],
                        "FromUserName": msg_xml_dict["ToUserName"],
                        "CreateTime": int(time.time()),
                        "MsgType": "text",
                    }
                }
                # 当msg_type消息类型的值为event时, 表示该消息类型为推送消息, 例如微信用户 关注公众号(subscribe),取消关注(unsubscribe)
                if msg_type == "event":
                    # 事件推送消息
                    msg_event = msg_xml_dict["Event"]
                    if msg_event == "subscribe":
                        # 用户关注公众号, 回复感谢信息
                        response_dict["xml"]["Content"] = "感谢您的关注!"
                        response_xml_str = xmltodict.unparse(response_dict)
                        return HttpResponse(response_xml_str)
                    elif msg_event == "VIEW":
                        menuid = msg_xml_dict["MenuId"]
                        print(menuid)
                        return render(request, "index.html")

                        pass
                elif msg_type == "text":
                    # 文本消息, 获取消息内容, 用户发送 哈哈, 回复 呵呵
                    msg_body = msg_xml_dict["Content"]
                    if msg_body == "哈哈":
                        response_dict["xml"]["Content"] = "呵呵"
                        response_xml_str = xmltodict.unparse(response_dict)
                        return HttpResponse(response_xml_str)
                # 其他一律回复 success
                else:
                    return HttpResponse("success")
        except Exception as e:
            print(e)
            return HttpResponse("success")


class Tutorial(View):
    def get(self, request):
        try:
            code = request.GET.get("code")  # 获取随机字符串

            if code:
                url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid=wx96f147a2125ebb3a&secret=a063a2cfbdbe0a948b2af3cbaa62e45d&code={code}&grant_type=authorization_code".format(
                    code=code)
                res = requests.get(url)
                if res.status_code == 200:
                    json_data = res.json()
                    if json_data:
                        access_token = json_data.get("access_token", "")
                        expires_in = json_data.get("expires_in", "")
                        refresh_token = json_data.get("refresh_token", "")
                        openid = json_data.get("openid", "")
                        scope = json_data.get("scope", "")
                        print([access_token, expires_in, refresh_token, openid, scope])
                        return render(request, "index.html", {
                            "openid": openid
                        })
            else:
                return JsonResponse({"msg": "only open in wechat"})
        except Exception as e:
            print(e)
            return JsonResponse({"msg": "fail"})


class Index(View):
    def get(self, request):
        return render(request, "index.html")


class BeginMakeMoney(View):
    def get(self, request):
        try:
            code = request.GET.get("code")  # 获取随机字符串
            if code:
                url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid=wx96f147a2125ebb3a&secret=a063a2cfbdbe0a948b2af3cbaa62e45d&code={code}&grant_type=authorization_code".format(
                    code=code)
                res = requests.get(url)
                if res.status_code == 200:
                    json_data = res.json()
                    if json_data:
                        openid = json_data.get("openid", "")
                        if openid:
                            m1 = hashlib.md5()
                            m1.update(openid.encode("utf-8"))
                            openid_md5 = m1.hexdigest()
                            select_sql = "SELECT * from wechat_related where openid='{oid}'".format(oid=openid_md5)
                            info = self.select_openid(select_sql)
                            if not info:
                                insert_sql = "insert into wechat_related(openid,add_time) VALUES(%s,NOW())"
                                self.insert_openid(insert_sql, openid_md5)

                            return render(request, "tutorial.html", {
                                "openid": openid_md5
                            })
                        else:
                            return JsonResponse({"msg": "网站维护中！请耐心等待"})
            else:
                return JsonResponse({"msg": "请先在公众号中获取业务码并且不要在微信以外的地方打开"})
        except Exception as e:
            print(e)
            return JsonResponse({"msg": "请先在关注公众号(球球趣玩)获取业务码并且不要在微信以外的地方打开"})

    def select_openid(self, sql):
        try:
            cursor = connection.cursor()
            info = cursor.execute(sql)
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("查询openid有误")
            return 0

    def insert_openid(self, sql, param):
        try:
            cursor = connection.cursor()
            cursor.execute(sql, param)
            cursor.close()
        except Exception as e:
            print(e)
            print("插入openid有误")


class Weteam(View):

    def get(self, request):
        res = request.body.decode()
        print(res)
        return JsonResponse({"result": "success"})

    def post(self, request):
        res = request.body.decode()
        json_data = json.loads(res)
        if json_data:
            message = json_data.get("message", {})
            if message:
                if not isinstance(message, dict):
                    message = json.loads(message)
                messageType = message.get("messageType", "")
                print(messageType)
                if str(messageType) == str(2):
                    data = message.get("data",{})
                    if data:
                        if not isinstance(data,dict):
                            data = json.loads(data)
                        content = data.get("content","")
                        if len(content)==32:
                            flag = 0
                            if not isinstance(content,str):
                                content = str(content)
                            for per in content:
                                if per.isdigit():
                                    flag+=1
                                elif per.encode('utf-8').isalpha():
                                    flag+=1
                                else:
                                    continue
                            print("32位",flag)
                            if flag==32:
                                fromUser = data.get("fromUser","")
                                if fromUser:
                                    info = self.sendMsg(fromUser)
                                    if info:
                                        print("发送成功")
                                    else:
                                        print("发送消息失败")
                                else:
                                    print("fromuser为空",fromUser)
                            else:
                                print("不是业务码",)
                        else:
                            print("conetent不等32位",str(len(content)))
                    else:
                        print("获取data有误")
                else:
                    print("messageytpe不等于2")
            else:
                print("获取message有误")
        else:
            print("json_Data有误")
        return JsonResponse({"result": "success"})

    def sendMsg(self,wcId):
        Authorization = rdc_local.get("Authorization")
        wid = rdc_local.get("wid")
        Authorization = str(Authorization, encoding='utf-8')
        wid = str(wid, encoding='utf-8')
        url = "http://134.175.73.113:8080/sendText"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': Authorization
        }
        data = {
            "wId": wid,
            "wcId": wcId,
            "content": "绑定客服成功！接下来开始刷广告之旅吧！详情关注公众号（球球趣玩)"
        }
        res = requests.post(url=url, headers=headers, json=data)
        if res.status_code == 200:
            result = res.json()
            print(result)
            if result:
                code = result.get("code","")
                if str(code)==str(1000):
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
