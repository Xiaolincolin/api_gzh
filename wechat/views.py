import datetime
import json
import time
from io import StringIO, BytesIO

import requests
import xmltodict
from PIL import Image, ImageEnhance
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View
import redis
import hashlib
import logging
from pyzbar.pyzbar import decode

rdp_local = redis.ConnectionPool(host='127.0.0.1', port=6379, db=1)  # 默认db=0，测试使用db=1
rdc_local = redis.StrictRedis(connection_pool=rdp_local)
redis_conn = redis.Redis(connection_pool=redis.ConnectionPool(host='127.0.0.1', port=6379, db=2))
from django.db import connection
from api.settings import MEDIA_ROOT

logger = logging.getLogger('')


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
                        return JsonResponse({"msg": "fail"}, json_dumps_params={'ensure_ascii': False})
                else:
                    return JsonResponse({"msg": "fail"}, json_dumps_params={'ensure_ascii': False})
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
            return JsonResponse({"msg": "fail"}, json_dumps_params={'ensure_ascii': False})

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

                        response_dict["xml"][
                            "Content"] = "感谢您关注球球趣玩！\n1.开始刷广告请点击教程\n2.查看收益，提现请点击赚钱\n3.上传收付款方法请发送收付款到公众号"
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
                    if "收付款" in str(msg_body):
                        response_dict["xml"][
                            "Content"] = "1.请点击微信右上角的加号\n2.点击微信的收付款\n3.二维码收款\n4.长按二维码保存到手机\n5.将收款码发送到公众号"
                        response_xml_str = xmltodict.unparse(response_dict)
                        return HttpResponse(response_xml_str)
                    else:
                        response_dict["xml"][
                            "Content"] = "感谢您关注球球趣玩！\n1.开始刷广告请点击教程\n2.查看收益，提现请点击赚钱\n3.上传收付款方法请发送收付款到公众号"
                        response_xml_str = xmltodict.unparse(response_dict)
                        return HttpResponse(response_xml_str)
                elif msg_type == "image":
                    PicUrl = msg_xml_dict["PicUrl"]
                    FromUserName = msg_xml_dict["FromUserName"]
                    if PicUrl and FromUserName:
                        openid_md5 = self.get_md5(FromUserName)
                        has_exist_sql = "select openid from wechat_pay_img where openid='{openid}'".format(
                            openid=openid_md5)
                        has_exist = self.select_openid(has_exist_sql)
                        if not has_exist:
                            boolean = self.get_img(PicUrl, openid_md5)
                            if boolean:
                                insert_qr_sql = "insert into wechat_pay_img(openid,image_id,add_time) values (%s,%s,NOW())"
                                insert_qr_result = self.insert_openid(insert_qr_sql, [openid_md5, openid_md5])
                                if insert_qr_result:
                                    response_dict["xml"]["Content"] = "上传收款码成功，我们将在1-3个工作日进行审核！现在开始愉快的（发起提现）吧！"
                                    response_xml_str = xmltodict.unparse(response_dict)
                                    return HttpResponse(response_xml_str)
                                else:
                                    response_dict["xml"]["Content"] = "非常抱歉！上传收款码失败，请确保上传的是本人的微信收款码，详情请联系客服处理！"
                                    response_xml_str = xmltodict.unparse(response_dict)
                                    return HttpResponse(response_xml_str)
                            else:
                                response_dict["xml"][
                                    "Content"] = "请问您是想上传收款码吗？请点击微信的收付款->二维码收款->长按二维码->保存到手机->将收款码发送到公众号"
                                response_xml_str = xmltodict.unparse(response_dict)
                                return HttpResponse(response_xml_str)
                        else:
                            response_dict["xml"]["Content"] = "您已经上传过收付款了\n1.开始刷广告请点击教程\n2.查看收益，提现请点击赚钱"
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
            info = cursor.execute(sql, param)
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("插入数据有误")
            return 0

    def get_md5(self, strs):
        m1 = hashlib.md5()
        m1.update(strs.encode("utf-8"))
        strs_md5 = m1.hexdigest()
        return strs_md5

    def get_img(self, url, openid):
        # 保存收款码并且判断是不是收款码
        try:
            res = requests.get(url)
            if res.status_code == 200:
                img = res.content
                imgs = BytesIO(img)
                flag = self.qrcode_recongnize(imgs)
                if flag:
                    file_name = str(MEDIA_ROOT) + "/paycode/" + str(openid) + ".png"
                    with open(file_name, 'wb+') as f:
                        f.write(img)
                    return True
                else:
                    return False
        except Exception as e:
            print("判断收款码报错", e)
            return False

    def qrcode_recongnize(self, filename):
        # 判断是不是二维码
        try:
            img = Image.open(filename).convert('RGB')
            img = ImageEnhance.Brightness(img).enhance(1.0)
            img = ImageEnhance.Sharpness(img).enhance(1.5)
            img = ImageEnhance.Contrast(img).enhance(2.0)
            img = img.convert('L')
            result = decode(img)
            if len(result) > 0:
                return True
            else:
                return False
        except:
            return False


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
                return JsonResponse({"msg": "only open in wechat"}, json_dumps_params={'ensure_ascii': False})
                # return render(request, "tutorial.html", {
                #     "openid": openid
                # })
        except Exception as e:
            print(e)
            return JsonResponse({"msg": "fail"}, json_dumps_params={'ensure_ascii': False})


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
                            today_sql = "SELECT n.`name`,l.product,l.creative,l.type_id,l.day FROM wechat_related as r,wechat_distinct as d,wechat_name as n,wechat_log as l where r.wx_id=d.wx_id and d.statextstr=l.statextstr and r.wx_id=n.wx_id  and openid='{openid}' ORDER BY `day` desc".format(
                                openid=openid)
                            all_data = self.select_data(today_sql)
                            month = str(datetime.datetime.now().strftime('%m'))

                            today_data = []
                            month_data = []
                            history_data = []

                            month_page = []
                            history_page = []
                            name = ""

                            today_game_count = 0
                            today_app_count = 0

                            month_game_count = 0
                            month_app_count = 0

                            history_game_count = 0
                            history_app_count = 0

                            if all_data:
                                all_data = list(all_data)
                            for per in all_data:
                                ml = len(month_page)
                                hl = len(history_page)
                                per = list(per)
                                per = ["无" if str(i) == "None" or i == "" else i for i in per]
                                if not name:
                                    name = per[0]
                                ad_type = per[3]
                                if str(ad_type) == "1":
                                    history_game_count += 1
                                else:
                                    history_app_count += 1

                                if hl <= 7:
                                    history_page.append(per)
                                else:
                                    history_data.append(per)

                                days = per[4]
                                if str(days) == time_now:
                                    if str(ad_type) == "1":
                                        today_game_count += 1
                                    else:
                                        today_app_count += 1
                                    today_data.append(per)

                                per_month = str(per[4]).split("-")[1]
                                if month == per_month:
                                    if ml <= 7:
                                        month_page.append(per)
                                    else:
                                        month_data.append(per)
                                    if str(ad_type) == "1":
                                        month_game_count += 1
                                    else:
                                        month_app_count += 1
                            return render(request, "index.html", {
                                "openid": openid,
                                "name": name,
                                "today_data": today_data,
                                "month_page": month_page,
                                "month_data": month_data,
                                "history_page": history_page,
                                "history_data": history_data,
                                "today_game_count": today_game_count,
                                "today_app_count": today_app_count,
                                "month_game_count": month_game_count,
                                "month_app_count": month_app_count,
                                "history_game_count": history_game_count,
                                "history_app_count": history_app_count,
                            })
                        return JsonResponse({"msg": "request err"}, json_dumps_params={'ensure_ascii': False})
            else:
                # openid = "测试"
                return JsonResponse({"msg": "only open in wechat"}, json_dumps_params={'ensure_ascii': False})
                # return render(request, "tutorial.html", {
                #     "openid": openid
                # })
        except Exception as e:
            print(e)
            return JsonResponse({"msg": "fail"}, json_dumps_params={'ensure_ascii': False})

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
                            # select_pay = "SELECT openid from wechat_pay where openid='{oid}'".format(
                            #     oid=openid_md5)
                            # pay_info = self.select_openid(select_pay)
                            # if pay_info:
                            order_result = []
                            select_sql = "SELECT totalmoney,withdrawable,alread,`status` from wechat_money where openid='{oid}'".format(
                                oid=openid_md5)
                            info = self.select_money(select_sql)
                            order_sql = "SELECT `name`,amount,`status`,add_time,auditor_remark from wechat_order where openid='{oid}' and `status`!=1 ORDER BY add_time desc".format(
                                oid=openid_md5)
                            order_data = self.select_order(order_sql)
                            user_status = 1
                            if order_data:
                                order_data = list(order_data)
                                for order in order_data:
                                    if order:
                                        order = list(order)
                                        status = order[2]
                                        if str(status) == "0":
                                            user_status = 0
                                        elif str(status) == "3":
                                            user_status = 3
                                        order_result.append(order)

                            totalmoney = 0
                            withdrawable = 0
                            alread = 0
                            if info:
                                try:
                                    info = list(info)
                                    totalmoney = info[0]
                                    withdrawable = info[1]
                                    alread = info[2]
                                except Exception as e:
                                    print(e)

                            return render(request, "money.html", {
                                "totalmoney": totalmoney,
                                "withdrawable": withdrawable,
                                "alread": alread,
                                "status": int(user_status),
                                "openid": openid_md5,
                                "order_result": order_result
                            })
                            # else:
                            #     return render(request, "uploadimage.html", {
                            #         "openid": openid_md5
                            #     })
                        else:
                            return JsonResponse({"msg": "网站维护中！请耐心等待"}, json_dumps_params={'ensure_ascii': False})
                else:
                    return JsonResponse({"msg": "当前网络不佳，请稍后再试"}, json_dumps_params={'ensure_ascii': False})
            else:
                return JsonResponse({"msg": "请先在公众号中获取业务码并且不要在微信以外的地方打开"}, json_dumps_params={'ensure_ascii': False})
        except Exception as e:
            print(e)
            return JsonResponse({"msg": "请先在关注公众号(球球趣玩)获取业务码并且不要在微信以外的地方打开"}, json_dumps_params={'ensure_ascii': False})

        return render(request, 'money.html')

    def post(self, request):
        return HttpResponse("错误的请求！")

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

    def select_order(self, sql):
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            info = cursor.fetchall()
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("查询订单有误")
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
    # 发起提现，生成订单
    def get(self):
        return HttpResponse({"msg": "错误的请求"})

    def post(self, request):
        logger_money = logging.getLogger('collect')
        user = request.POST.get("user", "")
        money = request.POST.get("money", "")
        remark = request.POST.get("remark", "")
        openid = request.POST.get("openid", "")
        if money:
            money = float(money)
        else:
            money = 0
        if not user:
            user = "匿名"
        data = {}
        today = (datetime.date.today()).strftime("%d")
        ts = (datetime.date.today()).strftime("%Y-%m-%d")
        if str(today) == "15" or str(today) == "16":
            if openid:
                # openid不存在
                qr_sql = "select openid from wechat_pay_img where openid='{openid}'".format(
                    openid=openid)
                ql_code = self.select_qrcode(qr_sql)
                if ql_code:
                    # 判断是否上传收款码
                    order_sql = "SELECT openid,`status` from wechat_order where openid='{oid}'  and `status`!=1 and add_time like '{ts}%' ORDER BY add_time desc".format(
                        oid=openid,ts=ts)
                    order_result = self.select_order(order_sql)
                    order_status = 0
                    if order_result:
                        order_result = list(order_result)
                        order_status = len(order_result)

                    if order_status >= 5:
                        # 判断是否有订单未审核，防止代码发起post请求
                        data["code"] = 0
                        data["msg"] = "抱歉，每天最多只能发起5次提现"
                        msg = openid + " " + str(money) + " " + "有未审核的订单（前端规则被越过）"
                        logger_money.info(msg)
                    else:
                        print("test:", order_status)
                        if money and money >= 10 and money < 101:
                            select_sql = "SELECT totalmoney,withdrawable,alread,`status` FROM wechat_money where openid='{oid}'".format(
                                oid=openid)
                            result = self.select_openid(select_sql)
                            if result:
                                # 生成订单号
                                orderid = self.get_order_code(openid)
                                result = list(result)
                                try:
                                    totalmoney = result[0]
                                    withdrawable = result[1]
                                    alread = result[2]
                                    status = result[3]
                                except Exception as e:
                                    msg = openid + "查询金额结果下标取值报错"
                                    logger_money.info(msg)
                                    totalmoney = 0
                                    withdrawable = 0
                                    alread = 0
                                    status = 0

                                msg = openid + " 发起提现 " + str(money)
                                logger_money.info(msg)
                                if withdrawable:
                                    withdrawable = float(withdrawable)
                                    before_amount = withdrawable
                                    after_amount = withdrawable - money
                                else:
                                    before_amount = 0
                                    after_amount = 0
                                if withdrawable < 10 or withdrawable < money:
                                    data["code"] = 0
                                    data["msg"] = "可提现余额不足10元"
                                    msg = openid + " " + str(money) + " " + "可提现余额不足10元(理论上越过规则,及时处理)"
                                    logger_money.info(msg)
                                else:
                                    if status:
                                        if withdrawable and money <= withdrawable:
                                            update_sql = "UPDATE wechat_money set withdrawable=withdrawable-'{money}',alread=alread+'{money}',update_time=NOW() where openid='{oid}'".format(
                                                money=money, oid=openid)
                                            update_result = self.update_money(update_sql)
                                            if update_result:
                                                # 账户金额修改成功
                                                insert_sql = "insert into wechat_order(openid,`name`,orderid, amount,totalmoney,before_amount,after_amount,remark, add_time) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, NOW())"
                                                insert_result = self.insert_order(insert_sql,
                                                                                  [openid, str(user), orderid,
                                                                                   str(money),
                                                                                   str(totalmoney), str(before_amount),
                                                                                   str(after_amount), remark])
                                                if insert_result:
                                                    # 订单生成成功
                                                    data["code"] = "1"
                                                    data["msg"] = "提现成功"
                                                    data["withdrawable"] = str(round(withdrawable - money,2))
                                                    data["alread"] = str(round(alread + money,2))
                                                    msg = openid + " " + str(orderid) + " " + str(money) + " 提现发起成功"
                                                    logger_money.info(msg)
                                                    if str(order_status) == "3":
                                                        delete_sql = "DELETE FROM wechat_order WHERE openid='{oid}' and `status` =3".format(
                                                            oid=openid)
                                                        del_status = self.update_money(delete_sql)
                                                        if del_status:
                                                            msg = openid + " 提现失败订单删除成功，已经从新发起提现"
                                                            logger_money.info(msg)
                                                        else:
                                                            msg = openid + " 提现失败订单删除失败"
                                                            logger_money.info(msg)
                                                else:
                                                    # 订单生成失败
                                                    exc_update_sql = "UPDATE wechat_money set withdrawable=withdrawable+'{money}',alread=alread-'{money}',update_time=NOW() where openid='{oid}'".format(
                                                        money=money, oid=openid)
                                                    exc_result = self.update_money(exc_update_sql)
                                                    if exc_result:
                                                        # 订单生成失败，金额还原成功
                                                        msg = openid + " " + str(orderid) + " " + str(
                                                            money) + " 提现失败 " + "金额还原成功"
                                                        logger_money.info(msg)
                                                    else:
                                                        # 订单生成失败，金额还原失败，进行账户锁定
                                                        exc_sql = "UPDATE wechat_money set `status`=0,update_time=NOW() where openid='{oid}'".format(
                                                            oid=openid)
                                                        up_result = self.update_money(exc_sql)
                                                        if up_result:
                                                            # 账户锁定成功，用户不能发起提现
                                                            msg = openid + " " + str(orderid) + " " + str(
                                                                money) + " 提现失败，金额还原失败,账号锁定成功"
                                                            logger_money.info(msg)
                                                        else:
                                                            # 账户锁定失败，用户金额还原失败，紧急处理
                                                            msg = openid + " " + str(orderid) + " " + str(
                                                                money) + " 提现失败，金额还原失败,账号锁定失败"
                                                            logger_money.info(msg)
                                                    data["code"] = 0
                                                    data["msg"] = "提现失败"
                                            else:
                                                data["code"] = 0
                                                data["msg"] = "提现失败"
                                                msg = openid + " " + str(money) + " 提现失败，金额不变"
                                                logger_money.info(msg)
                                        else:
                                            data["code"] = 0
                                            data["msg"] = "提现失败,剩余金额异常,账号冻结，请联系管理解除冻结"
                                            exc_sql = "UPDATE wechat_money set `status`=0,update_time=NOW() where openid='{oid}'".format(
                                                oid=openid)
                                            up_result = self.update_money(exc_sql)
                                            if up_result:
                                                msg = openid + " " + str(money) + " 提现失败，错误操作,账号锁定成功"
                                                logger_money.info(msg)
                                            else:
                                                msg = openid + " " + str(money) + " 提现失败，错误操作,账号锁定失败"
                                                logger_money.info(msg)
                        elif money > 100:
                            data["code"] = 0
                            data["msg"] = "金额不能大于100元"
                            msg = openid + " " + str(money) + " " + "金额为空"
                            logger_money.info(msg)
                        else:
                            data["code"] = 0
                            data["msg"] = "金额不能为空或者小于10元"
                            msg = openid + " " + str(money) + " " + "金额为空"
                            logger_money.info(msg)
                else:
                    data["code"] = 0
                    data["msg"] = "抱歉，您未绑定收款码！暂不能提现！发送消息（收付款）到公众号，详情查看教程！"
                    msg = openid + " " + str(money) + " " + "金额为空"
                    logger_money.info(msg)
            else:
                data["code"] = 0
                data["msg"] = "请务将链接分享到外部使用，仅能从公众号中发起提现"
                msg = openid + " " + str(money) + " " + "公众号外部链接渗透"
                logger_money.info(msg)
        else:
            data["code"] = 0
            data["msg"] = "只能每月15或者16号发起提现"
            msg = openid + " " + str(money) + " " + "非15或者16号发起"
            logger_money.info(msg)

        return JsonResponse(data, json_dumps_params={'ensure_ascii': False})

    def update_money(self, sql):
        try:
            cursor = connection.cursor()
            info = cursor.execute(sql)
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("还原金额失败")
            return 0

    def select_qrcode(self, sql):
        try:
            cursor = connection.cursor()
            info = cursor.execute(sql)
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("查询收款码有误")
            return 0

    def insert_order(self, sql, param):
        try:
            cursor = connection.cursor()
            info = cursor.execute(sql, param)
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("插入订单失败")
            return 0

    def get_order_code(self, openid):
        ts = str(int(time.time() * 1000))
        code = str(openid) + ts
        m1 = hashlib.md5()
        m1.update(code.encode("utf-8"))
        order_code = m1.hexdigest()
        return order_code

    def select_openid(self, sql):
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            info = cursor.fetchone()
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("查询金额失败")
            return 0

    def select_order(self, sql):
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            info = cursor.fetchall()
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("查询金额失败")
            return 0


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
            return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
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
                            return JsonResponse({"msg": "网站维护中！请耐心等待"}, json_dumps_params={'ensure_ascii': False})
                else:
                    return JsonResponse({"msg": "当前网络不佳，请稍后再试"})
            else:
                return JsonResponse({"msg": "请先在公众号中获取业务码并且不要在微信以外的地方打开"}, json_dumps_params={'ensure_ascii': False})
        except Exception as e:
            print(e)
            return JsonResponse({"msg": "请先在关注公众号(球球趣玩)获取业务码并且不要在微信以外的地方打开"}, json_dumps_params={'ensure_ascii': False})

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
        return JsonResponse({"result": "success"}, json_dumps_params={'ensure_ascii': False})

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
                                            up_info = self.update_wxid(insert_sql)
                                            if up_info:
                                                content = "绑定客服成功！接下来开始刷广告之旅吧！详情关注公众号（球球趣玩)"
                                            else:
                                                content = "绑定客服失败！一个微信只能绑定一个业务码"
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
        return JsonResponse({"result": "success"}, json_dumps_params={'ensure_ascii': False})

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
            info = cursor.execute(sql)
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("插入微信id有误")
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


class Withdraw(View):
    # 订单
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
                        order_result = []
                        if openid:
                            openid_md5 = self.get_md5(openid)
                            order_sql = "SELECT `name`,amount,audittime,add_time from wechat_order where openid='{oid}' and `status`=1 ORDER BY add_time desc".format(
                                oid=openid_md5)
                            order_data = self.select_order(order_sql)
                            if order_data:
                                order_data = list(order_data)
                                for order in order_data:
                                    if order:
                                        tmp = []
                                        order = list(order)
                                        tmp.append(order[0])
                                        tmp.append(order[1])
                                        tmp.append(str(order[2]).split(" ")[0])
                                        tmp.append(str(order[3]).split(" ")[0])
                                        order_result.append(tmp)

                        return render(request, "tx_log.html", {
                            "order_result": order_result
                        })
            else:
                return JsonResponse({"msg": "only open in wechat"}, json_dumps_params={'ensure_ascii': False})
        except Exception as e:
            print(e)
            return JsonResponse({"msg": "fail"}, json_dumps_params={'ensure_ascii': False})

    def post(self, request):
        return HttpResponse("错误的请求")

    def get_md5(self, strs):
        m1 = hashlib.md5()
        m1.update(strs.encode("utf-8"))
        strs_md5 = m1.hexdigest()
        return strs_md5

    def select_order(self, sql):
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            info = cursor.fetchall()
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("查询订单有误")
            return 0


class Video(View):
    def get(self, request):
        return render(request, "video.html")


class Test(View):
    def get(self, request):
        return HttpResponse("功能开发中")
