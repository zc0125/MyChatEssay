#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @author fengye
# @date 2022/5/19 10:39
import json
import socket
import threading
import time

class CClient:

    def __init__(self, ip, port, name, recv_name):
        self.m_ip = ip
        self.m_port = port
        self.m_name = name
        self.m_uid = 0
        self.m_recv_uid = 0
        self.m_recv_name = recv_name
        self.m_recv_flag = True
        self.m_tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.m_tcp_client.connect((self.m_ip, self.m_port))

    def start(self):
        self.m_tcp_client.send(self.m_name.encode("utf-8"))

    def exit(self):
        self.m_recv_flag = False
        self.m_tcp_client.close()

    def set_recv(self, recv_uid, recv_name):
        self.m_recv_uid = recv_uid
        self.m_recv_name = recv_name

    def send_msg(self, msg):
        now_time = time.time()
        data = {
            "time"     : now_time,
            "send_uid" : self.m_uid,
            "send_name": "",
            "recv_uid" : self.m_recv_uid,
            "recv_name": self.m_recv_name,
            "msg"      : msg,
        }
        json_data = json.dumps(data).encode("utf-8")
        self.m_tcp_client.send(json_data)

    def recv_msg(self):
        while self.m_recv_flag:
            json_data, addr = self.m_tcp_client.recvfrom(1024)
            data = json.loads(json_data.decode("utf-8"))
            send_time = data.get("time", 0)
            send_name = data.get("send_name", "")
            send_msg = data.get("msg", "")
            if send_time and send_name and send_msg:
                time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(send_time))
                print(f"\n{send_name}:{time_str}\n\t{send_msg}\n")


if __name__ == "__main__":
    server_ip = input("服务器ip:")
    server_port = int(input("服务器端口:"))
    name = input("你的名字:")
    client_istance = CClient(server_ip, server_port, name, "")
    client_istance.start()
    thread_recv_msg = threading.Thread(target=client_istance.recv_msg)
    thread_recv_msg.setDaemon(True)
    thread_recv_msg.start()
    while True:
        recv_name = input("与谁对话:")
        if recv_name == "exit client":
            client_istance.send_msg('exit-server')
            client_istance.exit()
            break
        client_istance.set_recv(0, recv_name)
        while True:
            msg = input("输入信息：")
            if msg == "change_user" or msg == "exit client":
                break
            client_istance.send_msg(msg)
        if msg == "exit client":
            client_istance.exit()
            break




