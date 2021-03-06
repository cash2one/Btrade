#coding:utf8
from kafka import KafkaConsumer
import json
import sys,os
sys.path.append(os.path.join(sys.path[0],".."))
from globalconfig import *
# kafka consumer

class KafkaConsumerServer(object):
    def __init__(self,topic,server):
        if type(server)!=list:
            server=[server]
        self._consumer= KafkaConsumer(topic,
                         bootstrap_servers=server,
                         group_id="consumer-group",
                         value_deserializer=lambda m: json.loads(m.decode('utf8')))
    def getConsumer(self):
        return self._consumer
    def close(self):
        self._consumer.close()




if __name__ == "__main__":
    kafkaserver = KafkaConsumerServer(send_task_topic,kafka_server)
    for message in kafkaserver.getConsumer():
        print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                          message.offset, message.key,
                                         message.value))
    #items=[{"phone":"1312222","vars":{},"message":"手机号格式错误"},{"phone":"131222456","vars":{},"message":"手机号格式错误"}]

    #not_send_list = [item["phone"] for item in items]
   # print "1312222" not in not_send_list