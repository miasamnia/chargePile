# chargePile
再说一下程序运行的逻辑吧，用户点击按钮，会调用对应的函数（大伙写的 ），可能有输入类似于 name = self.in_act.text().lower()，
要表达的信息用self.show_info.setText("login succeed!")，
要传递信息用
IP = '127.0.0.1'\n
SERVER_PORT = 56789
BUFLEN = 512
dataSocket = socket(AF_INET, SOCK_STREAM)
dataSocket.connect((IP, SERVER_PORT)
dataSocket.send(data.encode())
接收received = dataSocket.recv(BUFLEN).decode()
