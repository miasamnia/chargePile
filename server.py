import os
import time
from socket import *
import json
import sqlite3
import threading

IP = '0.0.0.0'
PORT = 56789
BUFLEN = 512

log = open('log/' + time.asctime().replace(':', '_') + '.txt', 'w')
# cd = open('cd.txt','w')

listenSocket = socket(AF_INET, SOCK_STREAM)
listenSocket.bind((IP, PORT))
listenSocket.listen(5)

# fast_pile = [True, True]  # 快充桩是否忙
# slow_pile = [False, False, False]  # 慢充是否忙
# fast_pile1={}
# fast_pile2={}
# slow_pile1={}
# slow_pile2={}
# slow_pile3={}
fast_pile = [True, True]  # 桩是否空闲
slow_pile = [True, True, True]
piles = [{}, {}, {}, {}, {}]  # 每个桩正在充电的信息
fast_waiting = [True, True]  # 充电区的等候位置是否空闲
slow_waiting = [True, True, True]
pile_waiting = [{}, {}, {}, {}, {}]  # 充电区等候位置的车辆信息
waiting_list = []  # 等候区车辆信息
f = 0  # 等候区快充编号
s = 0  # 等候区慢充编号
time = 5 * 60 + 55
billid = 0

db = sqlite3.connect('data/charge.db')
cdb = db.cursor()
cdb.execute('''
CREATE TABLE IF NOT EXISTS detailed_bill(
DetailedBillNum int,
USER_ID vchar(20),
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
PRIMARY KEY(DetailedBillNum,USER_ID)
)''')


# 检查用户密码是否正确
def check_user(name, pwd):
    if name in os.listdir('data/users'):
        f = open('data/users/' + name + '/pwd', 'r')
        p = f.readline()
        f.close()
        if pwd == p:
            return True
    return False


# 检查管理员
def check_admin(name, pwd):
    if name in os.listdir('data/admins'):
        f = open('data/admins/' + name + '/pwd', 'r')
        p = f.readline()
        f.close()
        if pwd == p:
            return True
    return False


# 注册
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


# 登录
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


# 充电请求处理
# 如果等待区满，返回错误，否则加入等待区
def chargereq(name, chargemode, chargeamount):
    global waiting_list
    if (len(waiting_list) == 6):  # 队列满了
        datasend(['__SubmitRequestReturn', 0, {'Billid': 1, 'USERID': '1', 'CreateTime':
            1684540800, 'chargeMode': 0, 'requestCharge': 1.0, 'Status': 0, 'startTime': -1,
                                               'endTime': -1, 'chargeCost': 0, 'serveCost': 0, 'charged': 0, 'NO': 'F1',
                                               'servingPile': -1, 'otherinfo': ''}])
        return
    global billid
    global time
    global f
    global s
    if chargemode == 0:
        no = ''
        f = f + 1
        no = f'F{f}'
        billid = billid + 1
        data = ['__SubmitRequestReturn', 1, {'Billid': billid, 'USERID': name, 'CreateTime':
            time, 'chargeMode': chargemode, 'requestCharge': chargeamount, 'Status': 0, 'startTime': -1,
                                             'endTime': -1, 'chargeCost': 0, 'serveCost': 0, 'charged': 0, 'NO': no,
                                             'servingPile': -1, 'otherinfo': ''}]
        waiting_list.append(data[2])
        datasend(data)
    else:
        no = ''
        s = s + 1
        no = f'F{s}'
        billid = billid + 1
        data = ['__SubmitRequestReturn', 1, {'Billid': billid, 'USERID': name, 'CreateTime':
            time, 'chargeMode': chargemode, 'requestCharge': chargeamount, 'Status': 0, 'startTime': -1,
                                             'endTime': -1, 'chargeCost': 0, 'serveCost': 0, 'charged': 0, 'NO': no,
                                             'servingPile': -1, 'otherinfo': ''}]
        waiting_list.append(data[2])
        datasend(data)


# 未测试
# 电冲完/用户在充电区改变充电模式或电量，调用此函数将其清除，并将目前的结果存入数据库
def rm_from_pile(name):  # 从充电区移除，成功返回True，没找到返回False
    global piles
    global time
    global pile_waiting
    for i in range(5):
        if piles[i]!={}and name == piles[i]['USERID']:
            global cdb
            #
            # 这里是计算花了多少钱
            #
            piles[i]['chargeCost'] = 0
            piles[i]['serverCost'] = 0
            piles[i]['servingPile'] = -1
            piles[i]['endTime'] = time
            data=list(piles[i].values())
            data.insert(4,i)
            data[11]=data[9]+data[10]
            del data[-1]
            del data[-2]
            del data[-2]
            del data[6]

            cdb.execute('INSERT INTO detailed_bill (DetailedBillNum,USER_ID,createTime,mode,pile,charge,startTime,'
                        'endTime,chargeCost,serveCost,allCost,other) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                        data)
            piles[i]={}
            if i <=1:
                fast_pile[i]=True
            else:
                slow_pile[i-2]=True
            return
        if name == pile_waiting[i]['USERID']:
            pile_waiting = {}
            if i <= 1:
                fast_waiting[i] = True
            else:
                slow_waiting[i - 2] = True
            return
        i+=1

# 未测试
# 改变充电模式
# 如果在等候区，直接修改。
# 如果在充电区，停止充电插入等待区。如果等待区满，不停止充电直接返回改变失败
def changemode(name):
    global f
    global s
    global waiting_list
    global billid
    global tim
    for car in piles:
        if car!={}and car['USERID']==name:#正在充电
            if len(waiting_list)<6:
                rm_from_pile(name)
                if car['chargeMode']==1:#要改为快
                    f = f + 1
                    no = f'F{f}'
                    billid = billid + 1
                    car['Billid']=billid
                    car['CreateTime']=time
                    car['chargeMode']=0
                    car['NO']=no
                    waiting_list.append(car)
                else:
                    s = s + 1
                    no = f'S{s}'
                    billid = billid + 1
                    car['Billid'] = billid
                    car['CreateTime'] = time
                    car['chargeMode'] = 1
                    car['NO'] = no
                    waiting_list.append(car)
                datasend(['__ChangemodeReturn', 1])
            else:
                datasend(['__ChangemodeReturn', 0])
            return
    for car in pile_waiting:
        if car!={}and car['USERID']==name:#正在充电
            if len(waiting_list)<6:
                rm_from_pile(name)
                if car['chargeMode'] == 1:  # 要改为快
                    f = f + 1
                    no = f'F{f}'
                    billid = billid + 1
                    car['Billid'] = billid
                    car['CreateTime'] = time
                    car['chargeMode'] = 0
                    car['NO'] = no
                    waiting_list.append(car)
                else:
                    s = s + 1
                    no = f'S{s}'
                    billid = billid + 1
                    car['Billid'] = billid
                    car['CreateTime'] = time
                    car['chargeMode'] = 1
                    car['NO'] = no
                    waiting_list.append(car)
                datasend(['__ChangemodeReturn', 1])
            else:
                datasend(['__ChangemodeReturn', 0])
            return
    for waiting in waiting_list:
        if waiting!={}and waiting['USERID'] == name:  # 在等待队列，直接改变
            if waiting['chargeMode'] == 0:
                f = f - 1
                s = s + 1
                no = f'S{s}'
                waiting['chargeMode'] = 1
            else:
                f = f + 1
                s = s - 1
                no = f'F{f}'
                waiting['chargeMode'] = 0
            waiting['NO'] = no
            datasend(['__ChangemodeReturn', 1])
            return

# 未测试
# 改变充电电量
# 如果在等候区，直接修改。
# 如果在充电区，停止充电插入等待区。如果等待区满，不停止充电直接返回改变失败
def chargechange(name,chargeamount):
    global f
    global s
    global waiting_list
    global billid
    global time
    for car in piles:
        if car!={}and car['USERID']==name:#正在充电
            car['requestCharge']=chargeamount
            if len(waiting_list)<6:
                rm_from_pile(name)
                if car['chargeMode']==0:
                    f = f + 1
                    no = f'F{f}'
                    billid = billid + 1
                    car['Billid']=billid
                    car['CreateTime']=time
                    car['chargeMode']=0
                    car['NO']=no
                    waiting_list.append(car)
                else:
                    s = s + 1
                    no = f'S{s}'
                    billid = billid + 1
                    car['Billid'] = billid
                    car['CreateTime'] = time
                    car['chargeMode'] = 1
                    car['NO'] = no
                    waiting_list.append(car)
                datasend(['__ChangerequestReturn', 1])
            else:
                datasend(['__ChangerequestReturn', 0])
            return
    for car in pile_waiting:
        if car!={}and car['USERID']==name:#正在充电
            car['requestCharge'] = chargeamount
            if len(waiting_list) < 6:
                rm_from_pile(name)
                if car['chargeMode'] == 0:
                    f = f + 1
                    no = f'F{f}'
                    billid = billid + 1
                    car['Billid'] = billid
                    car['CreateTime'] = time
                    car['chargeMode'] = 0
                    car['NO'] = no
                    waiting_list.append(car)
                else:
                    s = s + 1
                    no = f'S{s}'
                    billid = billid + 1
                    car['Billid'] = billid
                    car['CreateTime'] = time
                    car['chargeMode'] = 1
                    car['NO'] = no
                    waiting_list.append(car)
                datasend(['__ChangerequestReturn', 1])
            else:
                datasend(['__ChangerequestReturn', 0])
            return
    for waiting in waiting_list:
        if waiting['USERID'] == name:  # 在等待队列，直接改变
            waiting['requesCharge']=chargeamount
            datasend(['__ChangerequestReturn', 1])
            return
    datasend(['__ChangerequestReturn',0])

# 未测试
# 根据用户id查其名下所有充电信息，前端需要根据这些信息生成详单
def showdetailedbill(user_id):
    conn = sqlite3.connect('data/charge.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM detailed_bill WHERE USER_ID = {user_id}"
    cursor.execute(query)
    result = cursor.fetchall()
    output = []
    for row in result:
        output.append(['__ShowDetailedBillReturn', [row]])
    datasend(output)
    conn.close()

# 未测试
# 查充电桩数量（列表元素数量）
def getpilennum():
    pilenum = len(fast_pile) + len(slow_pile)
    datasend(['__GetPilenReturn', pilenum])

# 所有发送信息调用这个函数，data就是要发送的列表和文档里格式一样，不做别的处理
def datasend(data):
    dataSocket.send(json.dumps(data).encode())
    log.writelines(json.dumps(data))
    log.flush()


# 未完成：
# 每隔一秒检查各个队列，充电是否完成、充电区空闲就看看后面有没有车要挪进来等等
def timer():
    global fast_pile1
    global fast_pile2
    global slow_pile1
    global slow_pile2
    global slow_pile3
    global fast_pile
    global slow_pile
    global piles
    global fast_waiting
    global slow_waiting
    global pile_waiting
    global waiting_num
    timerr = threading.Timer(1, timer)
    timerr.start()
    global time
    i = 0
    for pile in fast_pile:
        if pile:  # 桩空闲
            if not fast_waiting[i]:  # 有正在等的
                fast_pile[i] = False
                piles[i] = pile_waiting[i]
                piles[i]['startTime'] = time
                piles[i]['servingPile']= i
                pile_waiting[i] = {}
                fast_waiting[i] = True
        i = i + 1
    for pile in slow_pile:
        if pile:  # 桩空闲
            if not slow_waiting[i - 2]:  # 有正在等的
                slow_pile[i - 2] = False
                piles[i] = pile_waiting[i]
                piles[i]['startTime'] = time
                piles[i]['servingPile'] = i
                pile_waiting[i] = {}
                slow_waiting[i - 2] = True

        i+=1

    i=0
    for pile in fast_waiting:
        if pile:  # 充电区等候空闲
            for car in waiting_list:
                if car['chargeMode']==0:
                    fast_waiting[i]=False
                    pile_waiting[i]=car
                    waiting_list.remove(car)
                    break
        i = i + 1
    for pile in slow_waiting:
        if pile:  # 充电区等候空闲
            for car in waiting_list:
                if car['chargeMode'] == 1:
                    slow_waiting[i-2] = False
                    pile_waiting[i] = car
                    waiting_list.remove(car)
                    break
        i += 1
timer()


# 时钟，每隔十秒time加5（分钟）
def timer_clock():
    timerc = threading.Timer(10, timer_clock)
    timerc.start()
    global time
    time = time + 5


timer_clock()

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
            print(f'{name} register')
            register(name, pwd)
        elif act == '__login':
            name = request[1]
            pwd = request[2]
            isuser = request[3]
            print(f'{name} login')
            login(name, pwd)
        elif act == '__SubmitRequest':
            content = request[1]
            name = request[2]
            chargemode = content['chargeMode']
            chargeamount = content['requestCharge']
            print(f'{name} request')
            chargereq(name, chargemode, chargeamount)
        elif act=='__Changemode':
            name=request[1]
            print(f'{name} change mode')
            changemode(name)
        elif act == '__ShowDetailedBill':
            user_id = request[1]
            showdetailedbill(user_id)
        elif act == '__GetPilen':
            getpilennum()
    except Exception as e:
        log.writelines(f'ERROR: {e}\n')
        log.flush()
        print(e)
        continue
