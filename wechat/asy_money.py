"""
author: Colin
@time: 2020-05-24 9:38
explain:

"""

import datetime
import hashlib

import pymysql
import redis
from DBUtils.PooledDB import PooledDB

MYSQL_DB_NAME = "adi"
MYSQL_DB_USER = "root"
MYSQL_DB_PWD = "timt!m"
# MYSQL_DB_PWD = "xiaolin"
MYSQL_DB_HOST = "127.0.0.1"
# MYSQL_DB_HOST = "39.104.143.109"

pool = PooledDB(pymysql, host=MYSQL_DB_HOST, user=MYSQL_DB_USER, passwd=MYSQL_DB_PWD, db='adi', port=3306,
                charset="utf8")
rdp_local = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0, decode_responses=True)  # 默认db=0，测试使用db=1
rdc_local = redis.StrictRedis(connection_pool=rdp_local)


class PayAsy:
    def __init__(self):
        pass

    def handle_money(self):
        openid_list = []
        wx_list = []
        select_opneid = "SELECT DISTINCT openid FROM wechat_money;"
        select_all_wx_id = "SELECT DISTINCT wx_id FROM wechat_material"
        all_openid = self.select_data(select_opneid)
        if all_openid:
            for per in all_openid:
                openid_list.append(per[0])

        all_wx_id = self.select_data(select_all_wx_id)
        if all_wx_id:
            for per in all_wx_id:
                wx_list.append(per[0])

        if not wx_list:
            return
        for wx_id in wx_list:
            self.amount_money(wx_id, openid_list)

    def amount_money(self, wx_id, open_list):
        game_amount = 0
        app_amount = 0
        withdrawable = 0
        alread = 0
        select_ad = "SELECT m.type_id,r.openid FROM wechat_material as m,wechat_related as r where r.wx_id=m.wx_id and r.wx_id='{wx_id}'".format(
            wx_id=wx_id)
        all_ad = self.select_data(select_ad)
        if not all_ad:
            return
        openid = (all_ad[0])[1]
        for ad in all_ad:
            type_id = ad[0]
            if str(type_id) == "1":
                game_amount += 1
            else:
                app_amount += 1
        game_price, app_price = self.unit_price()
        if not game_price and not app_price:
            game_price = 1
            app_price = 0.2
        sum_money = round(float(game_amount) * float(game_price), 2) + round(float(app_amount) * float(app_price), 2)
        if openid not in open_list:
            insert_sql = "insert into wechat_money(openid,withdrawable,totalmoney,alread,add_time) values (%s,%s,%s,0,NOW())"
            insert_result = self.insert_money(insert_sql, [openid, sum_money, sum_money])
            if insert_result:
                print(wx_id + "插入金额" + str(sum_money) + "成功")
            else:
                print(wx_id + "插入金额" + str(sum_money) + "失败")
        else:
            alread_sql = "SELECT alread FROM wechat_money where openid='{openid}'".format(openid=openid)
            alread_result = self.select_data(alread_sql)
            if alread_result:
                alread = (alread_result[0])[0]
                if not alread:
                    alread = 0
                alread = round(float(alread), 2)
                withdrawable = round(sum_money - alread, 2)
                update_sql = "UPDATE wechat_money set withdrawable='%s',totalmoney='%s',update_time=NOW() where openid='%s'" % (
                    withdrawable, sum_money, openid)
                info = self.update_money(update_sql)
                if info:
                    print(wx_id + "更新金额" + str(sum_money), " " + str(withdrawable) + "成功")
                else:
                    print(wx_id + " " + openid + "更新失败")
        print(wx_id, " ", game_amount, " ", app_amount)
        print(wx_id, " ", sum_money, " ", withdrawable, " ", alread)

    def unit_price(self):
        prices = rdc_local.mget("game_price", "app_price")
        if prices and len(prices) == 2:
            return prices[0], prices[1]
        else:
            return "", ""

    def select_data(self, sql):
        try:
            conn = pool.connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            info = cursor.fetchall()
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("查询数据有误")
            return []

    def select_openid(self, sql):
        try:
            conn = pool.connection()
            cursor = conn.cursor()
            info = cursor.execute(sql)
            cursor.close()
            return info
        except Exception as e:
            print(e)
            print("查询数据有误")
            return 0

    def update_money(self, sql):
        try:
            conn = pool.connection()
            cursor = conn.cursor()
            info = cursor.execute(sql)
            conn.commit()
            cursor.close()
            conn.close()
            return info
        except Exception as e:
            print(e)
            print("更新金额")
            return 0

    def insert_money(self, sql, param):
        try:
            conn = pool.connection()
            cursor = conn.cursor()
            info = cursor.execute(sql, param)
            conn.commit()
            cursor.close()
            conn.close()
            return info
        except Exception as e:
            print(e)
            print("更新金额")
            return 0


if __name__ == '__main__':
    ps = PayAsy()
    ps.handle_money()
