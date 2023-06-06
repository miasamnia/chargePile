import os
import time
from socket import *
import json

IP = '0.0.0.0'
PORT = 56789
BUFLEN = 512

log = open('log/' + time.asctime().replace(':', '_') + '.txt', 'w')
# cd = open('cd.txt','w')
room = ''
beHost = True  # True表示他该开房，否则加入

listenSocket = socket(AF_INET, SOCK_STREAM)
listenSocket.bind((IP, PORT))
listenSocket.listen(5)


def check_user(name, pwd):
    if name in os.listdir('data/users'):
        f = open('data/users/' + name + '/pwd', 'r')
        p = f.readline()
        f.close()
        if pwd == p:
            return True
    return False


def check_admin(name, pwd):
    if name in os.listdir('data/admins'):
        f = open('data/admins/' + name + '/pwd', 'r')
        p = f.readline()
        f.close()
        if pwd == p:
            return True
    return False


def checkroom(room):  # 8位字母数字组合
    if room.__len__() == 8:
        return room.isalnum()
    else:
        return False;


# def checkCD(name):

while True:
    try:
        dataSocket, addr = listenSocket.accept()
        print('connected:', addr)
        received = dataSocket.recv(BUFLEN)
        info = received.decode()
        log.writelines(info + '  from' + f'{addr}\n')
        log.flush()
        request = json.loads(info)
        # name = request['username']
        # pwd = request['password']
        # act = request['request']
        act=request[0]
        name=request[1]
        pwd=request[2]
        print(received)
        # name, pwd, act = info.split('|')
        if act == 'register':
            if name in os.listdir('data/users'):
                dataSocket.send('account already exist!'.encode())
                log.writelines('account already exist:{name}\n')
                log.flush()
            else:
                os.mkdir('data/users/' + name)
                f = open('data/users/' + name + '/pwd', 'w')
                f.writelines(pwd)
                log.writelines('register succeed:{name}\n')
                log.flush()
                dataSocket.send('register succeed!'.encode())
        elif act == 'login':
            legal = check_user(name, pwd)
            if not legal:
                dataSocket.send('password or account wrong!'.encode())
                log.writelines('login failed\n')
                log.flush()
            else:
                dataSocket.send('login succeed!'.encode())
                log.writelines('login succeed:{name}\n')
                log.flush()
        elif act == 'admin':
            legal = check_admin()

    except Exception as e:
        log.writelines(f'ERROR: {e}\n')
        log.flush()
        continue
