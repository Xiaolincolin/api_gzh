"""
author: Colin
@time: 2020-03-21 14:42
explain:

"""

import os

import requests
from PIL import Image, ImageEnhance
from pyzbar.pyzbar import decode
import cv2
from io import StringIO

"""
图片包含二维码检测
"""
def qrcode_recongnize(filename):
    try:
        img = Image.open(filename).convert('RGB')
        img = ImageEnhance.Brightness(img).enhance(1.0)
        img = ImageEnhance.Sharpness(img).enhance(1.5)
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = img.convert('L')
        result = decode(img)
        if len(result)>0:
            return True
        else:
            return False
    except:
        return False


def get_image():
    res = requests.get("http://mmbiz.qpic.cn/mmbiz_jpg/7UibrgjXLfNeiaJJcQDjHkuQzjk56IDP4lR5JRBvEL4FciaLFSZIia4CMcfJ0oiaV9xqz6iaac2w4gDThPx5w9rszFCg/0")
    if res.status_code==200:
        img = res.content
        imgs = StringIO(img)
        flag = qrcode_recongnize(imgs)
        print(flag)
        # with open("c.png",'wb+') as f:
        #     f.write(img)


if __name__ == '__main__':

    # filepath="F:/img_spam/"
    # for parent,dirnames,filenames in os.walk(filepath):
    #  for filename in filenames:
    #     print(filename)
    #     kk=qrcode_recongnize(filepath,filename)
    #     print(filename,kk)

    # get_image()
    flag = qrcode_recongnize("./c.png")
    print(flag)