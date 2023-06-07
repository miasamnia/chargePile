import sys
from socket import *
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit, QWidget
import json

# IP = '101.42.228.137'
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
                subwin.show()
                mainwin.setVisible(False)

class SubWin(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('subwindow.ui',self)
        self.chargemodeButton.setVisible(False)
        self.chargechangeButton.setVisible(False)
        self.stopchargingButton.setVisible(False)
        self.chargeamountline.setVisible(False)
        self.chargeamounttext.setVisible(False)
        self.modeselectiontext.setVisible(False)
        self.modeselectioncombo.setVisible(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainwin = MainWin()
    mainwin.show()
    subwin=SubWin()
    sys.exit(app.exec_())
