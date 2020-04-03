import json

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
        data = request.POST.get("data")
        if data:
            ktw.sendjsondata(data)
            print('百度发送成功')
        return HttpResponse("成功")
