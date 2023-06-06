import os
import time
from socket import *
import json
from register import reg

IP = '0.0.0.0'
PORT = 56789
BUFLEN = 512


log = open('log/'+time.asctime().replace(':','_')+'.txt', 'w')
#cd = open('cd.txt','w')
room = ''
beHost = True  # True表示他该开房，否则加入

listenSocket = socket(AF_INET, SOCK_STREAM)

listenSocket.bind((IP, PORT))

listenSocket.listen(5)


def check(name, pwd):
    if name in os.listdir('data/users'):
        f = open('data/users/'+name+'/pwd','r')
        p = f.readline()
        f.close()
        if pwd == p:
            return True
    return False

def checkroom(room):#8位字母数字组合
    if room.__len__()==8:
        return room.isalnum()
    else:
        return False;

#def checkCD(name):

while True:
    try:
        dataSocket, addr = listenSocket.accept()
        print('connected:', addr)
        received = dataSocket.recv(BUFLEN)
        info = received.decode()
        log.writelines(info + '  from' + f'{addr}\n')
        log.flush()
        name,pwd,act=json.loads(received)
        print(received)
        #name, pwd, act = info.split('|')
        if(act=='register'):
            if name in os.listdir('data/users'):
                dataSocket.send('account already exist!'.encode())
            else:
                os.mkdir('data/users/' + nick_name)
                f = open('data/users/' + nick_name + '/pwd', 'w')
                f.writelines(pwd)

        elif(act=='login'):
            legal = check(name, pwd)
            if not legal:
                dataSocket.send('password or account wrong!'.encode())
                log.writelines('login failed\n')
                log.flush()
            else:
                print('legal')

    except Exception as e:
        log.writelines(f'ERROR: {e}\n')
        log.flush()
        continue


