import os
import time
from socket import *
import json
import sqlite3

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
        return False


def register(name,pwd):
    if name in os.listdir('data/users'):
        log.writelines('account already exist:{name}\n')
        log.flush()
    else:
        os.mkdir('data/users/' + name)
        f = open('data/users/' + name + '/pwd', 'w')
        f.writelines(pwd)
        log.writelines('register succeed:{name}\n')
        log.flush()
        dataSocket.send('register succeed!'.encode())

def login(name,pwd):
    if (isuser == 0):  # 用户
        legal = check_user(name, pwd)
    else:
        legal = check_admin(name, pwd)
    if not legal:
        dataSocket.send('password or account wrong!'.encode())
        log.writelines('login failed\n')
        log.flush()
    else:
        tosend = ['__LoginReturn', 1, 0]
        #dataSocket.send(json.dumps(tosend).encode())
        datasend(tosend)
        log.writelines('login succeed:{name}\n')
        log.flush()

def chargereq(name):
    datasend(['__SubmitRequestReturn', 1, {'Billid': 1, 'USERID': '1', 'CreateTime':
1684540800, 'chargeMode': 0, 'requestCharge': 1.0, 'Status': 0, 'startTime': -1,
'endTime': -1, 'chargeCost': 0, 'serveCost': 0, 'charged': 0, 'NO': 'F1',
'servingPile': -1, 'otherinfo': ''}])
def datasend(data):
    dataSocket.send(json.dumps(data).encode())
    log.writelines(json.dumps(data))
    log.flush()

db=sqlite3.connect('data/charge.db')
cdb=db.cursor()
cdb.execute('''
CREATE TABLE IF NOT EXISTS detailed_bill(
DetailedBillNum int,
USER_ID vchar(20),
seq int,
mode int,
createTime int,
pile int,
charge float,
startTime int,
endTime int,
chargeCost float,
serveCost float,
allCost float,
other vchar(40),
PRIMARY KEY(DetailedBillNum,USER_ID,seq)
)''')

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
        isuser=request[3]
        print(received)
        # name, pwd, act = info.split('|')
        if act == '__register':
            register(name,pwd)
        elif act == '__login':
            login(name,pwd)
        elif act=='__SubmitRequest':
            print('unfinished')
        elif act=='__SubmitRequest':
            chargereq(name)
    except Exception as e:
        log.writelines(f'ERROR: {e}\n')
        log.flush()
        continue
