from scapy.all import *
from Design import *

class Server:

    def __init__(self):
        self.sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sockUDP.bind(('', 0))
        self.sockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockTCP.setblocking(False)
        self.sockTCP.settimeout(10)  # stop looking for clients after 10 seconds
        self.ip = "0"
        self.broadcastIP = "0"
        self.port = 13117
        self.tcpPort = 2100
        self.ip_mode()
        self.sockTCP.bind((self.ip, self.tcpPort))
        #self.sockUDP.bind(('', 0))
        self.sockTCP.listen(250)
        self.group1 = []
        self.group2 = []
        self.clientsCounter = 0
        self.group1Score = 0
        self.group2Score = 0
        self.threadPool = []
        self.clientConnection = []
        self.charDict = {}  # bonus
        self.bestTeam = ([], -1)  # bonus
        self.lock = threading.Lock()

    def ip_mode(self):
        print("Is it grading mode?(y/n)")
        c = sys.stdin.read(1)
        if c.__eq__("y\n"):
            self.ip = get_if_addr("eth2")
            self.broadcastIP = self.calculate_broadcast_ip(self.ip)
        else:
            self.ip = get_if_addr('eth1')
            print(self.ip)
            #ip = socket.gethostbyname_ex(socket.gethostname())[-1]
            #self.ip = ip[len(ip) - 1]
            #self.ip = ip[0]
            self.broadcastIP = self.calculate_broadcast_ip(self.ip)
            print(self.broadcastIP)
            #self.broadcastIP = "255.255.255.255"

    def calculate_broadcast_ip(self, serverIP):
        broadcastIP = serverIP.split('.')
        broadcastIP[3] = '255'
        return '.'.join(broadcastIP)

    def talkToClient(self, clientName, connectionSocket):
        msg = self.create_client_start_msg()
        try:
            connectionSocket.send(str.encode(msg))
            oldtime = time.time()
            while not self.ten_seconds_passed(oldtime):
                char, clientAddr = connectionSocket.recvfrom(1024)
                char = char.decode("utf-8")
                self.increase_group_score(clientName)
                self.collect_chars(char)
        except ConnectionResetError:
            print(fg.red + "The client " + clientName + " disconnected" + colors.reset)
            return
        except:
            return

    def ten_seconds_passed(self, oldtime):
        return time.time() - oldtime >= 10

    def broadcastToClients(self):
        try:
            self.broadcastIP = "255.255.255.255"
            msg = struct.pack('!IBH', 0xfeedbeef, 0x2, self.tcpPort)
            self.sockUDP.sendto(msg, ('localhost', self.port))
            print(str(self.tcpPort) + " " + self.broadcastIP + " " + str(self.port))
            print(fg.pink + "sent broadcast" + colors.reset)
        except:
            print(fg.red + "Couldn't send a broadcast msg" + colors.reset)

    def create_client_start_msg(self):
        msg = "Welcome to Keyboard Spamming Battle Royal.\nGroup 1:\n==\n"
        for cName in self.group1:
            msg = msg + cName + "\n"
        msg = msg + "Group 2:\n==\n"
        for cName in self.group2:
            msg = msg + cName + "\n"
        msg = msg + "\nStart pressing keys on your keyboard as fast as you can!!"
        return msg

    def increase_group_score(self, clientName):
        for name in self.group1:
            if name == clientName:
                with self.lock:
                    self.group1Score = self.group1Score + 1
                return
        for name in self.group2:
            if name == clientName:
                with self.lock:
                    self.group2Score = self.group2Score + 1
                return

    def collect_chars(self, char):
        if len(str(char)) > 1:
            return
        self.lock.acquire()
        if char in self.charDict:
            oldCount = self.charDict[char]
            self.charDict[char] = oldCount + 1
        elif char == '':
             return
        else:
            self.charDict[char] = 1
        self.lock.release()

    def run_game(self):
        for t in self.threadPool:
            t.start()
        for t in self.threadPool:
            t.join(10)  # wait for the clients to finish the game - 10 seconds

        winner = "Group 1"
        group = self.group1
        if self.group2Score > self.group1Score:
            winner = "Group 2"
            group = self.group2
        msg = "Game over!\nGroup 1 typed in " + str(self.group1Score) + "  characters. Group 2 typed in "
        msg = msg + str(self.group2Score) + "  characters.\n" + winner + " wins!\n\nCongratulations to the winners:\n"
        msg = msg + "==\n" + '\n'.join(group)
        for conn in self.clientConnection:
            try:
                conn.send(str.encode(msg))
            except:
                print(fg.red + "Some client disconnected..." + colors.reset)
        return winner

    def check_best_team(self, winner):
        if winner == "Group 1":
            if self.bestTeam[1] < self.group1Score:
                self.bestTeam = (self.group1, self.group1Score)
        else:
            if self.bestTeam[1] < self.group2Score:
                self.bestTeam = (self.group2, self.group2Score)

    def clear_data(self):
        self.group1 = []
        self.group2 = []
        self.clientsCounter = 0
        self.group1Score = 0
        self.group2Score = 0
        self.threadPool = []
        self.clientConnection = []
        self.charDict = {}

    def show_statistics(self):
        commChar = ""
        max = 0
        for c in self.charDict:
            if self.charDict[c] > max:
                commChar = c
                max = self.charDict[c]
        print(fg.orange + colors.bold + colors.underline + "And here some statistics: " + colors.reset)
        print(colors.bold + "The most commonly typed character is: " + commChar + " and it was typed: "
              + str(max) + " times" + colors.reset,
              end="\n")
        print(colors.bold + "Currently the best team is: " + colors.underline + ','.join(self.bestTeam[0]) + colors.reset)

    def listen_clients(self):
        while True:
            #m, firstClientAddr = self.sockUDP.recvfrom(2048)
            oldtime = time.time()
            timer = None
            while not (self.ten_seconds_passed(oldtime)):
                try:
                    timer = threading.Timer(1, self.broadcastToClients)  # sending broadcast msg every second
                    timer.daemon = True
                    timer.start()
                    connectionSocket, addr = self.sockTCP.accept()
                    clientName, clientAddr = connectionSocket.recvfrom(1024)
                    clientName = clientName.decode("utf-8")  # turns bytes to string
                    if self.clientsCounter % 2 == 0:
                        self.group1.append(clientName)
                    else:
                        self.group2.append(clientName)
                    self.clientsCounter = self.clientsCounter + 1
                    self.clientConnection.append(connectionSocket)
                    t = threading.Thread(target=self.talkToClient, args=(clientName, connectionSocket,))
                    self.threadPool.append(t)
                except:
                    print(fg.darkgrey + "10 seconds has passed - the game shall begin!" + colors.reset)
            timer.cancel()  # after 10 seconds the game need to start - no more broadcast msg
            winner = self.run_game()
            self.check_best_team(winner)
            print("Game over, sending out offer requests...")
            self.show_statistics()
            self.clear_data()


if __name__ == '__main__':
    b = Server()
    print('Initializing Server')
    b.listen_clients()
