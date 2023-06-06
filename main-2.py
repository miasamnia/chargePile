import sys
from  socket import *
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow
import json


#DOMAIN = 'cher.中国'
#IP = getaddrinfo(DOMAIN, None)[0][4][0]
#IP = '101.42.228.137'
IP = '127.0.0.1'
SERVER_PORT = 56789
BUFLEN = 512
CDTIME = 60#匹配成功一次的cd

class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui.ui", self)
        self.show_info.setAlignment(Qt.AlignHCenter)
        self.regesterButton.clicked.connect(self.regester)

    def regester(self):
        name = self.in_act.text().lower()
        pwd = self.in_pwd.text()
        dataSocket = socket(AF_INET, SOCK_STREAM)
        dataSocket.connect((IP, SERVER_PORT))
        request = {
            'username': name,
            'password': pwd,
            'request': 'register',
        }
        data=json.dumps((request))
        #tosend = name + '|' + pwd + '|1'
        dataSocket.send(data.encode())

        received = dataSocket.recv(BUFLEN).decode()
        rec=json.loads(received)
        if rec['status'] == 'password or account wrong!':
            self.show_info.setText(received)
            self.show_info.setAlignment(Qt.AlignHCenter)
        else:
            self.show_info.setText("login succeed!")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainwin = MainWin()
    mainwin.show()

    sys.exit(app.exec_())
