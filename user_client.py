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
CDTIME = 60  # 匹配成功一次的cd


def datasend(data):
    dataSocket = socket(AF_INET, SOCK_STREAM)
    dataSocket.connect((IP, SERVER_PORT))
    dataSocket.send(json.dumps(data).encode())
    return dataSocket.recv(BUFLEN).decode()


class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.subwin = None
        uic.loadUi("ui.ui", self)
        self.in_pwd.setEchoMode(QLineEdit.Password)
        self.in_act.setPlaceholderText("不区分大小写")
        self.show_info.setAlignment(Qt.AlignHCenter)
        self.loginButton.clicked.connect(self.login)
        self.registerButton.clicked.connect(self.register)


    def register(self):
        name = self.in_act.text().lower()
        pwd = self.in_pwd.text()
        if len(name) == 0 or len(pwd) == 0:
            self.show_info.setText('不允许为空')
            self.show_info.setAlignment(Qt.AlignHCenter)
        else:
            request = ['__register', name, pwd, 0]
            data = json.dumps(request)
            received = datasend(data)
            rec = json.loads(received)
            if rec['status'] == 'account already exist!':
                self.show_info.setText(received)
                self.show_info.setAlignment(Qt.AlignHCenter)
            else:
                self.show_info.setText("register succeed!\nyou may login now")

    def login(self):
        name = self.in_act.text().lower()
        pwd = self.in_pwd.text()
        if len(name) == 0 or len(pwd) == 0:
            self.show_info.setText('不允许为空')
            self.show_info.setAlignment(Qt.AlignHCenter)
        else:
            request = ['__login', name, pwd, 0]
            received = datasend(request)
            rec = json.loads(received)
            if rec[1] == 0:
                self.show_info.setText(received)
                self.show_info.setAlignment(Qt.AlignHCenter)
            else:
                self.show_info.setText("login succeed!")
                self.loginButton.setVisible(False)
                self.registerButton.setVisible(False)
                mainwin.setVisible(False)
                self.subwin = SubWin(name)
                self.subwin.show()

class SubWin(QMainWindow):
    def __init__(self,name):
        super().__init__()
        uic.loadUi('subwindow.ui',self)
        # self.chargemodeButton.setVisible(False)
        # self.chargechangeButton.setVisible(False)
        # self.stopchargingButton.setVisible(False)
        self.name=name
        self.req=0
        self.chargeamountline.setVisible(False)
        self.chargeamounttext.setVisible(False)
        self.modeselectiontext.setVisible(False)
        self.modeselectioncombo.setVisible(False)
        self.confirmButton.setVisible(False)
        self.backButton.setVisible(False)
        # self.chargingButton.setVisible(False)
        self.chargereqButton.clicked.connect(self.chargereq)
        self.detailbillButton.clicked.connect(self.detailedbill)
        self.chargemodeButton.clicked.connect(self.chargemode)
        self.chargingButton.clicked.connect(self.charging)
        self.chargechangeButton.clicked.connect(self.chargechange)
        self.stopchargingButton.clicked.connect(self.stopcharging)
        self.confirmButton.clicked.connect(self.chargereq_confirm)
        self.backButton.clicked.connect(self.back)

    def chargereq(self):
        self.req=1
        self.chargereqButton.setVisible(False)
        self.chargeamountline.setVisible(True)
        self.chargeamounttext.setVisible(True)
        self.confirmButton.setVisible(True)
        self.backButton.setVisible(True)
        self.modeselectiontext.setVisible(True)
        self.modeselectioncombo.setVisible(True)

    def chargereq_confirm(self):
        if self.req==1:#充电请求
            chargeamount=float(self.chargeamountline.text())
            chargemode=int(self.modeselectioncombo.currentIndex())
            data=['__SubmitRequest',{'chargeMode':chargemode,'requestCharge':chargeamount,'creatTime':time.time()},self.name]
            received=datasend(data)
            if received[1]==0:
                self.showinfo.setText('request failed!')
            else:
                billid=received[3]['BillId']
                pos=received[3]['NO']
                pile=received[3]['servingPile']
                self.showinfo.setText(f'BillId:{billid}\n排队号:{pos}\n充电桩编号:{pile}')
        elif self.req==2:#改变模式
            data = ['__Changemode', self.name]
            received = datasend(data)
            if received != 1:
                self.showinfo.setText('failed!')
            else:
                self.showinfo.setText('succeed!')
        elif self.req==3:#改变电量
            chargeamount = float(self.chargeamountline.text())
            data = ['__Changerequest', self.name, chargeamount]
            received = datasend(data)
            if received != 1:
                self.showinfo.setText('failed!')
            else:
                self.showinfo.setText('succeed!')

        self.chargeamountline.setVisible(False)
        self.chargeamounttext.setVisible(False)
        self.modeselectiontext.setVisible(False)
        self.modeselectioncombo.setVisible(False)
        self.confirmButton.setVisible(False)
        self.backButton.setVisible(False)
    def back(self):
        self.req=0
        self.chargeamountline.setVisible(False)
        self.chargeamounttext.setVisible(False)
        self.modeselectiontext.setVisible(False)
        self.modeselectioncombo.setVisible(False)
        self.confirmButton.setVisible(False)
        self.backButton.setVisible(False)
        self.chargereqButton.setVisible(True)
        self.chargemodeButton.setVisible(True)
        self.chargechangeButton.setVisible(True)
    def detailedbill(self):
        data=['__ShowDetailedBill',self.name]
        received=datasend(data)
        self.showinfo.setText('detailed bill stored in Dbill.csv')
        with open('Dbill.csv','w')as f:
            f.write(received)

    def chargemode(self):
        self.req=2
        self.confirmButton.setVisible(True)
        self.modeselectiontext.setVisible(True)
        self.modeselectioncombo.setVisible(True)
        self.backButton.setVisible(True)
    def stopcharging(self):
        data=['__StopCharge', self.name]
        received=datasend(data)
        if received!=1:
            self.showinfo.setText('failed!')
        else:
            self.showinfo.setText('succeed!')

    def chargechange(self):
        self.req=3
        self.chargeamountline.setVisible(True)
        self.chargeamounttext.setVisible(True)
        self.confirmButton.setVisible(True)
        self.backButton.setVisible(True)

    def charging(self):
        data=['__GetRIinfo', self.name]
        received=datasend(data)
        self.showinfo.setText('detailed bill stored in Dbill.csv')
        with open('Dbill.csv','w')as f:
            f.write(received)

    #def chargemode(self):


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainwin = MainWin()
    mainwin.show()
    sys.exit(app.exec_())
