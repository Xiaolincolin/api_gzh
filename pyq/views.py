import logging

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View


# Create your views here.


class Pyq(View):
    def get(self, request):
        return HttpResponse("成功")

    def post(self, request):
        logger_pyq = logging.getLogger('pyq')
        data = request.POST.get("data")
        logger_pyq.info(data)
        if data:
            code = data.get("code", "")
            adinfo = data.get("adinfo", "")
            if code:
                username = data.get("username", "")
                extraname = data.get("extraname", "")

            elif adinfo:
                ad_type = data.get("tyoe", "")
            else:
                logger_pyq.info("null")
        else:
            logger_pyq.info("data is null")
        return HttpResponse("成功")
