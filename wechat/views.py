import hashlib
import json
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
            print(signature)
            xml_data = request.body
            if xml_data:
                xml_data = str(xml_data, encoding="utf-8")
                json_data = xmltodict.parse(xml_data)
                json.dumps(json_data)
            list = [token, timestamp, nonce]
            list.sort()

            # 进行sha1加密
            temp = ''.join(list)
            sha1 = hashlib.sha1(temp.encode('utf-8'))
            hashcode = sha1.hexdigest()
            xml_str = """
            <xml>
          <ToUserName><![CDATA[toUser]]></ToUserName>
          <FromUserName><![CDATA[fromUser]]></FromUserName>
          <CreateTime>12345678</CreateTime>
          <MsgType><![CDATA[text]]></MsgType>
          <Content><![CDATA[你好]]></Content>
        </xml>
            """

            # 将加密后的字符串和signatrue对比，如果相同返回echostr,表示验证成功
            return JsonResponse(xml_str, safe=False)

        except Exception as e:
            print(e)
            return JsonResponse(xml_str)


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
