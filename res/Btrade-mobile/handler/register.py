# -*- coding: utf-8 -*-

from base import BaseHandler
import re
from utils import *
import config
import time

class RegisterHandler(BaseHandler):
    def get(self):
	    self.render("register.html")

    def post(self):
        username = self.get_argument("username")
        pattern = re.compile(r'^[A-Za-z0-9]{3,20}$')
        match = pattern.match(username)
        if match is False and username is None:
            self.api_response({'status':'fail','message':'会员名填写错误'})
            return
        usercount = self.db.execute_rowcount("select * from users where username = %s", username)
        if usercount > 0:
            self.api_response({'status':'fail','message':'此会员名已被使用'})
            return
        phone = self.get_argument("phone")
        phonepattern = re.compile(r'^1(3[0-9]|4[57]|5[0-35-9]|8[0-9]|70)\d{8}$')
        phonematch = phonepattern.match(phone)
        if phonematch is False and phone is None:
            self.api_response({'status':'fail','message':'手机号填写错误'})
            return
        phonecount = self.db.execute_rowcount("select * from users where phone = %s", phone)
        if phonecount > 0:
            self.api_response({'status':'fail','message':'此手机号已被使用'})
            return
        #verifycode = self.get_argument("verifycode")
        #if verifycode != self.session.get("verifycode"):
        #    self.api_response({'status':'fail','message':'短信验证码不正确','data':phone})

        password = self.get_argument("password")
        repeatpassword = self.get_argument("repeatpassword")
        if password is None and repeatpassword is None and password != repeatpassword:
            self.api_response({'status':'fail','message':'密码和确认密码填写错误'})
            return
        type = self.get_argument("type")
        name = self.get_argument("name")
        if name is None:
            self.api_response({'status':'fail','message':'经营主体不能为空'})
            return
        nickname = self.get_argument("nickname")
        if name is None:
            self.api_response({'status':'fail','message':'真实姓名或单位名称不能为空'})
            return
        nickname = self.get_argument("nickname")
        if nickname is None:
            self.api_response({'status':'fail','message':'个人称呼不能为空'})
            return

        lastrowid = self.db.execute_lastrowid("insert into users (username, password, phone, type, name, nickname, status, createtime)"
                             "value(%s, %s, %s, %s, %s, %s, %s, %s)", username, md5(str(password + config.salt)), phone
                             , type, name, nickname, 1, int(time.time()))
        self.api_response({'status':'success','message':'注册成功','data':{'username':username}})

class GetSmsCodeHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        #self.session.get("verifycode", "123456"):
        pass

class RegSuccessHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        self.render("register_result.html")