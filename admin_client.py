# coding=utf-8
import sys
import time
from socket import *
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit, QWidget
import json


#IP = '101.42.228.137'
IP = '127.0.0.1'
SERVER_PORT = 56789
BUFLEN = 512


def datasend(data):
    dataSocket = socket(AF_INET, SOCK_STREAM)
    dataSocket.connect((IP, SERVER_PORT))
    dataSocket.send(json.dumps(data).encode())
    return json.loads(dataSocket.recv(BUFLEN).decode())



class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.subwin = None
        uic.loadUi("admin_ui.ui", self)
        self.in_pwd.setEchoMode(QLineEdit.Password)
        self.in_act.setPlaceholderText("不区分大小写")
        self.show_info.setAlignment(Qt.AlignHCenter)
        self.loginButton.clicked.connect(self.login)

    def login(self):
        name = self.in_act.text().lower()
        pwd = self.in_pwd.text()
        if len(name) == 0 or len(pwd) == 0:
            self.show_info.setText('不允许为空')
            self.show_info.setAlignment(Qt.AlignHCenter)
        else:
            request = ['__login', name, pwd, 1]
            received = datasend(request)
            if received[1] == 0:
                self.show_info.setText('login failed!')
                self.show_info.setAlignment(Qt.AlignHCenter)
            else:
                self.show_info.setText("login succeed!")
                self.show_info.setAlignment(Qt.AlignHCenter)
                self.loginButton.setVisible(False)
                mainwin.setVisible(False)
                self.subwin = SubWin(name)
                self.subwin.show()

class SubWin(QMainWindow):
    def __init__(self,name):
        super().__init__()
        uic.loadUi('sub_admin.ui',self)
        self.name=name
        self.pile=self.pileselectioncombo.currentIndex()+1
        self.stoppileButton.clicked.connect(self.stoppile)
        self.showpileButton.clicked.connect(self.showpile)
        self.waitinglistButton.clicked.connect(self.waitinglist)
        self.servingcarButton.clicked.connect(self.servingcar)
        self.pilebillButton.clicked.connect(self.pilebill)
        self.pileamountButton.clicked.connect(self.pileamount)

    def stoppile(self):
        received=datasend(['__Stopuppile', self.pile])
        if received[2]==1:#成功了
            if received[1]==0:#停掉
                self.showinfo.setText('shutdown succeed!')
            else:
                self.showinfo.setText('startup succeed!')
        else:
            self.showinfo.setText('failed!')
    def showpile(self):
        received=datasend(['__Showpile', self.pile])
        self.showinfo.setText(f'pile status:{received[1]}')

    def waitinglist(self):
        received=datasend(['__Getwaitinginfo'])
        self.showinfo.setText(f'waiting area:{received[1]}')
    def servingcar(self):
        received=datasend(['__Showcars', self.pile])
        self.showinfo.setText(f'serving car info:{received[1]}')

    def pilebill(self):
        received=datasend(['__Getreportform', self.pile])
        self.showinfo.setText(f'pile bill:{received[1]}')

    def pileamount(self):
        received=datasend(['__GetPilen'])
        self.showinfo.setText(f'pile amount:{received[1]}')
if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainwin = MainWin()
    mainwin.show()
    sys.exit(app.exec_())
