import socket
import pickle

class SocketComm:
    """Socket Communication"""
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket_o = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def send(self, data):
        self.socket_o.connect((self.host, self.port))
        data_b = pickle.dumps(data)
        self.socket_o.sendall(data_b)
        self.socket_o.close()
        
    def listen(self):
        self.socket_o.bind((self.host, self.port))
        self.socket_o.listen()
        connection, address = self.socket_o.accept()
        data_b = b''
        while True:
            data_i = connection.recv(1024)
            if not data_i:
                break
            data_b += data_i
        while True:
            try:
                data = pickle.loads(data_b)
                return data, address
            except: 
                return None, None

if __name__ == '__main__':
    from time import time
    skt = SocketComm('127.0.0.1', 65432)
    md = input('s/c:')
    if md == 's':
        stime = time()
        msg, addr = skt.listen()
        etime = time()
        print(msg, addr)
        print(list(msg))
        print(etime - stime)
    elif md == 'c':
        import random
        REP_N = 10000
        tag_l = [f'tag_{str(i).zfill(5)}' for i in range(REP_N)]
        val_l = [random.randint(0, 1000) for i in range(REP_N)]
        tot_l = zip(tag_l, val_l)
        tot_l = 'hello'
        skt.send(tot_l)