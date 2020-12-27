from Design import *
from scapy.all import *
from pynput import keyboard
import os

class Client:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST and socket.SO_REUSEADDR, 1)
        self.sockUDP.bind(('', 13117))
        #self.ip = "192.168.1.175" - no need for that: the client can know the address of the server from the udp broadcast request

    def play(self):
        print("Client started, listening for offer requests...")
        #self.sockUDP.sendto(str.encode("a"),(self.ip,13117))
        broadcastMsg,serverAddr = self.sockUDP.recvfrom(4096)
        pck = None
        try:
            pck = struct.unpack('!IBH', broadcastMsg)
        except:
            print(fg.red + "Wrong message format!" + colors.reset)
            return
        if pck[0] == 0xfeedbeef and pck[1] == 0x2:
            print("Received offer from " + serverAddr[0] + ", attempting to connect...")
            self.sock.connect((serverAddr[0], pck[2]))    # pck[2] = server port over TCP connection
            #name = input("Please enter your group name:")
            #name = name + '\n'
            name = "It Burns When IP\n"
            try:
                self.sock.send(str.encode(name))
                welcomeMsg = self.sock.recv(2048)
                print(welcomeMsg.decode("utf-8"))
            except:
                print(fg.red + "Warning - Could not reach the server!" + colors.reset)
            oldtime = time.time()
            print(fg.purple + "Enter chars here: " + colors.reset, end="")
            try:
                listener = keyboard.Listener(on_press=self.on_press,)
                listener.start()  # start to listen on a separate thread
                #listener.join()
                while not self.ten_seconds_passed(oldtime):     # the client will enter chars for 10 seconds
                    x = 0
                listener.stop()
            except:
                print(fg.red + "Can't enter any more chars - the game is OVER!" + colors.reset)

    def on_press(self,key):
        try:
            k = key.char  # single-char keys
            self.sock.sendall(str.encode(k))
        except:
            return False


    def ten_seconds_passed(self,oldtime):
        return time.time() - oldtime >= 10

    def end_connection(self):
        try:
            finishMsg = self.sock.recv(1024)
            print(finishMsg.decode("utf-8"))
            print("Server disconnected, listening for offer requests...")
            self.sock.close()
        except:
            print(fg.red + "Warning - Could not reach the server!" + colors.reset)

    def client_action(self):
        self.play()
        self.end_connection()

if __name__ == "__main__":
    while True:
        c = Client()
        c.client_action()
