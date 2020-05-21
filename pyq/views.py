import logging
import json
from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View
from baidu.utils.utils import KafkaTopicWriter
max_records = 1000
max_elapsed_time = 10
bootstrap_servers_list = ["node1:19092", "node2:19092", "node3:19092"]
ktw = KafkaTopicWriter(bootstrap_servers_list, "adi_flow_pyq_v2", acks='all')

# Create your views here.


class Pyq(View):
    def get(self, request):
        return HttpResponse("成功")

    def post(self, request):
        logger_pyq = logging.getLogger('pyq')
        try:
            data = request.body
            if data:
                data = json.loads(data)
                data = data.get("data")
                code = data.get("code", "")
                adinfo = data.get("adinfo", "")
                wxid = data.get("wxid", "")
                if code:
                    msg = str(self.get_now_str()) + " " +str(wxid)+" 绑定 "+json.dumps(data)
                    logger_pyq.info(msg)
                    ktw.sendjsondata(data)
                elif adinfo:
                    msg = str(self.get_now_str()) + " " +str(wxid)+ "广告 " + json.dumps(data)
                    logger_pyq.info(msg)
                    ktw.sendjsondata(data)
                else:
                    msg = str(self.get_now_str())+"data异常"
                    logger_pyq.info(msg)
            else:
                msg = str(self.get_now_str()) + "data不存在"
                logger_pyq.info(msg)
        except Exception as e:
            logger_pyq.info(e)
        return HttpResponse("成功")
    def get_now_str(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')