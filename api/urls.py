"""api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from api.settings import MEDIA_ROOT
from django.views.static import serve
from wechat.views import Wechat, Weteam, Tutorial, \
    Index, BeginMakeMoney, CashWithdrawal, Launch, UploadImage, Test, Withdraw

urlpatterns = [
    path('admin/', admin.site.urls),
    path('MP_verify_uDpBz4xRXeQ3bjPp.txt',
         TemplateView.as_view(template_name='MP_verify_uDpBz4xRXeQ3bjPp.txt', content_type='text/plain')),
    url(r'^$', csrf_exempt(Wechat.as_view()), name="wechat"),
    url(r'^api/wechat$', csrf_exempt(Weteam.as_view()), name="weteam"),
    url(r'^tutorial$', csrf_exempt(Tutorial.as_view()), name="tutorial"),
    url(r'^index$', csrf_exempt(Index.as_view()), name="index"),
    url(r'^getcode$', BeginMakeMoney.as_view(), name="begin"),
    url(r'^tx', CashWithdrawal.as_view(), name="tx"),
    url(r'^launch', Launch.as_view(), name="launch"),
    url(r'^upimg$', csrf_exempt(UploadImage.as_view()), name="upimg"),
    url(r'^media/(?P<path>.*)$', serve, {"document_root": MEDIA_ROOT}),
    url(r'^test', Test.as_view(), name="test"),
    # Withdraw
    url(r'^withdraw', Withdraw.as_view(), name="withdraw"),
]
