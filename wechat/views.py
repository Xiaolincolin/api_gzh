import hashlib
import json
import time

import xmltodict
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.generic import View
import xml.etree.ElementTree as ET
# Create your views here.
from wechat.WXBizMsgCrypt3 import WXBizMsgCrypt
import redis

rdp_local = redis.ConnectionPool(host='47.95.217.37', port=6379, db=0)  # 默认db=0，测试使用db=1
rdc_local = redis.StrictRedis(connection_pool=rdp_local)
redis_conn = redis.Redis(connection_pool=redis.ConnectionPool(host='47.95.217.37', port=6379, db=2))


class Wechat(View):
    def get(self, request):
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
                if echostr:
                    return JsonResponse(int(echostr), safe=False)
                else:
                    return JsonResponse({"msg": "fail"})
            else:
                return JsonResponse({"msg": "fail"})

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
                    msg_xml_str = str(msg_xml_str,encoding="utf-8")
                # 解析消息
                msg_xml_dict_all = xmltodict.parse(msg_xml_str)
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
        return render(request, "tutorial.html")


class Index(View):
    def get(self, request):
        return render(request, "index.html")


class Weteam(View):

    def get(self, request):
        res = request.body.decode()
        redis_conn.rpush(json.dumps(res))
        return JsonResponse({"result": "success"})

    def post(self, request):
        res = request.body.decode()
        redis_conn.rpush(json.dumps(res))
        return JsonResponse({"result": "success"})
