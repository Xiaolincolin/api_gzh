"""
author: Colin
@time: 2020-03-20 18:43
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
MYSQL_DB_HOST = "127.0.0.1"

pool = PooledDB(pymysql, host=MYSQL_DB_HOST, user=MYSQL_DB_USER, passwd=MYSQL_DB_PWD, db='adi', port=3306,
                charset="utf8")
rdp_local = redis.ConnectionPool(host='127.0.0.1', port=6379, db=3)  # 默认db=0，测试使用db=1
rdc_local = redis.StrictRedis(connection_pool=rdp_local)


class PayAsy:
    def get_data(self, days, yesterday, flag):
        if not flag:
            yesterday = (datetime.date.today() + datetime.timedelta(days=-1)).strftime("%Y-%m-%d")
            today = (datetime.date.today()).strftime("%Y-%m-%d")
        else:
            yesterday = yesterday
            today = days

        select_sql = "SELECT a.wx_id,amount,amount_app,n.name,r.openid,a.days FROM wechat_name as n,wechat_account_api as a,wechat_related as r where n.wx_id=a.wx_id and a.wx_id=r.wx_id and days='{days}'".format(
            days=str(today))
        data = self.select_data(select_sql)
        if data:
            data = list(data)

            for per in data:
                if per:
                    per = list(per)
                    try:
                        wx_id = per[0]
                        game = per[1]
                        app = per[2]
                        name = per[3]
                        openid = per[4]
                        days = per[5]
                    except Exception as e:
                        wx_id = ""
                        game = 0
                        app = 0
                        name = ""
                        openid = ""
                        days = ""

                    # redis中今天游戏的数据
                    game_flag = 0
                    update_game = 0
                    sum_today_game = int(game)
                    key_game = openid + ":" + days + ":game"
                    key_game_yesterday = openid + ":" + str(yesterday) + ":game"
                    redis_game_data = rdc_local.get(key_game)
                    if not redis_game_data:
                        # yesterday_data = rdc_local.get(key_game_yesterday)
                        # if yesterday_data:
                        #     rdc_local.delete(key_game_yesterday)

                        rdc_local.set(key_game, sum_today_game)
                        update_game = 0
                        game_flag = 1
                    else:
                        redis_game_data = int(redis_game_data)
                        if redis_game_data != sum_today_game:
                            rdc_local.set(key_game, sum_today_game)
                            update_game = sum_today_game - redis_game_data
                            game_flag = 1

                    # redis中今天应用的数据
                    app_flag = 0
                    update_app = 0
                    sum_today_app = int(app)
                    key_app = openid + ":" + days + ":app"
                    key_app_yesterday = openid + ":" + str(yesterday) + ":app"
                    redis_app_data = rdc_local.get(key_app)
                    if not redis_app_data:
                        # yesterday_data_app = rdc_local.get(key_app_yesterday)
                        # if yesterday_data_app:
                        #     rdc_local.delete(key_app_yesterday)
                        rdc_local.set(key_app, sum_today_app)
                        update_app = 0
                        app_flag = 1
                    else:
                        redis_app_data = int(redis_app_data)
                        if redis_app_data != sum_today_app:
                            rdc_local.set(key_app, sum_today_app)
                            update_app = sum_today_app - redis_app_data
                            app_flag = 1

                    if game_flag or app_flag:
                        if wx_id and openid:
                            select_sql = "SELECT id from wechat_money where openid='{oid}'".format(oid=openid)
                            select_result = self.select_openid(select_sql)

                            sum_money = 0

                            if game_flag == 1 and update_game == 0:
                                sum_money += game
                            else:
                                update_game = int(update_game)
                                sum_money += update_game

                            if app_flag == 1 and update_app == 0:
                                sum_money += round(app * 0.2, 2)
                            else:
                                update_app = float(update_app)
                                sum_money += round(update_app * 0.2, 2)

                            if not select_result:
                                insert_sql = "insert into wechat_money(openid,withdrawable,totalmoney,alread,add_time) values (%s,%s,%s,0,NOW())"
                                insert_result = self.insert_money(insert_sql, [openid, sum_money, sum_money])
                                if insert_result:
                                    print(name + "插入金额" + str(sum_money) + "成功")
                                else:
                                    print(name + "插入金额" + str(sum_money) + "失败")


                            elif sum_money != 0:
                                update_sql = "UPDATE wechat_money set withdrawable=withdrawable+'%.2f',totalmoney=totalmoney+'%.2f',update_time=NOW() where openid='%s'" % (
                                    sum_money, sum_money, openid)
                                info = self.update_money(update_sql)
                                if info:
                                    print(name + "更新金额" + str(sum_money) + "成功")
                                else:
                                    # 81b0180003fc096f9a446ac2c939ff5e
                                    print(name + " " + openid + "更新失败")
                            else:
                                print(name + "金额为0")
                        else:
                            print("openid或wx_id不存在")
                    else:
                        print(name + "暂未更新")

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
            return 0

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
    p = PayAsy()
    days = (datetime.date.today()).strftime("%d")
    for i in range(0, int(days)):
         t = (datetime.date.today() + datetime.timedelta(days=-i)).strftime("%Y-%m-%d")
         print(t)
         p.get_data(t, "", 1)
   # p.get_data("", "", 0)
