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

pile_info = []#充电桩号从1开始
for pile in os.listdir('data/piles'):
    info = open('data/piles/' + pile, 'r+')
    data = info.read().strip('(').strip(')').split(',')
    i = 0
    for thing in data:
        if i < 5:
            data[i] = int(thing)
        else:
            data[i] = float(thing)
        i += 1
    pile_info.append(data)

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
bill = open('data/bill_id', 'r+')
billid = int(bill.read()) + 1
bill.seek(0)
bill.write(str(billid))

db = sqlite3.connect('data/charge.db')
cdb = db.cursor()


# cdb.execute('''
# CREATE TABLE IF NOT EXISTS detailed_bill(
# DetailedBillNum int,
# USER_ID vchar(20),
# mode int,
# createTime int,
# pile int,
# charge float,
# startTime int,
# endTime int,
# chargeCost float,
# serveCost float,
# allCost float,
# other vchar(40),
# PRIMARY KEY(DetailedBillNum,USER_ID)
# )''')


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
        bill.seek(0)
        bill.write(str(billid))
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
        bill.seek(0)
        bill.write(str(billid))
        data = ['__SubmitRequestReturn', 1, {'Billid': billid, 'USERID': name, 'CreateTime':
            time, 'chargeMode': chargemode, 'requestCharge': chargeamount, 'Status': 0, 'startTime': -1,
                                             'endTime': -1, 'chargeCost': 0, 'serveCost': 0, 'charged': 0, 'NO': no,
                                             'servingPile': -1, 'otherinfo': ''}]
        waiting_list.append(data[2])
        datasend(data)


def calculate_charging_cost(start_minutes, end_minutes, power_mode):
    # # 时间转换为分钟
    # start_hour, start_minute = map(int, start_time.split(':'))
    # end_hour, end_minute = map(int, end_time.split(':'))
    # start_minutes = start_hour * 60 + start_minute
    # end_minutes = end_hour * 60 + end_minute
    if end_minutes < start_minutes:
        total_cost = calculate_charging_cost(start_minutes, 1440, power_mode) + calculate_charging_cost(0, end_minutes,
                                                                                                        power_mode)
        return total_cost
    else:
        # 计算总时间（分钟）
        total_minutes = end_minutes - start_minutes

        # 根据充电功率模式确定充电功率
        if power_mode == 'F':
            charging_power = 30
        elif power_mode == 'T':
            charging_power = 7
        else:
            return "Invalid charging power mode."

        # 定义峰时、平时、谷时时间段（分钟）
        peak1_start = 10 * 60
        peak1_end = 15 * 60
        peak2_start = 18 * 60
        peak2_end = 21 * 60
        off_peak1_start = 7 * 60
        off_peak1_end = 10 * 60
        off_peak2_start = 15 * 60
        off_peak2_end = 18 * 60
        off_peak3_start = 21 * 60
        off_peak3_end = 23 * 60
        valley1_start = 23 * 60
        valley1_end = 24 * 60
        valley2_start = 0 * 60
        valley2_end = 7 * 60

        # # 峰时、平时、谷时的时间（分钟）
        # peak1_time = 0
        # peak2_time = 0
        # off_peak1_time = 0
        # off_peak2_time = 0
        # off_peak3_time = 0
        # valley1_time = 0
        # valley2_time = 0
        #
        # # 峰时、平时、谷时总时间（小时
        # peak_hours = 0
        # off_peak_hours = 0
        # valley_hours = 0

        # 计算峰时、平时、谷时的时间（分钟）
        peak1_time = max(0, min(end_minutes, peak1_end) - max(start_minutes, peak1_start))
        peak2_time = max(0, min(end_minutes, peak2_end) - max(start_minutes, peak2_start))
        off_peak1_time = max(0, min(end_minutes, off_peak1_end) - max(start_minutes, off_peak1_start))
        off_peak2_time = max(0, min(end_minutes, off_peak2_end) - max(start_minutes, off_peak2_start))
        off_peak3_time = max(0, min(end_minutes, off_peak3_end) - max(start_minutes, off_peak3_start))
        valley1_time = max(0, min(end_minutes, valley1_end) - max(start_minutes, valley1_start))
        valley2_time = max(0, min(end_minutes, valley2_end) - max(start_minutes, valley2_start))

        # 转换为小时
        peak_hours = (peak1_time + peak2_time) / 60
        off_peak_hours = (off_peak1_time + off_peak2_time + off_peak3_time) / 60
        valley_hours = (valley1_time + valley2_time) / 60

        # 计算充电度数
        charging_kWh = charging_power * total_minutes / 60

        # 计算充电费用
        peak_price = 1.0  # 峰时电价（元/度）
        off_peak_price = 0.7  # 平时电价（元/度）
        valley_price = 0.4  # 谷时电价（元/度）
        serv_price = 0.8  # 服务费单价（元/度）

        charging_cost = peak_hours * peak_price * charging_power + off_peak_hours * off_peak_price * charging_power + valley_hours * valley_price * charging_power

        # 计算服务费用
        service_cost = serv_price * charging_kWh

        # 计算总费用
        total_cost = charging_cost + service_cost

        # print(peak_hours, off_peak_hours, valley_hours, charging_kWh, charging_cost, service_cost)
        return charging_cost, service_cost, total_cost


# 未测试
# 电冲完/用户在充电区改变充电模式或电量，调用此函数将其清除，并将目前的结果存入数据库
def rm_from_pile(name):  # 从充电区移除，成功返回True，没找到返回False
    global piles
    global time
    global pile_waiting
    for i in range(5):
        if piles[i] != {} and name == piles[i]['USERID']:
            global cdb
            if piles[i]['chargeMode'] == 0:
                mode = 'F'
            else:
                mode = 'S'
            piles[i]['chargeCost'], piles[i]['serverCost'], total = calculate_charging_cost(piles[i]['startTime'], time,
                                                                                            mode)
            piles[i]['servingPile'] = -1
            piles[i]['endTime'] = time
            data = list(piles[i].values())
            data.insert(4, i)
            data[11] = data[9] + data[10]
            del data[-1]
            del data[-2]
            del data[-2]
            del data[6]

            cdb.execute('INSERT INTO detailed_bill (DetailedBillNum,USER_ID,createTime,mode,pile,charge,startTime,'
                        'endTime,chargeCost,serveCost,allCost,other) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                        data)
            db.commit()
            pile_info[i][1] += 1
            pile_info[i][2] += piles[i]['startTime']
            pile
            piles[i] = {}
            if i <= 1:
                fast_pile[i] = True
            else:
                slow_pile[i - 2] = True
            return
        if pile_waiting[i] != {} and name == pile_waiting[i]['USERID']:
            pile_waiting[i] = {}
            if i <= 1:
                fast_waiting[i] = True
            else:
                slow_waiting[i - 2] = True
            return
        i += 1


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
        if car != {} and car['USERID'] == name:  # 正在充电
            if len(waiting_list) < 6:
                rm_from_pile(name)
                if car['chargeMode'] == 1:  # 要改为快
                    f = f + 1
                    no = f'F{f}'
                    billid = billid + 1
                    bill.seek(0)
                    bill.write(str(billid))
                    car['Billid'] = billid
                    car['CreateTime'] = time
                    car['chargeMode'] = 0
                    car['NO'] = no
                    waiting_list.append(car)
                else:
                    s = s + 1
                    no = f'S{s}'
                    billid = billid + 1
                    bill.seek(0)
                    bill.write(str(billid))
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
        if car != {} and car['USERID'] == name:  # 正在充电
            if len(waiting_list) < 6:
                rm_from_pile(name)
                if car['chargeMode'] == 1:  # 要改为快
                    f = f + 1
                    no = f'F{f}'
                    billid = billid + 1
                    bill.seek(0)
                    bill.write(str(billid))
                    car['Billid'] = billid
                    car['CreateTime'] = time
                    car['chargeMode'] = 0
                    car['NO'] = no
                    waiting_list.append(car)
                else:
                    s = s + 1
                    no = f'S{s}'
                    billid = billid + 1
                    bill.seek(0)
                    bill.write(str(billid))
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
        if waiting != {} and waiting['USERID'] == name:  # 在等待队列，直接改变
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
def chargechange(name, chargeamount):
    global f
    global s
    global waiting_list
    global billid
    global time
    for car in piles:
        if car != {} and car['USERID'] == name:  # 正在充电
            car['requestCharge'] = chargeamount
            if len(waiting_list) < 6:
                rm_from_pile(name)
                if car['chargeMode'] == 0:
                    f = f + 1
                    no = f'F{f}'
                    billid = billid + 1
                    bill.seek(0)
                    bill.write(str(billid))
                    car['Billid'] = billid
                    car['CreateTime'] = time
                    car['chargeMode'] = 0
                    car['NO'] = no
                    waiting_list.append(car)
                else:
                    s = s + 1
                    no = f'S{s}'
                    billid = billid + 1
                    bill.seek(0)
                    bill.write(str(billid))
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
        if car != {} and car['USERID'] == name:  # 正在充电
            car['requestCharge'] = chargeamount
            if len(waiting_list) < 6:
                rm_from_pile(name)
                if car['chargeMode'] == 0:
                    f = f + 1
                    no = f'F{f}'
                    billid = billid + 1
                    bill.seek(0)
                    bill.write(str(billid))
                    car['Billid'] = billid
                    car['CreateTime'] = time
                    car['chargeMode'] = 0
                    car['NO'] = no
                    waiting_list.append(car)
                else:
                    s = s + 1
                    no = f'S{s}'
                    billid = billid + 1
                    bill.seek(0)
                    bill.write(str(billid))
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
            waiting['requesCharge'] = chargeamount
            datasend(['__ChangerequestReturn', 1])
            return
    datasend(['__ChangerequestReturn', 0])


def showdetailedbill(user_id):
    conn = sqlite3.connect('data/charge.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM detailed_bill WHERE USER_ID = {user_id}"
    cursor.execute(query)
    conn.commit()
    result = cursor.fetchall()
    output = []
    for row in result:
        output.append([row])
    datasend(['__ShowDetailedBillReturn', output])
    conn.close()


def showcharginginfo(name):
    for car in waiting_list:
        if car != {} and car['USERID'] == name:
            datasend(['__SubmitRequestReturn', 1, car])
            return
    for car in pile_waiting:
        if car != {} and car['USERID'] == name:
            datasend(['__SubmitRequestReturn', 1, car])
            return
    for car in piles:
        if car != {} and car['USERID'] == name:
            datasend(['__SubmitRequestReturn', 1, car])
            return
    datasend(['__SubmitRequestReturn', 0, []])


def stopcharging(name):
    i = 0
    for car in waiting_list:
        if car != {} and car['USERID'] == name:
            waiting_list[i] = {}
            datasend(['__StopChargeReturn', 1])
            return
        i += 1
    i = 0
    for car in pile_waiting:
        if car != {} and car['USERID'] == name:
            rm_from_pile(name)
            datasend(['__StopChargeReturn', 1])
            return
        i += 1
    i = 0
    for car in piles:
        if car != {} and car['USERID'] == name:
            rm_from_pile(name)
            datasend(['__StopChargeReturn', 1])
            return
        i += 1
    datasend(['__SubmitRequestReturn', 0, []])

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
                piles[i]['servingPile'] = i
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

        i += 1

    i = 0
    for pile in fast_waiting:
        if pile:  # 充电区等候空闲
            for car in waiting_list:
                if car != {} and car['chargeMode'] == 0:
                    fast_waiting[i] = False
                    pile_waiting[i] = car
                    waiting_list[i] = {}
                    break
        i = i + 1
    for pile in slow_waiting:
        if pile:  # 充电区等候空闲
            for car in waiting_list:
                if car != {} and car['chargeMode'] == 1:
                    slow_waiting[i - 2] = False
                    pile_waiting[i] = car
                    waiting_list[i] = {}
                    break
        i += 1


timer()


# 时钟，每隔十秒time加5（分钟）
def timer_clock():
    timerc = threading.Timer(10, timer_clock)
    timerc.start()
    global time
    global pile_waiting
    time = time + 5
    print(f'time:{time}')
    print(f'pile:{piles}')
    # 下面改变所有桩的剩余电量
    for car in piles:
        if car != {}:
            car['charged'] += (((car['chargeMode'] + 1) % 2) * 23 + 7) / 6
            if car['charged'] >= car['requestCharge']:
                for i in range(5):
                    if piles[i] != {} and car['USERID'] == piles[i]['USERID']:
                        conn = sqlite3.connect('data/charge.db')
                        cursor = conn.cursor()
                        if piles[i]['chargeMode'] == 0:
                            mode = 'F'
                        else:
                            mode = 'S'
                        piles[i]['chargeCost'], piles[i]['serverCost'], total = calculate_charging_cost(
                            piles[i]['startTime'], time, mode)
                        piles[i]['servingPile'] = -1
                        piles[i]['endTime'] = time
                        data = list(piles[i].values())
                        data.insert(4, i)
                        data[11] = data[9] + data[10]
                        del data[-1]
                        del data[-2]
                        del data[-2]
                        del data[6]

                        cursor.execute(
                            'INSERT INTO detailed_bill (DetailedBillNum,USER_ID,createTime,mode,pile,charge,startTime,'
                            'endTime,chargeCost,serveCost,allCost,other) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                            data)
                        conn.commit()
                        conn.close()
                        piles[i] = {}
                        if i <= 1:
                            fast_pile[i] = True
                        else:
                            slow_pile[i - 2] = True
                        return
                    if pile_waiting[i] != {} and name == pile_waiting[i]['USERID']:
                        pile_waiting[i] = {}
                        if i <= 1:
                            fast_waiting[i] = True
                        else:
                            slow_waiting[i - 2] = True
                        return
                    i += 1


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
        elif act == '__Changemode':
            name = request[1]
            print(f'{name} change mode')
            changemode(name)

        elif act == '__Changerequest':
            name = request[1]
            chargeamount = request[2]
            print(f'{name} change amount')
            chargechange(name, chargeamount)
        elif act == '__ShowDetailedBill':
            user_id = request[1]
            showdetailedbill(user_id)
        elif act == '__GetRIinfo':
            name = request[1]
            showcharginginfo(name)
        elif act == '__GetPilen':
            getpilennum()
        elif act == '__StopCharge':
            name = request[1]
            stopcharging(name)
    except Exception as e:
        log.writelines(f'ERROR: {e}\n')
        log.flush()
        print(e)
        continue
