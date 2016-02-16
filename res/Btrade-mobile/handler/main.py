# -*- coding: utf-8 -*-

import tornado.web
from base import BaseHandler
import config
import json, os, datetime
import time
from collections import defaultdict
from utils import *

class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        userid = self.session.get("userid")
        user = self.db.get("select varietyids from users where id = %s", userid)
        varieties = self.db.query("select name from variety where id in (" + user["varietyids"] + ")")

        purchaseinf = defaultdict(list)
        purchases = self.db.query("select t.*,a.areaname from (select p.*,u.nickname,u.name,u.type from purchase p left join users u on p.userid = u.id order by p.createtime desc limit 0,5) t left join area a on t.areaid = a.id")
        if purchases:
            purchaseids = [str(purchase["id"]) for purchase in purchases]
            purchaseinfos = self.db.query("select p.*,s.specification from purchase_info p left join specification s on p.specificationid = s.id where p.purchaseid in ("+",".join(purchaseids)+")")
            purchaseinfoids = [str(purchaseinfo["id"]) for purchaseinfo in purchaseinfos]
            purchaseattachments = self.db.query("select * from purchase_attachment where purchase_infoid in ("+",".join(purchaseinfoids)+")")
            attachments = defaultdict(list)
            for attachment in purchaseattachments:
                attachments[attachment["purchase_infoid"]] = attachment
            for purchaseinfo in purchaseinfos:
                purchaseinfo["attachments"] = attachments.get(purchaseinfo["id"])
                purchaseinf[purchaseinfo["purchaseid"]].append(purchaseinfo)
        for purchase in purchases:
            purchase["purchaseinfo"] = purchaseinf.get(purchase["id"]) if purchaseinf.get(purchase["id"]) else []
            purchase["datetime"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(float(purchase["createtime"])))
            if purchase["limited"] == 1:
                purchase["expire"] = datetime.datetime.utcfromtimestamp(float(purchase["createtime"])) + datetime.timedelta(purchase["term"])
                purchase["timedelta"] = (purchase["expire"] - datetime.datetime.now()).days
        print purchases

        #用户报过价的品种
        quotevariety = self.db.query("select v.name name from (select pi.varietyid from quote q left join purchase_info pi on q.purchaseinfoid = pi.id where userid = %s) t"
                      " left join variety v on t.varietyid = v.id group by name", userid)

        self.render("index.html", varieties=varieties, purchases=purchases, quotevariety=quotevariety)

class YaocaigouHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("yaocaigou.html")

class CenterHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user = self.db.get("select * from users where id = %s", self.session.get("userid"))
        news = self.db.query("select * from notification where receiver = %s order by type asc limit 3", self.session.get("userid"))

        unread = 0
        sell = []
        purchase = []
        quoteid = []
        for new in news:
            if new.status == 0:
                unread =+ 1
            if new.type == 1:
                new["datetime"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(float(new["createtime"])))
                if new["content"].isdigit():
                    quoteid.append(new["content"])
                sell.append(new)
            if new.type == 2:
                new["datetime"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(float(new["createtime"])))
                purchase.append(new)
        #更新session中未读信息数
        self.session["notification"] = unread
        self.session.save()

        #报价收到回复消息的表情
        results = []
        if quoteid:
            results = self.db.query("select id,state from quote where userid = %s and id in ("+",".join(quoteid)+")", self.session.get("userid"))
        faces = {}
        for result in results:
            faces[str(result["id"])] = int(result["state"])
        print faces
        self.render("center.html", user=user, unread=unread, sell=sell, purchase=purchase, faces=faces)

    @tornado.web.authenticated
    def post(self):
        pass

class UserAttentionHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, page=0):
        userid = self.session.get("userid")
        user = self.db.get("select varietyids from users where id = %s", userid)
        varieties = self.db.query("select id,name from variety where id in (" + user["varietyids"] + ")")
        self.render("user_attention.html", varieties=varieties)

class UserListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, page=0):
        page = (int(page) - 1) if page > 0 else 0
        nav = {
            'model': 'users/userlist',
            'num': self.db.execute_rowcount("SELECT * FROM users"),
        }
        users = self.db.query("SELECT * FROM users LIMIT %s,%s", page * config.conf['POST_NUM'], config.conf['POST_NUM'])
        self.render("userlist.html", users=users, nav=nav)

class UserInfoHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        user = self.db.get("SELECT * FROM users where id = %s", self.session.get("userid"))
        varieties = self.db.query("select name from variety where id in (" + user["varietyids"] + ")")
        self.render("user_info.html", user=user, varieties=varieties)

    @tornado.web.authenticated
    def post(self):
        pass

class NewsHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, type):
        news = self.db.query("select * from notification where receiver = %s", self.session.get("userid"))
        unread = {}
        sell = []
        purchase = []
        grow = []
        system = []
        quoteid = []
        for new in news:
            if new.status == 0:
                if new.type == 1:
                    unread["sell"] = True
                elif new.type == 2:
                    unread["purchase"] = True
                elif new.type == 3:
                    unread["grow"] = True
                elif new.type == 4:
                    unread["system"] = True
            if new.type == 1:
                new["datetime"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(float(new["createtime"])))
                if new["content"].isdigit():
                    quoteid.append(new["content"])
                sell.append(new)
            if new.type == 2:
                new["datetime"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(float(new["createtime"])))
                purchase.append(new)
            if new.type == 3:
                new["datetime"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(float(new["createtime"])))
                grow.append(new)
            if new.type == 4:
                new["datetime"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(float(new["createtime"])))
                system.append(new)
        #报价收到回复消息的表情
        results = []
        if quoteid:
            results = self.db.query("select id,state from quote where userid = %s and id in ("+",".join(quoteid)+")", self.session.get("userid"))
        faces = {}
        for result in results:
            faces[str(result["id"])] = int(result["state"])
        print faces
        self.render("news.html", type=int(type), unread=unread, sell=sell, purchase=purchase, grow=grow, system=system, faces=faces)

    @tornado.web.authenticated
    def post(self):
        pass

class ArticleHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, articleid):
        article = self.db.get("select * from notification where receiver = %s and id = %s", self.session.get("userid"), articleid)
        result = self.db.execute("update notification set status = 1 where receiver = %s and id = %s", self.session.get("userid"), articleid)
        print result
        article["datetime"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(float(article["createtime"])))
        self.render("article.html", article=article)

    @tornado.web.authenticated
    def post(self):
        pass

class UserUpdatePasswordHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('update_password.html')

    @tornado.web.authenticated
    def post(self):
        userid = self.session.get("userid")
        author = self.db.get("SELECT * FROM users WHERE id = %s", userid)
        if not author:
            self.api_response({'status':'faile','message':'用户名不存在'})
        elif self.get_argument("oldpassword") == "" or self.get_argument("password") == "" or self.get_argument("passwordconfirm") == "":
            self.api_response({'status':'fail','message':'新旧密码必须填写'})
        elif self.get_argument("password") != self.get_argument("passwordconfirm"):
            self.api_response({'status':'fail','message':'新密码和确认密码不一致'})
        elif md5(str(self.get_argument("oldpassword")+config.salt)) != author.password:
            self.api_response({'status':'fail','message':'旧密码不对'})
        else:
            self.db.update("UPDATE users SET password = %s  WHERE id = %s", self.get_argument("password"), userid)
            self.api_response({'status':'success','message':'更新成功'})

class UserUpdateNicknameHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        userid = self.session.get("userid")
        user = self.db.get("SELECT * FROM users WHERE id = %s", userid)
        self.render('update_nickname.html', user=user)

    @tornado.web.authenticated
    def post(self):
        nickname = self.get_argument("nickname")
        if nickname:
            self.db.update("UPDATE users SET nickname = %s  WHERE id = %s", nickname, self.session.get("userid"))
            self.api_response({'status':'success','message':'更新成功'})
        else:
            self.api_response({'status':'fail','message':'个人称呼必填'})

class UserCategoryHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        userid = self.session.get("userid")
        user = self.db.get("SELECT * FROM users WHERE id = %s", userid)
        self.render('category.html', user=user)

    @tornado.web.authenticated
    def post(self):
        type = self.get_argument("type")
        if type:
            self.db.update("UPDATE users SET type = %s  WHERE id = %s", type, self.session.get("userid"))
            self.api_response({'status':'success','message':'更新成功'})
        else:
            self.api_response({'status':'fail','message':'请选择经营类型'})

class UserRecoverHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, userid):
        self.db.execute("update users set status=1 where id = %s", userid)
        self.redirect('/users/userlist')

class UserRemoveHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, userid):
        self.db.execute("update users set status=0 where id = %s", userid)
        self.redirect('/users/userlist')