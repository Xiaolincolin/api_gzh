from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import View


# 登录逻辑
from wkteam.forms import LoginForm


class LoginView(View):
    def get(self, request):
        return render(request, "login.html", {})

    def post(self, request):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user_name = request.POST.get("username", "")
            pass_word = request.POST.get("password", "")

            user = authenticate(username=user_name, password=pass_word)
            print(user)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('media/')
            else:
                return render(request, 'login.html', {"msg": "用户名或密码错误！"})
        else:
            return render(request, 'login.html', {"msg": "用户名或密码错误！"})

class WkSupervisory(View):
    def get(self):
        pass
