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
CDTIME = 60  # ƥ��ɹ�һ�ε�cd


def datasend(data):
    dataSocket = socket(AF_INET, SOCK_STREAM)
    dataSocket.connect((IP, SERVER_PORT))
    print(json.dumps(['__SubmitRequest', {'chargeMode': 0, 'requestCharge': 11.0, 'creatTime': 1686205442.2987475}, '1']))
    dataSocket.send(json.dumps(data).encode())
    return json.loads(dataSocket.recv(BUFLEN).decode())



class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.subwin = None
        uic.loadUi("admin_ui.ui", self)
        self.in_pwd.setEchoMode(QLineEdit.Password)
        self.in_act.setPlaceholderText("�����ִ�Сд")
        self.show_info.setAlignment(Qt.AlignHCenter)
        self.loginButton.clicked.connect(self.login)
        self.registerButton.clicked.connect(self.register)


    def register(self):
        name = self.in_act.text().lower()
        pwd = self.in_pwd.text()
        if len(name) == 0 or len(pwd) == 0:
            self.show_info.setText('������Ϊ��')
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
                self.show_info.setAlignment(Qt.AlignHCenter)

    def login(self):
        name = self.in_act.text().lower()
        pwd = self.in_pwd.text()
        if len(name) == 0 or len(pwd) == 0:
            self.show_info.setText('������Ϊ��')
            self.show_info.setAlignment(Qt.AlignHCenter)
        else:
            request = ['__login', name, pwd, 0]
            received = datasend(request)
            if received[1] == 0:
                self.show_info.setText('login failed!')
                self.show_info.setAlignment(Qt.AlignHCenter)
            else:
                self.show_info.setText("login succeed!")
                self.show_info.setAlignment(Qt.AlignHCenter)
                self.loginButton.setVisible(False)
                self.registerButton.setVisible(False)
                mainwin.setVisible(False)
                self.subwin = SubWin(name)
                self.subwin.show()

class SubWin(QMainWindow):
    def __init__(self,name):
        super().__init__()
        uic.loadUi('sub_admin.ui',self)
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
        if self.req==1:#�������
            chargeamount=float(self.chargeamountline.text())
            chargemode=int(self.modeselectioncombo.currentIndex())
            data=['__SubmitRequest',{'chargeMode':chargemode,'requestCharge':chargeamount,'creatTime':time.time()},self.name]
            received=datasend(data)
            self.chargereqButton.setVisible(True)
            if received[1]==0:
                self.showinfo.setText('request failed!')
            else:
                billid=received[2]['Billid']
                pos=received[2]['NO']
                pile=received[2]['servingPile']
                self.showinfo.setText(f'BillId:{billid}\n�ŶӺ�:{pos}')
        elif self.req==2:#�ı�ģʽ
            data = ['__Changemode', self.name]
            received = datasend(data)
            if received[1] != 1:
                self.showinfo.setText('failed!')
            else:
                self.showinfo.setText('succeed!')
        elif self.req==3:#�ı����
            chargeamount = float(self.chargeamountline.text())
            data = ['__Changerequest', self.name, chargeamount]
            received = datasend(data)
            if received[1] != 1:
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
            f.write(str(received[1]))
    def chargemode(self):
        self.req=2
        self.confirmButton.setVisible(True)
        self.modeselectiontext.setVisible(True)
        self.modeselectioncombo.setVisible(True)
        self.backButton.setVisible(True)
    def stopcharging(self):
        data=['__StopCharge', self.name]
        received=datasend(data)
        if received[1]!=1:
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
        if data[1]!=0:
            self.showinfo.setText('detailed bill stored in charging.csv')
            with open('charging.csv','w')as f:
                f.write(str(received[2]))
        else:
            self.showinfo.setText('no charging bill')
    #def chargemode(self):


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainwin = MainWin()
    mainwin.show()
    sys.exit(app.exec_())
