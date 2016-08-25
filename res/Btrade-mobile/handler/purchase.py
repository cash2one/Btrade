# -*- coding: utf-8 -*-

import tornado.web
from base import BaseHandler
import json, os, datetime, time, base64
from utils import *
from config import *
import random
from collections import defaultdict
from webbasehandler import purchase_push_trace

class PurchaseHandler(BaseHandler):
    def get(self):
        pass

    @purchase_push_trace
    def post(self, number=0):
        #列表一项是一个采购单多个品种
        # number = int(number) if number > 0 else 0
        # purchaseinf = defaultdict(list)
        # purchases = self.db.query("select t.*,a.areaname from "
        #                           "(select p.*,u.nickname,u.name from purchase p left join users u on p.userid = u.id order by p.createtime desc limit %s,%s) t "
        #                           "left join area a on t.areaid = a.id", number, config.conf['POST_NUM'])
        # if purchases:
        #     purchaseids = [str(purchase["id"]) for purchase in purchases]
        #     purchaseinfos = self.db.query("select p.*,count(q.id) quotecount from  purchase_info p "
        #                                   "left join quote q on p.id = q.purchaseinfoid where p.purchaseid in ("+",".join(purchaseids)+") group by p.id")
        #     purchaseinfoids = [str(purchaseinfo["id"]) for purchaseinfo in purchaseinfos]
        #     purchaseattachments = self.db.query("select * from purchase_attachment where purchase_infoid in ("+",".join(purchaseinfoids)+")")
        #     attachments = defaultdict(list)
        #     for attachment in purchaseattachments:
        #         attachments[attachment["purchase_infoid"]] = attachment
        #     for purchaseinfo in purchaseinfos:
        #         purchaseinfo["attachments"] = attachments.get(purchaseinfo["id"])
        #         purchaseinf[purchaseinfo["purchaseid"]].append(purchaseinfo)
        #     for purchase in purchases:
        #         purchase["purchaseinfo"] = purchaseinf.get(purchase["id"]) if purchaseinf.get(purchase["id"]) else []
        #         purchase["datetime"] = time.strftime("%Y/%m/%d %H:%M", time.localtime(float(purchase["createtime"])))
        #         if purchase["term"] != 0:
        #             # purchase["expire"] = datetime.datetime.fromtimestamp(float(purchase["createtime"])) + datetime.timedelta(purchase["term"])
        #             expire = datetime.datetime.fromtimestamp(float(purchase["createtime"])) + datetime.timedelta(purchase["term"])
        #             purchase["timedelta"] = (expire - datetime.datetime.now()).days
        #     print purchaseids
        #     self.api_response({'status':'success', 'list':purchases, 'message':'请求成功'})
        # else:
        #     self.api_response({'status':'nomore','message':'没有更多的采购订单'})
        #列表一项是一个采购单多个品种

        #列表一项是一个采购单一个品
        number = int(number) if number > 0 else 0
        myvarietyid = 0
        if self.session.get("userid", None):
            userid = self.session.get("userid")
            user = self.db.get("select varietyids from users where id = %s", userid)
            if user and user.get("varietyids", None):
                myvarietyid = user["varietyids"]

        #获取采购单的详细信息
        #purchases = self.db.query("select ta.*,u.nickname,u.name uname,u.type from (select pis.*,count(q.id) quotecount from "
        #                          "(select p.*,pi.id pid,pi.name,pi.price,pi.quantity,pi.unit,pi.quality,pi.origin,pi.specification,pi.views,"
        #                          "(case when p.term = 0 then 1 when p.createtime + p.term*86400 < unix_timestamp(now()) then 0 else 1 end) orderid,"
        #                          "(case when pi.varietyid in ("+str(myvarietyid)+") then 1 else 0 end) myvariety from "
        #                          "purchase_info pi left join purchase p on p.id = pi.purchaseid where p.status != 0 and pi.status=1 order by orderid desc,"
        #                          "myvariety desc,p.createtime desc,p.id desc limit %s,%s) "
        #                          "pis left join quote q on pis.pid = q.purchaseinfoid group by pis.pid order by orderid desc,myvariety desc,pis.createtime desc) ta "
        #                          "left join users u on ta.userid = u.id order by orderid desc,myvariety desc,ta.pid desc", number, config.conf['POST_NUM'])

        #获取采购单信息，优先显示我关注的
        purchases=self.db.query("select p.*,pi.id pid,pi.name,pi.price,pi.quantity,pi.unit,pi.quality,pi.origin,pi.specification,pi.views,pi.shine,"
                                 "(case when p.term = 0 then 1 when p.createtime + p.term*86400 < unix_timestamp(now()) then 0 else 1 end) orderid,"
                                  "(case when pi.varietyid in (%s)"%str(myvarietyid)+" then 1 else 0 end) myvariety from "
                                  "purchase_info pi left join purchase p on p.id = pi.purchaseid where p.status != 0 and pi.status=1 order by orderid desc,"
                                  "myvariety desc,p.createtime desc,p.id desc limit %s,%s",number, config.conf['POST_NUM'])


        if purchases:
            #拆分sql
            purchaseinfoids = [str(purchase["pid"]) for purchase in purchases]
            purchaseuseids = [str(purchase["userid"]) for purchase in purchases]
            purchaseuseids = list(set(purchaseuseids))  # 去重userid
            quoteinfos = self.db.query(
                "select purchaseinfoid,count(id) as quotecount from quote where purchaseinfoid in (%s) group by purchaseinfoid " % ",".join(purchaseinfoids))  # 获取报价个数
            quotecountlist= dict((i.purchaseinfoid, i.quotecount) for i in quoteinfos)
            userinfos = self.db.query(
                "select id,nickname,name,type from users where id in(%s) " % ",".join(purchaseuseids))  # 获取user信息
            purchaseuserinfo = dict((i.id, [i.nickname, i.name, i.type]) for i in userinfos)
            purchaseinfoids = [str(purchase["pid"]) for purchase in purchases]
            purchaseattachments = self.db.query("select * from purchase_attachment where purchase_infoid in (%s)"%",".join(purchaseinfoids))
            attachments = defaultdict(list)
            for attachment in purchaseattachments:
                base, ext = os.path.splitext(os.path.basename(attachment["attachment"]))
                attachment["attachment"] = config.img_domain+attachment["attachment"][attachment["attachment"].find("static"):].replace(base, base+"_thumb")
                attachments[attachment["purchase_infoid"]] = attachment

            for purchase in purchases:
                if quotecountlist.has_key(purchase.pid):
                    purchase["quotecount"]=quotecountlist[purchase.pid]
                else:
                    purchase["quotecount"] =0
                purchase["nickname"] = purchaseuserinfo[purchase.userid][0]
                purchase["uname"]= purchaseuserinfo[purchase.userid][1]
                purchase["type"] = purchaseuserinfo[purchase.userid][2]

                purchase["datetime"] = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(float(purchase["createtime"])))
                if int(purchase["term"]) != 0:
                    # purchase["expire"] = datetime.datetime.fromtimestamp(float(purchase["createtime"])) + datetime.timedelta(purchase["term"])
                    expire = datetime.datetime.fromtimestamp(float(purchase["createtime"])) + datetime.timedelta(purchase["term"])
                    purchase["timedelta"] = (expire - datetime.datetime.now()).days
                purchase["purchaseinfo"] = [{"id": purchase["pid"],"name": purchase["name"],"attachments":attachments.get(purchase["pid"]),
                                             "origin": purchase["origin"],"purchaseid": purchase["id"],"quality": purchase["quality"],"term": purchase["term"],
                                             "quantity": purchase["quantity"],"quotecount": purchase["quotecount"],"specification": purchase["specification"],"datetime": purchase["datetime"],
                                             "unit": purchase["unit"],"views": purchase["views"],"timedelta": purchase.get("timedelta")}]

            self.api_response({'status':'success', 'list':purchases, 'message':'请求成功'})
        else:
            self.api_response({'status':'nomore','message':'没有更多的采购订单'})
        #列表一项是一个采购单一个品种

class PurchaseInfoHandler(BaseHandler):
    @purchase_push_trace
    def get(self, id):
        #purchaseinfo = self.db.get("select t.*,a.position,a.parentid from "
        #"(select p.id,p.userid,p.pay,p.payday,p.payinfo,p.accept,p.send,p.receive,p.other,p.supplier,p.remark,p.createtime,"
        #"p.term,p.status,p.areaid,p.invoice,pi.id pid,pi.name,pi.price,pi.quantity,pi.unit,pi.quality,pi.origin,pi.specification,"
        #"pi.views from purchase p,purchase_info pi where p.id = pi.purchaseid and pi.id = %s) t left join area a on a.id = t.areaid",id)
        #获取采购单详细信息

        purchaseinfo =self.db.get("select p.id,p.userid,p.pay,p.payday,p.payinfo,p.accept,p.send,p.receive,p.other,p.supplier,p.remark,p.createtime,"
        "p.term,p.status,p.areaid,p.invoice,pi.id pid,pi.name,pi.price,pi.quantity,pi.unit,pi.quality,pi.origin,pi.specification,"
        "pi.views,pi.status,pi.shine from purchase p,purchase_info pi where p.id = pi.purchaseid and pi.id = %s",id)

        if purchaseinfo==None:
            self.error("采购单不存在", "/")
            return

        #获取采购单area信息
        areaid = purchaseinfo["areaid"]
        areainfo=self.db.get("select position,parentid from area where id =%s",areaid)
        if areainfo:
            purchaseinfo["position"]=areainfo.position
            purchaseinfo["parentid"] = areainfo.parentid
        else:
            purchaseinfo["position"] =""




        #获得采购品种图片
        attachments = self.db.query("select * from purchase_attachment where purchase_infoid = %s", id)
        for attachment in attachments:
            base, ext = os.path.splitext(os.path.basename(attachment["attachment"]))
            attachment["attachment"] = config.img_domain+attachment["attachment"][attachment["attachment"].find("static"):].replace(base, base+"_thumb")
        user = self.db.get("select * from users where id = %s", purchaseinfo["userid"])
        purchaseinfo["datetime"] = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(int(purchaseinfo["createtime"])))
        if purchaseinfo["term"] != 0:
            purchaseinfo["expire"] = datetime.datetime.fromtimestamp(float(purchaseinfo["createtime"])) + datetime.timedelta(purchaseinfo["term"])
            purchaseinfo["timedelta"] = (purchaseinfo["expire"] - datetime.datetime.now()).days
        purchaseinfo["attachments"] = attachments

        others = self.db.query("select id from purchase_info where purchaseid = %s and id != %s",
                                      purchaseinfo["id"], purchaseinfo["pid"])

        #此采购商成功采购单数
        purchases = self.db.execute_rowcount("select * from purchase where userid = %s and status = 4", user["id"])
        # 此采购商采购批次数
        purchasesinfocout = self.db.execute_rowcount("select * from purchase p  left join purchase_info pi on p.id=pi.purchaseid where userid = %s ", user["id"])

        #此采购单报价数
        quotes = self.db.execute_rowcount("select * from quote where purchaseinfoid = %s", purchaseinfo["pid"])
        #此采购商回复供应商比例
        purchaser_quotes = self.db.query("select p.id,p.userid,t.state state from purchase p left join "
            "(select pi.purchaseid,q.state from purchase_info pi left join quote q on pi.id = q.purchaseinfoid) t "
                "on p.id = t.purchaseid where p.userid = %s", user["id"])
        reply = 0

        for purchaser_quote in purchaser_quotes:
            if purchaser_quote.state is not None and purchaser_quote.state != 0:
                reply = reply + 1

        #浏览数加1
        self.db.execute("update purchase_info set views = views + 1 where id = %s", purchaseinfo["pid"])

        self.render("purchaseinfo.html", user=user, purchase=purchaseinfo, others=len(others), purchases=purchases,purchasesinfocout=purchasesinfocout,
                    quotes=quotes, reply=int((float(reply)/float(len(purchaser_quotes))*100) if len(purchaser_quotes) != 0 else 0))

    def post(self):
        pass

class PurchaseinfoBatchHandler(BaseHandler):

    @purchase_push_trace
    def get(self, purchaseid):
        purchaseinf = defaultdict(list)
        purchase = self.db.get("select t.*,a.position from "
                                  "(select p.*,u.nickname,u.name,u.type from purchase p left join users u on p.userid = u.id where p.id = %s) t"
                                  " left join area a on t.areaid = a.id", purchaseid)
        if purchase:
            user = self.db.get("select * from users where id = %s", purchase["userid"])
            if purchase:
                purchaseinfos = self.db.query("select p.*,count(q.id) quotecount from purchase_info p "
                                              "left join quote q on p.id = q.purchaseinfoid where p.purchaseid = %s group by p.id", purchaseid)
                purchaseinfoids = [str(purchaseinfo["id"]) for purchaseinfo in purchaseinfos]
                purchaseattachments = self.db.query("select * from purchase_attachment where purchase_infoid in ("+",".join(purchaseinfoids)+")")
                attachments = defaultdict(list)
                for attachment in purchaseattachments:
                    attachments[attachment["purchase_infoid"]] = attachment
                for purchaseinfo in purchaseinfos:
                    purchaseinfo["attachments"] = {}
                    if attachments.has_key(purchaseinfo["id"]):
                        base, ext = os.path.splitext(os.path.basename(attachments.get(purchaseinfo["id"])["attachment"]))
                        attachments.get(purchaseinfo["id"])["attachment"] = config.img_domain+attachments.get(purchaseinfo["id"])["attachment"][attachments.get(purchaseinfo["id"])["attachment"].find("static"):].replace(base, base+"_thumb")
                        purchaseinfo["attachments"] = attachments.get(purchaseinfo["id"])
                    purchaseinf[purchaseinfo["purchaseid"]].append(purchaseinfo)
                    purchase["views"] =+ purchaseinfo["views"]

            purchase["purchaseinfo"] = purchaseinf.get(purchase["id"]) if purchaseinf.get(purchase["id"]) else []
            purchase["datetime"] = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(float(purchase["createtime"])))
            if purchase["term"] != 0:
                purchase["expire"] = datetime.datetime.fromtimestamp(float(purchase["createtime"])) + datetime.timedelta(purchase["term"])
                purchase["timedelta"] = (purchase["expire"] - datetime.datetime.now()).days

            #此采购商成功采购单数
            purchases = self.db.execute_rowcount("select * from purchase where userid = %s and status = 4", user["id"])
            # 此采购商采购批次数
            purchasesinfocout = self.db.execute_rowcount(
                "select * from purchase p  left join purchase_info pi on p.id=pi.purchaseid where userid = %s ",
                user["id"])

            #此采购商回复供应商比例
            purchaser_quotes = self.db.query("select p.id,p.userid,t.state state from purchase p left join "
                "(select pi.purchaseid,q.state from purchase_info pi left join quote q on pi.id = q.purchaseinfoid) t "
                    "on p.id = t.purchaseid where p.userid = %s", user["id"])
            reply = 0
            for purchaser_quote in purchaser_quotes:
                if purchaser_quote.state is not None and purchaser_quote.state != 0:
                    reply = reply + 1

            self.render("purchaseinfo_batch.html", user=user, purchase=purchase, purchases=purchases,purchasesinfocout=purchasesinfocout,
                        reply=int((float(reply)/float(len(purchaser_quotes))*100) if len(purchaser_quotes) != 0 else 0))
        else:
            self.error("采购单不存在","/")

    @tornado.web.authenticated
    def post(self):
        pass

# class GetCityHandler(BaseHandler):
#
#     def get(self):
#         pass
#
#     def post(self):
#         provinceid = self.get_argument("provinceid")
#         if provinceid == "":
#             self.api_response({'status':'fail','message':'请选择省份'})
#         else:
#             cities = self.db.query("SELECT id,areaname FROM area WHERE parentid = %s", provinceid)
#             self.api_response({'status':'success','message':'请求成功','data':cities})

class UploadFileHandler(BaseHandler):

    @purchase_push_trace
    @tornado.web.authenticated
    def get(self):
        pass

    @purchase_push_trace
    @tornado.web.authenticated
    def post(self):
        type = self.get_argument("type")
        base64_string = self.get_argument("base64_string")
        imgData = base64.b64decode(base64_string)
        now = datetime.date.today().strftime("%Y%m%d")
        #文件的暂存路径
        # root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        root_path = config.img_path
        upload_path = os.path.join(root_path, now)
        if os.path.exists(upload_path) is False:
            os.mkdir(upload_path)
        name = str(int(time.time())) + str(self.session.get("userid")) + type
        ext = ".png"
        filename = md5(str(name))+ext
        filepath = os.path.join(upload_path,filename)
        try:
            #保存上传图片
            with open(filepath,'wb') as up:
                up.write(imgData)
            #生成缩略图
            make_thumb(filepath,upload_path,300,300)
            uploadfiles = self.session.get("uploadfiles_quote", {})
            uploadfiles[type] = filepath
            self.session["uploadfiles_quote"] = uploadfiles
            self.session.save()
            self.api_response({'status':'success','message':'上传成功','path':filepath})
        except IOError:
            print ' in  IOError'
            self.api_response({'status':'fail','message':'上传失败'})
            return


class DeleteFileHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        pass

    @purchase_push_trace
    @tornado.web.authenticated
    def post(self):
        type = self.get_argument("type")
        uploadfiles = self.session.get("uploadfiles_quote")
        if uploadfiles.has_key(type):
            if os.path.isfile(uploadfiles[type]):
                os.remove(uploadfiles[type])
                base, ext = os.path.splitext(os.path.basename(uploadfiles[type]))
                filename = uploadfiles[type].replace(base, base+"_thumb")
                os.remove(filename)
                del uploadfiles[type]
                self.session["uploadfiles_quote"] = uploadfiles
                self.session.save()
                self.api_response({'status':'success','message':'删除成功'})
            else:
                del uploadfiles[type]
                self.session["uploadfiles_quote"] = uploadfiles
                self.session.save()
                self.api_response({'status':'fail','message':'文件不存在'})
        else:
            self.api_response({'status':'success','message':'文件路径不存在'})

class GetVarietyInfoHandler(BaseHandler):

    def get(self):
        pass

    @purchase_push_trace
    def post(self):
        variety = self.get_argument("variety")
        if variety == "":
            self.api_response({'status':'fail','message':'请填写品种'})
        elif is_cn(variety):
            varietyinfo = self.db.query("SELECT id,name,origin FROM variety WHERE name like %s or alias like %s", "%"+variety+"%", "%"+variety+"%")
            if len(varietyinfo) == 0:
                self.api_response({'status':'fail','message':'没有该品种'})
            else:
                self.api_response({'status':'success','message':'请求成功','list':varietyinfo})
                # specifications = self.db.query("SELECT id,specification FROM specification WHERE varietyid = %s", varietyinfo[0]["id"])
                # self.api_response({'status':'success','message':'请求成功','list':varietyinfo,'specifications':specifications})
        else:
            self.api_response({'status':'fail','message':'请输入中文'})

class SaveVarietyHandler(BaseHandler):

    @purchase_push_trace
    def post(self):
        varietyids = self.get_argument("varietyids")
        if varietyids == "":
            self.api_response({'status':'fail','message':'请填写品种'})
        else:
            #print
            result = self.db.execute("update users set varietyids = %s where id = %s", varietyids, self.session.get("userid"))
            if result:
                self.api_response({'status':'fail','message':'没有该品种'})
            else:
                self.api_response({'status':'success','message':'请求成功'})

class RemovePurchaseHandler(BaseHandler):

    @purchase_push_trace
    @tornado.web.authenticated
    def post(self):
        rtype=self.get_argument("rtype",None)
        pid=self.get_argument("pid",None)
        if rtype and pid:
            if int(rtype)==0:
                self.db.execute("UPDATE purchase SET status = 0 WHERE id = %s", pid)
                self.db.execute("UPDATE purchase_info SET status = 0 WHERE  purchaseid = %s",
                                pid)  # 关闭所有该批次的采购单
                self.api_response({'status':'success','message':'请求成功'})
            else:
                purchase = self.db.query("SELECT distinct purchaseid FROM purchase_info WHERE id = %s",
                                         pid)
                if purchase:
                    self.db.execute("UPDATE purchase_info SET status = 0 WHERE  id = %s",
                                    pid)
                    notclose = self.db.query("select * from purchase_info where purchaseid = %s and status=1",
                                               purchase[0].purchaseid)
                    if len(notclose) == 0:
                        self.db.execute("UPDATE purchase SET status = 0 WHERE id = %s",
                                        purchase[0].purchaseid)
                    self.api_response({'status': 'success', 'message': '请求成功'})
                else:
                    self.api_response({'status': 'fail', 'message': '请求失败，没有该采购单'})
        else:
            self.api_response({'status': 'fail', 'message': '参数不全'})
