#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @author fengye
# @date 2022/5/19 14:00

import json
import threading
import socket
import time


class CClientConn(object):

    def __init__(self, conn, address):
        self.m_conn = conn
        self.m_address = address
        self.m_name = ""

    def close(self):
        if self.m_conn:
            self.m_conn.close()

    def del_client(self):
        CClientManage.del_name_addr(self.m_name)
        CClientManage.del_addr_client(self.m_address)
        self.close()

    def send_msg(self, data):
        if self.m_conn is None:
            print("Server> 未与客户端连接")
            self.del_client()
        self.m_conn.send(json.dumps(data).encode('utf-8'))

    def send_no_read_msg(self):
        if self.m_conn is None:
            print("Server> 未与客户端连接")
            self.del_client()
        no_read_msgs = CClientManage.get_no_read_message(self.m_name)
        for _data in no_read_msgs:
            self.send_msg(_data)

    def recv_msg(self):
        flag = True
        if self.m_conn is None:
            print("Server> 未与客户端连接")
            self.del_client()
        self.m_name = str(self.m_conn.recv(1024), encoding="utf-8")
        CClientManage.set_name_addr(self.m_address, self.m_name)
        self.send_no_read_msg()
        while flag:
            recv_data = self.m_conn.recv(1024)
            data = json.loads(recv_data.decode("utf-8"))
            if data.get('msg') == 'exit-server':
                flag = False
                self.del_client()
            else:
                data["send_name"] = self.m_name
                print(f"\nClient:<{self.m_address}>:\n{data}")
                CClientManage.set_message(self.m_address, data)


class CClientManage(object):
    # 名称ip标识
    NAME_ADDR_MAPPING = {}
    # IP对应连接
    ADDR_CLIENT = {}
    # 客户端消息队列
    CLIENT_DATA = []
    # 客户端未读消息
    NAME_NO_READ = {}

    # 客户端消息计数
    # CLIENT_DATA_COUNT = {}

    @classmethod
    def set_name_addr(cls, address, name):
        if cls.check_client(address):
            cls.NAME_ADDR_MAPPING[name] = address
            return True
        else:
            return False

    @classmethod
    def get_name_addr(cls, name):
        if name not in cls.NAME_ADDR_MAPPING:
            return None
        return cls.NAME_ADDR_MAPPING.get(name, None)

    @classmethod
    def del_name_addr(cls, name):
        address = cls.NAME_ADDR_MAPPING.pop(name, None)
        return address

    @classmethod
    def set_addr_client(cls, address, client_instance: CClientConn):
        if not cls.check_client(address):
            cls.ADDR_CLIENT[address] = client_instance
            return True
        else:
            return False

    @classmethod
    def get_addr_client(cls, address) -> CClientConn:
        if not cls.check_client(address):
            return None
        if address not in cls.ADDR_CLIENT:
            return None
        return cls.ADDR_CLIENT.get(address, None)

    @classmethod
    def del_addr_client(cls, address):
        if not cls.check_client(address):
            return None
        client_istance = cls.ADDR_CLIENT.pop(address, None)
        return client_istance

    @classmethod
    def check_client(cls, address):
        if address and address in cls.ADDR_CLIENT:
            return True
        return False

    @classmethod
    def set_message(cls, address, data):
        if not address:
            return False
        if cls.check_client(address):
            cls.CLIENT_DATA.append(data)
            return True
        else:
            name = data.get("name", "")
            name and cls.NAME_NO_READ.setdefault(name, []).append(data)
            return False

    @classmethod
    def get_message(cls):
        if cls.CLIENT_DATA:
            return cls.CLIENT_DATA.pop(0)
        return None

    @classmethod
    def get_no_read_message(cls, name):
        return cls.NAME_NO_READ.get(name, [])


class CTCPServerManage(object):
    def __init__(self, ip, port):
        self.m_ip = ip
        self.m_port = port
        self.m_tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.m_tcp_server.bind((self.m_ip, self.m_port))
        self.m_conns = []

    def listen_client(self):
        self.m_tcp_server.listen(5)
        print("Server> listen port...")
        while True:
            conn, address = self.m_tcp_server.accept()
            print(f"Server> 已与{address}建立连接")
            client_instance = CClientConn(conn, address)
            CClientManage.set_addr_client(address, client_instance)
            thrd = threading.Thread(target=client_instance.recv_msg)
            thrd.setDaemon(True)
            thrd.start()
            self.m_conns.append(conn)
            time.sleep(0.5)

    @classmethod
    def auto_send_msg(cls):
        while True:
            data = CClientManage.get_message()
            if data:
                address = CClientManage.get_name_addr(data.get("recv_name", ""))
                print(address)
                client_istance = CClientManage.get_addr_client(address)
                if client_istance:
                    client_istance.send_msg(data)
                else:
                    CClientManage.set_message(address, data)
            time.sleep(0.5)


if __name__ == "__main__":
    server_manage = CTCPServerManage("127.0.0.1", 9999)
    # 监听客户端连接
    thred_listen_client = threading.Thread(target=server_manage.listen_client)
    thred_listen_client.setDaemon(True)
    thred_listen_client.start()
    thred_auto_send_msg = threading.Thread(target=server_manage.auto_send_msg)
    thred_auto_send_msg.setDaemon(True)
    thred_auto_send_msg.start()
    while True:
        time.sleep(1)



