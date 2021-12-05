import server
import Pyro4
import socket as sk
import threading
import time

class Balancer():
    def __init__(self, hostname='localhost', port=25498, daemon_port=25499):
        
        print("Setting up load balancer")
        self.bal_socket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        self.bal_socket.bind((hostname, port))

        print("Setting up daemon in load balancer")
        self.daemon = Pyro4.Daemon(host=hostname, port=daemon_port)
        #"""Starts the daemon"""
        self.d_thread = threading.Thread(target=self.daemon.requestLoop)
        self.d_thread.daemon = True
        self.d_thread.start()


    def least_connections(self):
        if self.s1.clients<=self.s2.clients:
            return 'server1'
        else:
            return 'server2'


    def create_servers(self):
        self.server_info=[]
        self.s1=server.Server('localhost', 25500, 25501)
        self.server_info.append(('localhost', 25500))
        self.s2=server.Server('localhost', 25502, 25503)
        self.server_info.append(('localhost', 25502))
        self.s1.clients=0
        self.s2.clients=0


    def run_servers(self):
        self.s1.create_chat('Music Room 1')
        self.s1.create_chat('Music Room 2')
        self.s1.create_chat('Music Room 3')
        self.s1.run()

        self.s2.create_chat('Music Room 1')
        self.s2.create_chat('Music Room 2')
        self.s2.create_chat('Music Room 3')
        self.s2.run()



    def run(self):
        self.s_thread = threading.Thread(target=self._run)
        self.s_thread.daemon=True
        self.s_thread.start()


    def _run(self):
        print("Running load balancer")
        self.bal_socket.listen()

        while True:
            con, cliente = self.bal_socket.accept()
            serv=self.least_connections()

            server_ip=''
            server_port=''
            if serv=='server1':      
                server_ip=self.server_info[0][0]
                server_port=self.server_info[0][1]
                self.s1.clients=self.s1.clients+1
                print("client connected to server 1")
            else:
                server_ip=self.server_info[1][0]
                server_port=self.server_info[1][1]
                self.s2.clients=self.s2.clients+1
                print("client connected to server 2")

            
            con.send((server_ip +", "+ str(server_port)).encode())
            con.close()


if __name__=="__main__":
    balancer=Balancer()
    balancer.create_servers()
    balancer.run()
    balancer.run_servers()

    #keeping server alive
    while True:
        time.sleep(30)