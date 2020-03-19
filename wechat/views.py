import datetime
import hashlib
import json
import time

import requests
import xmltodict
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
# Create your views here.
import redis
import hashlib

rdp_local = redis.ConnectionPool(host='47.95.217.37', port=6379, db=1)  # 默认db=0，测试使用db=1
rdc_local = redis.StrictRedis(connection_pool=rdp_local)
redis_conn = redis.Redis(connection_pool=redis.ConnectionPool(host='47.95.217.37', port=6379, db=2))
from django.db import connection
from api.settings import MEDIA_ROOT


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
                        # 用户关注公众号, 绑定师徒关系
                        eventkey = msg_xml_dict["EventKey"]
                        apprentice = msg_xml_dict["FromUserName"]
                        if eventkey:
                            master = str(eventkey).replace("qrscene_", "")
                            if master != apprentice:
                                master_md5 = self.get_md5(master)
                                apprentice_md5 = self.get_md5(apprentice)
                                select_sql = "SELECT `master` from wechat_apprentice where `master`='{m}' and Apprentice='{a}'".format(
                                    m=master_md5, a=apprentice_md5)
                                info = self.select_openid(select_sql)
                                if not info:
                                    insert_sql = "insert into wechat_apprentice(Apprentice,`master`,add_time) VALUES(%s,%s,NOW())"
                                    self.insert_openid(insert_sql, [apprentice_md5, master_md5])

                        response_dict["xml"]["Content"] = "感谢您关注球球趣玩！!详情请点击教程学习"
                        response_xml_str = xmltodict.unparse(response_dict)
                        return HttpResponse(response_xml_str)
                    elif msg_event == "VIEW":
                        menuid = msg_xml_dict["MenuId"]
                        return render(request, "index.html")
                    else:
                        return HttpResponse("success")

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
            else:
                return HttpResponse("success")
        except Exception as e:
            print(e)
            return HttpResponse("success")

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

    def get_md5(self, strs):
        m1 = hashlib.md5()
        m1.update(strs.encode("utf-8"))
        strs_md5 = m1.hexdigest()
        return strs_md5


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
                        return render(request, "tutorial.html", {
                            "openid": openid
                        })
            else:
                # openid = "测试"
                return JsonResponse({"msg": "only open in wechat"})
                # return render(request, "tutorial.html", {
                #     "openid": openid
                # })
        except Exception as e:
            print(e)
            return JsonResponse({"msg": "fail"})


class Index(View):
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
                            openid = self.get_md5(openid)
                            # 今天数据
                            time_now = str(datetime.datetime.now().strftime('%Y-%m-%d'))
                            today_sql = "SELECT n.`name`,l.product,l.creative,l.type_id FROM wechat_related as r,wechat_distinct as d,wechat_name as n,wechat_log as l where r.wx_id=d.wx_id and d.statextstr=l.statextstr and r.wx_id=n.wx_id and l.`day`='{days}' and openid='{openid}'".format(
                                openid=openid, days=time_now)
                            today_data = self.select_data(today_sql)
                            # 所有数据
                            month = str(datetime.datetime.now().strftime('%m'))

                            all_sql = "SELECT a.amount,a.amount_app,a.days FROM wechat_related as r,wechat_account_api as a,wechat_name as n where r.wx_id=a.wx_id and a.wx_id=n.wx_id and  openid='{openid}' ORDER BY days desc".format(
                                openid=openid)
                            all_data = self.select_data(all_sql)
                            # 本月数据
                            month_data = []
                            for per in all_data:
                                per_month = str(per[2])
                                if month == per_month:
                                    month_data.append(per)
                            print(month_data)

                            if today_data:
                                today_data = list(today_data)
                                print(today_data)
                            else:
                                today_data = []
                            print(month_data)
                            print(all_data)

                            return render(request, "index.html", {
                                "openid": openid
                            })
                        return JsonResponse({"msg": "request err"})
            else:
                # openid = "测试"
                return JsonResponse({"msg": "only open in wechat"})
                # return render(request, "tutorial.html", {
                #     "openid": openid
                # })
        except Exception as e:
            print(e)
            return JsonResponse({"msg": "fail"})

    def get_md5(self, strs):
        m1 = hashlib.md5()
        m1.update(strs.encode("utf-8"))
        strs_md5 = m1.hexdigest()
        return strs_md5

    def select_data(self, sql):
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            info = cursor.fetchall()
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("查询openid有误")
            return 0


class CashWithdrawal(View):
    # 转发到页面提现
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
                            select_pay = "SELECT openid from wechat_pay where openid='{oid}'".format(
                                oid=openid_md5)
                            pay_info = self.select_openid(select_pay)
                            if pay_info:
                                select_sql = "SELECT totalmoney,withdrawable,alread,surplus from wechat_money where openid='{oid}'".format(
                                    oid=openid_md5)
                                info = self.select_money(select_sql)
                                totalmoney = 0
                                withdrawable = 0
                                alread = 0
                                surplus = 0
                                if info:
                                    try:
                                        info = list(info)
                                        totalmoney = info[0]
                                        withdrawable = info[1]
                                        alread = info[2]
                                        surplus = info[3]
                                    except Exception as e:
                                        print(e)

                                return render(request, "money.html", {
                                    "totalmoney": totalmoney,
                                    "withdrawable": withdrawable,
                                    "alread": alread,
                                    "surplus": surplus,
                                    "openid": openid_md5
                                })
                            else:
                                return render(request, "uploadimage.html", {
                                    "openid": openid_md5
                                })
                        else:
                            return JsonResponse({"msg": "网站维护中！请耐心等待"})
                else:
                    return JsonResponse({"msg": "当前网络不佳，请稍后再试"})
            else:
                return JsonResponse({"msg": "请先在公众号中获取业务码并且不要在微信以外的地方打开"})
        except Exception as e:
            print(e)
            return JsonResponse({"msg": "请先在关注公众号(球球趣玩)获取业务码并且不要在微信以外的地方打开"})

        return render(request, 'money.html')

    def select_money(self, sql):
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            info = cursor.fetchone()
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("查询openid有误")
            return 0

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


class Launch(View):
    def get(self):
        return HttpResponse({"msg": "错误的请求"})

    def post(self, request):
        user = request.POST.get("user", "")
        account = request.POST.get("account", "")
        money = request.POST.get("money", "")
        remark = request.POST.get("remark", "")
        openid = request.POST.get("openid", "")
        print(user)
        print(account)
        print(money)
        print(remark)
        print(openid)
        return HttpResponse({"msg": "success"})


class UploadImage(View):
    # 上传图片
    def get(self, request, code):
        return HttpResponse("请求错误")

    def post(self, request):
        result = {}
        file_obj = request.FILES.get("file")
        openid = request.POST.get("openid", "")
        wechat_id = request.POST.get("wechat_id", "")
        file_name = str(MEDIA_ROOT) + "/paycode/" + str(openid) + ".jpg"
        print("dir:", file_name)
        img_type = file_obj.name.split('.')[-1]
        if img_type not in ['jpeg', 'jpg', 'png']:
            result["code"] = 0
            result["msg"] = "图片仅支持'.jpeg', '.jpg', '.png'结尾的格式"
            return JsonResponse(result)
        else:
            if openid:
                try:
                    with open(file_name, 'wb+') as f:
                        f.write(file_obj.read())
                except Exception as e:
                    return
                else:
                    select_sql = "SELECT openid from wechat_pay where openid='{oid}'".format(
                        oid=openid)
                    select_info = self.select_openid(select_sql)
                    if not select_info:
                        insert_sql = "insert into wechat_pay(wx_code,image_id,openid,add_time) VALUES(%s,%s,%s,NOW())"
                        info = self.insert_openid(insert_sql, [wechat_id, openid, openid])
                        if info:
                            result["code"] = 1
                            result["src"] = " http://wxapi.adinsights.cn/media/paycode/" + str(openid) + "." + str(
                                img_type)
                            result["msg"] = "上传成功"
                            return JsonResponse(result)
                        else:
                            result["code"] = 0
                            result["msg"] = "上传失败"
                            return JsonResponse(result)
                    else:
                        result["code"] = 3
                        result["msg"] = "上传失败"
                        return JsonResponse(result)
            else:
                result["code"] = 0
                result["msg"] = "上传失败"
                return JsonResponse(result)

    def insert_openid(self, sql, param):
        try:
            cursor = connection.cursor()
            cursor.execute(sql, param)
            cursor.close()
            return 1
        except Exception as e:
            print(e)
            print("插入openid有误")
            return 0

    def select_openid(self, sql):
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            info = cursor.fetchone()
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("查询openid有误")
            return 0


class BeginMakeMoney(View):
    # 用于提取业务码，并保存到数据库
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
                    return JsonResponse({"msg": "当前网络不佳，请稍后再试"})
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
    # 用来接收绑定微信客服，提示是否绑定成功！

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
                if str(messageType) == str(2):
                    data = message.get("data", {})
                    if data:
                        if not isinstance(data, dict):
                            data = json.loads(data)
                        content = data.get("content", "")
                        if len(content) == 32:
                            flag = 0
                            if not isinstance(content, str):
                                content = str(content)
                            for per in content:
                                if per.isdigit():
                                    flag += 1
                                elif per.encode('utf-8').isalpha():
                                    flag += 1
                                else:
                                    continue
                            print("32位", flag)
                            if flag == 32:
                                fromUser = data.get("fromUser", "")
                                if fromUser:
                                    select_sql = "SELECT openid,flag from wechat_related where openid='{oid}'".format(
                                        oid=content)
                                    select_result = self.select_openid(select_sql)
                                    if select_result:
                                        select_result = list(select_result)
                                        relate_code = select_result[1]
                                        if str(relate_code) == str(0):
                                            insert_sql = 'UPDATE wechat_related set wx_id="{wx_id}",update_time=NOW(),flag=1 where openid="{openid}"'.format(
                                                wx_id=fromUser, openid=content)
                                            self.update_wxid(insert_sql)
                                            content = "绑定客服成功！接下来开始刷广告之旅吧！详情关注公众号（球球趣玩)"
                                            info = self.sendMsg(fromUser, content)
                                            if info:
                                                print("发送成功")
                                            else:
                                                print("发送消息失败")
                                        else:
                                            content = "您已经绑定过客服了，详情关注公众号（球球趣玩)"
                                            info = self.sendMsg(fromUser, content)
                                            if info:
                                                print("发送成功")
                                            else:
                                                print("发送消息失败")
                                    else:
                                        content = "绑定客服失败！请关注公众号（球球趣玩)提取业务码"
                                        info = self.sendMsg(fromUser, content)
                                        if info:
                                            print("发送成功")
                                        else:
                                            print("发送消息失败")
                                else:
                                    print("fromuser为空", fromUser)
                            else:
                                print("不是业务码", )
                        else:
                            print("conetent不等32位", str(len(content)))
                    else:
                        print("获取data有误")
                else:
                    print("messageytpe不等于2")
            else:
                print("获取message有误")
        else:
            print("json_Data有误")
        return JsonResponse({"result": "success"})

    def sendMsg(self, wcId, content):
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
            "content": content
        }
        res = requests.post(url=url, headers=headers, json=data)
        if res.status_code == 200:
            result = res.json()
            if result:
                code = result.get("code", "")
                if str(code) == str(1000):
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def update_wxid(self, sql):
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            cursor.close()
        except Exception as e:
            print(e)
            print("插入微信id有误")

    def select_openid(self, sql):
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            info = cursor.fetchone()
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("查询openid有误")
            return 0


class Test(View):
    def get(self, request):
        openid_md5 = "sda"
        return render(request, "uploadimage.html", {
            "openid": openid_md5
        })
