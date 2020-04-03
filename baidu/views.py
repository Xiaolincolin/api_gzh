import json
import logging
from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

from baidu.utils.utils import KafkaTopicWriter

max_records = 1000
max_elapsed_time = 10
bootstrap_servers_list = ["node1:19092", "node2:19092", "node3:19092"]
ktw = KafkaTopicWriter(bootstrap_servers_list, "adi_flow_json_v7", acks='all')


class Baidu(View):
    def get(self, request):
        return HttpResponse("错误的请求")

    def post(self, request):
        logger_money = logging.getLogger('baidu')
        data = request.POST.get("data")
        if data:
            tmp_data = json.loads(data)
            product = tmp_data.get("product", "")
            creative = tmp_data.get("creative", "")
            ktw.sendjsondata(data)
            msg = str(self.get_now_str()) + " " + product + " " + str(creative) + " " + "发送成功"
            logger_money.info(msg)
        else:
            msg = str(self.get_now_str()) + " data为空"
            logger_money.info(msg)
        return HttpResponse("成功")

    def get_now_str(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
