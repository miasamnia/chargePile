import os
import time
from socket import *
import json
import sqlite3
import threading
import queue

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

waiting_queue = queue.Queue(maxsize=6)  # 等待区队列
# fast_pile = [True, True]  # 快充桩是否忙
# slow_pile = [False, False, False]  # 慢充是否忙
fast_pile1={}
fast_pile2={}
slow_pile1={}
slow_pile2={}
slow_pile3={}
piles=[fast_pile1,fast_pile2,slow_pile1,slow_pile2,slow_pile3]
fast_waiting=[True,True]#充电区的等候位置
slow_waiting=[True,True]
f=0#等候区快充编号
s=0#等候区慢充编号
time = 5 * 60 + 55
billid=0




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


def register(name, pwd):
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


def login(name, pwd):
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
        # dataSocket.send(json.dumps(tosend).encode())
        datasend(tosend)
        log.writelines('login succeed:{name}\n')
        log.flush()


def chargereq(name,chargemode,chargeamount):
    if(waiting_queue.full()):#队列满了
        datasend(['__SubmitRequestReturn', 0, {'Billid': 1, 'USERID': '1', 'CreateTime':
1684540800, 'chargeMode': 0, 'requestCharge': 1.0, 'Status': 0, 'startTime': -1,
'endTime': -1, 'chargeCost': 0, 'serveCost': 0, 'charged': 0, 'NO': 'F1',
'servingPile': -1, 'otherinfo': ''}])
        return
    else:
        global billid
        global time
        global f
        global s
        no=''
        if chargemode==0:#快充
            f=f+1
            no=f'F{f}'
        else:
            s=s+1
            no=f'S{s}'
        billid=billid+1
        data=['__SubmitRequestReturn', 1, {'Billid': billid, 'USERID': name, 'CreateTime':
time, 'chargeMode': chargemode, 'requestCharge': chargeamount, 'Status': 0, 'startTime': -1,
'endTime': -1, 'chargeCost': 0, 'serveCost': 0, 'charged': 0, 'NO': no,
'servingPile': -1, 'otherinfo': ''}]
        waiting_queue.put(data)
        datasend(data)


def changemode(name):
    global f
    global s
    for waiting in waiting_queue:
        if waiting['USERID']==name:#在等待队列，直接改变
            if waiting['chargeMode']==0:
                f=f-1
                s=s+1
                no = f'S{s}'
                waiting['chargeMode']=1
                waiting['NO']=no
            else:
                f=f+1
                s=s-1
                no = f'F{f}'
                waiting['chargeMode']=0
                waiting['NO']=no
            return
    #没找到，已经在充电区
    global time
    for pile in piles:
        if pile!={} and pile['USERID']==name:
            chargemode = pile['chargeMode']%1
            chargeamount = pile['requestCharge'] - (time - pile['startTime'])/60 * (chargemode % 1 * 23 + 7)
            if (waiting_queue.full()):  # 队列满了
                datasend(['__ChangemodeReturn', 0])
                return
            else:
                global billid
                no = ''
                if chargemode == 0:  # 快充
                    f = f + 1
                    no = f'F{f}'
                else:
                    s = s + 1
                    no = f'S{s}'
                billid = billid + 1
                waiting_queue.put(pile)
                pile={}
            return

def ShowDetailedBill(bill_id):
    conn = sqlite3.connect('data/charge.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM detailed_bill WHERE DetailedBillNum = {bill_id}"
    cursor.execute(query)
    result = cursor.fetchall()
    for row in result:
        tosend=['__ShowDetailedBillReturn', [row]]
    datasend(tosend)
    conn.close()
        
def datasend(data):
    dataSocket.send(json.dumps(data).encode())
    log.writelines(json.dumps(data))
    log.flush()


db = sqlite3.connect('data/charge.db')
cdb = db.cursor()
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


def timer():
    timerr = threading.Timer(5, timer)
    timerr.start()
    global time
    time = time + 5
    print(time)


timer()

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
        act = request[0]
        print(received)
        # name, pwd, act = info.split('|')
        if act == '__register':
            name = request[1]
            pwd = request[2]
            isuser = request[3]
            register(name, pwd)
        elif act == '__login':
            name = request[1]
            pwd = request[2]
            isuser = request[3]
            login(name, pwd)
        elif act == '__SubmitRequest':
            content = request[1]
            name = request[2]
            chargemode=content['chargeMode']
            chargeamount=content['requestCharge']
            print('unfinished')
            chargereq(name,chargemode,chargeamount)
        elif act == '__ShowDetailedBill':
            billid = request[1]
            ShowDetailedBill(billid)
    except Exception as e:
        log.writelines(f'ERROR: {e}\n')
        log.flush()
        continue
